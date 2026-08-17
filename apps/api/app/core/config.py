"""Application configuration — all values via OPSPILOT_* env vars."""

from __future__ import annotations

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

    # ── Auth / JWT ────────────────────────────────────────
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_COOKIE_NAME: str = "opspilot_refresh_token"
    REFRESH_COOKIE_SECURE: bool = False
    REFRESH_COOKIE_SAMESITE: str = "lax"

    # ── Auth provider ─────────────────────────────────────
    AUTH_PROVIDER: str = "jwt"

    # ── CORS ──────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]


def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()
