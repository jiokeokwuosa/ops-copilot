import os
from collections.abc import AsyncGenerator

import pytest

# Force memory checkpointer in pytest to avoid cross-test connection reuse issues.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("CHECKPOINT_BACKEND", "memory")

from app.db.session import engine
from app.graph.checkpointer import ensure_checkpointer, reset_checkpointer


@pytest.fixture(autouse=True)
async def _dispose_engine_between_tests() -> AsyncGenerator[None, None]:
    """Avoid asyncpg 'attached to a different loop' across pytest-asyncio tests."""
    await ensure_checkpointer()
    yield
    await engine.dispose()
    await reset_checkpointer()
