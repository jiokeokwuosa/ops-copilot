"""Add documents and document_chunks with pgvector."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_documents"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("uri", sa.String(1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_documents_tenant_id", "documents", ["tenant_id"])
    op.execute(
        """
        CREATE TABLE document_chunks (
            id UUID PRIMARY KEY,
            document_id UUID NOT NULL REFERENCES documents(id),
            tenant_id UUID NOT NULL,
            content TEXT NOT NULL,
            embedding vector(1536),
            metadata JSONB
        )
        """
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_document_chunks_tenant_id", "document_chunks", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("document_chunks")
    op.drop_table("documents")
