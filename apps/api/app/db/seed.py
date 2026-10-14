"""Seed two tenants, demo users, and stub ticket/CRM rows."""

import asyncio
import uuid

from sqlalchemy import select

from app.auth.jwt import hash_password
from app.db.models import CrmContactStub, Tenant, TicketStub, User
from app.db.session import SessionLocal

TENANT_A_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
TENANT_B_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
USER_A_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
USER_B_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


async def seed() -> None:
    async with SessionLocal() as db:
        existing = await db.execute(select(Tenant).where(Tenant.id == TENANT_A_ID))
        if existing.scalar_one_or_none() is None:
            tenant_a = Tenant(id=TENANT_A_ID, name="Tenant A")
            tenant_b = Tenant(id=TENANT_B_ID, name="Tenant B")
            user_a = User(
                id=USER_A_ID,
                tenant_id=TENANT_A_ID,
                email="alice@tenant-a.example",
                password_hash=hash_password("password123"),
                display_name="Alice (Tenant A)",
            )
            user_b = User(
                id=USER_B_ID,
                tenant_id=TENANT_B_ID,
                email="bob@tenant-b.example",
                password_hash=hash_password("password123"),
                display_name="Bob (Tenant B)",
            )
            db.add_all([tenant_a, tenant_b, user_a, user_b])
            await db.commit()
            print("Seeded Tenant A/B and alice/bob users (password: password123)")
        else:
            print("Tenants already present")

        tickets = [
            ("TKT-1001", "MFA reset request", "open", "User locked out of MFA."),
            ("TKT-1002", "VPN access", "open", "Need VPN for contractor."),
            ("TKT-1003", "Laptop shipping", "in_progress", "Waiting on depot."),
        ]
        for external_id, subject, status, body in tickets:
            found = await db.execute(
                select(TicketStub).where(
                    TicketStub.tenant_id == TENANT_A_ID,
                    TicketStub.external_id == external_id,
                )
            )
            if found.scalar_one_or_none() is None:
                db.add(
                    TicketStub(
                        tenant_id=TENANT_A_ID,
                        external_id=external_id,
                        subject=subject,
                        status=status,
                        body=body,
                    )
                )

        contact = await db.execute(
            select(CrmContactStub).where(
                CrmContactStub.tenant_id == TENANT_A_ID,
                CrmContactStub.email == "customer@example.com",
            )
        )
        if contact.scalar_one_or_none() is None:
            db.add(
                CrmContactStub(
                    tenant_id=TENANT_A_ID,
                    name="Casey Customer",
                    email="customer@example.com",
                    notes=["Initial onboarding complete"],
                )
            )

        await db.commit()
        print("Seeded ticket/CRM stubs for Tenant A")


if __name__ == "__main__":
    asyncio.run(seed())
