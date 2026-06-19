from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CodebookVariable(Base):
    __tablename__ = "codebook_variables"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    family: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    data_type: Mapped[str] = mapped_column(String(50), nullable=False)
    allowed_values: Mapped[list | dict | None] = mapped_column(JSONB)
    inclusion_criteria: Mapped[list[str] | None] = mapped_column(JSONB)
    exclusion_criteria: Mapped[list[str] | None] = mapped_column(JSONB)
    dependencies: Mapped[dict | None] = mapped_column(JSONB)
    positive_examples: Mapped[list[dict] | None] = mapped_column(JSONB)
    negative_examples: Mapped[list[dict] | None] = mapped_column(JSONB)
    risk_level: Mapped[str] = mapped_column(String(50), default="medium")
    mandatory_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    codebook_version: Mapped[str] = mapped_column(String(50), nullable=False)

