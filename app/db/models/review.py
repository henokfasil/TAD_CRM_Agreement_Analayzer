from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CodingDecision(Base):
    __tablename__ = "coding_decisions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    agreement_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("agreements.id"))
    document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("documents.id"))
    provision_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("provisions.id"))
    variable_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("codebook_variables.id"))
    proposed_value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB)
    final_value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB)
    ai_confidence: Mapped[float | None]
    ai_rationale: Mapped[str | None] = mapped_column(Text)
    evidence_quote: Mapped[str | None] = mapped_column(Text)
    evidence_page: Mapped[int | None]
    evidence_article: Mapped[str | None] = mapped_column(String(100))
    evidence_char_start: Mapped[int | None]
    evidence_char_end: Mapped[int | None]
    evidence_strength: Mapped[float | None]
    negative_search_scope: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str | None] = mapped_column(String(100))
    model_provider: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str | None] = mapped_column(String(100))
    codebook_version: Mapped[str] = mapped_column(String(50))
    first_pass_status: Mapped[str] = mapped_column(String(50), default="proposed")
    verification_status: Mapped[str] = mapped_column(String(50), default="not_verified")
    reviewer_status: Mapped[str] = mapped_column(String(50), default="pending")
    adjudication_status: Mapped[str] = mapped_column(String(50), default="not_required")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    coding_decision_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("coding_decisions.id")
    )
    verifier_model: Mapped[str] = mapped_column(String(100))
    verifier_prompt_version: Mapped[str] = mapped_column(String(100))
    support_status: Mapped[str] = mapped_column(String(50))
    contradiction_status: Mapped[str] = mapped_column(String(50))
    verified_value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB)
    confidence: Mapped[float | None]
    critique: Mapped[str | None] = mapped_column(Text)
    missing_evidence: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    coding_decision_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("coding_decisions.id")
    )
    reviewer_id: Mapped[str] = mapped_column(String(100))
    reviewer_role: Mapped[str] = mapped_column(String(100))
    decision: Mapped[str] = mapped_column(String(50))
    revised_value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB)
    comment: Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AdjudicationDecision(Base):
    __tablename__ = "adjudication_decisions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    coding_decision_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("coding_decisions.id")
    )
    adjudicator_id: Mapped[str] = mapped_column(String(100))
    final_value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB)
    rationale: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

