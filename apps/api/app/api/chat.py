"""Chat router — grounded knowledge base Q&A endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.engine import get_session
from app.models.user import User
from app.schemas.auth import ErrorResponse
from app.schemas.chat import ChatRequest, ChatResponse
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
    },
)
async def ask_chat(
    body: ChatRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[User, Depends(get_current_user)],
) -> ChatResponse:
    """Ask a question grounded in the OpsPilot knowledge base.

    Returns an answer synthesized from relevant documents along with source
    citations. If context is insufficient or irrelevant, declines cleanly.
    """
    return await _service.answer_question(body, session)
