"""Seed the database with teams and realistic users.

Usage:
    python -m app.seed.seed

Idempotent — skips if teams already exist.
"""

from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from passlib.hash import bcrypt  # type: ignore[import-untyped]
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session_factory, engine
from app.models.team import Team
from app.models.user import User, UserRole, UserStatus

# ── Seed data ─────────────────────────────────────────────

TEAM_NAMES = [
    "Engineering",
    "Product",
    "Design",
    "Sales",
    "Support",
    "Executive",
]

FIRST_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "George",
    "Hannah", "Ivan", "Julia", "Kevin", "Laura", "Michael", "Nina",
    "Oscar", "Patricia", "Quinn", "Rachel", "Samuel", "Tina",
    "Ursula", "Victor", "Wendy", "Xavier", "Yvonne", "Zachary",
    "Aiden", "Bella", "Caleb", "Daphne", "Elena", "Felix", "Grace",
    "Henry", "Iris", "Jake", "Kira", "Leo", "Maya", "Nathan",
    "Olivia", "Paul", "Rosa", "Sean", "Tara", "Uma", "Vera",
    "Will", "Xena", "Yara", "Zoe",
]

LAST_NAMES = [
    "Anderson", "Brown", "Chen", "Davis", "Evans", "Foster",
    "Garcia", "Hayes", "Ibrahim", "Johnson", "Kim", "Lee",
    "Martinez", "Nguyen", "O'Brien", "Patel", "Quinn", "Rodriguez",
    "Smith", "Taylor", "Ueda", "Vasquez", "Wang", "Xu", "Yang", "Zhang",
]

ROLE_WEIGHTS: list[tuple[UserRole, float]] = [
    (UserRole.ADMIN, 0.08),
    (UserRole.MANAGER, 0.18),
    (UserRole.VIEWER, 0.64),
    (UserRole.GUEST, 0.10),
]

STATUS_WEIGHTS: list[tuple[UserStatus, float]] = [
    (UserStatus.ACTIVE, 0.72),
    (UserStatus.PENDING, 0.15),
    (UserStatus.INACTIVE, 0.13),
]


def _pick_weighted(choices: list[tuple[object, float]]) -> object:
    """Pick a value from a weighted list."""
    values, weights = zip(*choices, strict=False)
    return random.choices(values, weights=weights, k=1)[0]


async def _seed(session: AsyncSession) -> None:
    """Insert teams and users if the DB is empty."""
    # Check idempotency
    existing = await session.execute(select(Team).limit(1))
    if existing.scalar_one_or_none() is not None:
        print("⏭  Teams already exist — skipping seed.")
        return

    # ── Insert teams ──────────────────────────────────────
    teams: list[Team] = []
    for name in TEAM_NAMES:
        team = Team(id=uuid.uuid4(), name=name)
        session.add(team)
        teams.append(team)

    await session.flush()
    print(f"✓  Inserted {len(teams)} teams.")

    # ── Insert users ──────────────────────────────────────
    now = datetime.now(timezone.utc)
    used_emails: set[str] = set()
    users_created = 0

    # Ensure at least one admin
    admin = User(
        id=uuid.uuid4(),
        name="Admin User",
        email="admin@opspilot.dev",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        password_hash=bcrypt.hash("admin123"),
        is_guest=False,
        team_id=teams[0].id,  # Engineering
        last_active=now - timedelta(minutes=random.randint(5, 120)),
    )
    session.add(admin)
    used_emails.add("admin@opspilot.dev")
    users_created += 1

    for i in range(49):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"

        # Generate unique email
        base_email = f"{first.lower()}.{last.lower()}@opspilot.dev"
        email = base_email
        suffix = 1
        while email in used_emails:
            email = f"{first.lower()}.{last.lower()}{suffix}@opspilot.dev"
            suffix += 1
        used_emails.add(email)

        role: UserRole = _pick_weighted(ROLE_WEIGHTS)  # type: ignore[assignment]
        user_status: UserStatus = _pick_weighted(STATUS_WEIGHTS)  # type: ignore[assignment]
        is_guest = role == UserRole.GUEST
        team = random.choice(teams) if not is_guest else None

        # Random last_active in past 30 days (None for some inactive)
        last_active = None
        if user_status == UserStatus.ACTIVE:
            last_active = now - timedelta(
                hours=random.randint(1, 720),
                minutes=random.randint(0, 59),
            )

        user = User(
            id=uuid.uuid4(),
            name=name,
            email=email if not is_guest else None,
            role=role,
            status=user_status,
            password_hash=bcrypt.hash("password123") if not is_guest else None,
            is_guest=is_guest,
            team_id=team.id if team else None,
            last_active=last_active,
        )
        session.add(user)
        users_created += 1

    await session.flush()
    print(f"✓  Inserted {users_created} users.")


async def main() -> None:
    """Entry point for the seed script."""
    async with async_session_factory() as session:
        await _seed(session)
        await session.commit()
    await engine.dispose()
    print("🌱 Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
