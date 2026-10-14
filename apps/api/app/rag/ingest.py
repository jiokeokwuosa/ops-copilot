"""Ingest markdown corpus into documents/chunks for a tenant."""

import asyncio
import uuid
from pathlib import Path

from sqlalchemy import select

from app.db.models.document import Document, DocumentChunk
from app.db.seed import TENANT_A_ID, TENANT_B_ID
from app.db.session import SessionLocal


def _corpus_dir() -> Path:
    """Local checkouts use <repo>/docs/corpus. The API container mounts it at /app/corpus."""
    mounted = Path("/app/corpus")
    file_path = Path(__file__).resolve()
    if len(file_path.parents) > 4:
        local = file_path.parents[4] / "docs" / "corpus"
        if local.exists():
            return local
    return mounted


def _chunk_markdown(text: str, max_len: int = 800) -> list[str]:
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for part in parts:
        if len(buf) + len(part) + 2 <= max_len:
            buf = f"{buf}\n\n{part}".strip()
        else:
            if buf:
                chunks.append(buf)
            buf = part
    if buf:
        chunks.append(buf)
    return chunks or [text[:max_len]]


async def ingest_corpus(tenant_ids: list[uuid.UUID] | None = None) -> None:
    tenant_ids = tenant_ids or [TENANT_A_ID, TENANT_B_ID]
    corpus = _corpus_dir()
    files = sorted(corpus.glob("**/*.md"))
    if not files:
        print(f"No markdown files in {corpus}")
        return

    async with SessionLocal() as db:
        for tenant_id in tenant_ids:
            # Clear existing docs for tenant (demo-friendly re-ingest)
            existing = await db.execute(select(Document).where(Document.tenant_id == tenant_id))
            for doc in existing.scalars().all():
                await db.delete(doc)
            await db.commit()

            for path in files:
                text = path.read_text(encoding="utf-8")
                title = path.stem.replace("-", " ").title()
                uri = f"docs/corpus/{path.name}"
                doc = Document(id=uuid.uuid4(), tenant_id=tenant_id, title=title, uri=uri)
                db.add(doc)
                await db.flush()
                for i, chunk_text in enumerate(_chunk_markdown(text)):
                    db.add(
                        DocumentChunk(
                            id=uuid.uuid4(),
                            document_id=doc.id,
                            tenant_id=tenant_id,
                            content=chunk_text,
                            embedding=None,
                            chunk_metadata={"index": i},
                        )
                    )
            await db.commit()
        print(f"Ingested {len(files)} files for {len(tenant_ids)} tenants from {corpus}")


if __name__ == "__main__":
    asyncio.run(ingest_corpus())
