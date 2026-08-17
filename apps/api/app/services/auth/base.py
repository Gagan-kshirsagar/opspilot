"""AuthProvider protocol — the pluggable seam for authentication backends."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True, slots=True)
class AuthUser:
    """Lightweight user identity returned by auth operations."""

    id: uuid.UUID
    email: str | None
    name: str
    role: str
    is_guest: bool


@dataclass(frozen=True, slots=True)
class TokenPair:
    """Access + refresh token pair."""

    access_token: str
    refresh_token: str
    expires_in: int  # seconds until access_token expires


@dataclass(frozen=True, slots=True)
class TokenClaims:
    """Decoded claims from a verified token."""

    sub: str  # user id
    role: str
    type: str  # "access" | "refresh"


class AuthProvider(Protocol):
    """Strategy interface for authentication backends.

    Routers and services depend ONLY on this protocol, never on a
    concrete JWT / Firebase implementation.
    """

    async def authenticate(
        self, email: str, password: str, session: AsyncSession
    ) -> AuthUser | None:
        """Verify credentials and return the user, or ``None``."""
        ...

    async def create_user(
        self, email: str, password: str, name: str, session: AsyncSession
    ) -> AuthUser:
        """Register a new user and return it."""
        ...

    def issue_tokens(self, user: AuthUser) -> TokenPair:
        """Mint an access + refresh token pair for *user*."""
        ...

    def verify_token(self, token: str) -> TokenClaims:
        """Decode and validate *token*; raise on failure."""
        ...

    async def create_guest(self, session: AsyncSession) -> AuthUser:
        """Create an ephemeral guest user for demo access."""
        ...
