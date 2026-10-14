"""Helpers to parse SSE streams in tests."""

import json
from typing import Any

from httpx import Response


def parse_sse(text: str) -> list[tuple[str, dict[str, Any]]]:
    events: list[tuple[str, dict[str, Any]]] = []
    event_name = "message"
    data_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("event:"):
            event_name = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data_lines.append(line.removeprefix("data:").strip())
        elif line == "" and data_lines:
            raw = "\n".join(data_lines)
            events.append((event_name, json.loads(raw)))
            event_name = "message"
            data_lines = []
    if data_lines:
        events.append((event_name, json.loads("\n".join(data_lines))))
    return events


def sse_events(response: Response) -> list[tuple[str, dict[str, Any]]]:
    assert "text/event-stream" in response.headers.get("content-type", "")
    return parse_sse(response.text)


def final_message(events: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    for name, data in reversed(events):
        if name == "message_completed":
            return data
    raise AssertionError("message_completed not found")
