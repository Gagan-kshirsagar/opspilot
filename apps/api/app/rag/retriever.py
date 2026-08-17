"""Retriever module using pgvector cosine similarity search."""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.document import Document, DocumentChunk
from app.rag.embeddings import get_embeddings_provider


@dataclass(frozen=True)
class RetrievedChunk:
    """Represents a chunk retrieved by semantic similarity."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    ordinal: int
    content: str
    score: float


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two float vectors in pure Python."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2, strict=False))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class Retriever:
    """Retrieves top-k relevant document chunks using vector similarity."""

    def __init__(self, top_k: int | None = None) -> None:
        settings = get_settings()
        self.top_k = top_k or settings.RAG_TOP_K

    async def retrieve(
        self,
        query: str,
        session: AsyncSession,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve top-k chunks matching the search query."""
        k = top_k or self.top_k
        provider = get_embeddings_provider()
        query_vector = await provider.embed_query(query)

        # Detect if database dialect supports native pgvector
        bind = session.bind
        dialect_name = bind.dialect.name if bind else "postgresql"

        if dialect_name == "postgresql":
            # Native pgvector cosine distance: 1 - (embedding <=> query_vector)
            distance_expr = DocumentChunk.embedding.cosine_distance(query_vector)
            similarity_expr = (1.0 - distance_expr).label("similarity")

            stmt = (
                select(
                    DocumentChunk,
                    Document.title.label("document_title"),
                    similarity_expr,
                )
                .join(Document, DocumentChunk.document_id == Document.id)
                .order_by(distance_expr.asc())
                .limit(k)
            )

            result = await session.execute(stmt)
            rows = result.all()

            return [
                RetrievedChunk(
                    chunk_id=row.DocumentChunk.id,
                    document_id=row.DocumentChunk.document_id,
                    document_title=row.document_title,
                    ordinal=row.DocumentChunk.ordinal,
                    content=row.DocumentChunk.content,
                    score=float(row.similarity),
                )
                for row in rows
            ]

        # In-memory cosine similarity fallback for SQLite / test environments
        stmt_all = select(
            DocumentChunk,
            Document.title.label("document_title"),
        ).join(Document, DocumentChunk.document_id == Document.id)

        result_all = await session.execute(stmt_all)
        rows_all = result_all.all()

        scored: list[tuple[RetrievedChunk, float]] = []
        for row in rows_all:
            emb = list(row.DocumentChunk.embedding) if row.DocumentChunk.embedding is not None else []
            sim = _cosine_similarity(query_vector, emb)
            chunk = RetrievedChunk(
                chunk_id=row.DocumentChunk.id,
                document_id=row.DocumentChunk.document_id,
                document_title=row.document_title,
                ordinal=row.DocumentChunk.ordinal,
                content=row.DocumentChunk.content,
                score=sim,
            )
            scored.append((chunk, sim))

        # Sort descending by similarity
        scored.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in scored[:k]]
