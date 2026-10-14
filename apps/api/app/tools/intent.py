"""Lightweight intent routing for demo tool paths (keyword heuristics)."""

import re

TICKET_ID_RE = re.compile(r"TKT-\d+", re.IGNORECASE)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")


def detect_intent(question: str) -> str:
    q = question.lower()
    write_verbs = ("update ", "change ", "set ", "close ", "add note", "add a note")
    if any(v in q for v in write_verbs) and ("ticket" in q or "crm" in q or "note" in q):
        return "write"
    if "ticket" in q:
        return "ticket_read"
    if "crm" in q or "contact" in q or "customer" in q:
        return "crm_read"
    if "search docs" in q or "find docs" in q or "documentation" in q:
        return "docs_search"
    return "rag"


def extract_ticket_id(question: str) -> str | None:
    match = TICKET_ID_RE.search(question)
    return match.group(0).upper() if match else None


def extract_status(question: str) -> str | None:
    match = re.search(r"status\s+to\s+(\w+)", question, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    if "close" in question.lower():
        return "closed"
    return None


def extract_email(question: str) -> str | None:
    match = EMAIL_RE.search(question)
    return match.group(0).lower() if match else None
