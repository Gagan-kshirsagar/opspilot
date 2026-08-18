"""Auth endpoint tests — happy paths + failure cases."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

_REGISTER = "/api/v1/auth/register"
_LOGIN = "/api/v1/auth/login"
_GUEST = "/api/v1/auth/guest"
_REFRESH = "/api/v1/auth/refresh"
_ME = "/api/v1/auth/me"


@pytest.fixture
async def registered_user(client: AsyncClient) -> dict[str, object]:
    """Register a user and return the response JSON."""
    resp = await client.post(
        _REGISTER,
        json={
            "email": "alice@example.com",
            "password": "strongpass123",
            "name": "Alice",
        },
    )
    assert resp.status_code == 201
    return resp.json()


# ── 1. Register → Login → /me happy path ─────────────────


async def test_register_login_me(
    client: AsyncClient, registered_user: dict[str, object]
) -> None:
    """Full happy-path: register, login with same creds, then GET /me."""
    data = registered_user
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["name"] == "Alice"
    assert data["user"]["role"] == "viewer"
    assert data["tokens"]["token_type"] == "bearer"

    # Login with the same credentials.
    login_resp = await client.post(
        _LOGIN,
        json={"email": "alice@example.com", "password": "strongpass123"},
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()["tokens"]

    # GET /me with the access token.
    me_resp = await client.get(
        _ME,
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "alice@example.com"
    assert me_data["name"] == "Alice"


# ── 2. Login with wrong password → 401 ───────────────────


async def test_login_wrong_password(
    client: AsyncClient, registered_user: dict[str, object]
) -> None:
    """Bad password must return 401."""
    resp = await client.post(
        _LOGIN,
        json={"email": "alice@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert "Invalid" in resp.json()["detail"]


# ── 3. Guest login → usable token with role=guest ────────


async def test_guest_login(client: AsyncClient) -> None:
    """Guest endpoint returns a usable token with role=guest."""
    resp = await client.post(_GUEST)
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["role"] == "guest"
    assert data["user"]["is_guest"] is True

    # Token works for /me.
    me_resp = await client.get(
        _ME,
        headers={"Authorization": f"Bearer {data['tokens']['access_token']}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["role"] == "guest"


# ── 4. Refresh → new tokens; invalid token → 401 ────────


async def test_refresh_token(
    client: AsyncClient, registered_user: dict[str, object]
) -> None:
    """Refresh returns new tokens; garbage token returns 401."""
    refresh_token = registered_user["tokens"]["refresh_token"]  # type: ignore[index]

    # Valid refresh.
    resp = await client.post(_REFRESH, json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    # Invalid refresh token.
    bad_resp = await client.post(_REFRESH, json={"refresh_token": "not-a-real-token"})
    assert bad_resp.status_code == 401


# ── 5. /me without token → 401 ───────────────────────────


async def test_me_without_token(client: AsyncClient) -> None:
    """GET /me with no Authorization header returns 401."""
    resp = await client.get(_ME)
    assert resp.status_code == 401


# ── 6. Refresh via httpOnly cookie + Logout clears cookie ─


async def test_refresh_via_cookie_and_logout(
    client: AsyncClient, registered_user: dict[str, object]
) -> None:
    """Verify cookies are set on login, /refresh works via cookie, and logout clears cookie."""
    login_resp = await client.post(
        _LOGIN,
        json={"email": "alice@example.com", "password": "strongpass123"},
    )
    assert login_resp.status_code == 200
    assert "opspilot_refresh_token" in login_resp.cookies

    # POST /refresh with empty body should pick up the cookie from client session
    refresh_resp = await client.post(_REFRESH)
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert "access_token" in new_tokens
    assert "opspilot_refresh_token" in refresh_resp.cookies

    # POST /logout should delete the cookie
    logout_resp = await client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 204
    assert (
        "opspilot_refresh_token" not in logout_resp.cookies
        or logout_resp.cookies.get("opspilot_refresh_token") == ""
    )
