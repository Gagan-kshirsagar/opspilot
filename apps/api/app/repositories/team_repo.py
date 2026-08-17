"""Team repository — all DB access for team entities."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team


class TeamRepository:
    """Encapsulates all team-related database queries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Team]:
        """Return all teams, ordered by name."""
        stmt = select(Team).order_by(Team.name.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
