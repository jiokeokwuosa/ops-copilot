"""Map LangGraph node updates to SSE timeline events."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import AuthContext
from app.db.models import Message, PendingApproval, Thread
from app.graph.build import build_graph
from app.graph.checkpointer import ensure_checkpointer
from app.tools.intent import detect_intent

NODE_META: dict[str, tuple[str, str]] = {
    "retrieve": ("searching", "Searching docs"),
    "grade": ("grading", "Checking sources"),
    "rewrite": ("rewriting", "Rewriting query"),
    "refuse_ungrounded": ("refused", "Could not ground answer"),
    "route_or_refuse": ("refused", "Out of scope"),
    "generate": ("writing", "Writing answer"),
    "run_docs_search": ("tool", "Searching docs tool"),
    "run_ticket_read": ("tool", "Looking up ticket"),
    "run_crm_read": ("tool", "Looking up CRM contact"),
    "create_approval": ("approval", "Preparing write for approval"),
    "wait_approval": ("approval", "Waiting for approval"),
    "execute_write": ("tool", "Applying approved write"),
}

ANSWER_NODES = {
    "generate",
    "run_docs_search",
    "run_ticket_read",
    "run_crm_read",
    "execute_write",
    "refuse_ungrounded",
    "route_or_refuse",
}


def format_sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _chunk_tokens(text: str, size: int = 24) -> list[str]:
    if not text:
        return []
    return [text[i : i + size] for i in range(0, len(text), size)]


async def stream_chat(
    db: AsyncSession,
    auth: AuthContext,
    thread: Thread,
    message: str,
) -> AsyncIterator[str]:
    """Yield SSE frames for one chat turn."""
    steps: list[dict[str, Any]] = []
    step_ids: dict[str, str] = {}
    content = ""
    sources: list[dict[str, Any]] = []
    refused = False
    tokens_emitted = False

    def ensure_step(node: str) -> tuple[str, str, str]:
        step_type, label = NODE_META.get(node, ("tool", node))
        if node in step_ids:
            return step_ids[node], step_type, label
        step_id = f"s_{uuid4().hex[:8]}"
        step_ids[node] = step_id
        steps.append(
            {
                "id": step_id,
                "type": step_type,
                "label": label,
                "status": "running",
                "detail": {},
            }
        )
        return step_id, step_type, label

    def mark_completed(step_id: str) -> None:
        for step in steps:
            if step["id"] == step_id:
                step["status"] = "completed"

    await ensure_checkpointer()
    graph = build_graph(db, auth.tenant_id, thread.id)
    config = {"configurable": {"thread_id": str(thread.id)}}
    inputs = {
        "question": message,
        "tenant_id": str(auth.tenant_id),
        "thread_id": str(thread.id),
        "intent": detect_intent(message),
        "messages": [],
    }

    try:
        async for update in graph.astream(inputs, config=config, stream_mode="updates"):
            if not isinstance(update, dict):
                continue
            for node, payload in update.items():
                if node.startswith("__") or not isinstance(payload, dict):
                    continue
                # route_or_refuse only surfaces when it actually refuses
                if node == "route_or_refuse" and not payload.get("refused"):
                    continue

                step_id, step_type, label = ensure_step(node)
                yield format_sse(
                    "step",
                    {
                        "step_id": step_id,
                        "type": step_type,
                        "label": label,
                        "status": "running",
                    },
                )

                detail: dict[str, Any] = {}
                if node == "retrieve":
                    detail["query"] = payload.get("query") or message
                    docs = payload.get("docs") or []
                    detail["sources"] = [
                        {"id": d.get("id"), "title": d.get("title"), "uri": d.get("uri")}
                        for d in docs
                    ]
                elif node == "generate":
                    sources = payload.get("sources") or []
                    content = payload.get("answer") or ""
                    refused = bool(payload.get("refused"))
                    read_id = f"s_{uuid4().hex[:8]}"
                    steps.append(
                        {
                            "id": read_id,
                            "type": "reading",
                            "label": "Reading sources",
                            "status": "completed",
                            "detail": {"sources": sources},
                        }
                    )
                    yield format_sse(
                        "step",
                        {
                            "step_id": read_id,
                            "type": "reading",
                            "label": "Reading sources",
                            "status": "completed",
                        },
                    )
                    if sources:
                        yield format_sse(
                            "step_detail",
                            {"step_id": read_id, "detail": {"sources": sources}},
                        )
                    detail["sources"] = sources
                elif node in ANSWER_NODES:
                    if payload.get("answer"):
                        content = payload["answer"]
                    if payload.get("sources") is not None:
                        sources = payload.get("sources") or []
                    if payload.get("refused"):
                        refused = True
                    if node.startswith("run_") or node == "execute_write":
                        detail["tool_name"] = node
                elif node == "create_approval":
                    detail["tool_name"] = (payload.get("pending_write") or {}).get(
                        "tool_name"
                    )
                elif node == "rewrite":
                    detail["query"] = payload.get("query")

                if detail:
                    for step in steps:
                        if step["id"] == step_id:
                            step["detail"] = {**(step.get("detail") or {}), **detail}
                    yield format_sse("step_detail", {"step_id": step_id, "detail": detail})

                mark_completed(step_id)
                yield format_sse(
                    "step",
                    {
                        "step_id": step_id,
                        "type": step_type,
                        "label": label,
                        "status": "completed",
                    },
                )

                if node in ANSWER_NODES and content and not tokens_emitted:
                    write_id = step_id if step_type == "writing" else f"s_{uuid4().hex[:8]}"
                    if step_type != "writing":
                        steps.append(
                            {
                                "id": write_id,
                                "type": "writing",
                                "label": "Writing answer",
                                "status": "running",
                                "detail": {},
                            }
                        )
                        yield format_sse(
                            "step",
                            {
                                "step_id": write_id,
                                "type": "writing",
                                "label": "Writing answer",
                                "status": "running",
                            },
                        )
                    for delta in _chunk_tokens(content):
                        yield format_sse("token", {"step_id": write_id, "delta": delta})
                    mark_completed(write_id)
                    yield format_sse(
                        "step",
                        {
                            "step_id": write_id,
                            "type": "writing",
                            "label": "Writing answer",
                            "status": "completed",
                        },
                    )
                    tokens_emitted = True

        state = await graph.aget_state(config)
        if state and state.next:
            approval_result = await db.execute(
                select(PendingApproval).where(
                    PendingApproval.thread_id == thread.id,
                    PendingApproval.status == "pending",
                )
            )
            pending = approval_result.scalar_one_or_none()
            if pending:
                yield format_sse(
                    "approval_required",
                    {
                        "approval_id": str(pending.id),
                        "tool_name": pending.tool_name,
                        "payload": pending.payload,
                        "rationale": pending.rationale,
                    },
                )
                if not content:
                    content = "A write action needs your approval before it can run."

        assistant = Message(
            thread_id=thread.id,
            role="assistant",
            content=content,
            sources=sources or None,
            steps=steps or None,
        )
        db.add(assistant)
        if not thread.title or thread.title == "New conversation":
            thread.title = message[:80]
        await db.commit()
        await db.refresh(assistant)
        await db.refresh(thread)

        yield format_sse(
            "message_completed",
            {
                "message_id": str(assistant.id),
                "content": content,
                "steps": steps,
                "sources": sources,
                "refused": refused,
            },
        )
        yield format_sse("done", {"thread_id": str(thread.id), "status": thread.status})
    except Exception as exc:  # noqa: BLE001
        step_id = f"s_{uuid4().hex[:8]}"
        yield format_sse(
            "error",
            {"code": "chat_failed", "message": str(exc), "step_id": step_id},
        )
        yield format_sse("done", {"thread_id": str(thread.id), "status": thread.status})
        await db.rollback()
