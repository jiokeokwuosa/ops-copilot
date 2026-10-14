from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class GraphState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    question: str
    query: str
    tenant_id: str
    thread_id: str
    intent: str
    docs: list[dict[str, Any]]
    grade_ok: bool
    grade_rationale: str
    retries: int
    refused: bool
    answer: str
    sources: list[dict[str, Any]]
    tool_result: Any
    approval_id: str
    pending_write: dict[str, Any]
    approval_decision: str
    write_applied: bool
