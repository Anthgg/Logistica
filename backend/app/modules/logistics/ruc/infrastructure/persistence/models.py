"""SQLAlchemy 2.0 ORM Models for Phase 026 (RUC Module)."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RucDataSourceModel(Base):
    __tablename__ = "ruc_data_sources"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    authority: Mapped[str] = mapped_column(String(100), nullable=False, server_default="SUNAT")
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    base_domain: Mapped[str] = mapped_column(String(200), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("10"))
    confidence_policy: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    refresh_policy: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    licensing_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    terms_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="ACTIVE")
    last_successful_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failed_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class RucDatasetVersionModel(Base):
    __tablename__ = "ruc_dataset_versions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    data_source_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("ruc_data_sources.id", ondelete="CASCADE"), nullable=False)
    dataset_type: Mapped[str] = mapped_column(String(40), nullable=False)  # RUC_GENERAL, RUC_ANNEX_ADDRESS
    source_published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    import_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    import_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="DISCOVERED")
    parser_version: Mapped[str] = mapped_column(String(30), nullable=False, server_default="1.0.0")
    schema_version: Mapped[str] = mapped_column(String(30), nullable=False, server_default="1.0.0")
    source_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    compressed_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    uncompressed_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    archive_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    total_rows: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    accepted_rows: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    rejected_rows: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    duplicate_rows: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    inserted_rows: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    updated_rows: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    unchanged_rows: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    removed_rows: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    import_job_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    activated_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RucImportJobModel(Base):
    __tablename__ = "ruc_import_jobs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    data_source_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("ruc_data_sources.id", ondelete="CASCADE"), nullable=False)
    dataset_type: Mapped[str] = mapped_column(String(40), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(30), nullable=False, server_default="SCHEDULED")
    requested_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="QUEUED")
    idempotency_key_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    request_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    current_stage: Mapped[str] = mapped_column(String(50), nullable=False, server_default="INIT")
    progress_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    downloaded_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    processed_rows: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    accepted_rows: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    rejected_rows: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    error_code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    correlation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class RucRegistryEntryModel(Base):
    __tablename__ = "ruc_registry_entries"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    dataset_version_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("ruc_dataset_versions.id", ondelete="CASCADE"), nullable=False)
    ruc: Mapped[str] = mapped_column(String(11), nullable=False)
    normalized_ruc: Mapped[str] = mapped_column(String(11), nullable=False, index=True)
    legal_name: Mapped[str] = mapped_column(String(300), nullable=False)
    normalized_legal_name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    taxpayer_status_raw: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    taxpayer_status_normalized: Mapped[str] = mapped_column(String(50), nullable=False, server_default="UNKNOWN")
    domicile_condition_raw: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    domicile_condition_normalized: Mapped[str] = mapped_column(String(50), nullable=False, server_default="UNKNOWN")
    ubigeo_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    source_published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    record_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    row_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")


class RucRegistryAnnexAddressModel(Base):
    __tablename__ = "ruc_registry_annex_addresses"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    dataset_version_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("ruc_dataset_versions.id", ondelete="CASCADE"), nullable=False)
    ruc: Mapped[str] = mapped_column(String(11), nullable=False, index=True)
    ubigeo_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    address_raw: Mapped[str] = mapped_column(Text, nullable=False)
    address_normalized: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    record_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    row_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")


class RucAssistedVerificationModel(Base):
    __tablename__ = "ruc_assisted_verifications"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False)
    business_partner_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="SET NULL"), nullable=True)
    ruc: Mapped[str] = mapped_column(String(11), nullable=False, index=True)
    verification_reason: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, server_default="ASSISTED_OFFICIAL_REVIEW")
    source_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reviewed_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    observed_legal_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    observed_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    observed_condition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    observed_ubigeo: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_reference_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    result: Mapped[str] = mapped_column(String(30), nullable=False, server_default="MATCH_CONFIRMED")
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False, server_default="MEDIUM")
    approved_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class BusinessPartnerRucVerificationModel(Base):
    __tablename__ = "business_partner_ruc_verifications"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False)
    business_partner_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=False)
    identifier_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("business_partner_identifiers.id", ondelete="CASCADE"), nullable=True)
    ruc: Mapped[str] = mapped_column(String(11), nullable=False, index=True)
    verification_method: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    dataset_version_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("ruc_dataset_versions.id", ondelete="SET NULL"), nullable=True)
    provider_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    assisted_verification_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("ruc_assisted_verifications.id", ondelete="SET NULL"), nullable=True)
    verification_result: Mapped[str] = mapped_column(String(30), nullable=False, server_default="VERIFIED")
    verified_legal_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    verified_taxpayer_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    verified_domicile_condition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    verified_ubigeo: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    source_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    verified_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False, server_default="HIGH")
    snapshot_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="CURRENT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RucDataConflictModel(Base):
    __tablename__ = "ruc_data_conflicts"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False)
    business_partner_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=True)
    ruc: Mapped[str] = mapped_column(String(11), nullable=False, index=True)
    conflict_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_a: Mapped[str] = mapped_column(String(50), nullable=False)
    value_a: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_b: Mapped[str] = mapped_column(String(50), nullable=False)
    value_b: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="OPEN")
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
