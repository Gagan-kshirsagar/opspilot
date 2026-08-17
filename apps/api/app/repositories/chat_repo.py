"""Chat repository — DB access for sessions and messages."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage, ChatSession, MessageRole


class ChatRepository:
    """Repository managing chat session threads and message logs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_session(self, user_id: uuid.UUID, title: str) -> ChatSession:
        """Create a new chat conversation thread."""
        chat_session = ChatSession(
            id=uuid.uuid4(),
            user_id=user_id,
            title=title.strip() or "New Conversation",
        )
        self.session.add(chat_session)
        await self.session.flush()
        return chat_session

    async def list_sessions(self, user_id: uuid.UUID) -> list[ChatSession]:
        """List all chat sessions belonging to the given user, ordered by most recently updated."""
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> ChatSession | None:
        """Retrieve a session by ID. If user_id is provided, checks ownership."""
        stmt = select(ChatSession).where(ChatSession.id == session_id)
        if user_id is not None:
            stmt = stmt.where(ChatSession.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a chat session and cascade delete its messages."""
        stmt = delete(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return (result.rowcount or 0) > 0

    async def add_message(
        self,
        session_id: uuid.UUID,
        role: MessageRole | str,
        content: str,
        citations: list[dict[str, Any]] | None = None,
    ) -> ChatMessage:
        """Append a message turn to the session and update the session updated_at timestamp."""
        role_enum = MessageRole(role) if isinstance(role, str) else role
        msg = ChatMessage(
            id=uuid.uuid4(),
            session_id=session_id,
            role=role_enum,
            content=content,
            citations=citations,
        )
        self.session.add(msg)

        # Update session timestamp
        session_obj = await self.get_session(session_id)
        if session_obj:
            session_obj.updated_at = datetime.now(timezone.utc)

        await self.session.flush()
        return msg

    async def get_messages(
        self,
        session_id: uuid.UUID,
        limit: int = 50,
    ) -> list[ChatMessage]:
        """Fetch the chronological messages for a session (up to limit)."""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_messages_for_memory(
        self,
        session_id: uuid.UUID,
        limit: int = 6,
    ) -> list[ChatMessage]:
        """Fetch the most recent N messages in chronological order for conversation memory."""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        messages.reverse()
        return messages
