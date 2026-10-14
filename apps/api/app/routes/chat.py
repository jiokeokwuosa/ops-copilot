from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import AuthContext, get_current_user
from app.db.session import get_db
from app.schemas import ChatRequest, ChatResponse
from app.services.chat import send_message
from app.services.threads import ThreadNotFound

router = APIRouter(prefix="/v1/threads", tags=["chat"])


@router.post("/{thread_id}/chat", response_model=ChatResponse)
async def chat(
    thread_id: UUID,
    body: ChatRequest,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    try:
        return await send_message(db, auth, thread_id, body.message)
    except ThreadNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        ) from None
