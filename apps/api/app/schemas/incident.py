"""Pydantic v2 schemas for incident endpoints."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import SortDirection


class IncidentSortByField(enum.StrEnum):
    """Allowed sort columns for incident listing."""

    TITLE = "title"
    SEVERITY = "severity"
    STATUS = "status"
    SERVICE_NAME = "service_name"
    CREATED_AT = "created_at"


class IncidentListParams(BaseModel):
    """Query parameters for GET /incidents."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: IncidentSortByField = IncidentSortByField.CREATED_AT
    sort_dir: SortDirection = SortDirection.DESC
    search: str | None = None
    status: list[str] | None = None
    severity: list[str] | None = None
    service_id: uuid.UUID | None = None


class IncidentOut(BaseModel):
    """Incident item representation in list and detail responses."""

    id: uuid.UUID
    title: str
    severity: str
    status: str
    service_id: uuid.UUID
    service_name: str
    assignee_id: uuid.UUID | None = None
    assignee_name: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedIncidents(BaseModel):
    """Paginated incident list response."""

    items: list[IncidentOut]
    total: int
    page: int
    page_size: int
