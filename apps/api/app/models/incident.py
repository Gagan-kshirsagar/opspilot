"""Incident ORM model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.service import Service
    from app.models.user import User


class IncidentSeverity(enum.StrEnum):
    """Severity levels for incidents."""

    SEV1 = "sev1"
    SEV2 = "sev2"
    SEV3 = "sev3"


class IncidentStatus(enum.StrEnum):
    """Incident lifecycle status."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class Incident(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represents an operational incident."""

    __tablename__ = "incidents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity, native_enum=False, length=20),
        nullable=False,
        default=IncidentSeverity.SEV3,
        index=True,
    )
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus, native_enum=False, length=20),
        nullable=False,
        default=IncidentStatus.OPEN,
        index=True,
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    service: Mapped[Service] = relationship(
        "Service", back_populates="incidents", lazy="selectin"
    )
    assignee: Mapped[User | None] = relationship("User", lazy="selectin")
