"""Stub ticket read/write tools."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.stubs import TicketStub


async def ticket_get(
    db: AsyncSession, *, tenant_id: UUID, external_id: str
) -> dict | None:
    result = await db.execute(
        select(TicketStub).where(
            TicketStub.tenant_id == tenant_id,
            TicketStub.external_id == external_id,
        )
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        return None
    return {
        "id": str(ticket.id),
        "external_id": ticket.external_id,
        "subject": ticket.subject,
        "status": ticket.status,
        "body": ticket.body,
    }


async def ticket_update(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    external_id: str,
    status: str,
) -> dict | None:
    result = await db.execute(
        select(TicketStub).where(
            TicketStub.tenant_id == tenant_id,
            TicketStub.external_id == external_id,
        )
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        return None
    ticket.status = status
    await db.flush()
    return {
        "id": str(ticket.id),
        "external_id": ticket.external_id,
        "subject": ticket.subject,
        "status": ticket.status,
        "body": ticket.body,
    }
