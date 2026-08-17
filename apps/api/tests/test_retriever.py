"""Tests for RAG vector similarity retriever."""

from __future__ import annotations

import uuid

import pytest

from app.models.document import Document, DocumentChunk, DocumentKind
from app.rag.embeddings import EmbeddingsProvider, set_embeddings_provider
from app.rag.retriever import Retriever
from tests.conftest import _session_factory


class DirectionalMockEmbeddings(EmbeddingsProvider):
    """Mock embeddings that return vectors tailored to match specific chunks."""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        res = []
        for t in texts:
            if "incident" in t.lower():
                v = [1.0] + [0.0] * 767
            else:
                v = [0.0, 1.0] + [0.0] * 766
            res.append(v)
        return res

    async def embed_query(self, text: str) -> list[float]:
        if "incident" in text.lower():
            return [1.0] + [0.0] * 767
        return [0.0, 1.0] + [0.0] * 766


@pytest.fixture(autouse=True)
def _setup_embeddings() -> None:
    set_embeddings_provider(DirectionalMockEmbeddings())


@pytest.mark.asyncio
async def test_retriever_top_k_ordering() -> None:
    """Retriever returns top-k chunks ordered by similarity."""
    async with _session_factory() as session:
        doc = Document(
            id=uuid.uuid4(),
            title="Ops Runbook",
            source="seed/kb/incident.md",
            kind=DocumentKind.RUNBOOK,
        )
        session.add(doc)
        await session.flush()

        c1 = DocumentChunk(
            id=uuid.uuid4(),
            document_id=doc.id,
            ordinal=0,
            content="Critical incident escalation instructions.",
            token_count=10,
            embedding=[1.0] + [0.0] * 767,  # Exact match for query
        )
        c2 = DocumentChunk(
            id=uuid.uuid4(),
            document_id=doc.id,
            ordinal=1,
            content="General onboarding steps.",
            token_count=8,
            embedding=[0.0, 1.0] + [0.0] * 766,  # Orthogonal vector
        )
        session.add_all([c1, c2])
        await session.commit()

        retriever = Retriever(top_k=2)
        results = await retriever.retrieve("How to handle incident?", session)

        assert len(results) == 2
        assert results[0].chunk_id == c1.id
        assert results[0].score > results[1].score
        assert results[0].document_title == "Ops Runbook"
