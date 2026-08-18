"""Scorer for evaluating RAG retrieval hit-rate, tool selection, answer quality, and grounding."""

from __future__ import annotations

import datetime
import json
import logging
import re

import httpx

from app.evals.models import (
    AggregateReport,
    CaseResult,
    CategorySummary,
    EvalCase,
    EvalCategory,
)

logger = logging.getLogger(__name__)

DECLINE_PHRASES = [
    "don't have enough information",
    "do not have enough information",
    "not enough information",
    "out of scope",
    "cannot answer",
    "unable to answer",
    "no information",
    "not found in the knowledge base",
    "not found in system records",
]


def _normalize(text: str) -> str:
    """Normalize string for fuzzy substring matching."""
    return re.sub(r"\s+", " ", text.lower().strip())


def calculate_retrieval_hit(cited_sources: list[str], must_cite: list[str]) -> float:
    """Calculate recall of must_cite sources against actual cited document titles."""
    if not must_cite:
        return 1.0

    if not cited_sources:
        return 0.0

    normalized_citations = [_normalize(c) for c in cited_sources]
    hits = 0

    for required in must_cite:
        norm_req = _normalize(required)
        # 1. Direct substring match
        found = any(
            norm_req in cited or cited in norm_req for cited in normalized_citations
        )
        # 2. Token overlap match (all keywords with len > 3 present in cited doc title)
        if not found:
            req_words = [w for w in norm_req.split() if len(w) > 3]
            if req_words:
                found = any(
                    all(w in cited for w in req_words) for cited in normalized_citations
                )

        if found:
            hits += 1

    return hits / len(must_cite)


def calculate_tool_selection(
    invoked_tools: list[str], expected_tools: list[str]
) -> float:
    """Calculate recall of expected tools against actual invoked tools."""
    if not expected_tools:
        # If no tools were expected (e.g. out of scope)
        return 1.0 if not invoked_tools else 0.5

    if not invoked_tools:
        return 0.0

    expected_set = set(expected_tools)
    invoked_set = set(invoked_tools)

    intersection = expected_set.intersection(invoked_set)
    return len(intersection) / len(expected_set)


def calculate_point_coverage(answer: str, expected_points: list[str]) -> float:
    """Calculate deterministic keyword/phrase point coverage in answer."""
    if not expected_points:
        return 1.0

    if not answer:
        return 0.0

    norm_answer = _normalize(answer)
    hits = 0

    for point in expected_points:
        norm_point = _normalize(point)
        # Check direct substring
        if norm_point in norm_answer:
            hits += 1
            continue

        # Check individual tokens if multi-word phrase
        tokens = [t for t in norm_point.split() if len(t) > 2]
        if tokens and all(t in norm_answer for t in tokens):
            hits += 1

    return hits / len(expected_points)


def detect_decline(answer: str) -> bool:
    """Detect whether the agent correctly declined to answer an out-of-scope query."""
    norm_answer = _normalize(answer)
    return any(phrase in norm_answer for phrase in DECLINE_PHRASES)


async def evaluate_with_llm_judge(
    question: str,
    answer: str,
    expected_points: list[str],
    api_key: str,
    model_name: str = "gemini-1.5-flash",
) -> float | None:
    """Evaluate factual answer completeness using Gemini as an LLM judge (1.0 to 5.0 scale)."""
    if not api_key or not expected_points:
        return None

    prompt = f"""You are an expert impartial judge evaluating the quality and factual correctness of an AI assistant's answer for Site Reliability Engineering (SRE) operations.

QUESTION:
{question}

EXPECTED KEY FACTS:
{json.dumps(expected_points, indent=2)}

ACTUAL AI ANSWER:
{answer}

Evaluate whether the actual answer accurately and factually covers the expected key facts.
Rate the answer on a scale from 1.0 to 5.0:
- 5.0: Fully complete, accurate, grounded, with no missing facts.
- 4.0: Mostly complete, accurate, misses minor nuance.
- 3.0: Partially complete, covers main idea but misses key points.
- 2.0: Major factual omissions or slight inaccuracies.
- 1.0: Completely irrelevant, hallucinated, or ungrounded.

Respond ONLY with a JSON object in this exact format:
{{"score": 4.5, "reason": "brief explanation"}}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json",
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)
                return float(parsed.get("score", 3.0))
    except Exception as e:
        logger.warning("LLM judge evaluation failed: %s", e)

    return None


def score_case(
    case: EvalCase,
    actual_answer: str,
    cited_sources: list[str],
    invoked_tools: list[str],
    latency_ms: float,
    llm_judge_score: float | None = None,
) -> CaseResult:
    """Score a single evaluation case against ground truth."""
    retrieval_hit = calculate_retrieval_hit(cited_sources, case.must_cite)
    tool_selection = calculate_tool_selection(invoked_tools, case.expected_tools)
    point_coverage = calculate_point_coverage(actual_answer, case.expected_points)
    declined = detect_decline(actual_answer)

    failure_reasons: list[str] = []

    if case.should_decline:
        passed = declined
        if not declined:
            failure_reasons.append(
                "Agent failed to decline an out-of-scope query (hallucination risk)"
            )
    elif case.category == EvalCategory.KB:
        passed = retrieval_hit >= 1.0 and point_coverage >= 0.70
        if retrieval_hit < 1.0:
            failure_reasons.append(
                f"Missing required citations: expected {case.must_cite}, got {cited_sources}"
            )
        if point_coverage < 0.70:
            failure_reasons.append(
                f"Low point coverage ({point_coverage:.1%}): missing key facts"
            )
    elif case.category == EvalCategory.MULTI_TOOL:
        passed = (
            tool_selection >= 1.0 and retrieval_hit >= 1.0 and point_coverage >= 0.60
        )
        if tool_selection < 1.0:
            failure_reasons.append(
                f"Missing required tools: expected {case.expected_tools}, got {invoked_tools}"
            )
        if retrieval_hit < 1.0:
            failure_reasons.append(
                f"Missing required citations: expected {case.must_cite}, got {cited_sources}"
            )
        if point_coverage < 0.60:
            failure_reasons.append(
                f"Low point coverage ({point_coverage:.1%}) in multi-tool synthesis"
            )
    else:  # Services, Incidents, Users
        passed = tool_selection >= 1.0 and point_coverage >= 0.60
        if tool_selection < 1.0:
            failure_reasons.append(
                f"Missing expected tools: expected {case.expected_tools}, got {invoked_tools}"
            )
        if point_coverage < 0.60:
            failure_reasons.append(
                f"Low point coverage ({point_coverage:.1%}) in database answer"
            )

    return CaseResult(
        case_id=case.id,
        category=case.category,
        question=case.question,
        passed=passed,
        retrieval_hit=retrieval_hit,
        tool_selection=tool_selection,
        point_coverage=point_coverage,
        llm_judge_score=llm_judge_score,
        declined=declined,
        latency_ms=latency_ms,
        invoked_tools=invoked_tools,
        cited_sources=cited_sources,
        actual_answer=actual_answer,
        failure_reasons=failure_reasons,
    )


def aggregate_results(
    results: list[CaseResult],
    threshold: float,
    mode: str = "offline",
) -> AggregateReport:
    """Aggregate individual case results into an evaluation report."""
    total_cases = len(results)
    passed_cases = sum(1 for r in results if r.passed)
    pass_rate = (passed_cases / total_cases) if total_cases > 0 else 0.0

    kb_cases = [
        r for r in results if r.category in (EvalCategory.KB, EvalCategory.MULTI_TOOL)
    ]
    retrieval_hit_rate = (
        sum(r.retrieval_hit for r in kb_cases) / len(kb_cases) if kb_cases else 1.0
    )

    tool_cases = [
        r
        for r in results
        if r.category
        in (
            EvalCategory.SERVICES,
            EvalCategory.INCIDENTS,
            EvalCategory.USERS,
            EvalCategory.MULTI_TOOL,
        )
    ]
    tool_accuracy = (
        sum(r.tool_selection for r in tool_cases) / len(tool_cases)
        if tool_cases
        else 1.0
    )

    decline_cases = [r for r in results if r.category == EvalCategory.OUT_OF_SCOPE]
    decline_accuracy = (
        sum(1.0 if r.declined else 0.0 for r in decline_cases) / len(decline_cases)
        if decline_cases
        else 1.0
    )

    avg_latency_ms = (
        sum(r.latency_ms for r in results) / total_cases if total_cases > 0 else 0.0
    )

    # Breakdown by category
    by_category: dict[str, CategorySummary] = {}
    for cat in EvalCategory:
        cat_cases = [r for r in results if r.category == cat]
        if not cat_cases:
            continue
        c_passed = sum(1 for r in cat_cases if r.passed)
        by_category[cat.value] = CategorySummary(
            total_cases=len(cat_cases),
            passed_cases=c_passed,
            pass_rate=c_passed / len(cat_cases),
            avg_point_coverage=sum(r.point_coverage for r in cat_cases)
            / len(cat_cases),
            avg_retrieval_hit=sum(r.retrieval_hit for r in cat_cases) / len(cat_cases),
            avg_tool_accuracy=sum(r.tool_selection for r in cat_cases) / len(cat_cases),
            avg_latency_ms=sum(r.latency_ms for r in cat_cases) / len(cat_cases),
        )

    return AggregateReport(
        timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
        mode=mode,
        threshold=threshold,
        total_cases=total_cases,
        passed_cases=passed_cases,
        pass_rate=round(pass_rate, 4),
        overall_passed=pass_rate >= threshold,
        retrieval_hit_rate=round(retrieval_hit_rate, 4),
        tool_accuracy=round(tool_accuracy, 4),
        decline_accuracy=round(decline_accuracy, 4),
        avg_latency_ms=round(avg_latency_ms, 2),
        by_category=by_category,
        results=results,
    )
