"""Integration: off-topic refusal."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_refuse_offtopic() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/login",
            json={"email": "alice@tenant-a.example", "password": "password123"},
        )
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        thread = await client.post("/v1/threads", headers=headers, json={})
        tid = thread.json()["id"]
        chat = await client.post(
            f"/v1/threads/{tid}/chat",
            headers=headers,
            json={"message": "What is the weather in Chennai today?"},
        )
        assert chat.status_code == 200
        body = chat.json()
        assert body["refused"] is True
        assert "outside" in body["content"].lower() or "scope" in body["content"].lower()
