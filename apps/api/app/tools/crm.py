"""Stub CRM read/write tools."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.stubs import CrmContactStub


async def crm_get(db: AsyncSession, *, tenant_id: UUID, email: str) -> dict | None:
    result = await db.execute(
        select(CrmContactStub).where(
            CrmContactStub.tenant_id == tenant_id,
            CrmContactStub.email == email,
        )
    )
    contact = result.scalar_one_or_none()
    if contact is None:
        return None
    return {
        "id": str(contact.id),
        "name": contact.name,
        "email": contact.email,
        "notes": contact.notes or [],
    }


async def crm_add_note(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    email: str,
    note: str,
) -> dict | None:
    result = await db.execute(
        select(CrmContactStub).where(
            CrmContactStub.tenant_id == tenant_id,
            CrmContactStub.email == email,
        )
    )
    contact = result.scalar_one_or_none()
    if contact is None:
        return None
    notes = list(contact.notes or [])
    notes.append(note)
    contact.notes = notes
    await db.flush()
    return {
        "id": str(contact.id),
        "name": contact.name,
        "email": contact.email,
        "notes": contact.notes,
    }
