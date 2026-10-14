from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import AuthContext, get_current_user
from app.db.session import get_db
from app.schemas import ChatRequest
from app.services.chat import prepare_chat
from app.services.threads import ThreadNotFound

router = APIRouter(prefix="/v1/threads", tags=["chat"])


@router.post("/{thread_id}/chat")
async def chat(
    thread_id: UUID,
    body: ChatRequest,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    try:
        _thread, events = await prepare_chat(db, auth, thread_id, body.message)
    except ThreadNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        ) from None

    return StreamingResponse(
        events,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
