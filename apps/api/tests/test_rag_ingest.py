"""Tests for knowledge base ingestion pipeline."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.models.document import Document, DocumentChunk
from app.rag.embeddings import EmbeddingsProvider, set_embeddings_provider
from app.rag.ingest import ingest_knowledge_base
from tests.conftest import _session_factory


class MockEmbeddingsProvider(EmbeddingsProvider):
    """Deterministic mock embeddings provider for tests."""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # Return deterministic vector for each text
        return [[0.1] * 768 for _ in texts]

    async def embed_query(self, text: str) -> list[float]:
        return [0.1] * 768


@pytest.fixture(autouse=True)
def _setup_mock_embeddings() -> None:
    """Ensure mock embeddings provider is active for tests."""
    set_embeddings_provider(MockEmbeddingsProvider())


@pytest.mark.asyncio
async def test_ingest_knowledge_base_idempotent() -> None:
    """Verify ingestion creates records and repeated runs do not duplicate."""
    async with _session_factory() as session:
        stats1 = await ingest_knowledge_base(session)
        assert stats1["documents"] >= 14
        assert stats1["chunks"] >= 14

        # Verify DB counts
        doc_count = await session.scalar(select(func.count(Document.id)))
        chunk_count = await session.scalar(select(func.count(DocumentChunk.id)))
        assert doc_count == stats1["documents"]
        assert chunk_count == stats1["chunks"]

        # Run ingestion a second time — must be idempotent
        stats2 = await ingest_knowledge_base(session)
        assert stats2["documents"] == stats1["documents"]
        assert stats2["chunks"] == stats1["chunks"]

        doc_count_after = await session.scalar(select(func.count(Document.id)))
        chunk_count_after = await session.scalar(select(func.count(DocumentChunk.id)))
        assert doc_count_after == doc_count
        assert chunk_count_after == chunk_count
