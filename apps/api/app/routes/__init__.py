from fastapi import APIRouter

from app.routes.approvals import router as approvals_router
from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router
from app.routes.threads import router as threads_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(threads_router)
router.include_router(chat_router)
router.include_router(approvals_router)
