"""User repository — all DB access for user entities."""

from __future__ import annotations

import uuid

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.models.user import User, UserRole, UserStatus


class UserRepository:
    """Encapsulates all user-related database queries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Fetch a user by primary key."""
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email address."""
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Persist a new user and return it with generated fields."""
        self._session.add(user)
        await self._session.flush()  # populate id / defaults
        await self._session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """Flush pending changes on the user and refresh from DB."""
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Remove a user from the database."""
        await self._session.delete(user)
        await self._session.flush()

    async def delete_many(self, ids: list[uuid.UUID]) -> int:
        """Bulk-delete users by ID. Returns the number of deleted rows."""
        stmt = delete(User).where(User.id.in_(ids))
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount  # type: ignore[return-value]

    async def list_paginated(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        search: str | None = None,
        role_filter: list[str] | None = None,
        status_filter: list[str] | None = None,
        team_id_filter: uuid.UUID | None = None,
    ) -> tuple[list[User], int]:
        """List users with server-side pagination, sorting, and filtering.

        Returns a tuple of (users, total_count).
        """
        base: Select[tuple[User]] = select(User)

        # ── Filters ──────────────────────────────────────
        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(
                    User.name.ilike(pattern),
                    User.email.ilike(pattern),
                )
            )
        if role_filter:
            roles = [
                UserRole(r) if isinstance(r, str) and r in UserRole._value2member_map_ else r
                for r in role_filter
            ]
            base = base.where(User.role.in_(roles))
        if status_filter:
            statuses = [
                UserStatus(s) if isinstance(s, str) and s in UserStatus._value2member_map_ else s
                for s in status_filter
            ]
            base = base.where(User.status.in_(statuses))
        if team_id_filter is not None:
            base = base.where(User.team_id == team_id_filter)

        # ── Count ────────────────────────────────────────
        count_stmt = select(func.count()).select_from(base.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        # ── Sorting ──────────────────────────────────────
        sort_column = getattr(User, sort_by, User.created_at)
        # For team_name sorting, we'd need a join — fall back to created_at
        if sort_by == "team_name":
            base = base.outerjoin(Team, User.team_id == Team.id)
            sort_column = Team.name

        order = sort_column.desc() if sort_dir == "desc" else sort_column.asc()
        base = base.order_by(order)

        # ── Pagination ───────────────────────────────────
        offset = (page - 1) * page_size
        base = base.offset(offset).limit(page_size)

        result = await self._session.execute(base)
        users = list(result.scalars().all())

        return users, total
