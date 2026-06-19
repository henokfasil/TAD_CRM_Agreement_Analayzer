from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Agreement(Base):
    __tablename__ = "agreements"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    canonical_title: Mapped[str] = mapped_column(String(500), nullable=False)
    short_title: Mapped[str | None] = mapped_column(String(200))
    agreement_family: Mapped[str | None] = mapped_column(String(100))
    agreement_type: Mapped[str | None] = mapped_column(String(100))
    legal_status: Mapped[str | None] = mapped_column(String(100))
    bindingness_status: Mapped[str | None] = mapped_column(String(100))
    enforceability_level: Mapped[str | None] = mapped_column(String(100))
    signature_date: Mapped[date | None] = mapped_column(Date)
    entry_into_force_date: Mapped[date | None] = mapped_column(Date)
    termination_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(String(100))
    scope: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    source_language: Mapped[str | None] = mapped_column(String(50))
    countries: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    organisations: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    producer_consumer_pair: Mapped[str | None] = mapped_column(String(100))
    crm_specific: Mapped[bool | None] = mapped_column(Boolean)
    inclusion_status: Mapped[str | None] = mapped_column(String(100))
    inclusion_reason: Mapped[str | None] = mapped_column(Text)
    validation_status: Mapped[str] = mapped_column(String(50), default="provisional")
    codebook_version: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parties: Mapped[list["AgreementParty"]] = relationship(back_populates="agreement")


class Party(Base):
    __tablename__ = "parties"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    canonical_name: Mapped[str] = mapped_column(String(300), nullable=False)
    iso_code: Mapped[str | None] = mapped_column(String(3))
    party_type: Mapped[str | None] = mapped_column(String(50))
    region: Mapped[str | None] = mapped_column(String(100))
    is_g7: Mapped[bool] = mapped_column(Boolean, default=False)
    is_global_south: Mapped[bool] = mapped_column(Boolean, default=False)
    producer_consumer_classification: Mapped[str | None] = mapped_column(String(100))
    classification_period: Mapped[str | None] = mapped_column(String(100))
    source: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    agreements: Mapped[list["AgreementParty"]] = relationship(back_populates="party")


class AgreementParty(Base):
    __tablename__ = "agreement_parties"

    agreement_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("agreements.id"), primary_key=True
    )
    party_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("parties.id"), primary_key=True
    )
    role: Mapped[str | None] = mapped_column(String(100))

    agreement: Mapped[Agreement] = relationship(back_populates="parties")
    party: Mapped[Party] = relationship(back_populates="agreements")

