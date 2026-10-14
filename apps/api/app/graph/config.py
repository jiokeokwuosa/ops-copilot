"""Typed LangGraph / LangChain runnable configs."""

from langchain_core.runnables import RunnableConfig


def thread_config(thread_id: str) -> RunnableConfig:
    """Build a RunnableConfig keyed by app thread id for checkpointing."""
    return RunnableConfig(configurable={"thread_id": thread_id})
