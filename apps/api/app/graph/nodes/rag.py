from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.graph.state import GraphState
from app.rag.grade import grade_documents
from app.rag.retrieve import retrieve_chunks
from app.rag.rewrite import rewrite_query
from app.rag.route import is_off_topic


def make_nodes(db: AsyncSession, tenant_id: UUID):
    async def route_or_refuse(state: GraphState) -> GraphState:
        question = state.get("question") or ""
        if is_off_topic(question):
            return {
                "refused": True,
                "answer": (
                    "I can only help with internal support and operations topics "
                    "(policies, runbooks, account procedures). That question is outside my scope."
                ),
                "docs": [],
                "sources": [],
            }
        return {"refused": False, "query": question, "retries": 0}

    async def retrieve(state: GraphState) -> GraphState:
        query = state.get("query") or state.get("question") or ""
        docs = await retrieve_chunks(db, tenant_id=tenant_id, query=query)
        return {"docs": docs, "query": query}

    async def grade(state: GraphState) -> GraphState:
        result = grade_documents(state.get("query") or "", state.get("docs") or [])
        return {"grade_ok": result.sufficient, "grade_rationale": result.rationale}

    async def rewrite(state: GraphState) -> GraphState:
        retries = int(state.get("retries") or 0) + 1
        new_q = rewrite_query(state.get("question") or "", state.get("grade_rationale") or "")
        return {"query": new_q, "retries": retries}

    async def refuse_ungrounded(state: GraphState) -> GraphState:
        return {
            "refused": True,
            "answer": (
                "I could not find reliable internal documentation to answer that. "
                "Please rephrase or point me to the relevant runbook."
            ),
            "sources": [],
        }

    async def generate(state: GraphState) -> GraphState:
        docs = state.get("docs") or []
        sources = [{"id": d["id"], "title": d["title"], "uri": d["uri"]} for d in docs]
        context = "\n\n".join(f"### {d['title']}\n{d['content']}" for d in docs)
        answer = (
            f"Based on internal docs:\n\n{context}\n\n"
            f"— Answer synthesized for: {state.get('question')}"
        )
        return {"answer": answer, "sources": sources, "refused": False}

    return {
        "route_or_refuse": route_or_refuse,
        "retrieve": retrieve,
        "grade": grade,
        "rewrite": rewrite,
        "refuse_ungrounded": refuse_ungrounded,
        "generate": generate,
    }
