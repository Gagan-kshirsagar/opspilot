"""Chat service — orchestrates retrieval, grounded prompting, and citations."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.rag.llm import get_llm_provider
from app.rag.prompt import DECLINE_MESSAGE, format_rag_prompt
from app.rag.retriever import Retriever
from app.schemas.chat import ChatRequest, ChatResponse, Citation


class ChatService:
    """Orchestrates grounded RAG question answering."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.retriever = Retriever(top_k=self.settings.RAG_TOP_K)

    async def answer_question(
        self,
        request: ChatRequest,
        session: AsyncSession,
    ) -> ChatResponse:
        """Answer question using knowledge base retrieval, or decline cleanly."""
        question = request.question.strip()

        # 1. Retrieve top-k relevant chunks
        chunks = await self.retriever.retrieve(question, session)

        # 2. Guardrail baseline: check similarity score threshold
        threshold = self.settings.RAG_SIMILARITY_THRESHOLD
        relevant_chunks = [c for c in chunks if c.score >= threshold]

        if not relevant_chunks:
            # Below relevance threshold — decline without calling LLM
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
