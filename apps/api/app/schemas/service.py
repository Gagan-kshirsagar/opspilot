"""Pydantic v2 schemas for service endpoints."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import SortDirection


class ServiceSortByField(str, enum.Enum):
    """Allowed sort columns for service listing."""

    NAME = "name"
    STATUS = "status"
    UPTIME_PCT = "uptime_pct"
    CREATED_AT = "created_at"


class ServiceListParams(BaseModel):
    """Query parameters for GET /services."""

    search: str | None = None
    status: list[str] | None = None
    sort_by: ServiceSortByField = ServiceSortByField.NAME
    sort_dir: SortDirection = SortDirection.ASC


class ServiceOut(BaseModel):
    """Service item representation in list and detail responses."""

    id: uuid.UUID
    name: str
    status: str
    uptime_pct: float
    owner_user_id: uuid.UUID
    owner_name: str
    note: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ServiceDetailOut(ServiceOut):
    """Service detail with aggregated open incidents."""

    open_incident_count: int = 0
