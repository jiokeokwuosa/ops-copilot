from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import AuthContext, get_current_user
from app.db.session import get_db
from app.evals.run import run_eval_suite

router = APIRouter(prefix="/v1/evals", tags=["evals"])


class EvalRunRequest(BaseModel):
    suite: str = Field(default="golden")


@router.post("/run")
async def run_evals(
    body: EvalRunRequest | None = None,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _ = auth  # authenticated builder/operator
    suite = (body.suite if body else "golden") or "golden"
    return await run_eval_suite(db, suite=suite)
