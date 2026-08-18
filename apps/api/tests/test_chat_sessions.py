"""Tests for chat session management and user isolation."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.models.chat import MessageRole
from app.repositories.chat_repo import ChatRepository
from tests.conftest import _session_factory


@pytest.fixture
async def user_a_token(client: AsyncClient) -> str:
    """Register User A and return token."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_a@test.com",
            "password": "password123",
            "name": "User A",
        },
    )
    assert resp.status_code == 201
    return resp.json()["tokens"]["access_token"]


@pytest.fixture
async def user_b_token(client: AsyncClient) -> str:
    """Register User B and return token."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_b@test.com",
            "password": "password123",
            "name": "User B",
        },
    )
    assert resp.status_code == 201
    return resp.json()["tokens"]["access_token"]


@pytest.mark.asyncio
async def test_chat_session_lifecycle(client: AsyncClient, user_a_token: str) -> None:
    """Test creating messages in a session and retrieving list & detail."""
    # List sessions initially empty
    resp = await client.get(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []

    # Create session directly in DB
    async with _session_factory() as session:
        # Get user A ID
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {user_a_token}"},
        )
        user_a_id = uuid.UUID(me_resp.json()["id"])
        repo = ChatRepository(session)
        s = await repo.create_session(user_a_id, title="Test Incident Discussion")
        await repo.add_message(
            s.id, MessageRole.USER, "What happened with API gateway?"
        )
        await repo.add_message(
            s.id, MessageRole.ASSISTANT, "API gateway had latency spike."
        )
        await session.commit()
        session_id = str(s.id)

    # List sessions now returns 1 session
    resp = await client.get(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert resp.status_code == 200
    sessions = resp.json()
    assert len(sessions) == 1
    assert sessions[0]["id"] == session_id
    assert sessions[0]["title"] == "Test Incident Discussion"

    # Get session detail with messages
    resp_detail = await client.get(
        f"/api/v1/chat/sessions/{session_id}",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert resp_detail.status_code == 200
    detail = resp_detail.json()
    assert detail["title"] == "Test Incident Discussion"
    assert len(detail["messages"]) == 2
    assert detail["messages"][0]["role"] == "user"
    assert detail["messages"][1]["role"] == "assistant"

    # Delete session
    del_resp = await client.delete(
        f"/api/v1/chat/sessions/{session_id}",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert del_resp.status_code == 204

    # Verify deleted
    resp_detail_after = await client.get(
        f"/api/v1/chat/sessions/{session_id}",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert resp_detail_after.status_code == 404


@pytest.mark.asyncio
async def test_chat_session_user_isolation(
    client: AsyncClient,
    user_a_token: str,
    user_b_token: str,
) -> None:
    """User B cannot access or delete User A's chat session (403)."""
    # Create session for User A
    async with _session_factory() as session:
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {user_a_token}"},
        )
        user_a_id = uuid.UUID(me_resp.json()["id"])
        repo = ChatRepository(session)
        s = await repo.create_session(user_a_id, title="User A Confidential Chat")
        await session.commit()
        user_a_session_id = str(s.id)

    # User B attempts to access User A's session -> 403 Forbidden
    resp = await client.get(
        f"/api/v1/chat/sessions/{user_a_session_id}",
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert resp.status_code == 403
    assert "forbidden" in resp.json()["detail"].lower()

    # User B attempts to delete User A's session -> 404/403
    del_resp = await client.delete(
        f"/api/v1/chat/sessions/{user_a_session_id}",
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert del_resp.status_code == 404
