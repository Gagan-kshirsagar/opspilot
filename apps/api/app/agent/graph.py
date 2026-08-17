"""LangGraph ReAct Agent engine for OpsPilot.

Orchestrates multi-turn reasoning, typed tool calling across live databases
(services, incidents, users) and the pgvector Knowledge Base, loop guardrails,
and streaming step/token SSE events.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any, Callable

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools import TOOL_DEFINITIONS, execute_tool
from app.core.config import get_settings
from app.rag.retriever import Retriever
from app.schemas.chat import Citation

logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = """You are OpsPilot AI, an expert operational assistant for site reliability and infrastructure engineering.

YOUR RESPONSIBILITIES & RULES:
1. ALWAYS use the provided tools to query factual data before answering:
   - Use `retrieve_docs` to find operational runbooks, SLAs, disaster recovery procedures, or troubleshooting guides.
   - Use `query_services` to inspect service health statuses, availability uptime %, and descriptions.
   - Use `query_incidents` to inspect active/past incidents by severity (sev1/sev2/sev3) or status (open/investigating/resolved).
   - Use `query_users` to look up service owners, teams, or administrators.
   - Use `get_service_detail` to inspect a single service with its active incident count.
2. If the user's question requires information from both the live database and runbooks (e.g. "Which services are degraded and what's the runbook for them?"), call `query_services` first, then call `retrieve_docs` for the relevant services, and synthesize both in your answer.
3. GROUNDING: Do NOT fabricate service names, incident counts, uptime metrics, or procedures. Only state facts returned by your tools.
4. CITATIONS: When stating facts from `retrieve_docs`, naturally cite the source document name (e.g. "[Incident Response Runbook, Section 0]").
5. If after querying tools the data is completely missing or out of scope, state clearly:
   "I don't have enough information in the system or knowledge base to answer that."
6. Provide clear, structured, well-formatted markdown answers with bullet points.
"""


# ── Mock Tool Call Registry for Offline / Test Execution ─────


_custom_agent_llm_handler: Callable[..., Any] | None = None


def set_agent_llm_handler(handler: Callable[..., Any] | None) -> None:
    """Set custom agent LLM handler for offline tests."""
    global _custom_agent_llm_handler
    _custom_agent_llm_handler = handler


class AgentRunner:
    """Executes ReAct agent graph with tool calling and SSE streaming."""

    def __init__(
        self,
        session: AsyncSession,
        retriever: Retriever | None = None,
    ) -> None:
        self.session = session
        self.settings = get_settings()
        self.retriever = retriever or Retriever(top_k=self.settings.RAG_TOP_K)
        self.api_key = self.settings.GEMINI_API_KEY
        self.model_name = self.settings.GEMINI_CHAT_MODEL
        self.max_iterations = self.settings.AGENT_MAX_ITERS
        self.temperature = self.settings.AGENT_TEMPERATURE
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def run_stream(
        self,
        question: str,
        conversation_history: list[tuple[str, str]] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Execute the ReAct agent graph and yield structured SSE events."""
        # Yield dictionary events that the caller serializes to SSE:
        # {"event": "step", "data": {...}}
        # {"event": "citations", "data": {...}}
        # {"event": "token", "data": {...}}
        # {"event": "done", "data": {...}}

        accumulated_citations: list[Citation] = []
        recorded_steps: list[dict[str, Any]] = []

        # ── Test / Offline Handler Intercept ─────────────────────
        if _custom_agent_llm_handler is not None:
            async for evt in _custom_agent_llm_handler(
                question=question,
                conversation_history=conversation_history,
                session=self.session,
                retriever=self.retriever,
            ):
                yield evt
            return

        # ── Setup Gemini Conversation Contents ───────────────────
        contents: list[dict[str, Any]] = []

        # Add prior conversation turns if any
        if conversation_history:
            for role, text in conversation_history:
                g_role = "user" if role == "user" else "model"
                contents.append({"role": g_role, "parts": [{"text": text}]})

        # Add current question
        contents.append({"role": "user", "parts": [{"text": question}]})

        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        url_generate = f"{self.base_url}/models/{self.model_name}:generateContent"

        iteration = 0
        final_answer_accumulated: list[str] = []

        async with httpx.AsyncClient(timeout=45.0) as client:
            while iteration < self.max_iterations:
                iteration += 1

                payload = {
                    "system_instruction": {
                        "parts": [{"text": AGENT_SYSTEM_PROMPT}],
                    },
                    "contents": contents,
                    "tools": [{"function_declarations": TOOL_DEFINITIONS}],
                    "generationConfig": {
                        "temperature": self.temperature,
                        "thinkingConfig": {"thinkingBudget": 0},
                    },
                }

                try:
                    resp = await client.post(url_generate, headers=headers, json=payload)
                    if resp.status_code != 200:
                        logger.warning("Agent LLM call returned %s: %s", resp.status_code, resp.text)
                        break

                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        break

                    candidate = candidates[0]
                    content_obj = candidate.get("content", {})
                    parts = content_obj.get("parts", [])

                    # Check for tool / function calls
                    function_calls = [p["functionCall"] for p in parts if "functionCall" in p]

                    if not function_calls:
                        # Model generated final text directly without tool calls
                        contents.append(content_obj)
                        for p in parts:
                            if "text" in p and not p.get("thought"):
                                final_answer_accumulated.append(p["text"])
                        break

                    # Append model tool call to contents history
                    contents.append(content_obj)

                    # Execute each tool call
                    tool_responses: list[dict[str, Any]] = []
                    for call in function_calls:
                        tool_name = call.get("name", "")
                        tool_args = call.get("args", {})

                        # 1. Emit tool_call step event
                        step_call = {
                            "type": "tool_call",
                            "tool": tool_name,
                            "args": tool_args,
                        }
                        recorded_steps.append(step_call)
                        yield {"event": "step", "data": step_call}

                        # 2. Execute tool
                        result_data, summary = await execute_tool(
                            name=tool_name,
                            args=tool_args,
                            session=self.session,
                            retriever=self.retriever,
                        )

                        # If tool was retrieve_docs, extract citations
                        if tool_name == "retrieve_docs" and "chunks" in result_data:
                            for c in result_data["chunks"]:
                                accumulated_citations.append(
                                    Citation(
                                        document_title=c["document_title"],
                                        ordinal=c["ordinal"],
                                        snippet=c["snippet"],
                                        score=c["score"],
                                    )
                                )

                        # 3. Emit tool_result step event
                        step_res = {
                            "type": "tool_result",
                            "tool": tool_name,
                            "summary": summary,
                        }
                        recorded_steps.append(step_res)
                        yield {"event": "step", "data": step_res}

                        # Prepare response part for Gemini
                        tool_responses.append(
                            {
                                "functionResponse": {
                                    "name": tool_name,
                                    "response": result_data,
                                }
                            }
                        )

                    # Append tool responses to contents
                    contents.append({"role": "user", "parts": tool_responses})

                except Exception as e:
                    logger.exception("Error in agent reasoning step: %s", e)
                    break

            # ── Stream Final Synthesis ───────────────────────────────
            # Emit citations if any were gathered
            if accumulated_citations:
                yield {
                    "event": "citations",
                    "data": {
                        "citations": [c.model_dump() for c in accumulated_citations],
                        "used_context": True,
                    },
                }

            # If we already have final answer text from non-streaming return, stream tokens
            if final_answer_accumulated:
                full_text = "".join(final_answer_accumulated)
                # Stream out chunked tokens
                words = full_text.split(" ")
                for i, w in enumerate(words):
                    token_str = w + (" " if i < len(words) - 1 else "")
                    yield {"event": "token", "data": {"text": token_str}}
                    await asyncio.sleep(0.01)
            else:
                # Request streaming synthesis from Gemini
                url_stream = f"{self.base_url}/models/{self.model_name}:streamGenerateContent?alt=sse"
                stream_payload = {
                    "system_instruction": {
                        "parts": [{"text": AGENT_SYSTEM_PROMPT}],
                    },
                    "contents": contents,
                    "generationConfig": {
                        "temperature": self.temperature,
                        "thinkingConfig": {"thinkingBudget": 0},
                    },
                }

                stream_started = False
                try:
                    async with client.stream("POST", url_stream, headers=headers, json=stream_payload) as stream_resp:
                        if stream_resp.status_code == 200:
                            async for line in stream_resp.aiter_lines():
                                if line.startswith("data: "):
                                    d_str = line[6:].strip()
                                    if not d_str:
                                        continue
                                    try:
                                        chunk = json.loads(d_str)
                                        cands = chunk.get("candidates", [])
                                        if cands:
                                            pts = cands[0].get("content", {}).get("parts", [])
                                            for p in pts:
                                                if "text" in p and not p.get("thought"):
                                                    txt = p["text"]
                                                    if txt:
                                                        stream_started = True
                                                        final_answer_accumulated.append(txt)
                                                        yield {"event": "token", "data": {"text": txt}}
                                    except json.JSONDecodeError:
                                        continue
                except Exception as e:
                    logger.warning("Final stream error: %s", e)

                if not stream_started:
                    fallback_text = "I don't have enough information in the system or knowledge base to answer that."
                    final_answer_accumulated.append(fallback_text)
                    yield {"event": "token", "data": {"text": fallback_text}}

        full_final_text = "".join(final_answer_accumulated).strip()
        yield {
            "event": "agent_done",
            "data": {
                "final_answer": full_final_text,
                "citations": [c.model_dump() for c in accumulated_citations],
                "steps": recorded_steps,
            },
        }
