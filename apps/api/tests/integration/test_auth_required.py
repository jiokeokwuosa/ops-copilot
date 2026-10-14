"""Integration: unauthenticated chat/threads return 401."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_unauthenticated_routes_return_401() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/v1/threads")).status_code == 401
        assert (await client.post("/v1/threads", json={})).status_code == 401
        assert (
            await client.get("/v1/threads/11111111-1111-1111-1111-111111111111")
        ).status_code == 401
        assert (
            await client.post(
                "/v1/threads/11111111-1111-1111-1111-111111111111/chat",
                json={"message": "hi"},
            )
        ).status_code == 401
        assert (
            await client.post(
                "/v1/threads/11111111-1111-1111-1111-111111111111/"
                "approvals/33333333-3333-3333-3333-333333333333",
                json={"decision": "approve"},
            )
        ).status_code == 401
