"""add teams table and extend users

Revision ID: 002
Revises: 001
Create Date: 2026-08-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Create teams table ────────────────────────────────
    op.create_table(
        "teams",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
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

    # ── Extend users table ────────────────────────────────
    op.add_column(
        "users",
        sa.Column(
            "team_id",
            sa.Uuid(),
            sa.ForeignKey("teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column("last_active", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_team_id", "users", ["team_id"])


def downgrade() -> None:
    op.drop_index("ix_users_team_id", table_name="users")
    op.drop_column("users", "last_active")
    op.drop_column("users", "team_id")
    op.drop_table("teams")
