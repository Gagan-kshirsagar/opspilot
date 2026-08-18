"""Seed the database with teams, realistic users, services, and incidents.

Usage:
    python -m app.seed.seed

Idempotent — skips if teams already exist.
"""

from __future__ import annotations

import asyncio
import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from passlib.hash import bcrypt  # type: ignore[import-untyped]
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session_factory, engine
from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.models.service import Service, ServiceStatus
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
    "Alice",
    "Bob",
    "Charlie",
    "Diana",
    "Ethan",
    "Fiona",
    "George",
    "Hannah",
    "Ivan",
    "Julia",
    "Kevin",
    "Laura",
    "Michael",
    "Nina",
    "Oscar",
    "Patricia",
    "Quinn",
    "Rachel",
    "Samuel",
    "Tina",
    "Ursula",
    "Victor",
    "Wendy",
    "Xavier",
    "Yvonne",
    "Zachary",
    "Aiden",
    "Bella",
    "Caleb",
    "Daphne",
    "Elena",
    "Felix",
    "Grace",
    "Henry",
    "Iris",
    "Jake",
    "Kira",
    "Leo",
    "Maya",
    "Nathan",
    "Olivia",
    "Paul",
    "Rosa",
    "Sean",
    "Tara",
    "Uma",
    "Vera",
    "Will",
    "Xena",
    "Yara",
    "Zoe",
]

LAST_NAMES = [
    "Anderson",
    "Brown",
    "Chen",
    "Davis",
    "Evans",
    "Foster",
    "Garcia",
    "Hayes",
    "Ibrahim",
    "Johnson",
    "Kim",
    "Lee",
    "Martinez",
    "Nguyen",
    "O'Brien",
    "Patel",
    "Quinn",
    "Rodriguez",
    "Smith",
    "Taylor",
    "Ueda",
    "Vasquez",
    "Wang",
    "Xu",
    "Yang",
    "Zhang",
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


def _pick_weighted(choices: Any) -> Any:
    """Pick a value from a weighted list."""
    values, weights = zip(*choices, strict=False)
    return random.choices(values, weights=weights, k=1)[0]


async def _seed(session: AsyncSession) -> None:
    """Insert teams, users, services, and incidents if DB is empty."""
    # Check idempotency
    existing = await session.execute(select(Team).limit(1))
    if existing.scalar_one_or_none() is not None:
        print("⏭  Teams already exist — checking services and incidents...")
        existing_srv = await session.execute(select(Service).limit(1))
        if existing_srv.scalar_one_or_none() is not None:
            print("⏭  Services already exist — skipping seed.")
            return

    # ── Insert teams (if not exist) ───────────────────────────
    teams_result = await session.execute(select(Team))
    teams: list[Team] = list(teams_result.scalars().all())

    if not teams:
        for name in TEAM_NAMES:
            team = Team(id=uuid.uuid4(), name=name)
            session.add(team)
            teams.append(team)

        await session.flush()
        print(f"✓  Inserted {len(teams)} teams.")

    # ── Insert users (if not exist) ───────────────────────────
    users_result = await session.execute(select(User))
    all_users: list[User] = list(users_result.scalars().all())

    now = datetime.now(UTC)

    if not all_users:
        used_emails: set[str] = set()

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
        all_users.append(admin)
        used_emails.add("admin@opspilot.dev")

        # Ensure at least one manager
        manager = User(
            id=uuid.uuid4(),
            name="Manager User",
            email="manager@opspilot.dev",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
            password_hash=bcrypt.hash("manager123"),
            is_guest=False,
            team_id=teams[0].id,  # Engineering
            last_active=now - timedelta(minutes=random.randint(5, 120)),
        )
        session.add(manager)
        all_users.append(manager)
        used_emails.add("manager@opspilot.dev")

        for _ in range(48):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            name = f"{first} {last}"

            base_email = f"{first.lower()}.{last.lower()}@opspilot.dev"
            email = base_email
            suffix = 1
            while email in used_emails:
                email = f"{first.lower()}.{last.lower()}{suffix}@opspilot.dev"
                suffix += 1
            used_emails.add(email)

            role: UserRole = _pick_weighted(ROLE_WEIGHTS)
            user_status: UserStatus = _pick_weighted(STATUS_WEIGHTS)
            is_guest = role == UserRole.GUEST
            user_team: Team | None = random.choice(teams) if not is_guest else None

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
                team_id=user_team.id if user_team else None,
                last_active=last_active,
            )
            session.add(user)
            all_users.append(user)

        await session.flush()
        print(f"✓  Inserted {len(all_users)} users.")

    # ── Insert services ───────────────────────────────────────
    existing_services = await session.execute(select(Service).limit(1))
    if existing_services.scalar_one_or_none() is not None:
        print("⏭  Services already exist — skipping services & incidents seed.")
        return

    admin_user = next((u for u in all_users if u.role == UserRole.ADMIN), all_users[0])
    manager_users = [u for u in all_users if u.role == UserRole.MANAGER]
    mgr1 = manager_users[0] if manager_users else admin_user
    mgr2 = manager_users[1] if len(manager_users) > 1 else admin_user
    viewer_users = [u for u in all_users if u.role == UserRole.VIEWER]
    view1 = viewer_users[0] if viewer_users else admin_user
    view2 = viewer_users[1] if len(viewer_users) > 1 else admin_user

    service_definitions = [
        (
            "API Gateway",
            ServiceStatus.HEALTHY,
            99.98,
            admin_user.id,
            "Primary edge reverse proxy and traffic router",
        ),
        (
            "Auth Service",
            ServiceStatus.HEALTHY,
            99.95,
            admin_user.id,
            "Handles token validation and OAuth federation",
        ),
        (
            "Payment Processing",
            ServiceStatus.DEGRADED,
            97.30,
            mgr1.id,
            "Stripe and external settlement pipeline - elevated retry rates",
        ),
        (
            "Search Index",
            ServiceStatus.DOWN,
            84.50,
            mgr2.id,
            "Elasticsearch cluster offline due to out-of-memory error",
        ),
        (
            "Notification Service",
            ServiceStatus.HEALTHY,
            99.90,
            view1.id,
            "SMS, email and webhook dispatch worker fleet",
        ),
        (
            "Analytics Pipeline",
            ServiceStatus.DEGRADED,
            95.20,
            view2.id,
            "Kafka stream lag detected on telemetry consumer group",
        ),
    ]

    services: list[Service] = []
    for name, status, uptime, owner_id, note in service_definitions:
        srv = Service(
            id=uuid.uuid4(),
            name=name,
            status=status,
            uptime_pct=uptime,
            owner_user_id=owner_id,
            note=note,
        )
        session.add(srv)
        services.append(srv)

    await session.flush()
    print(f"✓  Inserted {len(services)} services.")

    # ── Insert incidents ──────────────────────────────────────
    # Map service names for deterministic association
    srv_by_name = {s.name: s for s in services}

    incident_definitions = [
        # (title, severity, status, srv_name, assignee_user, hours_ago, is_resolved)
        (
            "Elasticsearch memory exhaustion and node crash",
            IncidentSeverity.SEV1,
            IncidentStatus.OPEN,
            "Search Index",
            mgr2,
            2,
            False,
        ),
        (
            "Stripe webhook latency spike > 4000ms",
            IncidentSeverity.SEV2,
            IncidentStatus.INVESTIGATING,
            "Payment Processing",
            mgr1,
            5,
            False,
        ),
        (
            "Telemetry partition 3 rebalance loop",
            IncidentSeverity.SEV2,
            IncidentStatus.INVESTIGATING,
            "Analytics Pipeline",
            view2,
            8,
            False,
        ),
        (
            "TLS certificate expiration warning (3 days)",
            IncidentSeverity.SEV3,
            IncidentStatus.OPEN,
            "API Gateway",
            admin_user,
            12,
            False,
        ),
        (
            "SMS provider rate limit reached for non-critical alerts",
            IncidentSeverity.SEV3,
            IncidentStatus.OPEN,
            "Notification Service",
            view1,
            16,
            False,
        ),
        (
            "Intermittent 502 Bad Gateway during pod auto-scaling",
            IncidentSeverity.SEV1,
            IncidentStatus.RESOLVED,
            "API Gateway",
            admin_user,
            24,
            True,
        ),
        (
            "Token refresh deadlock under high concurrency",
            IncidentSeverity.SEV2,
            IncidentStatus.RESOLVED,
            "Auth Service",
            admin_user,
            36,
            True,
        ),
        (
            "Duplicate charge events generated on retry",
            IncidentSeverity.SEV1,
            IncidentStatus.RESOLVED,
            "Payment Processing",
            mgr1,
            48,
            True,
        ),
        (
            "Kafka broker disk utilization exceeded 90%",
            IncidentSeverity.SEV2,
            IncidentStatus.RESOLVED,
            "Analytics Pipeline",
            view2,
            72,
            True,
        ),
        (
            "Email delivery delayed via SendGrid bounce surge",
            IncidentSeverity.SEV3,
            IncidentStatus.RESOLVED,
            "Notification Service",
            view1,
            96,
            True,
        ),
        (
            "Search query timeout for wildcard queries",
            IncidentSeverity.SEV2,
            IncidentStatus.INVESTIGATING,
            "Search Index",
            mgr2,
            110,
            False,
        ),
        (
            "OAuth PKCE state mismatch on mobile callback",
            IncidentSeverity.SEV3,
            IncidentStatus.RESOLVED,
            "Auth Service",
            admin_user,
            120,
            True,
        ),
        (
            "Downstream bank gateway maintenance outage",
            IncidentSeverity.SEV1,
            IncidentStatus.RESOLVED,
            "Payment Processing",
            mgr1,
            140,
            True,
        ),
        (
            "Redis caching layer evictions causing latency",
            IncidentSeverity.SEV2,
            IncidentStatus.OPEN,
            "API Gateway",
            admin_user,
            150,
            False,
        ),
        (
            "Metrics aggregation task memory leak",
            IncidentSeverity.SEV3,
            IncidentStatus.INVESTIGATING,
            "Analytics Pipeline",
            view2,
            170,
            False,
        ),
        (
            "Dead letter queue overflow for failed webhooks",
            IncidentSeverity.SEV3,
            IncidentStatus.RESOLVED,
            "Notification Service",
            view1,
            200,
            True,
        ),
        (
            "High load on read replicas causing replication lag",
            IncidentSeverity.SEV2,
            IncidentStatus.RESOLVED,
            "Auth Service",
            admin_user,
            220,
            True,
        ),
        (
            "Cluster index sharding imbalance after cluster upgrade",
            IncidentSeverity.SEV2,
            IncidentStatus.RESOLVED,
            "Search Index",
            mgr2,
            250,
            True,
        ),
        (
            "Credit card validation regex backtrack freeze",
            IncidentSeverity.SEV1,
            IncidentStatus.RESOLVED,
            "Payment Processing",
            mgr1,
            280,
            True,
        ),
        (
            "Weekly batch report executor thread starved",
            IncidentSeverity.SEV3,
            IncidentStatus.RESOLVED,
            "Analytics Pipeline",
            view2,
            300,
            True,
        ),
    ]

    incidents_created = 0
    for (
        title,
        severity,
        inc_status,
        srv_name,
        assignee,
        hours_ago,
        is_resolved,
    ) in incident_definitions:
        created_time = now - timedelta(hours=hours_ago)
        resolved_time = (
            created_time + timedelta(hours=random.randint(1, 4))
            if is_resolved
            else None
        )

        inc = Incident(
            id=uuid.uuid4(),
            title=title,
            severity=severity,
            status=inc_status,
            service_id=srv_by_name[srv_name].id,
            assignee_id=assignee.id if assignee else None,
            created_at=created_time,
            updated_at=resolved_time or created_time,
            resolved_at=resolved_time,
        )
        session.add(inc)
        incidents_created += 1

    await session.flush()
    print(f"✓  Inserted {incidents_created} incidents.")


async def main() -> None:
    """Entry point for the seed script."""
    async with async_session_factory() as session:
        await _seed(session)
        await session.commit()
    await engine.dispose()
    print("🌱 Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
