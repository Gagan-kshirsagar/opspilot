from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Protocol

import httpx

from app.core.config import get_settings
from app.rag.prompt import DECLINE_MESSAGE, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for pluggable LLM chat completion providers."""

    async def generate_response(
        self,
        prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> str:
        """Generate text completion from prompt and system instructions."""
        ...

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> AsyncGenerator[str, None]:
        """Stream token chunks from prompt and system instructions."""
        ...


class GeminiLLMProvider:
    """Gemini gemini-1.5-flash provider using async HTTP REST requests."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        temperature: float | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_CHAT_MODEL
        self.temperature = (
            temperature if temperature is not None else settings.RAG_TEMPERATURE
        )
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate_response(
        self,
        prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> str:
        """Generate response from Gemini 1.5 Flash."""
        if not self.api_key:
            logger.warning("No GEMINI_API_KEY configured; returning decline message.")
            return DECLINE_MESSAGE

        url = f"{self.base_url}/models/{self.model_name}:generateContent"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": get_settings().GEMINI_MAX_OUTPUT_TOKENS,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }

        fallback_models = [
            self.model_name,
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash",
        ]
        # Deduplicate while preserving order
        candidate_models = list(dict.fromkeys(fallback_models))

        rate_limit_hit = False

        async with httpx.AsyncClient(timeout=30.0) as client:
            last_err: Exception | None = None
            for model in candidate_models:
                url = f"{self.base_url}/models/{model}:generateContent"
                for attempt in range(2):
                    try:
                        resp = await client.post(url, headers=headers, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if not candidates:
                                return DECLINE_MESSAGE
                            parts = candidates[0].get("content", {}).get("parts", [])
                            text_parts = [
                                p.get("text", "")
                                for p in parts
                                if "text" in p and not p.get("thought")
                            ]
                            result_text = "".join(text_parts).strip()
                            return result_text or DECLINE_MESSAGE

                        if resp.status_code == 429:
                            rate_limit_hit = True
                            await asyncio.sleep(0.5 * (attempt + 1))
                            continue

                        if resp.status_code in (500, 503):
                            await asyncio.sleep(0.5 * (attempt + 1))
                            continue

                        # Other status code (e.g. 404), try next model candidate
                        break
                    except (httpx.ConnectError, httpx.ReadTimeout) as e:
                        last_err = e
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue

            if rate_limit_hit:
                return "OpsPilot AI is currently experiencing high demand on the free-tier quota. Please wait a few moments and try asking again."

            if last_err:
                logger.error("LLM generateContent failed after retries: %s", last_err)
            return DECLINE_MESSAGE

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> AsyncGenerator[str, None]:
        """Stream token chunks from Gemini SSE stream."""
        if not self.api_key:
            logger.warning("No GEMINI_API_KEY configured; yielding decline message.")
            yield DECLINE_MESSAGE
            return

        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": 2048,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }

        fallback_models = [
            self.model_name,
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash",
        ]
        candidate_models = list(dict.fromkeys(fallback_models))

        stream_started = False
        import json

        async with httpx.AsyncClient(timeout=45.0) as client:
            for model in candidate_models:
                url = f"{self.base_url}/models/{model}:streamGenerateContent?alt=sse"
                try:
                    async with client.stream(
                        "POST", url, headers=headers, json=payload
                    ) as resp:
                        if resp.status_code != 200:
                            continue

                        async for line in resp.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                if not data_str:
                                    continue
                                try:
                                    chunk = json.loads(data_str)
                                    candidates = chunk.get("candidates", [])
                                    if candidates:
                                        parts = (
                                            candidates[0]
                                            .get("content", {})
                                            .get("parts", [])
                                        )
                                        for p in parts:
                                            if "text" in p and not p.get("thought"):
                                                text = p["text"]
                                                if text:
                                                    stream_started = True
                                                    yield text
                                except json.JSONDecodeError:
                                    continue

                    if stream_started:
                        return
                except Exception as e:
                    logger.warning("Streaming with model %s failed: %s", model, e)
                    continue

        if not stream_started:
            yield DECLINE_MESSAGE


_singleton_llm_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    """Return configured LLM provider singleton."""
    global _singleton_llm_provider
    if _singleton_llm_provider is None:
        _singleton_llm_provider = GeminiLLMProvider()
    return _singleton_llm_provider


def set_llm_provider(provider: LLMProvider) -> None:
    """Override singleton LLM provider (useful for tests)."""
    global _singleton_llm_provider
    _singleton_llm_provider = provider
