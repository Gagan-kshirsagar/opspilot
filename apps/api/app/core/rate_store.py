"""Pluggable RateStore protocol with in-memory and Redis backends."""

from __future__ import annotations

import asyncio
import logging
import math
import time
from typing import Protocol

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class RateStore(Protocol):
    """Protocol for pluggable rate limiting and daily quota storage."""

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """Check rate limit for a key.

        Returns:
            (allowed: bool, remaining_requests: int, retry_after_seconds: int)
        """
        ...

    async def increment_daily_budget(
        self,
        date_key: str,
        max_budget: int,
    ) -> tuple[bool, int, int]:
        """Increment and check global daily AI request budget.

        Returns:
            (allowed: bool, current_count: int, remaining_budget: int)
        """
        ...

    async def get_daily_usage(self, date_key: str) -> int:
        """Get current daily usage count."""
        ...

    async def reset(self) -> None:
        """Clear all stored state (primarily for tests)."""
        ...


class MemoryRateStore:
    """Thread-safe, zero-dependency in-memory sliding window and daily budget store."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._sliding_windows: dict[str, list[float]] = {}
        self._daily_counts: dict[str, int] = {}

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        async with self._lock:
            now = time.time()
            cutoff = now - window_seconds
            timestamps = [t for t in self._sliding_windows.get(key, []) if t > cutoff]

            if len(timestamps) < limit:
                timestamps.append(now)
                self._sliding_windows[key] = timestamps
                remaining = max(0, limit - len(timestamps))
                return True, remaining, 0

            # Rate limit exceeded
            oldest = timestamps[0]
            retry_after = max(1, math.ceil(oldest + window_seconds - now))
            self._sliding_windows[key] = timestamps
            return False, 0, retry_after

    async def increment_daily_budget(
        self,
        date_key: str,
        max_budget: int,
    ) -> tuple[bool, int, int]:
        async with self._lock:
            current = self._daily_counts.get(date_key, 0)
            if current >= max_budget:
                return False, current, 0

            current += 1
            self._daily_counts[date_key] = current
            remaining = max(0, max_budget - current)
            return True, current, remaining

    async def get_daily_usage(self, date_key: str) -> int:
        async with self._lock:
            return self._daily_counts.get(date_key, 0)

    async def reset(self) -> None:
        async with self._lock:
            self._sliding_windows.clear()
            self._daily_counts.clear()


class UpstashRedisRateStore:
    """Upstash REST-based Redis rate store with automatic fallback to MemoryRateStore."""

    def __init__(self, rest_url: str, rest_token: str) -> None:
        self.rest_url = rest_url.rstrip("/")
        self.rest_token = rest_token
        self.headers = {"Authorization": f"Bearer {rest_token}"}
        self._fallback = MemoryRateStore()

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        try:
            # Multi-command pipeline via Upstash REST: ZREMRANGEBYSCORE, ZADD, ZCARD, EXPIRE
            now = time.time()
            cutoff = now - window_seconds
            redis_key = f"opspilot:ratelimit:{key}"

            commands = [
                ["ZREMRANGEBYSCORE", redis_key, "-inf", str(cutoff)],
                ["ZCARD", redis_key],
            ]

            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.post(
                    f"{self.rest_url}/pipeline",
                    headers=self.headers,
                    json=commands,
                )
                if resp.status_code == 200:
                    results = resp.json()
                    current_count = int(results[1].get("result", 0))
                    if current_count < limit:
                        # Append current timestamp
                        add_cmds = [
                            ["ZADD", redis_key, str(now), str(now)],
                            ["EXPIRE", redis_key, str(window_seconds + 5)],
                        ]
                        await client.post(
                            f"{self.rest_url}/pipeline",
                            headers=self.headers,
                            json=add_cmds,
                        )
                        return True, max(0, limit - current_count - 1), 0

                    return False, 0, window_seconds
        except Exception as e:
            logger.warning("Upstash Redis error on check_rate_limit: %s; falling back to memory store", e)

        return await self._fallback.check_rate_limit(key, limit, window_seconds)

    async def increment_daily_budget(
        self,
        date_key: str,
        max_budget: int,
    ) -> tuple[bool, int, int]:
        try:
            redis_key = f"opspilot:daily:{date_key}"
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.post(
                    f"{self.rest_url}/pipeline",
                    headers=self.headers,
                    json=[
                        ["INCR", redis_key],
                        ["EXPIRE", redis_key, "90000"],  # ~25h expiration
                    ],
                )
                if resp.status_code == 200:
                    results = resp.json()
                    current = int(results[0].get("result", 1))
                    if current > max_budget:
                        return False, current, 0
                    return True, current, max(0, max_budget - current)
        except Exception as e:
            logger.warning("Upstash Redis error on increment_daily_budget: %s; falling back to memory store", e)

        return await self._fallback.increment_daily_budget(date_key, max_budget)

    async def get_daily_usage(self, date_key: str) -> int:
        try:
            redis_key = f"opspilot:daily:{date_key}"
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(
                    f"{self.rest_url}/get/{redis_key}",
                    headers=self.headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    val = data.get("result")
                    return int(val) if val is not None else 0
        except Exception as e:
            logger.warning("Upstash Redis error on get_daily_usage: %s; falling back to memory store", e)

        return await self._fallback.get_daily_usage(date_key)

    async def reset(self) -> None:
        await self._fallback.reset()


_rate_store_instance: RateStore | None = None


def get_rate_store() -> RateStore:
    """Get the active RateStore instance."""
    global _rate_store_instance
    if _rate_store_instance is None:
        settings = get_settings()
        if settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN:
            _rate_store_instance = UpstashRedisRateStore(
                rest_url=settings.UPSTASH_REDIS_REST_URL,
                rest_token=settings.UPSTASH_REDIS_REST_TOKEN,
            )
        else:
            _rate_store_instance = MemoryRateStore()
    return _rate_store_instance


def set_rate_store(store: RateStore | None) -> None:
    """Override the RateStore instance (primarily for tests)."""
    global _rate_store_instance
    _rate_store_instance = store
