from dataclasses import dataclass


OFF_TOPIC_HINTS = (
    "weather",
    "recipe",
    "celebrity",
    "sports score",
    "movie review",
    "write a poem",
    "joke",
)


def is_off_topic(question: str) -> bool:
    q = question.lower()
    return any(h in q for h in OFF_TOPIC_HINTS)


@dataclass
class GradeResult:
    sufficient: bool
    rationale: str


def grade_documents(query: str, docs: list[dict]) -> GradeResult:
    if not docs:
        return GradeResult(False, "No documents retrieved")
    tokens = {t for t in query.lower().split() if len(t) > 2}
    if not tokens:
        return GradeResult(False, "Query too vague")
    best = 0
    for doc in docs:
        content = (doc.get("content") or "").lower()
        overlap = sum(1 for t in tokens if t in content)
        best = max(best, overlap)
    if best == 0:
        return GradeResult(False, "No lexical overlap with retrieved docs")
    return GradeResult(True, f"Matched {best} query tokens")


def rewrite_query(query: str, rationale: str) -> str:
    # Bounded, deterministic rewrite for demo/tests without an LLM call.
    base = query.strip()
    if "mfa" in base.lower() or "multi-factor" in base.lower():
        return f"{base} MFA reset runbook procedure"
    if "password" in base.lower():
        return f"{base} password reset policy procedure"
    return f"{base} internal support runbook ({rationale[:40]})"
