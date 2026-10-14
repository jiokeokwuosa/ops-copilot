"""LangGraph checkpointer with Postgres durability and MemorySaver for tests."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import MemorySaver

from app.core.settings import settings

_checkpointer: Any | None = None
_context_manager: Any | None = None


def _postgres_dsn() -> str:
    dsn = settings.database_url_sync
    return dsn.replace("postgresql+psycopg://", "postgresql://")


def use_postgres_checkpointer() -> bool:
    # Prefer explicit override; default postgres outside pytest.
    backend = (settings.checkpoint_backend or "").lower()
    if backend in {"memory", "postgres"}:
        return backend == "postgres"
    return settings.environment != "test"


async def ensure_checkpointer() -> Any:
    """Open checkpointer once (idempotent)."""
    global _checkpointer, _context_manager
    if _checkpointer is not None:
        return _checkpointer

    if not use_postgres_checkpointer():
        _checkpointer = MemorySaver()
        return _checkpointer

    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    _context_manager = AsyncPostgresSaver.from_conn_string(_postgres_dsn())
    saver = await _context_manager.__aenter__()
    await saver.setup()
    _checkpointer = saver
    return _checkpointer


async def reset_checkpointer() -> Any:
    """Close and reopen (simulates process restart)."""
    global _checkpointer, _context_manager
    if _context_manager is not None:
        try:
            await _context_manager.__aexit__(None, None, None)
        except Exception:
            pass
    _context_manager = None
    _checkpointer = None
    return await ensure_checkpointer()


def get_checkpointer() -> Any:
    if _checkpointer is not None:
        return _checkpointer
    return MemorySaver()
