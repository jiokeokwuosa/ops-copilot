from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.langsmith import configure_langsmith
from app.core.logging import configure_logging
from app.core.settings import settings
from app.graph.checkpointer import ensure_checkpointer
from app.routes import router as api_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    configure_langsmith()
    await ensure_checkpointer()
    yield


app = FastAPI(title="Ops Copilot API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
