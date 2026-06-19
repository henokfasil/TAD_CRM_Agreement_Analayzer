"""phase 1 foundation

Revision ID: 0001_phase1_foundation
Revises:
Create Date: 2026-06-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_phase1_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agreements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_title", sa.String(length=500), nullable=False),
        sa.Column("short_title", sa.String(length=200)),
        sa.Column("agreement_family", sa.String(length=100)),
        sa.Column("agreement_type", sa.String(length=100)),
        sa.Column("legal_status", sa.String(length=100)),
        sa.Column("bindingness_status", sa.String(length=100)),
        sa.Column("enforceability_level", sa.String(length=100)),
        sa.Column("signature_date", sa.Date()),
        sa.Column("entry_into_force_date", sa.Date()),
        sa.Column("termination_date", sa.Date()),
        sa.Column("status", sa.String(length=100)),
        sa.Column("scope", sa.Text()),
        sa.Column("summary", sa.Text()),
        sa.Column("source_language", sa.String(length=50)),
        sa.Column("countries", postgresql.ARRAY(sa.String())),
        sa.Column("organisations", postgresql.ARRAY(sa.String())),
        sa.Column("producer_consumer_pair", sa.String(length=100)),
        sa.Column("crm_specific", sa.Boolean()),
        sa.Column("inclusion_status", sa.String(length=100)),
        sa.Column("inclusion_reason", sa.Text()),
        sa.Column("validation_status", sa.String(length=50), nullable=False),
        sa.Column("codebook_version", sa.String(length=50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "parties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_name", sa.String(length=300), nullable=False),
        sa.Column("iso_code", sa.String(length=3)),
        sa.Column("party_type", sa.String(length=50)),
        sa.Column("region", sa.String(length=100)),
        sa.Column("is_g7", sa.Boolean(), nullable=False),
        sa.Column("is_global_south", sa.Boolean(), nullable=False),
        sa.Column("producer_consumer_classification", sa.String(length=100)),
        sa.Column("classification_period", sa.String(length=100)),
        sa.Column("source", sa.Text()),
        sa.Column("notes", sa.Text()),
    )
    op.create_table(
        "agreement_parties",
        sa.Column("agreement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agreements.id"), primary_key=True),
        sa.Column("party_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("parties.id"), primary_key=True),
        sa.Column("role", sa.String(length=100)),
    )
    op.create_table(
        "codebook_variables",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("family", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("data_type", sa.String(length=50), nullable=False),
        sa.Column("allowed_values", postgresql.JSONB()),
        sa.Column("inclusion_criteria", postgresql.JSONB()),
        sa.Column("exclusion_criteria", postgresql.JSONB()),
        sa.Column("dependencies", postgresql.JSONB()),
        sa.Column("positive_examples", postgresql.JSONB()),
        sa.Column("negative_examples", postgresql.JSONB()),
        sa.Column("risk_level", sa.String(length=50), nullable=False),
        sa.Column("mandatory_human_review", sa.Boolean(), nullable=False),
        sa.Column("codebook_version", sa.String(length=50), nullable=False),
    )
    op.create_index("ix_codebook_variables_code", "codebook_variables", ["code"])
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agreement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agreements.id")),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("document_type", sa.String(length=100)),
        sa.Column("version", sa.String(length=50)),
        sa.Column("language", sa.String(length=50)),
        sa.Column("source_url", sa.Text()),
        sa.Column("retrieval_date", sa.Date()),
        sa.Column("publication_date", sa.Date()),
        sa.Column("signature_date", sa.Date()),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(length=200)),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("extracted_text", sa.Text()),
        sa.Column("extraction_method", sa.String(length=100)),
        sa.Column("ocr_used", sa.Boolean(), nullable=False),
        sa.Column("page_count", sa.Integer()),
        sa.Column("parser_version", sa.String(length=100)),
        sa.Column("is_official_source", sa.Boolean(), nullable=False),
        sa.Column("authenticity_status", sa.String(length=50), nullable=False),
        sa.Column("supersedes_document_id", postgresql.UUID(as_uuid=True)),
        sa.Column("processing_status", sa.String(length=50), nullable=False),
    )
    op.create_table(
        "document_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("image_path", sa.Text()),
        sa.Column("extraction_confidence", sa.Float()),
        sa.Column("bounding_box_metadata", postgresql.JSONB()),
    )
    op.create_table(
        "provisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("agreement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agreements.id")),
        sa.Column("page_start", sa.Integer()),
        sa.Column("page_end", sa.Integer()),
        sa.Column("article_number", sa.String(length=100)),
        sa.Column("section_title", sa.String(length=300)),
        sa.Column("paragraph_number", sa.String(length=100)),
        sa.Column("provision_text", sa.Text(), nullable=False),
        sa.Column("parent_provision_id", postgresql.UUID(as_uuid=True)),
        sa.Column("provision_type", sa.String(length=100)),
        sa.Column("embedding", postgresql.JSONB()),
        sa.Column("text_hash", sa.String(length=64), nullable=False),
        sa.Column("segmentation_version", sa.String(length=50), nullable=False),
    )
    op.create_table(
        "coding_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agreement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agreements.id")),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("provision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("provisions.id")),
        sa.Column("variable_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("codebook_variables.id"), nullable=False),
        sa.Column("proposed_value", postgresql.JSONB()),
        sa.Column("final_value", postgresql.JSONB()),
        sa.Column("ai_confidence", sa.Float()),
        sa.Column("ai_rationale", sa.Text()),
        sa.Column("evidence_quote", sa.Text()),
        sa.Column("evidence_page", sa.Integer()),
        sa.Column("evidence_article", sa.String(length=100)),
        sa.Column("evidence_char_start", sa.Integer()),
        sa.Column("evidence_char_end", sa.Integer()),
        sa.Column("evidence_strength", sa.Float()),
        sa.Column("negative_search_scope", sa.Text()),
        sa.Column("model_name", sa.String(length=100)),
        sa.Column("model_provider", sa.String(length=100)),
        sa.Column("prompt_version", sa.String(length=100)),
        sa.Column("codebook_version", sa.String(length=50), nullable=False),
        sa.Column("first_pass_status", sa.String(length=50), nullable=False),
        sa.Column("verification_status", sa.String(length=50), nullable=False),
        sa.Column("reviewer_status", sa.String(length=50), nullable=False),
        sa.Column("adjudication_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "verification_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("coding_decision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("coding_decisions.id"), nullable=False),
        sa.Column("verifier_model", sa.String(length=100), nullable=False),
        sa.Column("verifier_prompt_version", sa.String(length=100), nullable=False),
        sa.Column("support_status", sa.String(length=50), nullable=False),
        sa.Column("contradiction_status", sa.String(length=50), nullable=False),
        sa.Column("verified_value", postgresql.JSONB()),
        sa.Column("confidence", sa.Float()),
        sa.Column("critique", sa.Text()),
        sa.Column("missing_evidence", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "review_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("coding_decision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("coding_decisions.id"), nullable=False),
        sa.Column("reviewer_id", sa.String(length=100), nullable=False),
        sa.Column("reviewer_role", sa.String(length=100), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("revised_value", postgresql.JSONB()),
        sa.Column("comment", sa.Text()),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "adjudication_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("coding_decision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("coding_decisions.id"), nullable=False),
        sa.Column("adjudicator_id", sa.String(length=100), nullable=False),
        sa.Column("final_value", postgresql.JSONB()),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user", sa.String(length=100)),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("object_type", sa.String(length=100), nullable=False),
        sa.Column("object_id", sa.String(length=100)),
        sa.Column("old_value", postgresql.JSONB()),
        sa.Column("new_value", postgresql.JSONB()),
        sa.Column("session_metadata", sa.Text()),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("adjudication_decisions")
    op.drop_table("review_decisions")
    op.drop_table("verification_results")
    op.drop_table("coding_decisions")
    op.drop_table("provisions")
    op.drop_table("document_pages")
    op.drop_table("documents")
    op.drop_index("ix_codebook_variables_code", table_name="codebook_variables")
    op.drop_table("codebook_variables")
    op.drop_table("agreement_parties")
    op.drop_table("parties")
    op.drop_table("agreements")

