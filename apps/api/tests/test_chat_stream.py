from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import set_agent_llm_handler
from app.models.chat import MessageRole
from app.models.document import Document, DocumentChunk, DocumentKind
from app.rag.embeddings import EmbeddingsProvider, set_embeddings_provider
from app.repositories.chat_repo import ChatRepository
from tests.conftest import _session_factory


class MockStreamEmbeddings(EmbeddingsProvider):
    """Deterministic mock embeddings for streaming tests."""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        res = []
        for t in texts:
            if "sla" in t.lower() or "availability" in t.lower():
                res.append([1.0] + [0.0] * 767)
            else:
                res.append([0.0, 1.0] + [0.0] * 766)
        return res

    async def embed_query(self, text: str) -> list[float]:
        if "sla" in text.lower() or "availability" in text.lower():
            return [1.0] + [0.0] * 767
        return [0.0] * 10 + [1.0] + [0.0] * 757


last_agent_prompt: str = ""


async def mock_agent_stream_handler(
    question: str,
    conversation_history: list[tuple[str, str]] | None = None,
    session: AsyncSession | None = None,
    retriever: Any = None,
) -> AsyncGenerator[dict[str, Any], None]:
    global last_agent_prompt
    history_lines = []
    if conversation_history:
        for r, c in conversation_history:
            history_lines.append(f"{r}: {c}")
    last_agent_prompt = (
        "Prior History: " + "\n".join(history_lines) + f" | Question: {question}"
    )

    if "tokyo" in question.lower():
        # Decline out of KB
        yield {"event": "citations", "data": {"citations": [], "used_context": False}}
        yield {
            "event": "token",
            "data": {"text": "I don't have that in the knowledge base."},
        }
        yield {
            "event": "agent_done",
            "data": {
                "final_answer": "I don't have that in the knowledge base.",
                "citations": [],
                "steps": [],
            },
        }
    else:
        yield {
            "event": "citations",
            "data": {
                "citations": [
                    {
                        "document_title": "Service Level Agreements",
                        "ordinal": 0,
                        "snippet": "API Gateway availability SLA is 99.98%.",
                        "score": 0.95,
                    }
                ],
                "used_context": True,
            },
        }
        tokens = ["The ", "API ", "Gateway ", "SLA ", "is ", "99.98%."]
        for t in tokens:
            yield {"event": "token", "data": {"text": t}}
        yield {
            "event": "agent_done",
            "data": {
                "final_answer": "The API Gateway SLA is 99.98%.",
                "citations": [
                    {
                        "document_title": "Service Level Agreements",
                        "ordinal": 0,
                        "snippet": "API Gateway availability SLA is 99.98%.",
                        "score": 0.95,
                    }
                ],
                "steps": [],
            },
        }


@pytest.fixture(autouse=True)
def _setup_stream_providers() -> None:
    set_embeddings_provider(MockStreamEmbeddings())
    set_agent_llm_handler(mock_agent_stream_handler)


@pytest.fixture
async def auth_user_token(client: AsyncClient) -> str:
    """Register and return token for streaming tests."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "stream_user@test.com",
            "password": "securepassword",
            "name": "Stream User",
        },
    )
    assert resp.status_code == 201
    return resp.json()["tokens"]["access_token"]


@pytest.fixture
async def seed_sla_chunk() -> None:
    """Insert SLA test document."""
    async with _session_factory() as session:
        doc = Document(
            id=uuid.uuid4(),
            title="Service Level Agreements",
            source="seed/kb/service_slas.md",
            kind=DocumentKind.SLA,
        )
        session.add(doc)
        await session.flush()

        chunk = DocumentChunk(
            id=uuid.uuid4(),
            document_id=doc.id,
            ordinal=0,
            content="API Gateway availability SLA is 99.98%. Auth Service SLA is 99.95%.",
            token_count=16,
            embedding=[1.0] + [0.0] * 767,
        )
        session.add(chunk)
        await session.commit()


def parse_sse_events(raw_text: str) -> list[tuple[str, dict]]:
    """Helper to parse raw SSE text into list of (event_type, data_json)."""
    events: list[tuple[str, dict]] = []
    blocks = raw_text.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        event_name = "message"
        data_str = "{}"
        for line in lines:
            if line.startswith("event: "):
                event_name = line[7:].strip()
            elif line.startswith("data: "):
                data_str = line[6:].strip()
        try:
            events.append((event_name, json.loads(data_str)))
        except json.JSONDecodeError:
            events.append((event_name, {"raw": data_str}))
    return events


@pytest.mark.asyncio
async def test_stream_chat_unauthenticated(client: AsyncClient) -> None:
    """Unauthenticated request returns 401."""
    resp = await client.post(
        "/api/v1/chat/stream", json={"question": "What is the SLA?"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_stream_chat_creates_session_and_messages(
    client: AsyncClient,
    auth_user_token: str,
    seed_sla_chunk: None,
) -> None:
    """Stream endpoint emits citations, token, done events and persists user & assistant messages."""
    resp = await client.post(
        "/api/v1/chat/stream",
        json={"question": "What are our service availability SLAs?"},
        headers={"Authorization": f"Bearer {auth_user_token}"},
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]

    events = parse_sse_events(resp.text)
    event_names = [e[0] for e in events]

    assert "citations" in event_names
    assert "token" in event_names
    assert "done" in event_names

    # Check citations event
    citations_event = next(e for e in events if e[0] == "citations")
    assert citations_event[1]["used_context"] is True
    assert len(citations_event[1]["citations"]) > 0
    assert (
        citations_event[1]["citations"][0]["document_title"]
        == "Service Level Agreements"
    )

    # Check token events
    token_events = [e for e in events if e[0] == "token"]
    full_text = "".join(e[1]["text"] for e in token_events)
    assert "API Gateway" in full_text

    # Check done event
    done_event = next(e for e in events if e[0] == "done")
    session_id = uuid.UUID(done_event[1]["session_id"])
    message_id = uuid.UUID(done_event[1]["message_id"])

    # Verify messages persisted in DB
    async with _session_factory() as session:
        repo = ChatRepository(session)
        messages = await repo.get_messages(session_id)
        assert len(messages) == 2
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "What are our service availability SLAs?"
        assert messages[1].role == MessageRole.ASSISTANT
        assert messages[1].id == message_id
        assert messages[1].citations is not None
        assert len(messages[1].citations) > 0


@pytest.mark.asyncio
async def test_stream_chat_multi_turn_memory(
    client: AsyncClient,
    auth_user_token: str,
    seed_sla_chunk: None,
) -> None:
    """Follow-up questions in the same session include prior turns in the prompt."""
    # Turn 1
    resp1 = await client.post(
        "/api/v1/chat/stream",
        json={"question": "What is the availability SLA for API gateway?"},
        headers={"Authorization": f"Bearer {auth_user_token}"},
    )
    assert resp1.status_code == 200
    events1 = parse_sse_events(resp1.text)
    done_event1 = next(e for e in events1 if e[0] == "done")
    session_id = done_event1[1]["session_id"]

    # Turn 2: Follow-up in the same session
    resp2 = await client.post(
        "/api/v1/chat/stream",
        json={
            "session_id": session_id,
            "question": "What about the Auth Service availability?",
        },
        headers={"Authorization": f"Bearer {auth_user_token}"},
    )
    assert resp2.status_code == 200

    # Verify agent received the prior conversation in history
    assert "Prior History:" in last_agent_prompt
    assert "What is the availability SLA for API gateway?" in last_agent_prompt
    assert "Question:" in last_agent_prompt
    assert "What about the Auth Service availability?" in last_agent_prompt


@pytest.mark.asyncio
async def test_stream_chat_decline_guardrail(
    client: AsyncClient,
    auth_user_token: str,
    seed_sla_chunk: None,
) -> None:
    """Out-of-KB question streams decline message with empty citations and used_context=False."""
    resp = await client.post(
        "/api/v1/chat/stream",
        json={"question": "What is the population of Tokyo?"},
        headers={"Authorization": f"Bearer {auth_user_token}"},
    )
    assert resp.status_code == 200
    events = parse_sse_events(resp.text)

    citations_event = next(e for e in events if e[0] == "citations")
    assert citations_event[1]["used_context"] is False
    assert citations_event[1]["citations"] == []

    token_events = [e for e in events if e[0] == "token"]
    full_text = "".join(e[1]["text"] for e in token_events)
    assert "I don't have that in the knowledge base." in full_text
