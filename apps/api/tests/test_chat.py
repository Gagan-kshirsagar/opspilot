"""Tests for RAG chat endpoint and chat service."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.models.document import Document, DocumentChunk, DocumentKind
from app.rag.embeddings import EmbeddingsProvider, set_embeddings_provider
from app.rag.llm import LLMProvider, set_llm_provider
from tests.conftest import _session_factory


class MockChatEmbeddings(EmbeddingsProvider):
    """Mock embeddings provider returning high similarity for matching keywords."""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        res = []
        for t in texts:
            if "p1" in t.lower() or "escalation" in t.lower():
                res.append([1.0] + [0.0] * 767)
            else:
                res.append([0.0, 1.0] + [0.0] * 766)
        return res

    async def embed_query(self, text: str) -> list[float]:
        if "p1" in text.lower() or "escalation" in text.lower():
            return [1.0] + [0.0] * 767
        # Out-of-domain query (e.g. France) -> orthogonal vector with low similarity to P1 docs
        return [0.0] * 10 + [1.0] + [0.0] * 757


class MockChatLLM(LLMProvider):
    """Mock LLM returning grounded answers or decline."""

    async def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        if "escalation" in prompt.lower() or "p1" in prompt.lower():
            return "For P1 critical incidents, page on-call immediately and declare in Slack [Incident Response Runbook, Section 0]."
        return "I don't have that in the knowledge base."


@pytest.fixture(autouse=True)
def _setup_providers() -> None:
    set_embeddings_provider(MockChatEmbeddings())
    set_llm_provider(MockChatLLM())


@pytest.fixture
async def auth_token(client: AsyncClient) -> str:
    """Register a user and return access token."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "chatuser@test.com",
            "password": "securepassword",
            "name": "Chat User",
        },
    )
    assert resp.status_code == 201
    return resp.json()["tokens"]["access_token"]


@pytest.fixture
async def seed_kb_chunk() -> None:
    """Insert a test document and chunk."""
    async with _session_factory() as session:
        doc = Document(
            id=uuid.uuid4(),
            title="Incident Response Runbook",
            source="seed/kb/incident_response_runbook.md",
            kind=DocumentKind.RUNBOOK,
        )
        session.add(doc)
        await session.flush()

        chunk = DocumentChunk(
            id=uuid.uuid4(),
            document_id=doc.id,
            ordinal=0,
            content="SEV-1 is critical customer-facing outage. Escalation steps require paging on-call immediately.",
            token_count=18,
            embedding=[1.0] + [0.0] * 767,
        )
        session.add(chunk)
        await session.commit()


@pytest.mark.asyncio
async def test_chat_unauthenticated(client: AsyncClient) -> None:
    """Unauthenticated chat request returns 401."""
    resp = await client.post("/api/v1/chat", json={"question": "What is P1?"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_chat_in_kb_question_success(
    client: AsyncClient,
    auth_token: str,
    seed_kb_chunk: None,
) -> None:
    """In-KB question returns grounded answer with citations and used_context=True."""
    resp = await client.post(
        "/api/v1/chat",
        json={"question": "What is the P1 escalation procedure?"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["used_context"] is True
    assert "P1 critical incidents" in data["answer"]
    assert len(data["citations"]) > 0
    assert data["citations"][0]["document_title"] == "Incident Response Runbook"
    assert data["citations"][0]["ordinal"] == 0
    assert data["citations"][0]["score"] >= 0.55


@pytest.mark.asyncio
async def test_chat_out_of_kb_question_declined(
    client: AsyncClient,
    auth_token: str,
    seed_kb_chunk: None,
) -> None:
    """Out-of-KB question declines without hallucination (used_context=False, empty citations)."""
    resp = await client.post(
        "/api/v1/chat",
        json={"question": "What is the capital of France?"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["used_context"] is False
    assert data["answer"] == "I don't have that in the knowledge base."
    assert data["citations"] == []
