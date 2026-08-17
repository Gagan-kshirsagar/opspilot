"""Knowledge base ingestion CLI and pipeline.

Usage:
    python -m app.rag.ingest

Reads markdown files from seed/kb, chunks them, generates embeddings,
and idempotently upserts documents and document_chunks.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import uuid
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session_factory, engine
from app.models.document import Document, DocumentChunk, DocumentKind
from app.rag.chunker import chunk_document
from app.rag.embeddings import get_embeddings_provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def _resolve_kb_dir() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "seed" / "kb",
        Path(__file__).resolve().parent.parent / "seed" / "kb",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


KB_DIR = _resolve_kb_dir()


def extract_title_and_kind(file_path: Path, text: str) -> tuple[str, DocumentKind]:
    """Extract document title and kind from markdown content and filename."""
    # Find first markdown # Header
    match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if match:
        title = match.group(1).strip()
    else:
        title = file_path.stem.replace("_", " ").title()

    filename = file_path.name.lower()
    if "runbook" in filename or "recovery" in filename or "troubleshooting" in filename or "procedure" in filename:
        kind = DocumentKind.RUNBOOK
    elif "policy" in filename or "rbac" in filename:
        kind = DocumentKind.POLICY
    elif "sla" in filename:
        kind = DocumentKind.SLA
    elif "faq" in filename:
        kind = DocumentKind.FAQ
    else:
        kind = DocumentKind.GUIDE

    return title, kind


async def ingest_knowledge_base(session: AsyncSession) -> dict[str, int]:
    """Ingest all markdown files in seed/kb into Postgres with embeddings."""
    if not KB_DIR.exists():
        raise FileNotFoundError(f"Knowledge base directory not found at: {KB_DIR}")

    md_files = sorted(KB_DIR.glob("*.md"))
    if not md_files:
        logger.warning("No markdown files found in %s", KB_DIR)
        return {"documents": 0, "chunks": 0, "tokens": 0}

    logger.info("Found %d markdown documents in %s", len(md_files), KB_DIR)

    embeddings_provider = get_embeddings_provider()

    total_chunks_created = 0
    total_tokens_computed = 0
    total_docs_processed = 0

    for file_path in md_files:
        content = file_path.read_text(encoding="utf-8")
        title, kind = extract_title_and_kind(file_path, content)
        source = f"seed/kb/{file_path.name}"

        # Check if document already exists
        stmt = select(Document).where(Document.title == title)
        result = await session.execute(stmt)
        existing_doc = result.scalar_one_or_none()

        if existing_doc is not None:
            # Idempotent cleanup: delete old chunks for this doc
            await session.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == existing_doc.id)
            )
            doc = existing_doc
            doc.source = source
            doc.kind = kind
        else:
            doc = Document(
                id=uuid.uuid4(),
                title=title,
                source=source,
                kind=kind,
            )
            session.add(doc)

        await session.flush()  # Ensure doc.id is persisted

        # Chunk the document
        chunks = chunk_document(content, document_title=title)
        if not chunks:
            continue

        chunk_texts = [c.content for c in chunks]
        embeddings = await embeddings_provider.embed_texts(chunk_texts)

        for chunk, embedding in zip(chunks, embeddings, strict=False):
            db_chunk = DocumentChunk(
                id=uuid.uuid4(),
                document_id=doc.id,
                ordinal=chunk.ordinal,
                content=chunk.content,
                token_count=chunk.token_count,
                embedding=embedding,
            )
            session.add(db_chunk)
            total_chunks_created += 1
            total_tokens_computed += chunk.token_count

        total_docs_processed += 1
        logger.info(
            "✓ Ingested '%s' (%s): %d chunks (~%d tokens)",
            title,
            kind.value,
            len(chunks),
            sum(c.token_count for c in chunks),
        )

    await session.commit()
    logger.info(
        "✨ Knowledge base ingestion complete! Summary: %d docs, %d chunks, %d estimated tokens.",
        total_docs_processed,
        total_chunks_created,
        total_tokens_computed,
    )
    return {
        "documents": total_docs_processed,
        "chunks": total_chunks_created,
        "tokens": total_tokens_computed,
    }


async def main() -> None:
    """CLI entrypoint for ingestion."""
    async with async_session_factory() as session:
        await ingest_knowledge_base(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
