"""Unit tests for markdown document chunker."""

from __future__ import annotations

from app.rag.chunker import chunk_document, estimate_tokens


def test_estimate_tokens() -> None:
    """Test token estimation logic."""
    assert estimate_tokens("") == 0
    assert estimate_tokens("hello world") == 2
    assert estimate_tokens("This is a longer sentence with several words.") >= 8


def test_chunk_document_basic() -> None:
    """Test splitting a short document into chunks."""
    text = (
        "# Incident Response Runbook\n\n"
        "## 1. Severity Levels\n"
        "SEV-1 is critical customer-facing outage.\n\n"
        "## 2. Escalation\n"
        "Page the on-call engineer immediately."
    )
    chunks = chunk_document(
        text, document_title="Incident Response Runbook", target_tokens=100
    )

    assert len(chunks) >= 1
    assert chunks[0].document_title == "Incident Response Runbook"
    assert chunks[0].ordinal == 0
    assert "Incident Response Runbook" in chunks[0].content
    assert chunks[0].token_count > 0


def test_chunk_document_large_splits_with_overlap() -> None:
    """Test chunking a larger document across multiple chunks with ordinal order."""
    paragraphs = [
        f"Paragraph {i}: " + ("This is detailed operational instruction text. " * 15)
        for i in range(10)
    ]
    doc_text = "\n\n".join(paragraphs)

    chunks = chunk_document(
        doc_text,
        document_title="Test Ops Guide",
        target_tokens=120,
        overlap_tokens=30,
    )

    assert len(chunks) > 1
    for i, c in enumerate(chunks):
        assert c.ordinal == i
        assert c.document_title == "Test Ops Guide"
        assert c.token_count > 0
