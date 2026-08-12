"""Database models for Document Series, Talonarios, Numbers, and Idempotency (Phase 013)."""

from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentSeriesModel(Base):
    """Represents a logical sequence space for a combination of Org + Type + Site + Year."""

    __tablename__ = "document_series"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_branches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    document_site_code_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_site_codes.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    document_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_types.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    document_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    code_standard_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    sequence_scope: Mapped[str] = mapped_column(String(64), nullable=False, default="TYPE_SITE_YEAR")

    prefix: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. OC-LIM-2026
    sequence_start: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    next_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sequence_max: Mapped[int] = mapped_column(Integer, nullable=False, default=999999)

    status: Mapped[str] = mapped_column(String(32), default="DRAFT", nullable=False, index=True)
    lock_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    close_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    exhausted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "document_type_id",
            "document_site_code_id",
            "document_year",
            name="uq_document_series_scope",
        ),
        CheckConstraint("next_sequence >= sequence_start", name="ck_series_next_seq_ge_start"),
        CheckConstraint("next_sequence <= sequence_max + 1", name="ck_series_next_seq_le_max"),
    )


class DocumentTalonarioModel(Base):
    """Digital block/batch of reserved document codes (e.g. TAL-OC-LIM-2026-000001-000100)."""

    __tablename__ = "document_talonarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    series_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_series.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    talonario_code: Mapped[str] = mapped_column(String(128), nullable=False)

    range_start: Mapped[int] = mapped_column(Integer, nullable=False)
    range_end: Mapped[int] = mapped_column(Integer, nullable=False)
    total_numbers: Mapped[int] = mapped_column(Integer, nullable=False)

    reserved_numbers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assigned_numbers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    issued_numbers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancelled_numbers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    voided_numbers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_numbers: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="RESERVED", nullable=False, index=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)

    requested_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reserved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    exhausted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    request_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    manifest_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "talonario_code", name="uq_document_talonario_code"),
        CheckConstraint("range_end >= range_start", name="ck_talonario_range_end_ge_start"),
        CheckConstraint("total_numbers > 0", name="ck_talonario_total_gt_zero"),
    )


class DocumentNumberModel(Base):
    """Ledger table recording every individual document code sequence number."""

    __tablename__ = "document_numbers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    series_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_series.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    talonario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_talonarios.id", ondelete="SET NULL"), nullable=True, index=True
    )

    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    full_document_code: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="RESERVED", nullable=False, index=True)

    reservation_type: Mapped[str] = mapped_column(String(32), default="INDIVIDUAL", nullable=False)
    reservation_purpose: Mapped[str | None] = mapped_column(Text, nullable=True)

    reserved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reserved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    assigned_resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assigned_resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    void_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("series_id", "sequence_number", name="uq_document_number_series_seq"),
        UniqueConstraint("organization_id", "full_document_code", name="uq_document_number_org_code"),
        CheckConstraint("sequence_number >= 1", name="ck_document_number_seq_ge_1"),
    )


class IdempotencyRecordModel(Base):
    """Tracks idempotency keys and request hashes for series and numbering operations."""

    __tablename__ = "idempotency_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    response_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="COMPLETED", nullable=False)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "operation", "idempotency_key", name="uq_idempotency_record"
        ),
    )
