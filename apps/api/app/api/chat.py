"""Chat router — grounded knowledge base Q&A, SSE streaming, and sessions."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.rate_limit import require_ai_rate_limit
from app.db.engine import get_session
from app.models.user import User
from app.schemas.auth import ErrorResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.chat_session import (
    ChatSessionDetailOut,
    ChatSessionOut,
    ChatStreamRequest,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

_service = ChatService()


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse},
        422: {"description": "Validation error on request body"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
)
async def ask_chat(
    body: ChatRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[User, Depends(get_current_user)],
    _rate_limit: Annotated[str, Depends(require_ai_rate_limit)],
) -> ChatResponse:
    """Ask a question grounded in the OpsPilot knowledge base (non-streaming)."""
    return await _service.answer_question(body, session)


@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse},
        422: {"description": "Validation error on request body"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
)
async def ask_chat_stream(
    body: ChatStreamRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    _rate_limit: Annotated[str, Depends(require_ai_rate_limit)],
) -> StreamingResponse:
    """Stream grounded answer token-by-token via Server-Sent Events (SSE)."""
    generator = _service.stream_chat(request=body, user_id=user.id, session=session)
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/sessions",
    response_model=list[ChatSessionOut],
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse},
    },
)
async def list_chat_sessions(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[ChatSessionOut]:
    """List all chat conversation threads belonging to the current user."""
    return await _service.list_sessions(user_id=user.id, session=session)


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionDetailOut,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse, "description": "Forbidden — user does not own session"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
async def get_chat_session_detail(
    session_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> ChatSessionDetailOut:
    """Retrieve full message history for a specific chat session."""
    # Check if session exists at all (for distinction between 404 and 403)
    from app.repositories.chat_repo import ChatRepository
    repo = ChatRepository(session)
    any_session = await repo.get_session(session_id)
    if any_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    if any_session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden to another user's chat session",
        )

    detail = await _service.get_session_detail(session_id=session_id, user_id=user.id, session=session)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    return detail


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "Session not found or not owned by user"},
    },
)
async def delete_chat_session(
    session_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a chat session and all its messages."""
    deleted = await _service.delete_session(session_id=session_id, user_id=user.id, session=session)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found or forbidden",
        )
