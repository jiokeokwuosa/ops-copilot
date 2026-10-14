"""Contract test for POST /v1/evals/run."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_evals_run_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/v1/evals/run", json={"suite": "golden"})
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_evals_run_returns_report() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/login",
            json={"email": "alice@tenant-a.example", "password": "password123"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        res = await client.post("/v1/evals/run", headers=headers, json={"suite": "golden"})
        assert res.status_code == 200
        body = res.json()
        assert "passed" in body and "total" in body and "results" in body
        assert body["total"] >= 1
