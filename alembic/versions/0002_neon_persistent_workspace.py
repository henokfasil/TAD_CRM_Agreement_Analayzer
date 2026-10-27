"""add Neon-backed persistent workspace

Revision ID: 0002_neon_persistent_workspace
Revises: 0001_phase1_foundation
Create Date: 2026-10-27
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_neon_persistent_workspace"
down_revision: str | None = "0001_phase1_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "crm_record_store",
        sa.Column("collection", sa.Text(), nullable=False),
        sa.Column("record_id", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("collection", "record_id"),
    )
    op.create_index(
        "ix_crm_record_store_collection",
        "crm_record_store",
        ["collection"],
    )
    op.create_table(
        "crm_document_files",
        sa.Column("document_id", sa.Text(), primary_key=True),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256_hash", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("crm_document_files")
    op.drop_index("ix_crm_record_store_collection", table_name="crm_record_store")
    op.drop_table("crm_record_store")
