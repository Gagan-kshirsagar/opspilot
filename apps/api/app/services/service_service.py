"""Service service — business logic for services domain."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service
from app.repositories.service_repo import ServiceRepository
from app.schemas.service import ServiceDetailOut, ServiceListParams, ServiceOut


class ServiceService:
    """Orchestrates service domain operations."""

    async def list_services(
        self, params: ServiceListParams, session: AsyncSession
    ) -> list[ServiceOut]:
        """List services with optional search, filtering, and sorting."""
        repo = ServiceRepository(session)
        services = await repo.list_services(
            search=params.search,
            status_filter=params.status,
            sort_by=params.sort_by.value,
            sort_dir=params.sort_dir.value,
        )
        return [self._to_out(s) for s in services]

    async def get_service(
        self, service_id: uuid.UUID, session: AsyncSession
    ) -> ServiceDetailOut:
        """Fetch a single service by ID with aggregated open incident count."""
        repo = ServiceRepository(session)
        service = await repo.get_by_id(service_id)
        if service is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found.",
            )

        open_incident_count = await repo.get_open_incident_count(service_id)
        return self._to_detail(service, open_incident_count)

    # ── Mappers ───────────────────────────────────────────

    @staticmethod
    def _to_out(service: Service) -> ServiceOut:
        """Map Service ORM model to ServiceOut schema."""
        return ServiceOut(
            id=service.id,
            name=service.name,
            status=service.status.value,
            uptime_pct=service.uptime_pct,
            owner_user_id=service.owner_user_id,
            owner_name=service.owner.name if service.owner else "Unknown",
            note=service.note,
            created_at=service.created_at,
            updated_at=service.updated_at,
        )

    @classmethod
    def _to_detail(cls, service: Service, open_incident_count: int) -> ServiceDetailOut:
        """Map Service ORM model to ServiceDetailOut schema."""
        base = cls._to_out(service)
        return ServiceDetailOut(
            **base.model_dump(),
            open_incident_count=open_incident_count,
        )
