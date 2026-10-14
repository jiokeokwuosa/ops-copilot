from uuid import UUID

from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.graph.checkpointer import get_checkpointer
from app.graph.nodes.rag import make_nodes
from app.graph.nodes.tools import make_tool_nodes
from app.graph.state import GraphState
from app.tools.intent import detect_intent


def build_graph(db: AsyncSession, tenant_id: UUID, thread_id: UUID):
    nodes = make_nodes(db, tenant_id)
    tool_nodes = make_tool_nodes(db, tenant_id, thread_id)
    graph = StateGraph(GraphState)
    graph.add_node("route_or_refuse", nodes["route_or_refuse"])
    graph.add_node("retrieve", nodes["retrieve"])
    graph.add_node("grade", nodes["grade"])
    graph.add_node("rewrite", nodes["rewrite"])
    graph.add_node("refuse_ungrounded", nodes["refuse_ungrounded"])
    graph.add_node("generate", nodes["generate"])
    graph.add_node("run_docs_search", tool_nodes["run_docs_search"])
    graph.add_node("run_ticket_read", tool_nodes["run_ticket_read"])
    graph.add_node("run_crm_read", tool_nodes["run_crm_read"])
    graph.add_node("create_approval", tool_nodes["create_approval"])
    graph.add_node("wait_approval", tool_nodes["wait_approval"])
    graph.add_node("execute_write", tool_nodes["execute_write"])

    graph.add_edge(START, "route_or_refuse")

    def after_route(state: GraphState) -> str:
        if state.get("refused"):
            return "end"
        intent = state.get("intent") or detect_intent(state.get("question") or "")
        return intent

    graph.add_conditional_edges(
        "route_or_refuse",
        after_route,
        {
            "end": END,
            "rag": "retrieve",
            "docs_search": "run_docs_search",
            "ticket_read": "run_ticket_read",
            "crm_read": "run_crm_read",
            "write": "create_approval",
        },
    )
    graph.add_edge("retrieve", "grade")

    def after_grade(state: GraphState) -> str:
        if state.get("grade_ok"):
            return "generate"
        if int(state.get("retries") or 0) < 2:
            return "rewrite"
        return "refuse_ungrounded"

    graph.add_conditional_edges(
        "grade",
        after_grade,
        {
            "generate": "generate",
            "rewrite": "rewrite",
            "refuse_ungrounded": "refuse_ungrounded",
        },
    )
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("generate", END)
    graph.add_edge("refuse_ungrounded", END)
    graph.add_edge("run_docs_search", END)
    graph.add_edge("run_ticket_read", END)
    graph.add_edge("run_crm_read", END)

    def after_create_approval(state: GraphState) -> str:
        return "end" if state.get("refused") else "wait_approval"

    graph.add_conditional_edges(
        "create_approval",
        after_create_approval,
        {"wait_approval": "wait_approval", "end": END},
    )
    graph.add_edge("wait_approval", "execute_write")
    graph.add_edge("execute_write", END)

    return graph.compile(checkpointer=get_checkpointer())
