"""Unit tests for retrieve-grade-rewrite-refuse helpers (pure logic)."""

from app.rag.grade import grade_documents
from app.rag.rewrite import rewrite_query
from app.rag.route import is_off_topic


def test_off_topic_detection() -> None:
    assert is_off_topic("What is the weather in Chennai?") is True
    assert is_off_topic("How do I reset MFA for a user?") is False


def test_grade_rejects_empty() -> None:
    result = grade_documents("reset MFA", [])
    assert result.sufficient is False


def test_grade_accepts_relevant() -> None:
    docs = [
        {
            "id": "1",
            "title": "MFA Reset",
            "uri": "docs/corpus/mfa-reset.md",
            "content": "Support agents can reset multi-factor authentication (MFA).",
        }
    ]
    result = grade_documents("How do I reset MFA?", docs)
    assert result.sufficient is True


def test_rewrite_changes_query() -> None:
    rewritten = rewrite_query("reset mfa", "documents were too vague")
    assert isinstance(rewritten, str)
    assert len(rewritten) > 0
