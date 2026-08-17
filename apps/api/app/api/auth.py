"""Auth router — thin endpoints that delegate to AuthService."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.engine import get_session
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    AuthUserResponse,
    ErrorResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from app.services.auth.factory import get_auth_provider
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _get_service() -> AuthService:
    """Build the auth service from the configured provider."""
    return AuthService(get_auth_provider())


# ── POST /register ────────────────────────────────────────


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
async def register(
    body: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[AuthService, Depends(_get_service)],
) -> AuthResponse:
    """Register a new account with email + password."""
    return await service.register(body.email, body.password, body.name, session)


# ── POST /login ───────────────────────────────────────────


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={401: {"model": ErrorResponse}},
)
async def login(
    body: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[AuthService, Depends(_get_service)],
) -> AuthResponse:
    """Authenticate with email + password."""
    return await service.login(body.email, body.password, session)


# ── POST /guest ───────────────────────────────────────────


@router.post(
    "/guest",
    response_model=AuthResponse,
)
async def guest_login(
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[AuthService, Depends(_get_service)],
) -> AuthResponse:
    """Create an ephemeral demo guest account."""
    return await service.guest_login(session)


# ── POST /refresh ─────────────────────────────────────────


@router.post(
    "/refresh",
    response_model=TokenPair,
    responses={401: {"model": ErrorResponse}},
)
async def refresh(
    body: RefreshRequest,
    service: Annotated[AuthService, Depends(_get_service)],
) -> TokenPair:
    """Exchange a refresh token for a new token pair."""
    return service.refresh(body.refresh_token)


# ── GET /me ───────────────────────────────────────────────


@router.get(
    "/me",
    response_model=AuthUserResponse,
    responses={401: {"model": ErrorResponse}},
)
async def me(
    user: Annotated[User, Depends(get_current_user)],
) -> AuthUserResponse:
    """Return the currently authenticated user."""
    return AuthUserResponse.model_validate(user)


# ── POST /logout ──────────────────────────────────────────


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout() -> Response:
    """Logout — stateless: the client discards its tokens."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)
