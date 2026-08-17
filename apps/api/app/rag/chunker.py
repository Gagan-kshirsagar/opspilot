"""Document chunker for splitting ops markdown documentation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    """Represents a text chunk produced from a document."""

    document_title: str
    ordinal: int
    content: str
    token_count: int


def estimate_tokens(text: str) -> int:
    """Estimate token count based on whitespace-separated words and punctuation (~1.3 tokens/word)."""
    words = text.split()
    if not words:
        return 0
    # Average ~1.3 tokens per word, or roughly len(text)/4 chars
    return max(1, int(len(words) * 1.3))


def chunk_document(
    text: str,
    document_title: str,
    target_tokens: int = 500,
    overlap_tokens: int = 60,
) -> list[Chunk]:
    """Split markdown document into coherent chunks with overlap.

    Splits by markdown structural headers and paragraphs while ensuring
    chunks stay within target token bounds and overlap with prior sections.
    """
    cleaned_text = text.strip()
    if not cleaned_text:
        return []

    # Split by double newlines (paragraphs / header blocks)
    paragraphs = [p.strip() for p in cleaned_text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [cleaned_text]

    chunks: list[Chunk] = []
    current_paragraphs: list[str] = []
    current_tokens = 0
    ordinal = 0

    for para in paragraphs:
        para_tokens = estimate_tokens(para)

        # If a single paragraph is larger than target_tokens, split by sentences/lines
        if para_tokens > target_tokens:
            sub_lines = para.split("\n")
            for line in sub_lines:
                line_tokens = estimate_tokens(line)
                if current_tokens + line_tokens > target_tokens and current_paragraphs:
                    chunk_text = "\n\n".join(current_paragraphs)
                    chunks.append(
                        Chunk(
                            document_title=document_title,
                            ordinal=ordinal,
                            content=chunk_text,
                            token_count=estimate_tokens(chunk_text),
                        )
                    )
                    ordinal += 1

                    # Retain last paragraph(s) for overlap
                    overlap_acc: list[str] = []
                    overlap_count = 0
                    for p in reversed(current_paragraphs):
                        t = estimate_tokens(p)
                        if overlap_count + t <= overlap_tokens:
                            overlap_acc.insert(0, p)
                            overlap_count += t
                        else:
                            break
                    current_paragraphs = overlap_acc
                    current_tokens = overlap_count

                current_paragraphs.append(line)
                current_tokens += line_tokens
            continue

        # Normal paragraph accumulation
        if current_tokens + para_tokens > target_tokens and current_paragraphs:
            chunk_text = "\n\n".join(current_paragraphs)
            chunks.append(
                Chunk(
                    document_title=document_title,
                    ordinal=ordinal,
                    content=chunk_text,
                    token_count=estimate_tokens(chunk_text),
                )
            )
            ordinal += 1

            # Retain overlap
            overlap_acc = []
            overlap_count = 0
            for p in reversed(current_paragraphs):
                t = estimate_tokens(p)
                if overlap_count + t <= overlap_tokens:
                    overlap_acc.insert(0, p)
                    overlap_count += t
                else:
                    break
            current_paragraphs = overlap_acc
            current_tokens = overlap_count

        current_paragraphs.append(para)
        current_tokens += para_tokens

    # Flush remaining text
    if current_paragraphs:
        chunk_text = "\n\n".join(current_paragraphs)
        chunks.append(
            Chunk(
                document_title=document_title,
                ordinal=ordinal,
                content=chunk_text,
                token_count=estimate_tokens(chunk_text),
            )
        )

    return chunks
