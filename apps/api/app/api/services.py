"""Services router — list and detail endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.engine import get_session
from app.models.user import User
from app.schemas.auth import ErrorResponse
from app.schemas.service import (
    ServiceDetailOut,
    ServiceListParams,
    ServiceOut,
    ServiceSortByField,
)
from app.schemas.user import SortDirection
from app.services.service_service import ServiceService

router = APIRouter(prefix="/api/v1/services", tags=["services"])

_service = ServiceService()


# ── GET / — list services ─────────────────────────────────


@router.get(
    "",
    response_model=list[ServiceOut],
)
async def list_services(
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[User, Depends(get_current_user)],
    search: str | None = Query(default=None),
    status_filter: list[str] | None = Query(default=None, alias="status"),
    status_bracket: list[str] | None = Query(default=None, alias="status[]"),
    sort_by: ServiceSortByField = Query(default=ServiceSortByField.NAME),
    sort_dir: SortDirection = Query(default=SortDirection.ASC),
) -> list[ServiceOut]:
    """List all services with optional search, status filtering, and sorting."""
    resolved_status = status_filter or status_bracket
    params = ServiceListParams(
        search=search,
        status=resolved_status,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return await _service.list_services(params, session)


# ── GET /{id} — get service detail ────────────────────────


@router.get(
    "/{service_id}",
    response_model=ServiceDetailOut,
    responses={404: {"model": ErrorResponse}},
)
async def get_service(
    service_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[User, Depends(get_current_user)],
) -> ServiceDetailOut:
    """Get service detail including count of active open incidents."""
    return await _service.get_service(service_id, session)
