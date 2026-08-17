"""Pydantic v2 schemas for RAG Chat & Knowledge Base endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """POST /api/v1/chat request body."""

    question: str = Field(
        min_length=1,
        max_length=1000,
        description="The operational or procedural question to answer from the knowledge base.",
    )


class Citation(BaseModel):
    """Citation reference for a retrieved knowledge base chunk."""

    document_title: str
    ordinal: int
    snippet: str
    score: float


class ChatResponse(BaseModel):
    """POST /api/v1/chat response body."""

    answer: str
    citations: list[Citation]
    used_context: bool
