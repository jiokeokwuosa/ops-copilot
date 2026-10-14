"""Integration: writes never apply without an explicit approve."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.models.stubs import TicketStub
from app.db.session import SessionLocal
from app.main import app


@pytest.mark.asyncio
async def test_write_does_not_apply_without_approve() -> None:
    async with SessionLocal() as db:
        before_reset = await db.execute(
            select(TicketStub).where(TicketStub.external_id == "TKT-1003")
        )
        ticket = before_reset.scalar_one()
        ticket.status = "in_progress"
        await db.commit()

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
            "/v1/threads", headers=headers, json={"title": "no silent write"}
        )
        assert thread.status_code == 201
        tid = thread.json()["id"]

        async with SessionLocal() as db:
            before = await db.execute(
                select(TicketStub).where(TicketStub.external_id == "TKT-1003")
            )
            status_before = before.scalar_one().status

        chat = await client.post(
            f"/v1/threads/{tid}/chat",
            headers=headers,
            json={"message": "Update ticket TKT-1003 status to resolved"},
        )
        assert chat.status_code == 200
        body = chat.json()
        assert body.get("pending_approval") is not None
        assert body["pending_approval"]["status"] == "pending"

        async with SessionLocal() as db:
            after = await db.execute(
                select(TicketStub).where(TicketStub.external_id == "TKT-1003")
            )
            assert after.scalar_one().status == status_before

        detail = await client.get(f"/v1/threads/{tid}", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["status"] == "pending_approval"
        assert detail.json()["pending_approval"]["id"] == body["pending_approval"]["id"]
