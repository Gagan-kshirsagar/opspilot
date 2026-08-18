"""FastAPI rate limiting dependencies and request key extractors."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.api.deps import get_current_user_optional
from app.core.config import get_settings
from app.core.rate_store import get_rate_store
from app.models.user import User

logger = logging.getLogger(__name__)


def extract_client_key(request: Request, user: User | None = None) -> str:
    """Extract rate limit key based on user ID if authenticated, else client IP."""
    if user is not None:
        return f"user:{user.id}"

    # Check proxy headers
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
        if ip:
            return f"ip:{ip}"

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return f"ip:{real_ip.strip()}"

    client_host = request.client.host if request.client else "127.0.0.1"
    return f"ip:{client_host}"


async def require_ai_rate_limit(
    request: Request,
    user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> str:
    """Enforce per-client AI message rate limit. Raises 429 if exceeded."""
    settings = get_settings()
    store = get_rate_store()
    client_key = extract_client_key(request, user)

    allowed, remaining, retry_after = await store.check_rate_limit(
        key=f"ai:{client_key}",
        limit=settings.AI_RATE_LIMIT_REQUESTS,
        window_seconds=settings.AI_RATE_LIMIT_WINDOW_SECONDS,
    )

    if not allowed:
        mins = max(1, round(settings.AI_RATE_LIMIT_WINDOW_SECONDS / 60))
        msg = (
            f"Rate limit reached: you've sent {settings.AI_RATE_LIMIT_REQUESTS} AI messages "
            f"within {mins} minutes. Please wait {retry_after} seconds before asking again."
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=msg,
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(settings.AI_RATE_LIMIT_REQUESTS),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(retry_after),
            },
        )

    return client_key


async def require_api_rate_limit(
    request: Request,
    user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> str:
    """Enforce general API request rate limit for non-AI endpoints."""
    settings = get_settings()
    store = get_rate_store()
    client_key = extract_client_key(request, user)

    allowed, remaining, retry_after = await store.check_rate_limit(
        key=f"api:{client_key}",
        limit=settings.API_RATE_LIMIT_REQUESTS,
        window_seconds=settings.API_RATE_LIMIT_WINDOW_SECONDS,
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"API rate limit exceeded. Please wait {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    return client_key
