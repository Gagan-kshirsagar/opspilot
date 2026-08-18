"""Tests for RateStore, per-IP rate limiting, global daily AI budget, and Gemini 429 handling."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from app.core.config import get_settings
from app.core.rate_store import MemoryRateStore, get_rate_store, set_rate_store
from app.models.user import User, UserRole, UserStatus
from app.rag.embeddings import EmbeddingsProvider, set_embeddings_provider
from app.rag.llm import GeminiLLMProvider
from app.services.auth.factory import get_auth_provider
from tests.conftest import _session_factory


class MockRateTestEmbeddings(EmbeddingsProvider):
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0] + [0.0] * 767 for _ in texts]

    async def embed_query(self, text: str) -> list[float]:
        return [1.0] + [0.0] * 767


@pytest.fixture(autouse=True)
async def _setup_rate_store() -> None:
    set_embeddings_provider(MockRateTestEmbeddings())
    store = MemoryRateStore()
    set_rate_store(store)
    await store.reset()


@pytest.fixture
async def auth_token() -> tuple[str, User]:
    """Create a test user and generate an access token."""
    async with _session_factory() as session:
        user = User(
            id=uuid.uuid4(),
            email=f"rate_test_{uuid.uuid4().hex[:6]}@test.com",
            name="Rate User",
            role=UserRole.VIEWER,
            status=UserStatus.ACTIVE,
        )
        session.add(user)
        await session.commit()

        provider = get_auth_provider()
        token_pair = provider.issue_tokens(provider._to_auth_user(user))
        return token_pair.access_token, user


# ── RateStore Unit Tests ─────────────────────────────────────


@pytest.mark.asyncio
async def test_memory_rate_store_sliding_window() -> None:
    """Test sliding window rate limiting."""
    store = MemoryRateStore()

    # 3 requests allowed in 2 seconds
    allowed1, rem1, retry1 = await store.check_rate_limit(
        "test_key", limit=3, window_seconds=2
    )
    assert allowed1 is True
    assert rem1 == 2
    assert retry1 == 0

    allowed2, rem2, retry2 = await store.check_rate_limit(
        "test_key", limit=3, window_seconds=2
    )
    assert allowed2 is True
    assert rem2 == 1

    allowed3, rem3, retry3 = await store.check_rate_limit(
        "test_key", limit=3, window_seconds=2
    )
    assert allowed3 is True
    assert rem3 == 0

    # 4th request must be rejected
    allowed4, rem4, retry4 = await store.check_rate_limit(
        "test_key", limit=3, window_seconds=2
    )
    assert allowed4 is False
    assert rem4 == 0
    assert retry4 >= 1


@pytest.mark.asyncio
async def test_memory_rate_store_daily_budget() -> None:
    """Test global daily AI budget increment and capping."""
    store = MemoryRateStore()
    date_key = "2026-08-18"

    # Budget of 2 requests
    allowed1, curr1, rem1 = await store.increment_daily_budget(date_key, max_budget=2)
    assert allowed1 is True
    assert curr1 == 1
    assert rem1 == 1

    allowed2, curr2, rem2 = await store.increment_daily_budget(date_key, max_budget=2)
    assert allowed2 is True
    assert curr2 == 2
    assert rem2 == 0

    # 3rd request should fail
    allowed3, curr3, rem3 = await store.increment_daily_budget(date_key, max_budget=2)
    assert allowed3 is False
    assert curr3 == 2
    assert rem3 == 0


# ── HTTP Rate Limiting Integration Tests ─────────────────────


@pytest.mark.asyncio
async def test_ai_endpoint_rate_limiting(
    client: AsyncClient, auth_token: tuple[str, User]
) -> None:
    """Test that hammering /api/v1/chat triggers HTTP 429."""
    token, _ = auth_token
    headers = {"Authorization": f"Bearer {token}"}
    settings = get_settings()

    store = get_rate_store()
    await store.reset()

    # Exhaust limit
    for _ in range(settings.AI_RATE_LIMIT_REQUESTS):
        resp = await client.post(
            "/api/v1/chat",
            json={"question": "What are the service SLAs?"},
            headers=headers,
        )
        assert resp.status_code in (200, 429)

    # Next request must be 429
    resp_blocked = await client.post(
        "/api/v1/chat",
        json={"question": "What are the service SLAs?"},
        headers=headers,
    )
    assert resp_blocked.status_code == 429
    assert "Retry-After" in resp_blocked.headers
    data = resp_blocked.json()
    assert "Rate limit reached" in data.get("detail", "")


@pytest.mark.asyncio
async def test_daily_ai_budget_blocks_without_gemini_call(
    client: AsyncClient,
    auth_token: tuple[str, User],
) -> None:
    """Test that reaching daily budget returns limit message and skips Gemini."""
    token, _ = auth_token
    headers = {"Authorization": f"Bearer {token}"}
    settings = get_settings()

    date_key = datetime.now(UTC).strftime("%Y-%m-%d")
    store = get_rate_store()

    # Pre-fill daily budget to max
    for _ in range(settings.DAILY_AI_LIMIT):
        await store.increment_daily_budget(date_key, max_budget=settings.DAILY_AI_LIMIT)

    # Now ask chat
    resp = await client.post(
        "/api/v1/chat",
        json={"question": "What is the rollback policy?"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "daily demo limit" in data["answer"].lower()
    assert data["used_context"] is False


@pytest.mark.asyncio
async def test_gemini_429_quota_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that Gemini 429 HTTP status is mapped to friendly message."""
    import httpx

    async def mock_post(*args: object, **kwargs: object) -> httpx.Response:
        req = httpx.Request("POST", "https://generativelanguage.googleapis.com")
        return httpx.Response(
            status_code=429,
            request=req,
            text='{"error": {"message": "Resource exhausted"}}',
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    provider = GeminiLLMProvider(api_key="mock-key")
    resp = await provider.generate_response(prompt="Hello")
    assert "experiencing high demand" in resp
