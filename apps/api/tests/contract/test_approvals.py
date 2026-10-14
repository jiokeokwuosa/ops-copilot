"""Contract tests for approval resolve API (OpenAPI resolveApproval)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_resolve_approval_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/v1/threads/11111111-1111-1111-1111-111111111111/"
            "approvals/33333333-3333-3333-3333-333333333333",
            json={"decision": "approve"},
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_resolve_approval_decision_body_validated() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/login",
            json={"email": "alice@tenant-a.example", "password": "password123"},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        thread = await client.post(
            "/v1/threads", headers=headers, json={"title": "approval contract"}
        )
        assert thread.status_code == 201
        tid = thread.json()["id"]
        res = await client.post(
            f"/v1/threads/{tid}/approvals/33333333-3333-3333-3333-333333333333",
            headers=headers,
            json={},
        )
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_resolve_approval_unknown_returns_404() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/login",
            json={"email": "alice@tenant-a.example", "password": "password123"},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        thread = await client.post(
            "/v1/threads", headers=headers, json={"title": "missing approval"}
        )
        assert thread.status_code == 201
        tid = thread.json()["id"]
        res = await client.post(
            f"/v1/threads/{tid}/approvals/33333333-3333-3333-3333-333333333333",
            headers=headers,
            json={"decision": "approve"},
        )
        assert res.status_code == 404
