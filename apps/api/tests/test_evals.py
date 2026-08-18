"""Unit and integration tests for the OpsPilot Evaluation Harness."""

from __future__ import annotations

from pathlib import Path
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.evals.dataset import load_eval_cases
from app.evals.models import EvalCase, EvalCategory
from app.evals.run import run_evaluations
from app.evals.scorer import (
    aggregate_results,
    calculate_point_coverage,
    calculate_retrieval_hit,
    calculate_tool_selection,
    detect_decline,
    score_case,
)
from app.models.document import Document, DocumentChunk, DocumentKind
from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.models.service import Service, ServiceStatus
from app.models.user import User, UserRole, UserStatus
from app.rag.embeddings import EmbeddingsProvider, set_embeddings_provider
from tests.conftest import _session_factory


class MockEvalsEmbeddings(EmbeddingsProvider):
    """Deterministic embeddings for eval unit tests."""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0] + [0.0] * 767 for _ in texts]

    async def embed_query(self, text: str) -> list[float]:
        return [1.0] + [0.0] * 767


@pytest.fixture(autouse=True)
def _setup_eval_embeddings() -> None:
    set_embeddings_provider(MockEvalsEmbeddings())


# ── Scorer Unit Tests ────────────────────────────────────────


def test_retrieval_hit_calculation() -> None:
    """Test retrieval hit rate (recall) calculation on cited sources."""
    must_cite = ["Payment Gateway Fallback", "Database Backup Runbook"]

    # Perfect recall (exact or substring)
    assert calculate_retrieval_hit(
        ["Payment Processing Gateway Fallback and Retry Policy", "Database Backup Runbook"],
        must_cite,
    ) == 1.0

    # 50% recall
    assert calculate_retrieval_hit(
        ["Payment Processing Gateway Fallback and Retry Policy"],
        must_cite,
    ) == 0.5

    # 0% recall
    assert calculate_retrieval_hit(["Elasticsearch Cluster Recovery"], must_cite) == 0.0

    # Empty must_cite defaults to 1.0
    assert calculate_retrieval_hit([], []) == 1.0


def test_tool_selection_calculation() -> None:
    """Test tool selection precision and recall scoring."""
    expected = ["query_services", "retrieve_docs"]

    # Perfect match
    assert calculate_tool_selection(["query_services", "retrieve_docs"], expected) == 1.0
    assert calculate_tool_selection(["query_services", "retrieve_docs", "get_service_detail"], expected) == 1.0

    # Partial match
    assert calculate_tool_selection(["query_services"], expected) == 0.5

    # Zero match
    assert calculate_tool_selection(["query_users"], expected) == 0.0

    # Empty expected tools (e.g. out of scope)
    assert calculate_tool_selection([], []) == 1.0
    assert calculate_tool_selection(["query_services"], []) == 0.5


def test_point_coverage_calculation() -> None:
    """Test deterministic factual point coverage logic."""
    expected = ["10%", "4,000ms", "secondary gateway", "circuit breaker"]

    answer_full = "The circuit breaker opens when error rate exceeds 10% or latency exceeds 4,000ms, routing to the secondary gateway."
    assert calculate_point_coverage(answer_full, expected) == 1.0

    answer_partial = "The error rate threshold is 10% and it switches to the secondary gateway."
    assert calculate_point_coverage(answer_partial, expected) == 0.5

    answer_none = "I have no information regarding payment gateways."
    assert calculate_point_coverage(answer_none, expected) == 0.0

    # Empty points
    assert calculate_point_coverage("Any answer", []) == 1.0


def test_decline_detection() -> None:
    """Test decline detection for out-of-scope safety guardrails."""
    assert detect_decline("I don't have enough information in the system or knowledge base to answer that.")
    assert detect_decline("This query is out of scope.")
    assert detect_decline("I am unable to answer this question.")
    assert not detect_decline("The payment service is currently healthy with 99.9% uptime.")


def test_score_case_kb_pass_and_fail() -> None:
    """Test case scoring for KB runbook cases."""
    case = EvalCase(
        id="test-kb",
        question="How does gateway failover work?",
        category=EvalCategory.KB,
        must_cite=["Payment Gateway Fallback"],
        expected_tools=["retrieve_docs"],
        expected_points=["secondary gateway", "circuit breaker"],
        should_decline=False,
    )

    # Passing case
    passing = score_case(
        case=case,
        actual_answer="When the circuit breaker opens, traffic routes to secondary gateway.",
        cited_sources=["Payment Gateway Fallback"],
        invoked_tools=["retrieve_docs"],
        latency_ms=120.0,
    )
    assert passing.passed
    assert passing.retrieval_hit == 1.0
    assert passing.point_coverage == 1.0
    assert not passing.failure_reasons

    # Failing case missing citations
    failing = score_case(
        case=case,
        actual_answer="When the circuit breaker opens, traffic routes to secondary gateway.",
        cited_sources=[],
        invoked_tools=["retrieve_docs"],
        latency_ms=120.0,
    )
    assert not failing.passed
    assert failing.retrieval_hit == 0.0
    assert any("Missing required citations" in r for r in failing.failure_reasons)


def test_score_case_out_of_scope() -> None:
    """Test case scoring for out-of-scope refusals."""
    case = EvalCase(
        id="test-oos",
        question="What is the CEO's home address?",
        category=EvalCategory.OUT_OF_SCOPE,
        expected_points=["don't have enough information"],
        should_decline=True,
    )

    # Properly declined
    declined_res = score_case(
        case=case,
        actual_answer="I don't have enough information in the system or knowledge base to answer that.",
        cited_sources=[],
        invoked_tools=[],
        latency_ms=50.0,
    )
    assert declined_res.passed
    assert declined_res.declined

    # Hallucinated / not declined
    hallucinated_res = score_case(
        case=case,
        actual_answer="The CEO lives at 123 Main Street.",
        cited_sources=[],
        invoked_tools=[],
        latency_ms=50.0,
    )
    assert not hallucinated_res.passed
    assert not hallucinated_res.declined
    assert any("hallucination risk" in r for r in hallucinated_res.failure_reasons)


def test_aggregation_and_threshold_gating() -> None:
    """Test aggregation calculation and pass/fail gate checking."""
    case = EvalCase(
        id="c1",
        question="q",
        category=EvalCategory.SERVICES,
        expected_points=["healthy"],
        expected_tools=["query_services"],
    )

    pass_result = score_case(
        case=case,
        actual_answer="The service is healthy.",
        cited_sources=[],
        invoked_tools=["query_services"],
        latency_ms=100.0,
    )

    fail_result = score_case(
        case=case,
        actual_answer="Something else.",
        cited_sources=[],
        invoked_tools=[],
        latency_ms=100.0,
    )

    # 1 pass, 1 fail = 50% pass rate
    report_fail = aggregate_results([pass_result, fail_result], threshold=0.80)
    assert report_fail.pass_rate == 0.5
    assert not report_fail.overall_passed

    # 1 pass, 0 fail = 100% pass rate
    report_pass = aggregate_results([pass_result], threshold=0.80)
    assert report_pass.pass_rate == 1.0
    assert report_pass.overall_passed


def test_dataset_loader() -> None:
    """Test loading golden evaluation cases from JSON dataset."""
    all_cases = load_eval_cases()
    assert len(all_cases) >= 25

    kb_cases = load_eval_cases(category=EvalCategory.KB)
    assert len(kb_cases) >= 5
    assert all(c.category == EvalCategory.KB for c in kb_cases)


@pytest.mark.asyncio
async def test_offline_eval_runner_end_to_end(tmp_path: Path) -> None:
    """Run full evaluation suite offline end-to-end and assert report generation."""
    report_dir = tmp_path / "eval_reports"

    report = await run_evaluations(
        offline=True,
        threshold=0.80,
        report_dir=report_dir,
        session_factory=_session_factory,
    )

    assert report.total_cases >= 25
    assert report.passed_cases >= 20
    assert report.pass_rate >= 0.80
    assert report.overall_passed
    assert report.retrieval_hit_rate >= 0.90
    assert report.tool_accuracy >= 0.90
    assert report.decline_accuracy == 1.0

    # Assert report files were written
    latest_md = report_dir / "latest.md"
    latest_json = report_dir / "latest.json"
    assert latest_md.exists()
    assert latest_json.exists()
    assert "# OpsPilot RAG & Agent Evaluation Report" in latest_md.read_text()
