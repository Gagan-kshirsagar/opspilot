"""Embeddings provider abstraction and Gemini implementation."""

from __future__ import annotations

import asyncio
import logging
from typing import Protocol

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingsProvider(Protocol):
    """Protocol for pluggable text embeddings providers."""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Compute embeddings for a batch of text chunks."""
        ...

    async def embed_query(self, text: str) -> list[float]:
        """Compute embedding for a single search query."""
        ...


class GeminiEmbeddingsProvider:
    """Gemini text-embedding-004 provider using async HTTP REST requests."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_EMBEDDING_MODEL
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def _embed_single(self, client: httpx.AsyncClient, text: str) -> list[float]:
        """Embed a single text string using embedContent endpoint."""
        url = f"{self.base_url}/models/{self.model_name}:embedContent"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "model": f"models/{self.model_name}",
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": 768,
        }

        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        raw_vals = data.get("embedding", {}).get("values", [0.0] * 768)
        return [float(x) for x in raw_vals]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Batch embed multiple texts concurrently using embedContent."""
        if not texts:
            return []

        if not self.api_key:
            logger.warning(
                "No GEMINI_API_KEY configured; returning zero vectors for embeddings."
            )
            return [[0.0] * 768 for _ in texts]

        # Use semaphore to bound concurrency to avoid rate limits
        sem = asyncio.Semaphore(10)

        async def _bounded_embed(client: httpx.AsyncClient, t: str) -> list[float]:
            async with sem:
                return await self._embed_single(client, t)

        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = [_bounded_embed(client, text) for text in texts]
            return await asyncio.gather(*tasks)

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single search query."""
        if not self.api_key:
            logger.warning("No GEMINI_API_KEY configured; returning zero vector.")
            return [0.0] * 768

        async with httpx.AsyncClient(timeout=15.0) as client:
            return await self._embed_single(client, text)


_singleton_embeddings_provider: EmbeddingsProvider | None = None


def get_embeddings_provider() -> EmbeddingsProvider:
    """Return configured embeddings provider instance."""
    global _singleton_embeddings_provider
    if _singleton_embeddings_provider is None:
        _singleton_embeddings_provider = GeminiEmbeddingsProvider()
    return _singleton_embeddings_provider


def set_embeddings_provider(provider: EmbeddingsProvider) -> None:
    """Override singleton embeddings provider (useful for tests)."""
    global _singleton_embeddings_provider
    _singleton_embeddings_provider = provider
