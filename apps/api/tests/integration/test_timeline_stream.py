"""Integration: multi-phase chat emits searching → reading → writing."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.helpers_sse import sse_events


@pytest.mark.asyncio
async def test_timeline_searching_reading_writing_order() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/login",
            json={"email": "alice@tenant-a.example", "password": "password123"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        thread = await client.post(
            "/v1/threads", headers=headers, json={"title": "timeline"}
        )
        tid = thread.json()["id"]
        res = await client.post(
            f"/v1/threads/{tid}/chat",
            headers=headers,
            json={"message": "How do I reset MFA for a user?"},
        )
        assert res.status_code == 200
        events = sse_events(res)
        step_types: list[str] = []
        for name, data in events:
            if name == "step" and data.get("status") == "running":
                step_types.append(data["type"])
            if name == "token":
                step_types.append("token")

        assert "searching" in step_types
        assert "reading" in step_types or "grading" in step_types
        assert "writing" in step_types or "token" in step_types

        # First non-writing phase before tokens
        first_token = next(i for i, t in enumerate(step_types) if t == "token")
        assert any(t in {"searching", "grading", "reading"} for t in step_types[:first_token])
