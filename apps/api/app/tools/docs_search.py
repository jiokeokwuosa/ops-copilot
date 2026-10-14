"""Read tool: search internal docs (wraps RAG retrieve)."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.retrieve import retrieve_chunks


async def docs_search(db: AsyncSession, *, tenant_id: UUID, query: str) -> list[dict]:
    return await retrieve_chunks(db, tenant_id=tenant_id, query=query, limit=5)
