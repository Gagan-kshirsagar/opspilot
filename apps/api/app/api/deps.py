"""FastAPI dependencies for authentication and authorisation."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.services.auth.base import AuthProvider
from app.services.auth.factory import get_auth_provider

# Reusable security scheme — extracts Bearer token from Authorization header.
_bearer_scheme = HTTPBearer(auto_error=False)


def _get_provider() -> AuthProvider:
    """Return the singleton auth provider."""
    return get_auth_provider()


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
    provider: Annotated[AuthProvider, Depends(_get_provider)],
) -> User:
    """Verify the Bearer token and load the full User from the DB.

    Raises ``401`` if the token is missing, invalid, expired, or the
    user no longer exists.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = provider.verify_token(credentials.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    if claims.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not an access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repo = UserRepository(session)
    user = await repo.get_by_id(uuid.UUID(claims.sub))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_optional(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
    provider: Annotated[AuthProvider, Depends(_get_provider)],
) -> User | None:
    """Extract user if valid token present, else return None."""
    if credentials is None:
        return None

    try:
        claims = provider.verify_token(credentials.credentials)
        if claims.type != "access":
            return None
        repo = UserRepository(session)
        return await repo.get_by_id(uuid.UUID(claims.sub))
    except Exception:
        return None


def require_role(
    *allowed_roles: str,
) -> Callable[..., Coroutine[Any, Any, User]]:
    """Return a dependency that enforces role-based access.

    Usage::

        @router.get("/admin-only")
        async def admin_view(
            user: Annotated[User, Depends(require_role("admin"))],
        ) -> ...:
    """

    async def _check(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return user

    return _check
