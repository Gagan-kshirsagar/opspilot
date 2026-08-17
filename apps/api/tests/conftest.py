"""Shared test fixtures — async SQLite DB + httpx test client."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Force SQLite for tests + jwt provider before anything imports settings.
os.environ.setdefault("OPSPILOT_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("OPSPILOT_AUTH_PROVIDER", "jwt")
os.environ.setdefault("OPSPILOT_JWT_SECRET", "test-secret-do-not-use")

from app.db.engine import get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402

_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
_session_factory = async_sessionmaker(
    _engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(autouse=True)
async def _setup_db() -> AsyncGenerator[None, None]:
    """Create all tables before each test, drop after."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide the test session to FastAPI dependencies."""
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Override the real session dependency with our in-memory SQLite session.
app.dependency_overrides[get_session] = _override_session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async httpx test client bound to the FastAPI app."""
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
