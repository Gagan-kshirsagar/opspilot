"""Tests for services API endpoints."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.models.service import Service, ServiceStatus
from app.models.user import User, UserRole
from tests.conftest import _session_factory


@pytest.fixture
async def auth_user_and_token(client: AsyncClient) -> tuple[uuid.UUID, str]:
    """Register a user and return (user_id, token)."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "tester@test.com",
            "password": "securepassword",
            "name": "Service Tester",
        },
    )
    assert resp.status_code == 201
    user_id = uuid.UUID(resp.json()["user"]["id"])
    token = resp.json()["tokens"]["access_token"]
    return user_id, token


@pytest.fixture
async def setup_services(auth_user_and_token: tuple[uuid.UUID, str]) -> list[uuid.UUID]:
    """Insert test services."""
    user_id, _ = auth_user_and_token
    service_ids = []
    async with _session_factory() as session:
        s1 = Service(
            id=uuid.uuid4(),
            name="API Gateway",
            status=ServiceStatus.HEALTHY,
            uptime_pct=99.99,
            owner_user_id=user_id,
            note="Edge proxy",
        )
        s2 = Service(
            id=uuid.uuid4(),
            name="Payment Service",
            status=ServiceStatus.DEGRADED,
            uptime_pct=97.5,
            owner_user_id=user_id,
            note="Payment processor",
        )
        s3 = Service(
            id=uuid.uuid4(),
            name="Search Service",
            status=ServiceStatus.DOWN,
            uptime_pct=85.0,
            owner_user_id=user_id,
            note="Search indexing engine",
        )
        session.add_all([s1, s2, s3])
        await session.commit()
        service_ids.extend([s1.id, s2.id, s3.id])
    return service_ids


@pytest.mark.asyncio
async def test_list_services_unauthorized(client: AsyncClient) -> None:
    """Anonymous access should be rejected with 401."""
    resp = await client.get("/api/v1/services")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_services_success(
    client: AsyncClient,
    auth_user_and_token: tuple[uuid.UUID, str],
    setup_services: list[uuid.UUID],
) -> None:
    """Authenticated user can list all services."""
    _, token = auth_user_and_token
    resp = await client.get(
        "/api/v1/services",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    names = [s["name"] for s in data]
    assert "API Gateway" in names
    assert data[0]["owner_name"] == "Service Tester"


@pytest.mark.asyncio
async def test_filter_services_by_status(
    client: AsyncClient,
    auth_user_and_token: tuple[uuid.UUID, str],
    setup_services: list[uuid.UUID],
) -> None:
    """Filter services by status."""
    _, token = auth_user_and_token
    resp = await client.get(
        "/api/v1/services?status=degraded",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Payment Service"


@pytest.mark.asyncio
async def test_search_services(
    client: AsyncClient,
    auth_user_and_token: tuple[uuid.UUID, str],
    setup_services: list[uuid.UUID],
) -> None:
    """Search services by name or note substring."""
    _, token = auth_user_and_token
    resp = await client.get(
        "/api/v1/services?search=indexing",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Search Service"


@pytest.mark.asyncio
async def test_get_service_detail(
    client: AsyncClient,
    auth_user_and_token: tuple[uuid.UUID, str],
    setup_services: list[uuid.UUID],
) -> None:
    """Get single service detail with open_incident_count."""
    _, token = auth_user_and_token
    service_id = setup_services[0]
    resp = await client.get(
        f"/api/v1/services/{service_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(service_id)
    assert data["open_incident_count"] == 0


@pytest.mark.asyncio
async def test_get_service_not_found(
    client: AsyncClient,
    auth_user_and_token: tuple[uuid.UUID, str],
) -> None:
    """Unknown service ID returns 404."""
    _, token = auth_user_and_token
    non_existent = uuid.uuid4()
    resp = await client.get(
        f"/api/v1/services/{non_existent}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
