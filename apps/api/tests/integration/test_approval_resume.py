"""Integration: pending approval survives restart and can be decided via DB fallback."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.models.stubs import TicketStub
from app.db.session import SessionLocal
from app.graph.checkpointer import reset_checkpointer
from app.main import app
from tests.helpers_sse import sse_events


@pytest.mark.asyncio
async def test_pending_approval_survives_restart() -> None:
    async with SessionLocal() as db:
        result = await db.execute(
            select(TicketStub).where(TicketStub.external_id == "TKT-1001")
        )
        ticket = result.scalar_one()
        ticket.status = "open"
        await db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/v1/auth/login",
            json={"email": "alice@tenant-a.example", "password": "password123"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        thread = await client.post(
            "/v1/threads", headers=headers, json={"title": "approval resume"}
        )
        tid = thread.json()["id"]
        chat = await client.post(
            f"/v1/threads/{tid}/chat",
            headers=headers,
            json={"message": "Update ticket TKT-1001 status to resolved"},
        )
        assert chat.status_code == 200
        approval = next(
            data for name, data in sse_events(chat) if name == "approval_required"
        )

        # Simulate process restart (memory checkpointer wiped; DB approval remains)
        await reset_checkpointer()

        detail = await client.get(f"/v1/threads/{tid}", headers=headers)
        assert detail.status_code == 200
        body = detail.json()
        assert body["status"] == "pending_approval"
        assert body["pending_approval"]["id"] == approval["approval_id"]

        decide = await client.post(
            f"/v1/threads/{tid}/approvals/{approval['approval_id']}",
            headers=headers,
            json={"decision": "approve"},
        )
        assert decide.status_code == 200
        assert decide.json()["applied"] is True

        async with SessionLocal() as db:
            after = await db.execute(
                select(TicketStub).where(TicketStub.external_id == "TKT-1001")
            )
            assert after.scalar_one().status == "resolved"
