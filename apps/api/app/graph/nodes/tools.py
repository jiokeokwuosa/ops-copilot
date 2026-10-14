"""Tool + write-approval graph nodes (human-in-the-loop via interrupt)."""

from datetime import UTC, datetime
from uuid import UUID

from langgraph.types import interrupt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.approval import PendingApproval
from app.db.models.thread import Thread
from app.graph.state import GraphState
from app.tools import crm as crm_tools
from app.tools import tickets as ticket_tools
from app.tools.docs_search import docs_search
from app.tools.intent import extract_email, extract_status, extract_ticket_id


def make_tool_nodes(db: AsyncSession, tenant_id: UUID, thread_id: UUID):
    async def run_docs_search(state: GraphState) -> GraphState:
        query = state.get("question") or ""
        docs = await docs_search(db, tenant_id=tenant_id, query=query)
        sources = [{"id": d["id"], "title": d["title"], "uri": d["uri"]} for d in docs]
        if not docs:
            answer = "I searched internal docs but found no matching material."
        else:
            context = "\n\n".join(f"### {d['title']}\n{d['content']}" for d in docs)
            answer = f"Docs search results:\n\n{context}"
        return {"answer": answer, "sources": sources, "refused": False, "tool_result": docs}

    async def run_ticket_read(state: GraphState) -> GraphState:
        question = state.get("question") or ""
        external_id = extract_ticket_id(question) or "TKT-1001"
        ticket = await ticket_tools.ticket_get(
            db, tenant_id=tenant_id, external_id=external_id
        )
        if ticket is None:
            return {
                "answer": f"I could not find ticket {external_id} for your tenant.",
                "refused": False,
                "sources": [],
            }
        answer = (
            f"Ticket {ticket['external_id']}: {ticket['subject']}\n"
            f"Status: {ticket['status']}\n{ticket['body']}"
        )
        return {"answer": answer, "refused": False, "tool_result": ticket, "sources": []}

    async def run_crm_read(state: GraphState) -> GraphState:
        question = state.get("question") or ""
        email = extract_email(question) or "customer@example.com"
        contact = await crm_tools.crm_get(db, tenant_id=tenant_id, email=email)
        if contact is None:
            return {
                "answer": f"I could not find a CRM contact for {email}.",
                "refused": False,
                "sources": [],
            }
        notes = contact.get("notes") or []
        notes_txt = "\n".join(f"- {n}" for n in notes) or "(no notes)"
        answer = f"CRM contact {contact['name']} <{contact['email']}>\nNotes:\n{notes_txt}"
        return {"answer": answer, "refused": False, "tool_result": contact, "sources": []}

    async def create_approval(state: GraphState) -> GraphState:
        if state.get("approval_id"):
            return {}

        question = state.get("question") or ""
        existing = await db.execute(
            select(PendingApproval).where(
                PendingApproval.thread_id == thread_id,
                PendingApproval.status == "pending",
            )
        )
        if existing.scalar_one_or_none():
            return {
                "refused": True,
                "answer": "This thread already has a pending write approval.",
            }

        # Prefer ticket write; fall back to CRM note write.
        external_id = extract_ticket_id(question)
        new_status = extract_status(question)
        if external_id and new_status:
            tool_name = "ticket_update"
            payload = {"external_id": external_id, "status": new_status}
            rationale = (
                f"Update ticket {external_id} status to '{new_status}' as requested."
            )
        else:
            email = extract_email(question) or "customer@example.com"
            tool_name = "crm_add_note"
            note = question.strip()
            payload = {"email": email, "note": note}
            rationale = f"Add a CRM note for {email}."

        approval = PendingApproval(
            thread_id=thread_id,
            tenant_id=tenant_id,
            tool_name=tool_name,
            payload=payload,
            rationale=rationale,
            status="pending",
        )
        db.add(approval)

        thread_result = await db.execute(
            select(Thread).where(Thread.id == thread_id, Thread.tenant_id == tenant_id)
        )
        thread = thread_result.scalar_one()
        thread.status = "pending_approval"
        await db.flush()

        return {
            "approval_id": str(approval.id),
            "pending_write": {
                "tool_name": tool_name,
                "payload": payload,
                "rationale": rationale,
            },
            "refused": False,
        }

    async def wait_approval(state: GraphState) -> GraphState:
        if state.get("refused"):
            return {}
        decision = interrupt(
            {
                "approval_id": state.get("approval_id"),
                "tool_name": (state.get("pending_write") or {}).get("tool_name"),
                "payload": (state.get("pending_write") or {}).get("payload"),
                "rationale": (state.get("pending_write") or {}).get("rationale"),
            }
        )
        # Client resumes with "approve" or "reject"
        return {"approval_decision": str(decision)}

    async def execute_write(state: GraphState) -> GraphState:
        decision = (state.get("approval_decision") or "").lower()
        approval_id = state.get("approval_id")
        pending = state.get("pending_write") or {}
        tool_name = pending.get("tool_name")
        payload = pending.get("payload") or {}

        approval = None
        if approval_id:
            result = await db.execute(
                select(PendingApproval).where(
                    PendingApproval.id == UUID(approval_id),
                    PendingApproval.tenant_id == tenant_id,
                )
            )
            approval = result.scalar_one_or_none()

        thread_result = await db.execute(
            select(Thread).where(Thread.id == thread_id, Thread.tenant_id == tenant_id)
        )
        thread = thread_result.scalar_one_or_none()

        if decision != "approve":
            if approval and approval.status == "pending":
                approval.status = "rejected"
                approval.resolved_at = datetime.now(UTC)
            if thread:
                thread.status = "active"
            await db.flush()
            return {
                "write_applied": False,
                "answer": "Write was not applied (rejected or cancelled).",
                "refused": False,
                "sources": [],
            }

        applied_result = None
        if tool_name == "ticket_update":
            applied_result = await ticket_tools.ticket_update(
                db,
                tenant_id=tenant_id,
                external_id=str(payload["external_id"]),
                status=str(payload["status"]),
            )
        elif tool_name == "crm_add_note":
            applied_result = await crm_tools.crm_add_note(
                db,
                tenant_id=tenant_id,
                email=str(payload["email"]),
                note=str(payload["note"]),
            )

        if approval and approval.status == "pending":
            approval.status = "approved"
            approval.resolved_at = datetime.now(UTC)
        if thread:
            thread.status = "active"
        await db.flush()

        if applied_result is None:
            answer = "Approval recorded, but the write target was not found."
            applied = False
        else:
            answer = f"Write applied via {tool_name}: {applied_result}"
            applied = True

        return {
            "write_applied": applied,
            "answer": answer,
            "tool_result": applied_result,
            "refused": False,
            "sources": [],
        }

    return {
        "run_docs_search": run_docs_search,
        "run_ticket_read": run_ticket_read,
        "run_crm_read": run_crm_read,
        "create_approval": create_approval,
        "wait_approval": wait_approval,
        "execute_write": execute_write,
    }
