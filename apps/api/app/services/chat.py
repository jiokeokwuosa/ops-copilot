from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.deps import AuthContext
from app.db.models import Message, Thread
from app.graph.streaming import stream_chat
from app.services.threads import ThreadNotFound


async def prepare_chat(
    db: AsyncSession,
    auth: AuthContext,
    thread_id: UUID,
    message: str,
) -> tuple[Thread, AsyncIterator[str]]:
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

    return thread, stream_chat(db, auth, thread, message)
