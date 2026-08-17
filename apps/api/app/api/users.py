"""Users router — CRUD with pagination, sorting, filtering, and RBAC."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.db.engine import get_session
from app.models.user import User
from app.schemas.auth import ErrorResponse
from app.schemas.user import (
    BulkDeleteRequest,
    BulkDeleteResponse,
    CreateUserRequest,
    PaginatedUsers,
    SortByField,
    SortDirection,
    UpdateUserRequest,
    UserDetailResponse,
    UserListParams,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])

_service = UserService()


# ── GET / — list users (paginated) ───────────────────────


@router.get(
    "",
    response_model=PaginatedUsers,
)
async def list_users(
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: SortByField = Query(default=SortByField.CREATED_AT),
    sort_dir: SortDirection = Query(default=SortDirection.DESC),
    search: str | None = Query(default=None),
    role: list[str] | None = Query(default=None),
    role_bracket: list[str] | None = Query(default=None, alias="role[]"),
    status_filter: list[str] | None = Query(default=None, alias="status"),
    status_bracket: list[str] | None = Query(default=None, alias="status[]"),
    team_id: uuid.UUID | None = Query(default=None),
) -> PaginatedUsers:
    """List users with server-side pagination, sorting, and filtering."""
    resolved_role = role or role_bracket
    resolved_status = status_filter or status_bracket
    params = UserListParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
        search=search,
        role=resolved_role,
        status=resolved_status,
        team_id=team_id,
    )
    return await _service.list_users(params, session)


# ── GET /{id} — get single user ──────────────────────────


@router.get(
    "/{user_id}",
    response_model=UserDetailResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_user(
    user_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[User, Depends(get_current_user)],
) -> UserDetailResponse:
    """Get a single user by ID."""
    return await _service.get_user(user_id, session)


# ── POST / — create user ─────────────────────────────────


@router.post(
    "",
    response_model=UserDetailResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
async def create_user(
    body: CreateUserRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[User, Depends(require_role("admin", "manager"))],
) -> UserDetailResponse:
    """Create a new user. Requires admin or manager role."""
    return await _service.create_user(body, session)


# ── PATCH /{id} — update user ────────────────────────────


@router.patch(
    "/{user_id}",
    response_model=UserDetailResponse,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def update_user(
    user_id: uuid.UUID,
    body: UpdateUserRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[User, Depends(require_role("admin", "manager"))],
) -> UserDetailResponse:
    """Update a user (partial). Requires admin or manager role."""
    return await _service.update_user(user_id, body, session)


# ── DELETE /{id} — delete user ────────────────────────────


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def delete_user(
    user_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(require_role("admin"))],
) -> None:
    """Delete a user. Requires admin role. Cannot delete yourself."""
    await _service.delete_user(user_id, current_user.id, session)


# ── POST /bulk-delete — bulk delete ──────────────────────


@router.post(
    "/bulk-delete",
    response_model=BulkDeleteResponse,
)
async def bulk_delete_users(
    body: BulkDeleteRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(require_role("admin"))],
) -> BulkDeleteResponse:
    """Bulk-delete users. Requires admin role. Cannot delete yourself."""
    deleted = await _service.delete_users(body.ids, current_user.id, session)
    return BulkDeleteResponse(deleted=deleted)
