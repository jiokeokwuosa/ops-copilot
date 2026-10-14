from collections.abc import AsyncGenerator

import pytest

from app.db.session import engine


@pytest.fixture(autouse=True)
async def _dispose_engine_between_tests() -> AsyncGenerator[None, None]:
    """Avoid asyncpg 'attached to a different loop' across pytest-asyncio tests."""
    yield
    await engine.dispose()
