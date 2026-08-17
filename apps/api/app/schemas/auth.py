"""Pydantic v2 request / response schemas for auth endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Requests ──────────────────────────────────────────────


class RegisterRequest(BaseModel):
    """POST /register body."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """POST /login body."""

    email: EmailStr
    password: str = Field(min_length=1)


class RefreshRequest(BaseModel):
    """POST /refresh body."""

    refresh_token: str | None = None


# ── Responses ─────────────────────────────────────────────


class TokenPair(BaseModel):
    """Pair of access + refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access_token expires


class AuthUserResponse(BaseModel):
    """Public user representation returned by the API."""

    id: uuid.UUID
    email: str | None
    name: str
    role: str
    status: str
    is_guest: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Combined user + tokens, returned on register / login / guest."""

    user: AuthUserResponse
    tokens: TokenPair


class ErrorResponse(BaseModel):
    """Standard error body."""

    detail: str
