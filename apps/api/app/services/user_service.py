"""User service — business logic for user management."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from passlib.hash import bcrypt  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole, UserStatus
from app.repositories.user_repo import UserRepository
from app.schemas.user import (
    CreateUserRequest,
    PaginatedUsers,
    UpdateUserRequest,
    UserDetailResponse,
    UserListParams,
    UserRow,
)


class UserService:
    """Orchestrates user CRUD operations."""

    async def list_users(
        self, params: UserListParams, session: AsyncSession
    ) -> PaginatedUsers:
        """List users with pagination, sorting, and filtering."""
        repo = UserRepository(session)
        users, total = await repo.list_paginated(
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by.value,
            sort_dir=params.sort_dir.value,
            search=params.search,
            role_filter=params.role,
            status_filter=params.status,
            team_id_filter=params.team_id,
        )

        items = [self._to_row(u) for u in users]
        return PaginatedUsers(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def get_user(
        self, user_id: uuid.UUID, session: AsyncSession
    ) -> UserDetailResponse:
        """Fetch a single user by ID."""
        repo = UserRepository(session)
        user = await repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return self._to_detail(user)

    async def create_user(
        self, data: CreateUserRequest, session: AsyncSession
    ) -> UserDetailResponse:
        """Create a new user. Raises 409 if email is taken."""
        repo = UserRepository(session)

        existing = await repo.get_by_email(data.email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )

        password_hash = None
        if data.password:
            password_hash = bcrypt.hash(data.password)

        user = User(
            id=uuid.uuid4(),
            name=data.name,
            email=data.email,
            role=UserRole(data.role),
            status=UserStatus(data.status),
            team_id=data.team_id,
            password_hash=password_hash,
            is_guest=False,
        )
        created = await repo.create(user)
        return self._to_detail(created)

    async def update_user(
        self,
        user_id: uuid.UUID,
        data: UpdateUserRequest,
        session: AsyncSession,
    ) -> UserDetailResponse:
        """Partially update a user. Raises 404/409 as appropriate."""
        repo = UserRepository(session)
        user = await repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if data.email is not None and data.email != user.email:
            existing = await repo.get_by_email(data.email)
            if existing is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A user with this email already exists.",
                )
            user.email = data.email

        if data.name is not None:
            user.name = data.name
        if data.role is not None:
            user.role = UserRole(data.role)
        if data.status is not None:
            user.status = UserStatus(data.status)
        if data.team_id is not None:
            user.team_id = data.team_id
        if data.password is not None:
            user.password_hash = bcrypt.hash(data.password)

        updated = await repo.update(user)
        return self._to_detail(updated)

    async def delete_user(
        self,
        user_id: uuid.UUID,
        current_user_id: uuid.UUID,
        session: AsyncSession,
    ) -> None:
        """Delete a user. Cannot delete yourself."""
        if user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot delete your own account.",
            )

        repo = UserRepository(session)
        user = await repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        await repo.delete(user)

    async def delete_users(
        self,
        ids: list[uuid.UUID],
        current_user_id: uuid.UUID,
        session: AsyncSession,
    ) -> int:
        """Bulk-delete users. Excludes the current user from deletion."""
        safe_ids = [uid for uid in ids if uid != current_user_id]
        if not safe_ids:
            return 0
        repo = UserRepository(session)
        return await repo.delete_many(safe_ids)

    # ── Mappers ───────────────────────────────────────────

    @staticmethod
    def _to_row(user: User) -> UserRow:
        """Map a User ORM model to a UserRow schema."""
        return UserRow(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.value,
            status=user.status.value,
            team_name=user.team.name if user.team else None,
            team_id=user.team_id,
            is_guest=user.is_guest,
            last_active=user.last_active,
            created_at=user.created_at,
        )

    @staticmethod
    def _to_detail(user: User) -> UserDetailResponse:
        """Map a User ORM model to a UserDetailResponse schema."""
        return UserDetailResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.value,
            status=user.status.value,
            team_name=user.team.name if user.team else None,
            team_id=user.team_id,
            is_guest=user.is_guest,
            last_active=user.last_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
