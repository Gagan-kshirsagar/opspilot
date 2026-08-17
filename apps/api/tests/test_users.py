"""Tests for users management endpoints."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


@pytest.fixture
async def admin_token(client: AsyncClient) -> str:
    """Register an admin user and return the access token.

    We register a normal user then update the DB directly to make them admin.
    For simplicity we use the register endpoint + manual DB update.
    """
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@test.com",
            "password": "securepassword",
            "name": "Test Admin",
        },
    )
    assert resp.status_code == 201
    token = resp.json()["tokens"]["access_token"]

    # Promote to admin via direct DB manipulation
    from app.models.user import User, UserRole

    from tests.conftest import _session_factory

    async with _session_factory() as session:
        from sqlalchemy import select, update

        user_id = resp.json()["user"]["id"]
        await session.execute(
            update(User)
            .where(User.id == uuid.UUID(user_id))
            .values(role=UserRole.ADMIN)
        )
        await session.commit()

    return token


@pytest.fixture
async def viewer_token(client: AsyncClient) -> str:
    """Register a viewer user and return the access token."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "viewer@test.com",
            "password": "securepassword",
            "name": "Test Viewer",
        },
    )
    assert resp.status_code == 201
    return resp.json()["tokens"]["access_token"]


def _auth(token: str) -> dict[str, str]:
    """Return Authorization header dict."""
    return {"Authorization": f"Bearer {token}"}


# ── List users ────────────────────────────────────────────


class TestListUsers:
    """GET /api/v1/users — pagination, search, filter."""

    async def test_list_users_paginated(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """Returns paginated results with correct structure."""
        resp = await client.get(
            "/api/v1/users",
            params={"page": 1, "page_size": 10},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert data["page"] == 1
        assert data["page_size"] == 10
        # Should have at least the admin user
        assert data["total"] >= 1

    async def test_list_users_search(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """Search by name filters results."""
        resp = await client.get(
            "/api/v1/users",
            params={"search": "Test Admin"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        names = [u["name"] for u in data["items"]]
        assert "Test Admin" in names

    async def test_list_users_filter_role(
        self, client: AsyncClient, admin_token: str, viewer_token: str
    ) -> None:
        """Filter by role returns correct users."""
        resp = await client.get(
            "/api/v1/users",
            params={"role": ["viewer"]},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["role"] == "viewer"

    async def test_list_users_filter_status_and_brackets(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """Filter by status and bracketed parameter formats returns matching users."""
        resp = await client.get(
            "/api/v1/users",
            params={"status[]": ["active"]},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["status"] == "active"

    async def test_list_users_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        """Unauthenticated request returns 401."""
        resp = await client.get("/api/v1/users")
        assert resp.status_code in (401, 403)


# ── Create user ───────────────────────────────────────────


class TestCreateUser:
    """POST /api/v1/users."""

    async def test_create_user_success(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """Admin can create a new user."""
        resp = await client.post(
            "/api/v1/users",
            json={
                "name": "New User",
                "email": "new@test.com",
                "role": "viewer",
                "status": "active",
            },
            headers=_auth(admin_token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New User"
        assert data["email"] == "new@test.com"
        assert data["role"] == "viewer"

    async def test_create_user_duplicate_email(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """Creating a user with a duplicate email returns 409."""
        payload = {
            "name": "Dup User",
            "email": "dup@test.com",
            "role": "viewer",
        }
        resp1 = await client.post(
            "/api/v1/users", json=payload, headers=_auth(admin_token)
        )
        assert resp1.status_code == 201

        resp2 = await client.post(
            "/api/v1/users", json=payload, headers=_auth(admin_token)
        )
        assert resp2.status_code == 409

    async def test_create_user_forbidden_for_viewer(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        """Viewer role cannot create users."""
        resp = await client.post(
            "/api/v1/users",
            json={"name": "Nope", "email": "nope@test.com"},
            headers=_auth(viewer_token),
        )
        assert resp.status_code == 403


# ── Update user ───────────────────────────────────────────


class TestUpdateUser:
    """PATCH /api/v1/users/{id}."""

    async def test_update_user_partial(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """Partial update changes only provided fields."""
        # Create a user first
        create_resp = await client.post(
            "/api/v1/users",
            json={"name": "Updatable", "email": "updatable@test.com"},
            headers=_auth(admin_token),
        )
        assert create_resp.status_code == 201
        user_id = create_resp.json()["id"]

        # Partial update
        resp = await client.patch(
            f"/api/v1/users/{user_id}",
            json={"name": "Updated Name"},
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"
        assert resp.json()["email"] == "updatable@test.com"  # unchanged


# ── Delete user ───────────────────────────────────────────


class TestDeleteUser:
    """DELETE /api/v1/users/{id}."""

    async def test_delete_user_forbidden_for_viewer(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        """Non-admin gets 403."""
        fake_id = str(uuid.uuid4())
        resp = await client.delete(
            f"/api/v1/users/{fake_id}",
            headers=_auth(viewer_token),
        )
        assert resp.status_code == 403

    async def test_delete_user_self(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """Admin cannot delete themselves — returns 400."""
        # Get own user ID from /me
        me_resp = await client.get(
            "/api/v1/auth/me", headers=_auth(admin_token)
        )
        assert me_resp.status_code == 200
        my_id = me_resp.json()["id"]

        resp = await client.delete(
            f"/api/v1/users/{my_id}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 400

    async def test_delete_user_success(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """Admin can delete another user."""
        # Create a user to delete
        create_resp = await client.post(
            "/api/v1/users",
            json={"name": "Deletable", "email": "deletable@test.com"},
            headers=_auth(admin_token),
        )
        assert create_resp.status_code == 201
        user_id = create_resp.json()["id"]

        resp = await client.delete(
            f"/api/v1/users/{user_id}",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 204

        # Verify it's gone
        get_resp = await client.get(
            f"/api/v1/users/{user_id}",
            headers=_auth(admin_token),
        )
        assert get_resp.status_code == 404
