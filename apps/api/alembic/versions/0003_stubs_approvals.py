"""Add ticket/CRM stubs and pending_approvals."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_stubs_approvals"
down_revision: Union[str, None] = "0002_documents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ticket_stubs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(64), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ticket_stubs_tenant_id", "ticket_stubs", ["tenant_id"])
    op.create_index("ix_ticket_stubs_external_id", "ticket_stubs", ["external_id"])

    op.create_table(
        "crm_contact_stubs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("notes", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_crm_contact_stubs_tenant_id", "crm_contact_stubs", ["tenant_id"])

    op.create_table(
        "pending_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_name", sa.String(128), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["thread_id"], ["threads.id"]),
    )
    op.create_index("ix_pending_approvals_thread_id", "pending_approvals", ["thread_id"])
    op.create_index("ix_pending_approvals_tenant_id", "pending_approvals", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("pending_approvals")
    op.drop_table("crm_contact_stubs")
    op.drop_table("ticket_stubs")
