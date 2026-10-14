"""Integration: grounded chat turn via SSE."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.helpers_sse import final_message, sse_events


@pytest.mark.asyncio
async def test_grounded_chat() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/login",
            json={"email": "alice@tenant-a.example", "password": "password123"},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        thread = await client.post("/v1/threads", headers=headers, json={"title": "MFA"})
        assert thread.status_code == 201
        tid = thread.json()["id"]
        chat = await client.post(
            f"/v1/threads/{tid}/chat",
            headers=headers,
            json={"message": "How do I reset MFA for a user?"},
        )
        assert chat.status_code == 200
        body = final_message(sse_events(chat))
        assert body["refused"] is False
        assert "MFA" in body["content"] or "multi-factor" in body["content"].lower()
