from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import AuthContext, get_current_user
from app.db.session import get_db
from app.schemas import ApprovalDecision, ApprovalResult
from app.services.approvals import resolve_approval
from app.services.threads import ThreadNotFound

router = APIRouter(prefix="/v1/threads", tags=["approvals"])


@router.post(
    "/{thread_id}/approvals/{approval_id}",
    response_model=ApprovalResult,
)
async def decide_approval(
    thread_id: UUID,
    approval_id: UUID,
    body: ApprovalDecision,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApprovalResult:
    try:
        return await resolve_approval(db, auth, thread_id, approval_id, body.decision)
    except ThreadNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        ) from None
