"""Database models for Document Coding Standard (Phase 012)."""

from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Boolean,
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


class DocumentCodeStandardModel(Base):
    """Versioned technical standard for document codes."""

    __tablename__ = "document_code_standards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), nullable=False, default="STD_LOGISTICS_CODE")
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    name: Mapped[str] = mapped_column(String(128), nullable=False, default="Estándar TIPO-SEDE-AÑO-CORRELATIVO")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    pattern: Mapped[str] = mapped_column(String(128), nullable=False, default="^[A-Z0-9]{2,8}-[A-Z0-9]{2,10}-[0-9]{4}-[0-9]{6}$")
    separator: Mapped[str] = mapped_column(String(4), nullable=False, default="-")

    document_type_min_length: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    document_type_max_length: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    site_code_min_length: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    site_code_max_length: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    year_length: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    sequence_length: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    sequence_start: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sequence_max: Mapped[int] = mapped_column(Integer, default=999999, nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, index=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("code", "version", name="uq_document_code_standard_version"),
    )


class DocumentSiteCodeModel(Base):
    """Human-readable short document site code for a branch (e.g. LIM, SJM)."""

    __tablename__ = "document_site_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_branches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_document_site_code_org"),
    )


class DocumentTypeCodePolicyModel(Base):
    """Coding policy mapping for a specific document type."""

    __tablename__ = "document_type_code_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_types.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_standard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_code_standards.id", ondelete="RESTRICT"), nullable=False
    )
    uses_internal_code: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    uses_site_segment: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    uses_year_segment: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    uses_sequence_segment: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sequence_scope: Mapped[str] = mapped_column(String(64), default="TYPE_SITE_YEAR", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("document_type_id", name="uq_document_type_code_policy"),
    )
