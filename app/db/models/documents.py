from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    agreement_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("agreements.id"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    document_type: Mapped[str | None] = mapped_column(String(100))
    version: Mapped[str | None] = mapped_column(String(50))
    language: Mapped[str | None] = mapped_column(String(50))
    source_url: Mapped[str | None] = mapped_column(Text)
    retrieval_date: Mapped[date | None] = mapped_column(Date)
    publication_date: Mapped[date | None] = mapped_column(Date)
    signature_date: Mapped[date | None] = mapped_column(Date)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(200))
    sha256_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    extraction_method: Mapped[str | None] = mapped_column(String(100))
    ocr_used: Mapped[bool] = mapped_column(Boolean, default=False)
    page_count: Mapped[int | None] = mapped_column(Integer)
    parser_version: Mapped[str | None] = mapped_column(String(100))
    is_official_source: Mapped[bool] = mapped_column(Boolean, default=False)
    authenticity_status: Mapped[str] = mapped_column(String(50), default="unverified")
    supersedes_document_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    processing_status: Mapped[str] = mapped_column(String(50), default="uploaded")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("documents.id"))
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    image_path: Mapped[str | None] = mapped_column(Text)
    extraction_confidence: Mapped[float | None]
    bounding_box_metadata: Mapped[dict | None] = mapped_column(JSONB)


class Provision(Base):
    __tablename__ = "provisions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("documents.id"))
    agreement_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("agreements.id"))
    page_start: Mapped[int | None] = mapped_column(Integer)
    page_end: Mapped[int | None] = mapped_column(Integer)
    article_number: Mapped[str | None] = mapped_column(String(100))
    section_title: Mapped[str | None] = mapped_column(String(300))
    paragraph_number: Mapped[str | None] = mapped_column(String(100))
    provision_text: Mapped[str] = mapped_column(Text, nullable=False)
    parent_provision_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    provision_type: Mapped[str | None] = mapped_column(String(100))
    embedding: Mapped[list[float] | None] = mapped_column(JSONB)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    segmentation_version: Mapped[str] = mapped_column(String(50), nullable=False)

