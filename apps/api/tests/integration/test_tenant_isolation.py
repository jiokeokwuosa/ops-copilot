"""Integration: Tenant A cannot open Tenant B threads."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_cross_tenant_thread_access_denied() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        alice = await client.post(
            "/v1/auth/login",
            json={"email": "alice@tenant-a.example", "password": "password123"},
        )
        bob = await client.post(
            "/v1/auth/login",
            json={"email": "bob@tenant-b.example", "password": "password123"},
        )
        alice_headers = {"Authorization": f"Bearer {alice.json()['access_token']}"}
        bob_headers = {"Authorization": f"Bearer {bob.json()['access_token']}"}

        thread = await client.post(
            "/v1/threads", headers=alice_headers, json={"title": "private A"}
        )
        tid = thread.json()["id"]

        denied = await client.get(f"/v1/threads/{tid}", headers=bob_headers)
        assert denied.status_code == 404

        chat = await client.post(
            f"/v1/threads/{tid}/chat",
            headers=bob_headers,
            json={"message": "How do I reset MFA?"},
        )
        assert chat.status_code == 404
