from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.deps import AuthContext
from app.db.models import PendingApproval, Thread
from app.schemas import (
    CreateThreadRequest,
    MessageOut,
    PendingApprovalOut,
    ThreadDetail,
    ThreadSummary,
)


class ThreadNotFound(Exception):
    pass


def _summary(thread: Thread) -> ThreadSummary:
    return ThreadSummary(
        id=str(thread.id),
        title=thread.title,
        status=thread.status,
        updated_at=thread.updated_at.isoformat() if thread.updated_at else "",
    )


async def list_threads(db: AsyncSession, auth: AuthContext) -> list[ThreadSummary]:
    result = await db.execute(
        select(Thread)
        .where(Thread.tenant_id == auth.tenant_id, Thread.user_id == auth.user_id)
        .order_by(Thread.updated_at.desc())
    )
    return [_summary(thread) for thread in result.scalars().all()]


async def create_thread(
    db: AsyncSession,
    auth: AuthContext,
    body: CreateThreadRequest,
) -> ThreadSummary:
    thread = Thread(
        tenant_id=auth.tenant_id,
        user_id=auth.user_id,
        title=body.title or "New conversation",
        status="active",
    )
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    return _summary(thread)


async def get_thread(db: AsyncSession, auth: AuthContext, thread_id: UUID) -> ThreadDetail:
    result = await db.execute(
        select(Thread)
        .options(selectinload(Thread.messages))
        .where(
            Thread.id == thread_id,
            Thread.tenant_id == auth.tenant_id,
            Thread.user_id == auth.user_id,
        )
    )
    thread = result.scalar_one_or_none()
    if thread is None:
        raise ThreadNotFound()
    messages = [
        MessageOut(
            id=str(message.id),
            role=message.role,
            content=message.content,
            steps=message.steps,
            sources=message.sources,
            created_at=message.created_at.isoformat() if message.created_at else "",
        )
        for message in sorted(thread.messages, key=lambda item: item.created_at or 0)
    ]

    pending_out = None
    if thread.status == "pending_approval":
        approval_result = await db.execute(
            select(PendingApproval).where(
                PendingApproval.thread_id == thread.id,
                PendingApproval.tenant_id == auth.tenant_id,
                PendingApproval.status == "pending",
            )
        )
        approval = approval_result.scalar_one_or_none()
        if approval:
            pending_out = PendingApprovalOut(
                id=str(approval.id),
                tool_name=approval.tool_name,
                payload=approval.payload,
                rationale=approval.rationale,
                status=approval.status,
            )

    return ThreadDetail(
        **_summary(thread).model_dump(),
        messages=messages,
        pending_approval=pending_out,
    )
