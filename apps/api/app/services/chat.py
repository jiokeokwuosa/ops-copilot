from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.deps import AuthContext
from app.db.models import Message, PendingApproval, Thread
from app.graph.build import build_graph
from app.schemas import ChatResponse, PendingApprovalOut
from app.services.threads import ThreadNotFound
from app.tools.intent import detect_intent


def _approval_out(approval: PendingApproval) -> PendingApprovalOut:
    return PendingApprovalOut(
        id=str(approval.id),
        tool_name=approval.tool_name,
        payload=approval.payload,
        rationale=approval.rationale,
        status=approval.status,
    )


async def send_message(
    db: AsyncSession,
    auth: AuthContext,
    thread_id: UUID,
    message: str,
) -> ChatResponse:
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

    if thread.status == "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Thread already pending approval",
        )

    db.add(Message(thread_id=thread.id, role="user", content=message))
    await db.flush()

    graph = build_graph(db, auth.tenant_id, thread.id)
    config = {"configurable": {"thread_id": str(thread.id)}}
    intent = detect_intent(message)
    final = await graph.ainvoke(
        {
            "question": message,
            "tenant_id": str(auth.tenant_id),
            "thread_id": str(thread.id),
            "intent": intent,
            "messages": [],
        },
        config=config,
    )

    interrupted = bool(final.get("__interrupt__"))
    pending_out: PendingApprovalOut | None = None

    if interrupted:
        await db.commit()
        approval_result = await db.execute(
            select(PendingApproval).where(
                PendingApproval.thread_id == thread.id,
                PendingApproval.status == "pending",
            )
        )
        approval = approval_result.scalar_one_or_none()
        content = (
            "A write action needs your approval before it can run."
            if approval
            else "Waiting for approval."
        )
        assistant = Message(
            thread_id=thread.id,
            role="assistant",
            content=content,
            sources=None,
            steps=None,
        )
        db.add(assistant)
        if not thread.title or thread.title == "New conversation":
            thread.title = message[:80]
        await db.commit()
        await db.refresh(assistant)
        if approval:
            pending_out = _approval_out(approval)
        return ChatResponse(
            message_id=str(assistant.id),
            content=content,
            sources=None,
            refused=False,
            pending_approval=pending_out,
        )

    content = final.get("answer") or ""
    sources = final.get("sources") or []
    refused = bool(final.get("refused"))

    assistant = Message(
        thread_id=thread.id,
        role="assistant",
        content=content,
        sources=sources or None,
        steps=None,
    )
    db.add(assistant)
    if not thread.title or thread.title == "New conversation":
        thread.title = message[:80]
    await db.commit()
    await db.refresh(assistant)

    return ChatResponse(
        message_id=str(assistant.id),
        content=content,
        sources=sources,
        refused=refused,
        pending_approval=None,
    )
