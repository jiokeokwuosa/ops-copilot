"""Message helpers for progress step snapshots (FR-022)."""

from typing import Any

from app.db.models.thread import Message


def attach_steps(message: Message, steps: list[dict[str, Any]] | None) -> Message:
    """Persist completed timeline steps on an assistant message."""
    message.steps = steps
    return message
