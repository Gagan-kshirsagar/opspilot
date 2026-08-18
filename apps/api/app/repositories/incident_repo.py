"""Incident repository — all DB access for incident entities."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.models.service import Service


class IncidentRepository:
    """Encapsulates all incident-related database queries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, incident_id: uuid.UUID) -> Incident | None:
        """Fetch an incident by primary key."""
        return await self._session.get(Incident, incident_id)

    async def resolve(self, incident: Incident) -> Incident:
        """Mark an incident as resolved and record resolved_at timestamp."""
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(incident)
        return incident

    async def list_paginated(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        search: str | None = None,
        status_filter: list[str] | None = None,
        severity_filter: list[str] | None = None,
        service_id_filter: uuid.UUID | None = None,
    ) -> tuple[list[Incident], int]:
        """List incidents with server-side pagination, sorting, and filtering.

        Supports operational rank sorting for severity (sev1 < sev2 < sev3)
        and status (open < investigating < resolved).
        """
        base: Select[tuple[Incident]] = select(Incident)

        # ── Filters ──────────────────────────────────────
        if search:
            pattern = f"%{search}%"
            base = base.where(Incident.title.ilike(pattern))

        if status_filter:
            statuses = [
                IncidentStatus(s)
                for s in status_filter
                if s in IncidentStatus._value2member_map_
            ]
            if statuses:
                base = base.where(Incident.status.in_(statuses))

        if severity_filter:
            severities = [
                IncidentSeverity(s)
                for s in severity_filter
                if s in IncidentSeverity._value2member_map_
            ]
            if severities:
                base = base.where(Incident.severity.in_(severities))

        if service_id_filter is not None:
            base = base.where(Incident.service_id == service_id_filter)

        # ── Count ────────────────────────────────────────
        count_stmt = select(func.count()).select_from(base.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        # ── Sorting ──────────────────────────────────────
        sort_expr: Any
        if sort_by == "severity":
            sort_expr = case(
                (Incident.severity == IncidentSeverity.SEV1, 1),
                (Incident.severity == IncidentSeverity.SEV2, 2),
                (Incident.severity == IncidentSeverity.SEV3, 3),
                else_=4,
            )
        elif sort_by == "status":
            sort_expr = case(
                (Incident.status == IncidentStatus.OPEN, 1),
                (Incident.status == IncidentStatus.INVESTIGATING, 2),
                (Incident.status == IncidentStatus.RESOLVED, 3),
                else_=4,
            )
        elif sort_by == "service_name":
            base = base.outerjoin(Service, Incident.service_id == Service.id)
            sort_expr = Service.name
        else:
            sort_expr = getattr(Incident, sort_by, Incident.created_at)

        order = sort_expr.desc() if sort_dir == "desc" else sort_expr.asc()
        base = base.order_by(order)

        # ── Pagination ───────────────────────────────────
        offset = (page - 1) * page_size
        base = base.offset(offset).limit(page_size)

        result = await self._session.execute(base)
        incidents = list(result.scalars().all())

        return incidents, total
