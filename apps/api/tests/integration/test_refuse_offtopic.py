"""Integration: off-topic refusal via SSE."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.helpers_sse import final_message, sse_events


@pytest.mark.asyncio
async def test_refuse_offtopic() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/login",
            json={"email": "alice@tenant-a.example", "password": "password123"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        thread = await client.post(
            "/v1/threads", headers=headers, json={"title": "offtopic"}
        )
        tid = thread.json()["id"]
        chat = await client.post(
            f"/v1/threads/{tid}/chat",
            headers=headers,
            json={"message": "Write a poem about today's celebrity gossip news"},
        )
        assert chat.status_code == 200
        body = final_message(sse_events(chat))
        assert body["refused"] is True
        assert "outside" in body["content"].lower() or "only help" in body["content"].lower()
