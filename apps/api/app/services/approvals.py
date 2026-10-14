from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from langgraph.types import Command
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import AuthContext
from app.db.models import Message, PendingApproval, Thread
from app.graph.build import build_graph
from app.graph.checkpointer import ensure_checkpointer
from app.graph.config import thread_config
from app.schemas import ApprovalResult
from app.services.threads import ThreadNotFound
from app.tools import crm as crm_tools
from app.tools import tickets as ticket_tools


async def _apply_from_payload(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    tool_name: str,
    payload: dict,
) -> tuple[bool, str]:
    applied_result = None
    if tool_name == "ticket_update":
        applied_result = await ticket_tools.ticket_update(
            db,
            tenant_id=tenant_id,
            external_id=str(payload["external_id"]),
            status=str(payload["status"]),
        )
    elif tool_name == "crm_add_note":
        applied_result = await crm_tools.crm_add_note(
            db,
            tenant_id=tenant_id,
            email=str(payload["email"]),
            note=str(payload["note"]),
        )
    if applied_result is None:
        return False, "Approval recorded, but the write target was not found."
    return True, f"Write applied via {tool_name}: {applied_result}"


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

    await ensure_checkpointer()
    graph = build_graph(db, auth.tenant_id, thread.id)
    config = thread_config(str(thread.id))

    content = ""
    applied = False
    state = await graph.aget_state(config)
    can_resume = bool(state and state.next)

    if can_resume:
        final = await graph.ainvoke(Command(resume=decision), config=config)
        content = final.get("answer") or ""
        applied = bool(final.get("write_applied")) if decision == "approve" else False
        await db.refresh(approval)
        await db.refresh(thread)
    else:
        # No checkpoint (e.g. process restart with memory saver): use DB payload
        if decision == "approve":
            applied, content = await _apply_from_payload(
                db,
                tenant_id=auth.tenant_id,
                tool_name=approval.tool_name,
                payload=approval.payload,
            )
            approval.status = "approved" if applied else "rejected"
        else:
            applied = False
            content = "Write was not applied (rejected or cancelled)."
            approval.status = "rejected"
        approval.resolved_at = datetime.now(UTC)
        thread.status = "active"

    if approval.status == "pending":
        approval.status = "approved" if decision == "approve" else "rejected"
        approval.resolved_at = datetime.now(UTC)
        thread.status = "active"

    if not content:
        content = (
            "Write applied."
            if decision == "approve" and applied
            else "Write was not applied."
        )

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

    return ApprovalResult(
        status=thread.status,
        applied=applied if decision == "approve" else False,
    )
