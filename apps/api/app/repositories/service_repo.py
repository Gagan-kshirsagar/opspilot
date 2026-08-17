"""Service repository — all DB access for service entities."""

from __future__ import annotations

import uuid

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident, IncidentStatus
from app.models.service import Service, ServiceStatus


class ServiceRepository:
    """Encapsulates all service-related database queries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, service_id: uuid.UUID) -> Service | None:
        """Fetch a service by primary key."""
        return await self._session.get(Service, service_id)

    async def get_open_incident_count(self, service_id: uuid.UUID) -> int:
        """Return the number of open/investigating incidents for a service."""
        stmt = (
            select(func.count())
            .select_from(Incident)
            .where(
                Incident.service_id == service_id,
                Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.INVESTIGATING]),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def list_services(
        self,
        *,
        search: str | None = None,
        status_filter: list[str] | None = None,
        sort_by: str = "name",
        sort_dir: str = "asc",
    ) -> list[Service]:
        """List services with search, status filtering, and sorting."""
        base: Select[tuple[Service]] = select(Service)

        # ── Filters ──────────────────────────────────────
        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(
                    Service.name.ilike(pattern),
                    Service.note.ilike(pattern),
                )
            )

        if status_filter:
            statuses = [
                ServiceStatus(s)
                for s in status_filter
                if s in ServiceStatus._value2member_map_
            ]
            if statuses:
                base = base.where(Service.status.in_(statuses))

        # ── Sorting ──────────────────────────────────────
        sort_column = getattr(Service, sort_by, Service.name)
        order = sort_column.desc() if sort_dir == "desc" else sort_column.asc()
        base = base.order_by(order)

        result = await self._session.execute(base)
        return list(result.scalars().all())
