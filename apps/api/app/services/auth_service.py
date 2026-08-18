"""Auth service — orchestrates provider + repository for auth operations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repo import UserRepository
from app.schemas.auth import AuthResponse, AuthUserResponse
from app.schemas.auth import TokenPair as TokenPairSchema
from app.services.auth.base import AuthProvider, AuthUser
from app.services.auth.base import TokenPair as TokenPairInternal


class AuthService:
    """Thin orchestration layer between the router and the auth provider.

    Handles business-level concerns (duplicate emails, mapping to response
    schemas) so the router stays maximally thin.
    """

    def __init__(self, provider: AuthProvider) -> None:
        self._provider = provider

    async def register(
        self, email: str, password: str, name: str, session: AsyncSession
    ) -> AuthResponse:
        """Register a new user; raise 409 if the email is taken."""
        repo = UserRepository(session)
        existing = await repo.get_by_email(email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        auth_user = await self._provider.create_user(email, password, name, session)
        tokens = self._provider.issue_tokens(auth_user)
        return self._build_response(auth_user, tokens)

    async def login(
        self, email: str, password: str, session: AsyncSession
    ) -> AuthResponse:
        """Authenticate with email + password; raise 401 on failure."""
        auth_user = await self._provider.authenticate(email, password, session)
        if auth_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        tokens = self._provider.issue_tokens(auth_user)
        return self._build_response(auth_user, tokens)

    async def guest_login(self, session: AsyncSession) -> AuthResponse:
        """Create a demo guest and return tokens."""
        auth_user = await self._provider.create_guest(session)
        tokens = self._provider.issue_tokens(auth_user)
        return self._build_response(auth_user, tokens)

    def refresh(self, refresh_token: str) -> TokenPairSchema:
        """Validate a refresh token and issue a new token pair.

        Raises 401 if the refresh token is invalid or expired.
        """
        try:
            claims = self._provider.verify_token(refresh_token)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            ) from None

        if claims.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is not a refresh token.",
            )

        # Re-issue tokens using the claims embedded in the refresh token.
        user = AuthUser(
            id=uuid.UUID(claims.sub),
            email=None,
            name="",
            role=claims.role,
            is_guest=claims.role == "guest",
        )
        tokens = self._provider.issue_tokens(user)
        return TokenPairSchema(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type="bearer",
            expires_in=tokens.expires_in,
        )

    # ── Helpers ───────────────────────────────────────────

    @staticmethod
    def _build_response(auth_user: AuthUser, tokens: TokenPairInternal) -> AuthResponse:
        """Map internal dataclasses → Pydantic response schemas."""
        user_resp = AuthUserResponse(
            id=auth_user.id,
            email=auth_user.email,
            name=auth_user.name,
            role=auth_user.role,
            status="active",
            is_guest=auth_user.is_guest,
            created_at=datetime.now(UTC),
        )
        token_resp = TokenPairSchema(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type="bearer",
            expires_in=tokens.expires_in,
        )
        return AuthResponse(user=user_resp, tokens=token_resp)
