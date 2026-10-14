"""Contract tests for SSE event shapes."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.helpers_sse import final_message, sse_events


@pytest.mark.asyncio
async def test_sse_event_shapes_for_grounded_chat() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/login",
            json={"email": "alice@tenant-a.example", "password": "password123"},
        )
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        thread = await client.post("/v1/threads", headers=headers, json={"title": "SSE"})
        tid = thread.json()["id"]
        res = await client.post(
            f"/v1/threads/{tid}/chat",
            headers=headers,
            json={"message": "How do I reset MFA for a user?"},
        )
        assert res.status_code == 200
        events = sse_events(res)
        names = [name for name, _ in events]
        assert "step" in names
        assert "message_completed" in names
        assert "done" in names

        for name, data in events:
            if name == "step":
                assert "step_id" in data
                assert data["type"] in {
                    "searching",
                    "grading",
                    "rewriting",
                    "reading",
                    "tool",
                    "approval",
                    "writing",
                    "refused",
                    "error",
                }
                assert data["status"] in {"running", "completed", "failed"}
            elif name == "token":
                assert "delta" in data and "step_id" in data
            elif name == "step_detail":
                assert "step_id" in data and "detail" in data
            elif name == "message_completed":
                assert "message_id" in data and "content" in data
            elif name == "done":
                assert "thread_id" in data and "status" in data

        msg = final_message(events)
        assert msg["refused"] is False
        assert msg["content"]
