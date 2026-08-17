"""add services and incidents tables

Revision ID: 003
Revises: 002
Create Date: 2026-08-17
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Create services table ─────────────────────────────
    op.create_table(
        "services",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="healthy"),
        sa.Column("uptime_pct", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column(
            "owner_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_services_name", "services", ["name"])
    op.create_index("ix_services_status", "services", ["status"])
    op.create_index("ix_services_owner_user_id", "services", ["owner_user_id"])

    # ── Create incidents table ────────────────────────────
    op.create_table(
        "incidents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="sev3"),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column(
            "service_id",
            sa.Uuid(),
            sa.ForeignKey("services.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assignee_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incidents_severity", "incidents", ["severity"])
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_service_id", "incidents", ["service_id"])
    op.create_index("ix_incidents_assignee_id", "incidents", ["assignee_id"])


def downgrade() -> None:
    op.drop_index("ix_incidents_assignee_id", table_name="incidents")
    op.drop_index("ix_incidents_service_id", table_name="incidents")
    op.drop_index("ix_incidents_status", table_name="incidents")
    op.drop_index("ix_incidents_severity", table_name="incidents")
    op.drop_table("incidents")

    op.drop_index("ix_services_owner_user_id", table_name="services")
    op.drop_index("ix_services_status", table_name="services")
    op.drop_index("ix_services_name", table_name="services")
    op.drop_table("services")
