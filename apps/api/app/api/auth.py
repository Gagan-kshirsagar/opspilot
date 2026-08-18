from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
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


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Attach httpOnly refresh token cookie to the response."""
    settings = get_settings()
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age,
        httponly=True,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        secure=settings.REFRESH_COOKIE_SECURE,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Remove httpOnly refresh token cookie from the client."""
    settings = get_settings()
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path="/",
    )


# ── POST /register ────────────────────────────────────────


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
async def register(
    body: RegisterRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[AuthService, Depends(_get_service)],
) -> AuthResponse:
    """Register a new account with email + password."""
    result = await service.register(body.email, body.password, body.name, session)
    _set_refresh_cookie(response, result.tokens.refresh_token)
    return result


# ── POST /login ───────────────────────────────────────────


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={401: {"model": ErrorResponse}},
)
async def login(
    body: LoginRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[AuthService, Depends(_get_service)],
) -> AuthResponse:
    """Authenticate with email + password."""
    result = await service.login(body.email, body.password, session)
    _set_refresh_cookie(response, result.tokens.refresh_token)
    return result


# ── POST /guest ───────────────────────────────────────────


@router.post(
    "/guest",
    response_model=AuthResponse,
)
async def guest_login(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[AuthService, Depends(_get_service)],
) -> AuthResponse:
    """Create an ephemeral demo guest account."""
    result = await service.guest_login(session)
    _set_refresh_cookie(response, result.tokens.refresh_token)
    return result


# ── POST /refresh ─────────────────────────────────────────


@router.post(
    "/refresh",
    response_model=TokenPair,
    responses={401: {"model": ErrorResponse}},
)
async def refresh(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(_get_service)],
    body: RefreshRequest | None = None,
) -> TokenPair:
    """Exchange a refresh token (from body or cookie) for a new token pair."""
    settings = get_settings()
    token_str = (
        body.refresh_token
        if body and body.refresh_token
        else request.cookies.get(settings.REFRESH_COOKIE_NAME)
    )

    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required.",
        )

    new_tokens = service.refresh(token_str)
    _set_refresh_cookie(response, new_tokens.refresh_token)
    return new_tokens


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
async def logout(response: Response) -> Response:
    """Logout — clears the refresh token cookie."""
    _clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
