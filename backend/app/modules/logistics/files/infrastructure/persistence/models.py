"""SQLAlchemy ORM models for Phase 030 — Files and Evidence Centralization."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.database.base import Base

JSON_TYPE = JSONB().with_variant(JSON(), "sqlite")


class FileAssetModel(Base):
    """Main logical file asset entity."""
    __tablename__ = "file_assets"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    file_code = Column(String(50), nullable=False)
    normalized_file_code = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    asset_type = Column(String(50), nullable=False, default="DOCUMENT", index=True)
    classification = Column(String(50), nullable=False, default="CONFIDENTIAL", index=True)
    lifecycle_status = Column(String(50), nullable=False, default="QUARANTINED", index=True)
    evidence_status = Column(String(50), nullable=False, default="NOT_EVIDENCE", index=True)
    owner_type = Column(String(50), nullable=False, default="ORGANIZATION")
    owner_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    owner_resource_type = Column(String(50), nullable=True)
    owner_resource_id = Column(String(100), nullable=True)
    current_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    retention_policy_id = Column(PG_UUID(as_uuid=True), nullable=True)
    access_scope = Column(String(50), nullable=False, default="RESOURCE_INHERITED")
    
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    archived_at = Column(DateTime(timezone=True), nullable=True)
    archived_by = Column(PG_UUID(as_uuid=True), nullable=True)
    archive_reason = Column(Text, nullable=True)
    deletion_requested_at = Column(DateTime(timezone=True), nullable=True)
    deletion_requested_by = Column(PG_UUID(as_uuid=True), nullable=True)
    row_version = Column(Integer, nullable=False, default=1)

    # Relationships
    versions = relationship("FileVersionModel", back_populates="file_asset", foreign_keys="FileVersionModel.file_asset_id", cascade="all, delete-orphan")
    metadata_records = relationship("FileMetadataModel", back_populates="file_asset", cascade="all, delete-orphan")
    ownerships = relationship("FileOwnershipModel", back_populates="file_asset", cascade="all, delete-orphan")
    associations = relationship("FileAssociationModel", back_populates="file_asset", cascade="all, delete-orphan")
    access_grants = relationship("FileAccessGrantModel", back_populates="file_asset", cascade="all, delete-orphan")
    integrity_records = relationship("FileIntegrityRecordModel", back_populates="file_asset", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "normalized_file_code", name="uq_file_assets_org_code"),
        Index("idx_file_assets_org_type", "organization_id", "asset_type"),
        Index("idx_file_assets_org_status", "organization_id", "lifecycle_status"),
    )


class FileVersionModel(Base):
    """Immutable binary version of a FileAsset."""
    __tablename__ = "file_versions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_asset_id = Column(PG_UUID(as_uuid=True), ForeignKey("file_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="QUARANTINED", index=True)
    storage_provider = Column(String(50), nullable=False, default="GCS")
    bucket_reference = Column(String(100), nullable=False)
    object_key = Column(String(500), nullable=False)
    object_generation = Column(String(100), nullable=True)
    original_filename = Column(String(255), nullable=False)
    sanitized_filename = Column(String(255), nullable=False)
    extension = Column(String(20), nullable=False)
    declared_MIME_type = Column(String(100), nullable=False)
    detected_MIME_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    SHA256 = Column(String(64), nullable=False, index=True)
    CRC32C = Column(String(50), nullable=True)
    MD5 = Column(String(50), nullable=True)
    
    page_count = Column(Integer, nullable=True)
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    XML_root_element = Column(String(100), nullable=True)
    schema_reference = Column(String(255), nullable=True)
    
    content_validation_status = Column(String(50), nullable=False, default="VALID")
    malware_scan_status = Column(String(50), nullable=False, default="NOT_SCANNED", index=True)
    malware_scanner_version = Column(String(100), nullable=True)
    metadata_schema_version = Column(String(20), nullable=False, default="1.0")
    source_type = Column(String(50), nullable=False, default="UPLOAD")
    source_reference = Column(String(255), nullable=True)
    
    uploaded_by = Column(PG_UUID(as_uuid=True), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    supersedes_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    file_asset = relationship("FileAssetModel", back_populates="versions", foreign_keys=[file_asset_id])

    __table_args__ = (
        UniqueConstraint("file_asset_id", "version_number", name="uq_file_versions_asset_version"),
        UniqueConstraint("storage_provider", "bucket_reference", "object_key", name="uq_file_versions_storage_location"),
    )


class FileMetadataModel(Base):
    """Typed metadata associated with a FileAsset."""
    __tablename__ = "file_metadata"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_asset_id = Column(PG_UUID(as_uuid=True), ForeignKey("file_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    file_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    document_type = Column(String(100), nullable=True)
    document_number = Column(String(100), nullable=True)
    issuer = Column(String(150), nullable=True)
    issued_at = Column(Date, nullable=True)
    valid_from = Column(Date, nullable=True)
    expires_at = Column(Date, nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=True)
    event_at = Column(DateTime(timezone=True), nullable=True)
    source = Column(String(100), nullable=True)
    language = Column(String(10), nullable=False, default="es")
    tags = Column(JSON_TYPE, nullable=False, server_default=text("'[]'"))
    attributes = Column(JSON_TYPE, nullable=False, server_default=text("'{}'"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    file_asset = relationship("FileAssetModel", back_populates="metadata_records")


class FileOwnershipModel(Base):
    """Ownership history and custodian tracking."""
    __tablename__ = "file_ownerships"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_asset_id = Column(PG_UUID(as_uuid=True), ForeignKey("file_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    owner_type = Column(String(50), nullable=False, default="ORGANIZATION")
    owner_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    owner_role_reference = Column(String(100), nullable=True)
    custodian_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    owner_resource_type = Column(String(50), nullable=True)
    owner_resource_id = Column(String(100), nullable=True)
    effective_from = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    effective_to = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="ACTIVE")
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    file_asset = relationship("FileAssetModel", back_populates="ownerships")


class FileAssociationModel(Base):
    """Linkage between FileAsset and domain resources."""
    __tablename__ = "file_associations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    file_asset_id = Column(PG_UUID(as_uuid=True), ForeignKey("file_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    file_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(100), nullable=False, index=True)
    association_type = Column(String(50), nullable=False, default="ATTACHMENT")
    is_primary = Column(Boolean, nullable=False, default=False)
    status = Column(String(50), nullable=False, default="ACTIVE")
    valid_from = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    valid_until = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    removed_by = Column(PG_UUID(as_uuid=True), nullable=True)
    removed_at = Column(DateTime(timezone=True), nullable=True)
    removal_reason = Column(Text, nullable=True)

    file_asset = relationship("FileAssetModel", back_populates="associations")

    __table_args__ = (
        Index("idx_file_assoc_resource", "organization_id", "resource_type", "resource_id"),
    )


class FileAccessGrantModel(Base):
    """Explicit temporary permissions grants for FileAssets."""
    __tablename__ = "file_access_grants"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_asset_id = Column(PG_UUID(as_uuid=True), ForeignKey("file_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    principal_type = Column(String(50), nullable=False)
    principal_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    allowed_actions = Column(JSONB, nullable=False, server_default=text("'[]'"))
    valid_from = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    valid_until = Column(DateTime(timezone=True), nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="ACTIVE")
    granted_by = Column(PG_UUID(as_uuid=True), nullable=False)
    revoked_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    file_asset = relationship("FileAssetModel", back_populates="access_grants")


class FileUploadSessionModel(Base):
    """Upload session control and progress tracking."""
    __tablename__ = "file_upload_sessions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    file_asset_id = Column(PG_UUID(as_uuid=True), nullable=True)
    intended_resource_type = Column(String(50), nullable=True)
    intended_resource_id = Column(String(100), nullable=True)
    intended_association_type = Column(String(50), nullable=True)
    expected_filename = Column(String(255), nullable=False)
    expected_size_bytes = Column(Integer, nullable=False)
    declared_MIME_type = Column(String(100), nullable=False)
    expected_SHA256 = Column(String(64), nullable=True)
    upload_mode = Column(String(50), nullable=False, default="DIRECT_SIGNED")
    status = Column(String(50), nullable=False, default="CREATED", index=True)
    quarantine_object_key = Column(String(500), nullable=False)
    storage_upload_reference = Column(String(500), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    initiated_by = Column(PG_UUID(as_uuid=True), nullable=False)
    finalized_by = Column(PG_UUID(as_uuid=True), nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    failure_code = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class FileIntegrityRecordModel(Base):
    """SHA-256 integrity verification log."""
    __tablename__ = "file_integrity_records"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_asset_id = Column(PG_UUID(as_uuid=True), ForeignKey("file_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    file_version_id = Column(PG_UUID(as_uuid=True), nullable=False)
    SHA256 = Column(String(64), nullable=False)
    storage_checksum = Column(String(64), nullable=True)
    calculated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    calculator_version = Column(String(50), nullable=False, default="1.0")
    verification_status = Column(String(50), nullable=False, default="VERIFIED")
    last_verified_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_verification_result = Column(Text, nullable=True)
    mismatch_detected_at = Column(DateTime(timezone=True), nullable=True)

    file_asset = relationship("FileAssetModel", back_populates="integrity_records")


class SignatureArtifactMetadataModel(Base):
    """Signature metadata distinguishing visual signature images from cryptographic digital signatures."""
    __tablename__ = "signature_artifact_metadata"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_asset_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    signature_kind = Column(String(50), nullable=False, default="VISUAL_SIGNATURE_IMAGE")
    signer_reference = Column(String(255), nullable=True)
    signed_file_asset_id = Column(PG_UUID(as_uuid=True), nullable=True)
    certificate_subject_masked = Column(String(255), nullable=True)
    certificate_issuer = Column(String(255), nullable=True)
    certificate_serial_hash = Column(String(64), nullable=True)
    signature_format = Column(String(50), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    verification_status = Column(String(50), nullable=False, default="FORMAT_VALID")
    verification_source = Column(String(100), nullable=False, default="INTERNAL_INSPECTOR")
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class EvidenceRecordModel(Base):
    """Formal immutable evidence record."""
    __tablename__ = "evidence_records"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    evidence_code = Column(String(50), nullable=False)
    evidence_type = Column(String(50), nullable=False, index=True)
    subject_type = Column(String(50), nullable=False)
    subject_id = Column(String(100), nullable=False)
    file_asset_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    file_version_id = Column(PG_UUID(as_uuid=True), nullable=False)
    captured_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    captured_by_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    captured_by_system = Column(String(100), nullable=True)
    acquisition_method = Column(String(100), nullable=False, default="SYSTEM_CAPTURE")
    source = Column(String(100), nullable=False, default="LOGISTICS_PLATFORM")
    source_reference = Column(String(255), nullable=True)
    location_reference = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="CANDIDATE")
    acceptance_status = Column(String(50), nullable=False, default="PENDING", index=True)
    accepted_by = Column(PG_UUID(as_uuid=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(PG_UUID(as_uuid=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    chain_of_custody_status = Column(String(50), nullable=False, default="VALID")
    retention_policy_id = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("organization_id", "evidence_code", name="uq_evidence_records_org_code"),
    )


class EvidenceCustodyEventModel(Base):
    """Append-only audit trail for Evidence chain of custody."""
    __tablename__ = "evidence_custody_events"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    evidence_id = Column(PG_UUID(as_uuid=True), ForeignKey("evidence_records.id", ondelete="CASCADE"), nullable=False, index=True)
    file_version_id = Column(PG_UUID(as_uuid=True), nullable=False)
    event_type = Column(String(50), nullable=False, index=True)
    actor_type = Column(String(50), nullable=False, default="USER")
    actor_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    actor_service = Column(String(100), nullable=True)
    source_IP_hash = Column(String(64), nullable=True)
    session_id = Column(String(100), nullable=True)
    device_reference = Column(String(255), nullable=True)
    event_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    reason = Column(Text, nullable=True)
    previous_hash = Column(String(64), nullable=True)
    event_hash = Column(String(64), nullable=False)
    correlation_id = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class FileRetentionPolicyModel(Base):
    """Retention rule configurations."""
    __tablename__ = "file_retention_policies"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), nullable=True, index=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(150), nullable=False)
    asset_type = Column(String(50), nullable=True)
    classification = Column(String(50), nullable=True)
    resource_type = Column(String(50), nullable=True)
    minimum_retention_days = Column(Integer, nullable=False, default=365)
    archive_after_days = Column(Integer, nullable=True)
    delete_after_days = Column(Integer, nullable=True)
    deletion_mode = Column(String(50), nullable=False, default="REVIEW_REQUIRED")
    status = Column(String(50), nullable=False, default="ACTIVE")
    effective_from = Column(Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    effective_to = Column(Date, nullable=True)
    legal_basis_reference = Column(String(255), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    approved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class FileLegalHoldModel(Base):
    """Legal hold overrides blocking deletion of files."""
    __tablename__ = "file_legal_holds"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_asset_id = Column(PG_UUID(as_uuid=True), ForeignKey("file_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    file_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    reason = Column(Text, nullable=False)
    authority_reference = Column(String(255), nullable=True)
    applied_by = Column(PG_UUID(as_uuid=True), nullable=False)
    applied_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="ACTIVE", index=True)
    released_by = Column(PG_UUID(as_uuid=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    release_reason = Column(Text, nullable=True)


class FileDeletionRequestModel(Base):
    """Multi-step approval request for file purge."""
    __tablename__ = "file_deletion_requests"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_asset_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    requested_by = Column(PG_UUID(as_uuid=True), nullable=False)
    reason = Column(Text, nullable=False)
    deletion_basis = Column(String(100), nullable=False, default="USER_REQUEST")
    requested_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    status = Column(String(50), nullable=False, default="REQUESTED", index=True)
    reviewed_by = Column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    decision_reason = Column(Text, nullable=True)
    scheduled_purge_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class FileProcessingJobModel(Base):
    """Background worker job for async scanning, validation and promotion."""
    __tablename__ = "file_processing_jobs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    job_type = Column(String(50), nullable=False, index=True)
    file_asset_id = Column(PG_UUID(as_uuid=True), nullable=True)
    file_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    upload_session_id = Column(PG_UUID(as_uuid=True), nullable=True)
    status = Column(String(50), nullable=False, default="QUEUED", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    error_message = Column(Text, nullable=True)
    correlation_id = Column(String(100), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
