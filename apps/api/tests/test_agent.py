"""Tests for LangGraph ReAct agent tools, graph execution, and step streaming."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest

from app.agent.graph import AgentRunner, set_agent_llm_handler
from app.agent.tools import (
    execute_tool,
)
from app.models.document import Document, DocumentChunk, DocumentKind
from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.models.service import Service, ServiceStatus
from app.models.user import User, UserRole, UserStatus
from app.rag.embeddings import EmbeddingsProvider, set_embeddings_provider
from app.rag.retriever import Retriever
from tests.conftest import _session_factory


class MockAgentEmbeddings(EmbeddingsProvider):
    """Deterministic embeddings for agent tests."""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0] + [0.0] * 767 for _ in texts]

    async def embed_query(self, text: str) -> list[float]:
        return [1.0] + [0.0] * 767


@pytest.fixture(autouse=True)
def _setup_agent_providers() -> None:
    set_embeddings_provider(MockAgentEmbeddings())
    set_agent_llm_handler(None)


@pytest.fixture
async def seed_agent_data() -> None:
    """Seed test user, services, incidents, and KB docs."""
    async with _session_factory() as session:
        # User
        user = User(
            id=uuid.uuid4(),
            email="sre_lead@test.com",
            password_hash="hash",
            name="Alex SRE",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )
        session.add(user)
        await session.flush()

        # Services
        s1 = Service(
            id=uuid.uuid4(),
            name="Payment Gateway",
            status=ServiceStatus.DEGRADED,
            uptime_pct=98.7,
            owner_user_id=user.id,
            note="Experiencing elevated p99 latency",
        )
        s2 = Service(
            id=uuid.uuid4(),
            name="Auth Service",
            status=ServiceStatus.HEALTHY,
            uptime_pct=99.99,
            owner_user_id=user.id,
            note="Operating normally",
        )
        session.add_all([s1, s2])
        await session.flush()

        # Incidents
        inc1 = Incident(
            id=uuid.uuid4(),
            title="Payment gateway connection timeout",
            severity=IncidentSeverity.SEV1,
            status=IncidentStatus.OPEN,
            service_id=s1.id,
            assignee_id=user.id,
        )
        session.add(inc1)

        # Knowledge Base Doc
        doc = Document(
            id=uuid.uuid4(),
            title="Payment Gateway Runbook",
            source="seed/kb/payment_runbook.md",
            kind=DocumentKind.RUNBOOK,
        )
        session.add(doc)
        await session.flush()

        chunk = DocumentChunk(
            id=uuid.uuid4(),
            document_id=doc.id,
            ordinal=0,
            content="To mitigate Payment Gateway latency: restart pods, enable rate limiting, and check downstream PSP.",
            token_count=20,
            embedding=[1.0] + [0.0] * 767,
        )
        session.add(chunk)
        await session.commit()


@pytest.mark.asyncio
async def test_tool_execute_query_services(seed_agent_data: None) -> None:
    """query_services tool lists live service statuses."""
    async with _session_factory() as session:
        res, summary = await execute_tool(
            "query_services", {"status": "degraded"}, session
        )
        assert res["count"] == 1
        assert res["services"][0]["name"] == "Payment Gateway"
        assert res["services"][0]["status"] == "degraded"
        assert "Retrieved 1 live service status" in summary


@pytest.mark.asyncio
async def test_tool_execute_query_incidents(seed_agent_data: None) -> None:
    """query_incidents tool lists active incidents with filters."""
    async with _session_factory() as session:
        res, summary = await execute_tool(
            "query_incidents", {"severity": "sev1", "status": "open"}, session
        )
        assert res["total_count"] == 1
        assert res["incidents"][0]["title"] == "Payment gateway connection timeout"
        assert res["incidents"][0]["severity"] == "sev1"


@pytest.mark.asyncio
async def test_tool_execute_get_service_detail(seed_agent_data: None) -> None:
    """get_service_detail returns service health and open incident count."""
    async with _session_factory() as session:
        res, summary = await execute_tool(
            "get_service_detail", {"name_or_id": "Payment Gateway"}, session
        )
        assert res["name"] == "Payment Gateway"
        assert res["status"] == "degraded"
        assert res["open_incidents"] == 1


@pytest.mark.asyncio
async def test_tool_execute_retrieve_docs(seed_agent_data: None) -> None:
    """retrieve_docs retrieves knowledge base chunks."""
    async with _session_factory() as session:
        retriever = Retriever(top_k=4)
        res, summary = await execute_tool(
            "retrieve_docs", {"query": "Payment Gateway Runbook"}, session, retriever
        )
        assert res["count"] > 0
        assert res["chunks"][0]["document_title"] == "Payment Gateway Runbook"


@pytest.mark.asyncio
async def test_agent_runner_incident_question(seed_agent_data: None) -> None:
    """Agent emits tool_call and tool_result steps and synthesizes answer."""

    async def mock_incident_handler(
        question: str, **kwargs: Any
    ) -> AsyncGenerator[dict[str, Any], None]:
        # Step 1: Tool call
        yield {
            "event": "step",
            "data": {
                "type": "tool_call",
                "tool": "query_incidents",
                "args": {"severity": "sev1", "status": "open"},
            },
        }
        # Step 2: Tool result
        res, summary = await execute_tool(
            "query_incidents", {"severity": "sev1", "status": "open"}, kwargs["session"]
        )
        yield {
            "event": "step",
            "data": {
                "type": "tool_result",
                "tool": "query_incidents",
                "summary": summary,
            },
        }
        # Step 3: Stream final tokens
        yield {
            "event": "token",
            "data": {
                "text": "There is currently 1 open SEV-1 incident: Payment gateway connection timeout."
            },
        }
        yield {
            "event": "agent_done",
            "data": {
                "final_answer": "There is currently 1 open SEV-1 incident: Payment gateway connection timeout.",
                "citations": [],
                "steps": [
                    {
                        "type": "tool_call",
                        "tool": "query_incidents",
                        "args": {"severity": "sev1", "status": "open"},
                    },
                    {
                        "type": "tool_result",
                        "tool": "query_incidents",
                        "summary": summary,
                    },
                ],
            },
        }

    set_agent_llm_handler(mock_incident_handler)

    async with _session_factory() as session:
        runner = AgentRunner(session=session)
        events = []
        async for evt in runner.run_stream("How many sev1 incidents are open?"):
            events.append(evt)

        event_names = [e["event"] for e in events]
        assert "step" in event_names
        assert "token" in event_names
        assert "agent_done" in event_names

        step_events = [e["data"] for e in events if e["event"] == "step"]
        assert step_events[0]["type"] == "tool_call"
        assert step_events[0]["tool"] == "query_incidents"
        assert step_events[1]["type"] == "tool_result"


@pytest.mark.asyncio
async def test_agent_runner_multi_tool_chaining(seed_agent_data: None) -> None:
    """Agent chains query_services then retrieve_docs and attaches citations."""

    async def mock_multitool_handler(
        question: str, **kwargs: Any
    ) -> AsyncGenerator[dict[str, Any], None]:
        # Step 1: query_services
        yield {
            "event": "step",
            "data": {
                "type": "tool_call",
                "tool": "query_services",
                "args": {"status": "degraded"},
            },
        }
        yield {
            "event": "step",
            "data": {
                "type": "tool_result",
                "tool": "query_services",
                "summary": "Found 1 degraded service",
            },
        }
        # Step 2: retrieve_docs
        yield {
            "event": "step",
            "data": {
                "type": "tool_call",
                "tool": "retrieve_docs",
                "args": {"query": "Payment Gateway Runbook"},
            },
        }
        yield {
            "event": "step",
            "data": {
                "type": "tool_result",
                "tool": "retrieve_docs",
                "summary": "Found 1 runbook",
            },
        }
        yield {
            "event": "citations",
            "data": {
                "citations": [
                    {
                        "document_title": "Payment Gateway Runbook",
                        "ordinal": 0,
                        "snippet": "restart pods",
                        "score": 0.9,
                    }
                ],
                "used_context": True,
            },
        }
        yield {
            "event": "token",
            "data": {
                "text": "Payment Gateway is degraded. Follow Payment Gateway Runbook to restart pods."
            },
        }
        yield {
            "event": "agent_done",
            "data": {
                "final_answer": "Payment Gateway is degraded. Follow Payment Gateway Runbook to restart pods.",
                "citations": [
                    {
                        "document_title": "Payment Gateway Runbook",
                        "ordinal": 0,
                        "snippet": "restart pods",
                        "score": 0.9,
                    }
                ],
                "steps": [],
            },
        }

    set_agent_llm_handler(mock_multitool_handler)

    async with _session_factory() as session:
        runner = AgentRunner(session=session)
        events = []
        async for evt in runner.run_stream(
            "Which services are degraded and what's the runbook?"
        ):
            events.append(evt)

        event_names = [e["event"] for e in events]
        assert event_names.count("step") == 4
        assert "citations" in event_names
        assert "token" in event_names
        assert "agent_done" in event_names
