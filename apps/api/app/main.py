"""OpsPilot API — FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.incidents import router as incidents_router
from app.api.services import router as services_router
from app.api.teams import router as teams_router
from app.api.users import router as users_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup / shutdown hooks."""
    # Startup: nothing to do yet (engine is lazy-created in db/engine.py)
    yield
    # Shutdown: dispose the engine so connections are released.
    from app.db.engine import engine

    await engine.dispose()


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title="OpsPilot API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(teams_router)
    app.include_router(services_router)
    app.include_router(incidents_router)
    app.include_router(chat_router)

    return app


app = create_app()
