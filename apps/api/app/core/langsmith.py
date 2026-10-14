"""LangSmith tracing configuration (optional; enabled via env)."""

import os

from app.core.settings import settings


def configure_langsmith() -> None:
    """Enable LangSmith when credentials are present."""
    if settings.langchain_tracing_v2 and settings.langchain_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    else:
        # Keep local runs quiet unless explicitly configured
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
