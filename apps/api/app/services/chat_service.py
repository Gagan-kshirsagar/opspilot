"""Chat service — orchestrates retrieval, grounded prompting, streaming, and session history."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.rate_store import get_rate_store
from app.models.chat import MessageRole
from app.rag.llm import get_llm_provider
from app.rag.prompt import DECLINE_MESSAGE, format_rag_prompt
from app.rag.retriever import Retriever
from app.repositories.chat_repo import ChatRepository
from app.schemas.chat import ChatRequest, ChatResponse, Citation
from app.schemas.chat_session import (
    ChatMessageOut,
    ChatSessionDetailOut,
    ChatSessionOut,
    ChatStreamRequest,
)

logger = logging.getLogger(__name__)


class ChatService:
    """Orchestrates grounded RAG question answering and multi-turn sessions."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.retriever = Retriever(top_k=self.settings.RAG_TOP_K)

    async def answer_question(
        self,
        request: ChatRequest,
        session: AsyncSession,
    ) -> ChatResponse:
        """Answer question using non-streaming knowledge base retrieval."""
        question = request.question.strip()

        # 0. Check global daily AI request budget
        date_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        rate_store = get_rate_store()
        allowed, _, _ = await rate_store.increment_daily_budget(
            date_key=date_key, max_budget=self.settings.DAILY_AI_LIMIT
        )
        if not allowed:
            return ChatResponse(
                answer=(
                    f"The daily demo limit of {self.settings.DAILY_AI_LIMIT} AI requests has been reached. "
                    "To protect free-tier quotas, AI queries will reset at midnight UTC (00:00 UTC). "
                    "Please try again tomorrow!"
                ),
                citations=[],
                used_context=False,
            )

        # 1. Retrieve top-k relevant chunks
        chunks = await self.retriever.retrieve(question, session)

        # 2. Guardrail baseline: check similarity score threshold
        threshold = self.settings.RAG_SIMILARITY_THRESHOLD
        relevant_chunks = [c for c in chunks if c.score >= threshold]

        if not relevant_chunks:
            return ChatResponse(
                answer=DECLINE_MESSAGE,
                citations=[],
                used_context=False,
            )

        # 3. Build grounded prompt and invoke LLM
        prompt = format_rag_prompt(question, relevant_chunks)
        llm = get_llm_provider()
        answer = await llm.generate_response(prompt)

        # 4. Check if LLM declined due to insufficient context
        if DECLINE_MESSAGE.lower() in answer.lower() or not answer.strip():
            return ChatResponse(
                answer=DECLINE_MESSAGE,
                citations=[],
                used_context=False,
            )

        # 5. Format citations from the relevant context chunks
        citations = [
            Citation(
                document_title=chunk.document_title,
                ordinal=chunk.ordinal,
                snippet=(
                    chunk.content[:200] + "..."
                    if len(chunk.content) > 200
                    else chunk.content
                ),
                score=round(chunk.score, 4),
            )
            for chunk in relevant_chunks
        ]

        return ChatResponse(
            answer=answer,
            citations=citations,
            used_context=True,
        )

    async def stream_chat(
        self,
        request: ChatStreamRequest,
        user_id: uuid.UUID,
        session: AsyncSession,
    ) -> AsyncGenerator[str, None]:
        """Stream token-by-token RAG answer via Server-Sent Events (SSE)."""
        repo = ChatRepository(session)
        question = request.question.strip()

        # 1. Resolve or create chat session
        if request.session_id is not None:
            chat_session = await repo.get_session(request.session_id, user_id=user_id)
            if chat_session is None:
                err_payload = json.dumps({"message": "Chat session not found or forbidden"})
                yield f"event: error\ndata: {err_payload}\n\n"
                return
        else:
            # Auto-title from the first question (truncated)
            title = question[:60].strip() + ("..." if len(question) > 60 else "")
            chat_session = await repo.create_session(user_id=user_id, title=title)

        # 2. Retrieve prior memory (last 6 messages capped) before inserting new message
        prior_turns = await repo.get_recent_messages_for_memory(
            session_id=chat_session.id, limit=6
        )
        conversation_history: list[tuple[str, str]] = [
            (msg.role.value if isinstance(msg.role, MessageRole) else str(msg.role), msg.content)
            for msg in prior_turns
        ]

        # 3. Persist user message turn
        await repo.add_message(
            session_id=chat_session.id,
            role=MessageRole.USER,
            content=question,
        )
        await session.commit()

        # 4. Check global daily AI request budget
        date_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        rate_store = get_rate_store()
        allowed, _, _ = await rate_store.increment_daily_budget(
            date_key=date_key, max_budget=self.settings.DAILY_AI_LIMIT
        )
        if not allowed:
            limit_msg = (
                f"The daily demo limit of {self.settings.DAILY_AI_LIMIT} AI requests has been reached. "
                "To protect free-tier quotas, AI queries will reset at midnight UTC (00:00 UTC). "
                "Please try again tomorrow!"
            )
            yield f"event: token\ndata: {json.dumps({'text': limit_msg})}\n\n"
            assistant_msg = await repo.add_message(
                session_id=chat_session.id,
                role=MessageRole.ASSISTANT,
                content=limit_msg,
                citations=None,
            )
            await session.commit()
            done_data = json.dumps(
                {
                    "session_id": str(chat_session.id),
                    "message_id": str(assistant_msg.id),
                    "title": chat_session.title,
                }
            )
            yield f"event: done\ndata: {done_data}\n\n"
            return

        # 4. Execute LangGraph ReAct Agent Runner
        from app.agent.graph import AgentRunner

        agent_runner = AgentRunner(session=session, retriever=self.retriever)

        final_answer_accum: str = ""
        final_citations: list[dict[str, Any]] | None = None

        try:
            async for evt in agent_runner.run_stream(
                question=question,
                conversation_history=conversation_history,
            ):
                evt_name = evt.get("event")
                evt_data = evt.get("data", {})

                if evt_name == "step":
                    yield f"event: step\ndata: {json.dumps(evt_data)}\n\n"
                elif evt_name == "citations":
                    yield f"event: citations\ndata: {json.dumps(evt_data)}\n\n"
                elif evt_name == "token":
                    yield f"event: token\ndata: {json.dumps(evt_data)}\n\n"
                elif evt_name == "agent_done":
                    final_answer_accum = evt_data.get("final_answer", "")
                    raw_cites = evt_data.get("citations", [])
                    if raw_cites:
                        final_citations = raw_cites

        except Exception as e:
            logger.exception("Error during ReAct agent execution: %s", e)
            err_data = json.dumps({"message": "Error streaming agent response"})
            yield f"event: error\ndata: {err_data}\n\n"
            return

        if not final_answer_accum:
            final_answer_accum = DECLINE_MESSAGE

        # 5. Persist assistant message
        assistant_msg = await repo.add_message(
            session_id=chat_session.id,
            role=MessageRole.ASSISTANT,
            content=final_answer_accum,
            citations=final_citations,
        )
        await session.commit()

        # 6. Emit done event
        done_data = json.dumps(
            {
                "session_id": str(chat_session.id),
                "message_id": str(assistant_msg.id),
                "title": chat_session.title,
            }
        )
        yield f"event: done\ndata: {done_data}\n\n"

    async def list_sessions(
        self,
        user_id: uuid.UUID,
        session: AsyncSession,
    ) -> list[ChatSessionOut]:
        """List all chat sessions for the user."""
        repo = ChatRepository(session)
        sessions = await repo.list_sessions(user_id)
        return [ChatSessionOut.model_validate(s) for s in sessions]

    async def get_session_detail(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        session: AsyncSession,
    ) -> ChatSessionDetailOut | None:
        """Fetch session and all its messages. Returns None if session does not exist or user doesn't own it."""
        repo = ChatRepository(session)
        session_obj = await repo.get_session(session_id, user_id=user_id)
        if session_obj is None:
            return None

        messages = await repo.get_messages(session_id, limit=100)
        return ChatSessionDetailOut(
            id=session_obj.id,
            user_id=session_obj.user_id,
            title=session_obj.title,
            created_at=session_obj.created_at,
            updated_at=session_obj.updated_at,
            messages=[
                ChatMessageOut(
                    id=m.id,
                    session_id=m.session_id,
                    role=m.role.value if isinstance(m.role, MessageRole) else str(m.role),
                    content=m.content,
                    citations=[Citation(**c) for c in m.citations] if m.citations else None,
                    created_at=m.created_at,
                )
                for m in messages
            ],
        )

    async def delete_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        session: AsyncSession,
    ) -> bool:
        """Delete session and messages owned by user."""
        repo = ChatRepository(session)
        deleted = await repo.delete_session(session_id, user_id=user_id)
        if deleted:
            await session.commit()
        return deleted
