"""Integration: write interrupt approve / reject."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.models.stubs import TicketStub
from app.db.session import SessionLocal
from app.main import app


async def _reset_ticket(external_id: str, status: str = "open") -> None:
    async with SessionLocal() as db:
        result = await db.execute(
            select(TicketStub).where(TicketStub.external_id == external_id)
        )
        ticket = result.scalar_one()
        ticket.status = status
        await db.commit()


async def _login_and_thread(client: AsyncClient) -> tuple[dict[str, str], str]:
    login = await client.post(
        "/v1/auth/login",
        json={"email": "alice@tenant-a.example", "password": "password123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    thread = await client.post("/v1/threads", headers=headers, json={"title": "ticket write"})
    assert thread.status_code == 201
    return headers, thread.json()["id"]


@pytest.mark.asyncio
async def test_write_approve_applies_once() -> None:
    await _reset_ticket("TKT-1001", "open")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers, tid = await _login_and_thread(client)
        chat = await client.post(
            f"/v1/threads/{tid}/chat",
            headers=headers,
            json={"message": "Update ticket TKT-1001 status to resolved"},
        )
        assert chat.status_code == 200
        body = chat.json()
        assert body.get("pending_approval") is not None
        approval = body["pending_approval"]
        assert approval["status"] == "pending"
        assert approval["tool_name"] == "ticket_update"

        async with SessionLocal() as db:
            before = await db.execute(
                select(TicketStub).where(TicketStub.external_id == "TKT-1001")
            )
            ticket = before.scalar_one()
            assert ticket.status != "resolved"

        decide = await client.post(
            f"/v1/threads/{tid}/approvals/{approval['id']}",
            headers=headers,
            json={"decision": "approve"},
        )
        assert decide.status_code == 200
        result = decide.json()
        assert result["status"] == "active"
        assert result["applied"] is True

        async with SessionLocal() as db:
            after = await db.execute(
                select(TicketStub).where(TicketStub.external_id == "TKT-1001")
            )
            ticket = after.scalar_one()
            assert ticket.status == "resolved"


@pytest.mark.asyncio
async def test_write_reject_applies_nothing() -> None:
    await _reset_ticket("TKT-1002", "open")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers, tid = await _login_and_thread(client)
        chat = await client.post(
            f"/v1/threads/{tid}/chat",
            headers=headers,
            json={"message": "Update ticket TKT-1002 status to closed"},
        )
        assert chat.status_code == 200
        approval = chat.json()["pending_approval"]
        assert approval is not None

        async with SessionLocal() as db:
            before = await db.execute(
                select(TicketStub).where(TicketStub.external_id == "TKT-1002")
            )
            status_before = before.scalar_one().status

        decide = await client.post(
            f"/v1/threads/{tid}/approvals/{approval['id']}",
            headers=headers,
            json={"decision": "reject"},
        )
        assert decide.status_code == 200
        result = decide.json()
        assert result["status"] == "active"
        assert result["applied"] is False

        async with SessionLocal() as db:
            after = await db.execute(
                select(TicketStub).where(TicketStub.external_id == "TKT-1002")
            )
            assert after.scalar_one().status == status_before
