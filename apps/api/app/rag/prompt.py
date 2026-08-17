"""Grounded prompt templates and context formatting for RAG Q&A."""

from __future__ import annotations

from app.rag.retriever import RetrievedChunk

SYSTEM_PROMPT = """You are OpsPilot AI, an expert operational assistant for site reliability and infrastructure operations.

YOUR RULES:
1. Answer the user's question STRICTLY and ONLY based on the provided Knowledge Base Context snippets below.
2. Standard operational synonyms (such as P1/SEV-1/Critical, P2/SEV-2/High, P3/SEV-3/Moderate, on-call/primary rotation) are interchangeable.
3. If the provided context is completely insufficient, irrelevant, or does not contain the answer, respond with EXACTLY:
   "I don't have that in the knowledge base."
4. Do NOT make up answers, hallucinate facts, or extrapolate beyond the documented context snippets.
5. When stating facts from the context, naturally reference the source document (e.g. "[Incident Response Runbook, Section 0]").
6. Keep your answer clear, well-formatted with markdown bullet points, direct, and actionable.
"""

DECLINE_MESSAGE = "I don't have that in the knowledge base."


def format_rag_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    """Format user question and retrieved chunks into the prompt context."""
    if not chunks:
        context_str = "No relevant context found."
    else:
        formatted_chunks: list[str] = []
        for i, chunk in enumerate(chunks, 1):
            formatted_chunks.append(
                f"--- CONTEXT SNIPPET {i} ---\n"
                f"Source: {chunk.document_title} (Section {chunk.ordinal})\n"
                f"Content:\n{chunk.content.strip()}\n"
            )
        context_str = "\n".join(formatted_chunks)

    return f"""Knowledge Base Context:
{context_str}

User Question:
{question.strip()}

Grounded Answer:"""
