"""User ORM model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(enum.StrEnum):
    """Roles supported by the system."""

    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"
    GUEST = "guest"


class UserStatus(enum.StrEnum):
    """Account status."""

    ACTIVE = "active"
    PENDING = "pending"
    INACTIVE = "inactive"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represents an application user."""

    __tablename__ = "users"

    email: Mapped[str | None] = mapped_column(
        String(320), unique=True, nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=20),
        nullable=False,
        default=UserRole.VIEWER,
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=False, length=20),
        nullable=False,
        default=UserStatus.ACTIVE,
    )
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_guest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    last_active: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    team = relationship("Team", lazy="selectin")
