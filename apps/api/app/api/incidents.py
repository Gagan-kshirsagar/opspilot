"""Incidents router — list, detail, and resolve endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.db.engine import get_session
from app.models.user import User
from app.schemas.auth import ErrorResponse
from app.schemas.incident import (
    IncidentListParams,
    IncidentOut,
    IncidentSortByField,
    PaginatedIncidents,
)
from app.schemas.user import SortDirection
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])

_service = IncidentService()


# ── GET / — list incidents (paginated) ────────────────────


@router.get(
    "",
    response_model=PaginatedIncidents,
)
async def list_incidents(
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: IncidentSortByField = Query(default=IncidentSortByField.CREATED_AT),
    sort_dir: SortDirection = Query(default=SortDirection.DESC),
    search: str | None = Query(default=None),
    status_filter: list[str] | None = Query(default=None, alias="status"),
    status_bracket: list[str] | None = Query(default=None, alias="status[]"),
    severity: list[str] | None = Query(default=None),
    severity_bracket: list[str] | None = Query(default=None, alias="severity[]"),
    service_id: uuid.UUID | None = Query(default=None),
) -> PaginatedIncidents:
    """List incidents with server-side pagination, rank sorting, and filtering."""
    resolved_status = status_filter or status_bracket
    resolved_severity = severity or severity_bracket
    params = IncidentListParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
        search=search,
        status=resolved_status,
        severity=resolved_severity,
        service_id=service_id,
    )
    return await _service.list_incidents(params, session)


# ── GET /{id} — get incident detail ──────────────────────


@router.get(
    "/{incident_id}",
    response_model=IncidentOut,
    responses={404: {"model": ErrorResponse}},
)
async def get_incident(
    incident_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[User, Depends(get_current_user)],
) -> IncidentOut:
    """Get single incident details."""
    return await _service.get_incident(incident_id, session)


# ── POST /{id}/resolve — resolve incident ─────────────────


@router.post(
    "/{incident_id}/resolve",
    response_model=IncidentOut,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def resolve_incident(
    incident_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[User, Depends(require_role("admin", "manager"))],
) -> IncidentOut:
    """Mark an incident as resolved. Requires admin or manager role."""
    return await _service.resolve_incident(incident_id, session)
