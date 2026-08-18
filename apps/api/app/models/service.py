"""Service ORM model."""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.user import User


class ServiceStatus(enum.StrEnum):
    """Operational status of a service."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class Service(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represents a microservice or system component."""

    __tablename__ = "services"

    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    status: Mapped[ServiceStatus] = mapped_column(
        Enum(ServiceStatus, native_enum=False, length=20),
        nullable=False,
        default=ServiceStatus.HEALTHY,
        index=True,
    )
    uptime_pct: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    owner: Mapped[User] = relationship("User", lazy="selectin")
    incidents: Mapped[list[Incident]] = relationship(
        "Incident", back_populates="service", lazy="noload"
    )
