"""Process-local checkpointer for interrupt/resume (Postgres saver lands in US3)."""

from langgraph.checkpoint.memory import MemorySaver

_checkpointer = MemorySaver()


def get_checkpointer() -> MemorySaver:
    return _checkpointer
