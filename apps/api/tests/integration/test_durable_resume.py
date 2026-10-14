"""Integration: thread history survives checkpointer reconnect (process restart)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.graph.checkpointer import reset_checkpointer
from app.main import app
from tests.helpers_sse import final_message, sse_events


@pytest.mark.asyncio
async def test_resume_after_checkpointer_restart() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/login",
            json={"email": "alice@tenant-a.example", "password": "password123"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        thread = await client.post(
            "/v1/threads", headers=headers, json={"title": "durable"}
        )
        tid = thread.json()["id"]
        chat = await client.post(
            f"/v1/threads/{tid}/chat",
            headers=headers,
            json={"message": "How do I reset MFA for a user?"},
        )
        assert chat.status_code == 200
        msg = final_message(sse_events(chat))
        assert msg["content"]

        # Simulate API process restart: reopen checkpointer connection
        await reset_checkpointer()

        detail = await client.get(f"/v1/threads/{tid}", headers=headers)
        assert detail.status_code == 200
        body = detail.json()
        assert len(body["messages"]) >= 2
        assert any(m["role"] == "user" for m in body["messages"])
        assert any(m["role"] == "assistant" for m in body["messages"])
