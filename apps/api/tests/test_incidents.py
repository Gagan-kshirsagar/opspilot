"""Tests for incidents API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.models.service import Service, ServiceStatus
from app.models.user import User, UserRole
from tests.conftest import _session_factory


@pytest.fixture
async def users_and_tokens(client: AsyncClient) -> dict[str, tuple[uuid.UUID, str]]:
    """Create manager and viewer users and return their info."""
    # Register manager
    resp_mgr = await client.post(
        "/api/v1/auth/register",
        json={"email": "manager@test.com", "password": "securepassword", "name": "Manager"},
    )
    mgr_id = uuid.UUID(resp_mgr.json()["user"]["id"])
    mgr_token = resp_mgr.json()["tokens"]["access_token"]

    # Register viewer
    resp_view = await client.post(
        "/api/v1/auth/register",
        json={"email": "viewer@test.com", "password": "securepassword", "name": "Viewer"},
    )
    view_id = uuid.UUID(resp_view.json()["user"]["id"])
    view_token = resp_view.json()["tokens"]["access_token"]

    # Promote manager to UserRole.MANAGER
    async with _session_factory() as session:
        await session.execute(
            update(User).where(User.id == mgr_id).values(role=UserRole.MANAGER)
        )
        await session.commit()

    return {
        "manager": (mgr_id, mgr_token),
        "viewer": (view_id, view_token),
    }


@pytest.fixture
async def setup_incident_data(
    users_and_tokens: dict[str, tuple[uuid.UUID, str]]
) -> tuple[uuid.UUID, list[uuid.UUID]]:
    """Set up service and multiple incidents."""
    mgr_id, _ = users_and_tokens["manager"]
    now = datetime.now(timezone.utc)
    service_id = uuid.uuid4()
    incident_ids = []

    async with _session_factory() as session:
        srv = Service(
            id=service_id,
            name="Core API",
            status=ServiceStatus.HEALTHY,
            uptime_pct=99.9,
            owner_user_id=mgr_id,
        )
        session.add(srv)

        i1 = Incident(
            id=uuid.uuid4(),
            title="Sev1 Open Outage",
            severity=IncidentSeverity.SEV1,
            status=IncidentStatus.OPEN,
            service_id=service_id,
            assignee_id=mgr_id,
            created_at=now,
        )
        i2 = Incident(
            id=uuid.uuid4(),
            title="Sev3 Investigating Bug",
            severity=IncidentSeverity.SEV3,
            status=IncidentStatus.INVESTIGATING,
            service_id=service_id,
            assignee_id=None,
            created_at=now,
        )
        i3 = Incident(
            id=uuid.uuid4(),
            title="Sev2 Resolved Alert",
            severity=IncidentSeverity.SEV2,
            status=IncidentStatus.RESOLVED,
            service_id=service_id,
            assignee_id=mgr_id,
            resolved_at=now,
            created_at=now,
        )
        session.add_all([i1, i2, i3])
        await session.commit()
        incident_ids.extend([i1.id, i2.id, i3.id])

    return service_id, incident_ids


@pytest.mark.asyncio
async def test_list_incidents_unauthorized(client: AsyncClient) -> None:
    """Anonymous access returns 401."""
    resp = await client.get("/api/v1/incidents")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_incidents_paginated(
    client: AsyncClient,
    users_and_tokens: dict[str, tuple[uuid.UUID, str]],
    setup_incident_data: tuple[uuid.UUID, list[uuid.UUID]],
) -> None:
    """Authenticated user can list incidents with pagination."""
    _, token = users_and_tokens["viewer"]
    resp = await client.get(
        "/api/v1/incidents?page=1&page_size=10",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["items"][0]["service_name"] == "Core API"


@pytest.mark.asyncio
async def test_filter_incidents(
    client: AsyncClient,
    users_and_tokens: dict[str, tuple[uuid.UUID, str]],
    setup_incident_data: tuple[uuid.UUID, list[uuid.UUID]],
) -> None:
    """Filter by severity, status, and service."""
    _, token = users_and_tokens["viewer"]
    service_id, _ = setup_incident_data

    # Filter by severity
    resp_sev = await client.get(
        "/api/v1/incidents?severity=sev1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_sev.status_code == 200
    assert resp_sev.json()["total"] == 1
    assert resp_sev.json()["items"][0]["severity"] == "sev1"

    # Filter by status
    resp_stat = await client.get(
        "/api/v1/incidents?status=open",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_stat.status_code == 200
    assert resp_stat.json()["total"] == 1
    assert resp_stat.json()["items"][0]["status"] == "open"

    # Filter by service_id
    resp_srv = await client.get(
        f"/api/v1/incidents?service_id={service_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_srv.status_code == 200
    assert resp_srv.json()["total"] == 3


@pytest.mark.asyncio
async def test_rank_based_sorting(
    client: AsyncClient,
    users_and_tokens: dict[str, tuple[uuid.UUID, str]],
    setup_incident_data: tuple[uuid.UUID, list[uuid.UUID]],
) -> None:
    """Operational rank sorting for severity (sev1 < sev2 < sev3) and status."""
    _, token = users_and_tokens["viewer"]

    # Severity ascending: sev1 -> sev2 -> sev3
    resp = await client.get(
        "/api/v1/incidents?sort_by=severity&sort_dir=asc",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    severities = [it["severity"] for it in items]
    assert severities == ["sev1", "sev2", "sev3"]

    # Status ascending: open -> investigating -> resolved
    resp_stat = await client.get(
        "/api/v1/incidents?sort_by=status&sort_dir=asc",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_stat.status_code == 200
    stat_items = resp_stat.json()["items"]
    statuses = [it["status"] for it in stat_items]
    assert statuses == ["open", "investigating", "resolved"]


@pytest.mark.asyncio
async def test_resolve_incident_by_manager(
    client: AsyncClient,
    users_and_tokens: dict[str, tuple[uuid.UUID, str]],
    setup_incident_data: tuple[uuid.UUID, list[uuid.UUID]],
) -> None:
    """Manager can resolve an open incident."""
    _, mgr_token = users_and_tokens["manager"]
    _, incident_ids = setup_incident_data
    open_inc_id = incident_ids[0]

    resp = await client.post(
        f"/api/v1/incidents/{open_inc_id}/resolve",
        headers={"Authorization": f"Bearer {mgr_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "resolved"
    assert data["resolved_at"] is not None


@pytest.mark.asyncio
async def test_resolve_incident_forbidden_for_viewer(
    client: AsyncClient,
    users_and_tokens: dict[str, tuple[uuid.UUID, str]],
    setup_incident_data: tuple[uuid.UUID, list[uuid.UUID]],
) -> None:
    """Viewer cannot resolve an incident (403)."""
    _, view_token = users_and_tokens["viewer"]
    _, incident_ids = setup_incident_data
    open_inc_id = incident_ids[0]

    resp = await client.post(
        f"/api/v1/incidents/{open_inc_id}/resolve",
        headers={"Authorization": f"Bearer {view_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_resolve_already_resolved_incident(
    client: AsyncClient,
    users_and_tokens: dict[str, tuple[uuid.UUID, str]],
    setup_incident_data: tuple[uuid.UUID, list[uuid.UUID]],
) -> None:
    """Resolving an already resolved incident returns 409 Conflict."""
    _, mgr_token = users_and_tokens["manager"]
    _, incident_ids = setup_incident_data
    resolved_inc_id = incident_ids[2]

    resp = await client.post(
        f"/api/v1/incidents/{resolved_inc_id}/resolve",
        headers={"Authorization": f"Bearer {mgr_token}"},
    )
    assert resp.status_code == 409
