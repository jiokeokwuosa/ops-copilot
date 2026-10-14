from uuid import UUID

from fastapi import HTTPException, status
from langgraph.types import Command
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import AuthContext
from app.db.models import Message, PendingApproval, Thread
from app.graph.build import build_graph
from app.schemas import ApprovalResult
from app.services.threads import ThreadNotFound


async def resolve_approval(
    db: AsyncSession,
    auth: AuthContext,
    thread_id: UUID,
    approval_id: UUID,
    decision: str,
) -> ApprovalResult:
    thread_result = await db.execute(
        select(Thread).where(
            Thread.id == thread_id,
            Thread.tenant_id == auth.tenant_id,
            Thread.user_id == auth.user_id,
        )
    )
    thread = thread_result.scalar_one_or_none()
    if thread is None:
        raise ThreadNotFound()

    approval_result = await db.execute(
        select(PendingApproval).where(
            PendingApproval.id == approval_id,
            PendingApproval.thread_id == thread_id,
            PendingApproval.tenant_id == auth.tenant_id,
        )
    )
    approval = approval_result.scalar_one_or_none()
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Not pending")

    graph = build_graph(db, auth.tenant_id, thread.id)
    config = {"configurable": {"thread_id": str(thread.id)}}
    final = await graph.ainvoke(Command(resume=decision), config=config)

    content = final.get("answer") or (
        "Write applied." if decision == "approve" else "Write was not applied."
    )
    applied = bool(final.get("write_applied")) if decision == "approve" else False

    db.add(
        Message(
            thread_id=thread.id,
            role="assistant",
            content=content,
            sources=None,
            steps=None,
        )
    )
    await db.commit()
    await db.refresh(thread)

    return ApprovalResult(status=thread.status, applied=applied)
