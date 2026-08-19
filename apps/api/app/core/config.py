"""Application configuration — all values via OPSPILOT_* env vars."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised, typed settings loaded from environment variables.

    Every field is prefixed ``OPSPILOT_`` in the environment
    (e.g. ``OPSPILOT_DATABASE_URL``).
    """

    model_config = SettingsConfigDict(
        env_prefix="OPSPILOT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/opspilot"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("postgres://"):
                v = "postgresql+asyncpg://" + v[len("postgres://") :]
            elif v.startswith("postgresql://"):
                v = "postgresql+asyncpg://" + v[len("postgresql://") :]
            if "sslmode=" in v:
                v = v.replace("sslmode=require", "ssl=require").replace(
                    "sslmode=", "ssl="
                )
        return v

    # ── Auth / JWT ────────────────────────────────────────
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_COOKIE_NAME: str = "opspilot_refresh_token"
    REFRESH_COOKIE_SECURE: bool = False
    REFRESH_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"

    # ── Auth provider ─────────────────────────────────────
    AUTH_PROVIDER: str = "jwt"

    # ── CORS ──────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://opspilot-eight-zeta.vercel.app",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                import json

                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ── RAG / Gemini / Agent ──────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GEMINI_CHAT_MODEL: str = "gemini-3.1-flash-lite"
    GEMINI_MAX_OUTPUT_TOKENS: int = 1024
    RAG_TOP_K: int = 4
    RAG_SIMILARITY_THRESHOLD: float = 0.55
    RAG_TEMPERATURE: float = 0.2
    AGENT_MAX_ITERS: int = 4
    AGENT_TEMPERATURE: float = 0.2

    # ── Rate Limiting & Daily AI Budget ───────────────────
    REDIS_URL: str | None = None
    UPSTASH_REDIS_REST_URL: str | None = None
    UPSTASH_REDIS_REST_TOKEN: str | None = None
    AI_RATE_LIMIT_REQUESTS: int = 10
    AI_RATE_LIMIT_WINDOW_SECONDS: int = 600
    API_RATE_LIMIT_REQUESTS: int = 60
    API_RATE_LIMIT_WINDOW_SECONDS: int = 60
    DAILY_AI_LIMIT: int = 500


def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()
