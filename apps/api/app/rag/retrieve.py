from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.document import DocumentChunk


async def retrieve_chunks(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    query: str,
    limit: int = 4,
) -> list[dict]:
    result = await db.execute(
        select(DocumentChunk)
        .options(selectinload(DocumentChunk.document))
        .where(DocumentChunk.tenant_id == tenant_id)
    )
    chunks = result.scalars().all()
    tokens = [t.lower() for t in query.split() if len(t) > 2]

    scored: list[tuple[int, DocumentChunk]] = []
    for chunk in chunks:
        content_l = chunk.content.lower()
        score = sum(1 for t in tokens if t in content_l)
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)

    out: list[dict] = []
    for _, chunk in scored[:limit]:
        out.append(
            {
                "id": str(chunk.id),
                "title": chunk.document.title,
                "uri": chunk.document.uri,
                "content": chunk.content,
            }
        )
    return out
