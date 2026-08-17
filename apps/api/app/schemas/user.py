"""Pydantic v2 request / response schemas for user management endpoints."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Enums ─────────────────────────────────────────────────


class SortByField(str, enum.Enum):
    """Allowed sort columns for user listing."""

    NAME = "name"
    EMAIL = "email"
    ROLE = "role"
    STATUS = "status"
    CREATED_AT = "created_at"
    LAST_ACTIVE = "last_active"


class SortDirection(str, enum.Enum):
    """Sort direction."""

    ASC = "asc"
    DESC = "desc"


# ── Query params ──────────────────────────────────────────


class UserListParams(BaseModel):
    """Query parameters for GET /users."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: SortByField = SortByField.CREATED_AT
    sort_dir: SortDirection = SortDirection.DESC
    search: str | None = None
    role: list[str] | None = None
    status: list[str] | None = None
    team_id: uuid.UUID | None = None


# ── Response schemas ──────────────────────────────────────


class UserRow(BaseModel):
    """Single user row in the list response."""

    id: uuid.UUID
    name: str
    email: str | None
    role: str
    status: str
    team_name: str | None
    team_id: uuid.UUID | None
    is_guest: bool
    last_active: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedUsers(BaseModel):
    """Paginated user list response."""

    items: list[UserRow]
    total: int
    page: int
    page_size: int


class UserDetailResponse(BaseModel):
    """Full user detail response."""

    id: uuid.UUID
    name: str
    email: str | None
    role: str
    status: str
    team_name: str | None
    team_id: uuid.UUID | None
    is_guest: bool
    last_active: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Request schemas ───────────────────────────────────────


class CreateUserRequest(BaseModel):
    """POST /users body."""

    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    role: str = Field(default="viewer")
    status: str = Field(default="active")
    team_id: uuid.UUID | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UpdateUserRequest(BaseModel):
    """PATCH /users/{id} body — all fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    role: str | None = None
    status: str | None = None
    team_id: uuid.UUID | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class BulkDeleteRequest(BaseModel):
    """POST /users/bulk-delete body."""

    ids: list[uuid.UUID] = Field(min_length=1)


class BulkDeleteResponse(BaseModel):
    """Response for bulk delete."""

    deleted: int
