"""Pydantic v2 schemas for chat sessions, messages, and streaming."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.chat import Citation


class ChatStreamRequest(BaseModel):
    """POST /api/v1/chat/stream request body."""

    question: str = Field(
        min_length=1,
        max_length=2000,
        description="User question to ask in the chat session.",
    )
    session_id: uuid.UUID | None = Field(
        default=None,
        description="Optional existing session ID. If omitted, a new session is created.",
    )


class ChatMessageOut(BaseModel):
    """Schema for an individual chat message turn."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    citations: list[Citation] | None = None
    created_at: datetime


class ChatSessionOut(BaseModel):
    """Schema for chat session summary in session list."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatSessionDetailOut(BaseModel):
    """Schema for chat session detail with full message thread history."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageOut]
