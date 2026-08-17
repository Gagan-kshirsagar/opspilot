"""Incident service — business logic for incidents domain."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident, IncidentStatus
from app.repositories.incident_repo import IncidentRepository
from app.schemas.incident import IncidentListParams, IncidentOut, PaginatedIncidents


class IncidentService:
    """Orchestrates incident domain operations."""

    async def list_incidents(
        self, params: IncidentListParams, session: AsyncSession
    ) -> PaginatedIncidents:
        """List incidents with pagination, ranking sort, and filtering."""
        repo = IncidentRepository(session)
        incidents, total = await repo.list_paginated(
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by.value,
            sort_dir=params.sort_dir.value,
            search=params.search,
            status_filter=params.status,
            severity_filter=params.severity,
            service_id_filter=params.service_id,
        )

        items = [self._to_out(inc) for inc in incidents]
        return PaginatedIncidents(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def get_incident(
        self, incident_id: uuid.UUID, session: AsyncSession
    ) -> IncidentOut:
        """Fetch a single incident by ID."""
        repo = IncidentRepository(session)
        incident = await repo.get_by_id(incident_id)
        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found.",
            )
        return self._to_out(incident)

    async def resolve_incident(
        self, incident_id: uuid.UUID, session: AsyncSession
    ) -> IncidentOut:
        """Mark an open incident as resolved.

        Raises 404 if missing, 409 if already resolved.
        """
        repo = IncidentRepository(session)
        incident = await repo.get_by_id(incident_id)
        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found.",
            )

        if incident.status == IncidentStatus.RESOLVED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Incident is already resolved.",
            )

        resolved = await repo.resolve(incident)
        return self._to_out(resolved)

    # ── Mappers ───────────────────────────────────────────

    @staticmethod
    def _to_out(incident: Incident) -> IncidentOut:
        """Map Incident ORM model to IncidentOut schema."""
        return IncidentOut(
            id=incident.id,
            title=incident.title,
            severity=incident.severity.value,
            status=incident.status.value,
            service_id=incident.service_id,
            service_name=incident.service.name if incident.service else "Unknown Service",
            assignee_id=incident.assignee_id,
            assignee_name=incident.assignee.name if incident.assignee else None,
            resolved_at=incident.resolved_at,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
        )
