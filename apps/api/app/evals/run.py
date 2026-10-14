"""Golden eval runner for grounding / refusal / tool cases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import AuthContext
from app.db.models import Thread
from app.db.seed import TENANT_A_ID, USER_A_ID
from app.graph.build import build_graph
from app.graph.checkpointer import ensure_checkpointer
from app.graph.config import thread_config
from app.graph.state import GraphState
from app.tools.intent import detect_intent

CASES_DIR = Path(__file__).parent / "cases"


def load_cases(suite: str = "golden") -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in sorted(CASES_DIR.glob("*.json")):
        cases.extend(json.loads(path.read_text()))
    if suite != "golden":
        cases = [c for c in cases if c.get("category") == suite]
    return cases


def _passes(result: dict[str, Any], expected: dict[str, Any]) -> tuple[bool, str]:
    if "refused" in expected and bool(result.get("refused")) != bool(expected["refused"]):
        return False, f"refused={result.get('refused')} expected={expected['refused']}"
    needles = expected.get("content_contains_any") or []
    content = (result.get("content") or "").lower()
    if needles and not any(n.lower() in content for n in needles):
        return False, f"content missing any of {needles}"
    return True, "ok"


async def run_eval_suite(db: AsyncSession, suite: str = "golden") -> dict[str, Any]:
    await ensure_checkpointer()
    cases = load_cases(suite)
    results: list[dict[str, Any]] = []
    auth = AuthContext(
        user_id=USER_A_ID,
        tenant_id=TENANT_A_ID,
        email="alice@tenant-a.example",
        display_name="Alice",
        tenant_name="Tenant A",
    )

    for case in cases:
        thread = Thread(
            id=uuid4(),
            tenant_id=auth.tenant_id,
            user_id=auth.user_id,
            title=f"eval:{case['id']}",
            status="active",
        )
        db.add(thread)
        await db.flush()

        graph = build_graph(db, auth.tenant_id, thread.id)
        config = thread_config(str(thread.id))
        inputs: GraphState = {
            "question": case["input"],
            "tenant_id": str(auth.tenant_id),
            "thread_id": str(thread.id),
            "intent": detect_intent(case["input"]),
            "messages": [],
        }
        final = await graph.ainvoke(inputs, config=config)
        outcome = {
            "content": final.get("answer") or "",
            "refused": bool(final.get("refused")),
        }
        # Interrupted writes still count as a tool path success if approval pending
        if final.get("__interrupt__"):
            outcome["content"] = outcome["content"] or "approval_required"
            outcome["refused"] = False

        ok, notes = _passes(outcome, case.get("expected") or {})
        results.append(
            {
                "case_id": case["id"],
                "pass": ok,
                "score": 1.0 if ok else 0.0,
                "notes": notes,
                "trace_url": None,
            }
        )

    await db.commit()
    passed = sum(1 for r in results if r["pass"])
    return {"passed": passed, "total": len(results), "results": results}
