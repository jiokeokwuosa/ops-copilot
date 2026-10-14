from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import AuthContext, get_current_user
from app.db.session import get_db
from app.schemas import CreateThreadRequest, ThreadDetail, ThreadSummary
from app.services.threads import ThreadNotFound, create_thread, get_thread, list_threads

router = APIRouter(prefix="/v1/threads", tags=["threads"])


@router.get("", response_model=dict)
async def list_threads_route(
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return {"items": await list_threads(db, auth)}


@router.post("", response_model=ThreadSummary, status_code=status.HTTP_201_CREATED)
async def create_thread_route(
    body: CreateThreadRequest,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ThreadSummary:
    return await create_thread(db, auth, body)


@router.get("/{thread_id}", response_model=ThreadDetail)
async def get_thread_route(
    thread_id: UUID,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ThreadDetail:
    try:
        return await get_thread(db, auth, thread_id)
    except ThreadNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        ) from None
