"""Database models for Document Catalog and Versioning (Phase 011)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentFamilyModel(Base):
    """Represents a logical grouping of document types (e.g. PURCHASING, INBOUND)."""

    __tablename__ = "document_families"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_module: Mapped[str] = mapped_column(String(64), nullable=False, default="logistics")
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    types: Mapped[list[DocumentTypeModel]] = relationship("DocumentTypeModel", back_populates="family")


class DocumentRetentionPolicyModel(Base):
    """Retention class and policy specifications for document types."""

    __tablename__ = "document_retention_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    retention_class: Mapped[str] = mapped_column(String(64), nullable=False)
    minimum_retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=365)
    maximum_retention_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    archive_after_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deletion_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    legal_hold_supported: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_manual_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    applies_to_origin_type: Mapped[str] = mapped_column(String(64), nullable=False, default="INTERNAL_GENERATED")
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class DocumentTypeModel(Base):
    """Document type definition within the central catalog."""

    __tablename__ = "document_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_families.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    origin_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    owner_module: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(64), nullable=False)

    catalog_status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, index=True)
    active_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    is_system: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_official_external: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    supports_internal_number: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_external_number: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_series: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_talonario: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_preview: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_issue: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_download: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_bulk_download: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_reprint: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_cancel: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_public_verification: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    requires_qr: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_signature: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_reason_on_reprint: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_reason_on_cancel: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    family: Mapped[DocumentFamilyModel] = relationship("DocumentFamilyModel", back_populates="types")
    versions: Mapped[list[DocumentTypeVersionModel]] = relationship(
        "DocumentTypeVersionModel", back_populates="document_type", cascade="all, delete-orphan"
    )


class DocumentTypeVersionModel(Base):
    """Immutable version contract for a document type."""

    __tablename__ = "document_type_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_types.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", nullable=False, index=True)

    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    required_fields_schema: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    optional_fields_schema: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    sections_schema: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    allowed_statuses: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    permission_policy: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)

    retention_policy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_retention_policies.id", ondelete="SET NULL"), nullable=True
    )
    template_key: Mapped[str] = mapped_column(String(128), default="PENDING_PHASE_014", nullable=False)
    template_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    document_type: Mapped[DocumentTypeModel] = relationship("DocumentTypeModel", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("document_type_id", "version", name="uq_document_type_version"),
    )


class DocumentCatalogVersionModel(Base):
    """Global version release tracking of the document catalog."""

    __tablename__ = "document_catalog_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    released_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    manifest_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class DocumentInstanceModel(Base):
    """Represents a specific document record through its operational lifecycle (Phase 020)."""

    __tablename__ = "document_instances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_branches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    document_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_types.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    document_type_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_type_versions.id", ondelete="RESTRICT"), nullable=True
    )
    template_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_template_versions.id", ondelete="RESTRICT"), nullable=True
    )

    source_resource_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    source_operation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    document_number_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_numbers.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    document_code: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", nullable=False, index=True)
    lifecycle_status: Mapped[str] = mapped_column(String(32), default="DRAFT", nullable=False, index=True)
    sensitivity: Mapped[str] = mapped_column(String(32), default="RESTRICTED", nullable=False)

    current_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    authoritative_artifact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    issued_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    reprint_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    print_request_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "document_code", name="uq_document_instance_org_code"),
    )


class DocumentSnapshotModel(Base):
    """Immutable copy of the document's canonical payload at issuance or cancellation (Phase 020)."""

    __tablename__ = "document_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_instances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    snapshot_type: Mapped[str] = mapped_column(String(32), default="ISSUANCE", nullable=False)  # ISSUANCE, REPLACEMENT, MIGRATION
    snapshot_schema_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)

    canonical_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    canonical_payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    document_type_code: Mapped[str] = mapped_column(String(32), nullable=False)
    document_type_version: Mapped[str] = mapped_column(String(32), nullable=False)
    catalog_version: Mapped[str] = mapped_column(String(32), nullable=False)
    template_key: Mapped[str] = mapped_column(String(128), nullable=False)
    template_version: Mapped[str] = mapped_column(String(32), nullable=False)

    renderer_name: Mapped[str] = mapped_column(String(64), default="Jinja2+WeasyPrint", nullable=False)
    renderer_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    code_standard_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)

    organization_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    branch_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    warehouse_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("document_id", "snapshot_version", name="uq_document_snapshot_ver"),
    )


class DocumentArtifactModel(Base):
    """Metadata details of physically stored document assets/files (Phase 020)."""

    __tablename__ = "document_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_instances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_snapshots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    artifact_type: Mapped[str] = mapped_column(String(32), nullable=False)  # ISSUED_PDF, CANCELLED_PDF, REPRINT_PDF, etc.
    representation_status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, index=True)

    mime_type: Mapped[str] = mapped_column(String(64), default="application/pdf", nullable=False)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(32), default="local", nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    template_version: Mapped[str] = mapped_column(String(32), nullable=False)
    renderer_version: Mapped[str] = mapped_column(String(32), nullable=False)
    copy_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    generated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_authoritative: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


class DocumentReprintModel(Base):
    """Historical record log of every reprint copy issued (Phase 020)."""

    __tablename__ = "document_reprints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_instances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_snapshots.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_artifacts.id", ondelete="RESTRICT"), nullable=False
    )
    generated_artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_artifacts.id", ondelete="RESTRICT"), nullable=False
    )

    copy_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    step_up_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    idempotency_key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("document_id", "copy_number", name="uq_document_reprint_num"),
    )


class DocumentCancellationModel(Base):
    """Immutable cancellation reason audit record (Phase 020)."""

    __tablename__ = "document_cancellations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_instances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_snapshots.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    issued_artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_artifacts.id", ondelete="RESTRICT"), nullable=False
    )
    cancelled_artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_artifacts.id", ondelete="RESTRICT"), nullable=False
    )

    reason: Mapped[str] = mapped_column(Text, nullable=False)
    cancelled_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    cancelled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    step_up_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    authorization_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    idempotency_key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("document_id", name="uq_document_cancellation_doc"),
    )


class DocumentExportJobModel(Base):
    """Queued or processed job to export document selections to ZIP formats (Phase 020)."""

    __tablename__ = "document_export_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    export_type: Mapped[str] = mapped_column(String(32), default="ZIP", nullable=False)  # ZIP, MERGED_PDF, MANIFEST_ONLY
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="QUEUED", nullable=False, index=True)
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_artifacts.id", ondelete="SET NULL"), nullable=True
    )
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

