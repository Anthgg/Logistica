"""SQLAlchemy 2.0 ORM Persistence Models for Phase 028 — Vehicle Verifications."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

JSONB = PG_JSONB().with_variant(JSON, "sqlite")


class VehicleVerificationSourceModel(Base):
    __tablename__ = "vehicle_verification_sources"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    authority: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, server_default="OTHER")
    base_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    verification_domains: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'[]'"))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    automation_mode: Mapped[str] = mapped_column(String(50), nullable=False, server_default="MANUAL_ASSISTED")
    authorization_status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="NOT_EVALUATED")
    authorization_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default="100")
    confidence_policy: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    refresh_policy: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    terms_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    privacy_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")
    last_health_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_successful_call_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failed_call_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class VehicleVerificationProviderConfigurationModel(Base):
    __tablename__ = "vehicle_verification_provider_configurations"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_verification_sources.id", ondelete="CASCADE"), nullable=False)
    provider_code: Mapped[str] = mapped_column(String(50), nullable=False)
    environment: Mapped[str] = mapped_column(String(20), nullable=False, server_default="PRODUCTION")
    secret_manager_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    endpoint_allowlisted: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, server_default="10")
    retry_limit: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    circuit_breaker_threshold: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("source_id", "environment", name="uq_provider_config_source_env"),
    )


class VehicleVerificationModel(Base):
    __tablename__ = "vehicle_verifications"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_version_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_versions.id", ondelete="SET NULL"), nullable=True)
    plate_assignment_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_plate_assignments.id", ondelete="SET NULL"), nullable=True)
    normalized_plate: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    verification_domain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    verification_method: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_verification_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    provider_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    request_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    external_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="DRAFT", index=True)
    result_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="UNKNOWN", index=True)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False, server_default="NOT_EVALUATED")
    source_data_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    stale_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_verification_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    verified_by_user_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    approved_by_user_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    original_response_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    normalized_result_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    evidence_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="NO_EVIDENCE")
    conflict_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="NO_CONFLICT")
    supersedes_verification_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_verifications.id", ondelete="SET NULL"), nullable=True)
    superseded_by_verification_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_verifications.id", ondelete="SET NULL"), nullable=True)
    failure_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    failure_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    source: Mapped[VehicleVerificationSourceModel] = relationship("VehicleVerificationSourceModel")


class VehicleVerificationResultModel(Base):
    __tablename__ = "vehicle_verification_results"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    verification_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_verifications.id", ondelete="CASCADE"), nullable=False, unique=True)
    queried_plate: Mapped[str] = mapped_column(String(20), nullable=False)
    source_plate: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    registered_owner_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    registered_owner_identifier_masked: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    make: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    manufacturing_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vin_masked: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    chassis_masked: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    engine_number_masked: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    registration_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    transport_authorization_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    technical_inspection_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    technical_inspection_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    insurance_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    insurance_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    insurance_provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    insurance_policy_masked: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    insurance_valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    insurance_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    liens_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    restrictions_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    normalized_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'"))
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, server_default="1.0.0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VehicleVerificationFieldProvenanceModel(Base):
    __tablename__ = "vehicle_verification_field_provenance"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    verification_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_verifications.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    normalized_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_value_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_verification_sources.id", ondelete="RESTRICT"), nullable=False)
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_data_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False, server_default="NOT_EVALUATED")
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    conflict_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="NO_CONFLICT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VehicleVerificationEvidenceModel(Base):
    __tablename__ = "vehicle_verification_evidence"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    verification_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_verifications.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_reference_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    captured_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")
    retention_policy: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AssistedVehicleVerificationModel(Base):
    __tablename__ = "assisted_vehicle_verifications"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    plate_assignment_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_plate_assignments.id", ondelete="SET NULL"), nullable=True)
    verification_domain: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_verification_sources.id", ondelete="RESTRICT"), nullable=False)
    verification_reason: Mapped[str] = mapped_column(Text, nullable=False)
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reviewed_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    observed_plate: Mapped[str] = mapped_column(String(20), nullable=False)
    observed_owner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    observed_make: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    observed_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    observed_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    observed_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    observed_expiration: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_reference_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    result_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="FOUND")
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False, server_default="MEDIUM")
    approval_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="SUBMITTED", index=True)
    approved_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VehicleVerificationConflictModel(Base):
    __tablename__ = "vehicle_verification_conflicts"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    verification_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_verifications.id", ondelete="CASCADE"), nullable=False, index=True)
    conflict_type: Mapped[str] = mapped_column(String(50), nullable=False)
    master_value_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    verified_value_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    master_display_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_display_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, server_default="MEDIUM")
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="OPEN", index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resolution_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    applied_vehicle_version_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_versions.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VehicleVerificationRequirementModel(Base):
    __tablename__ = "vehicle_verification_requirements"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    body_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ownership_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    carrier_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    verification_domain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_type_preference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    blocking: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    maximum_age_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="90")
    warning_days_before_expiration: Mapped[int] = mapped_column(Integer, nullable=False, server_default="15")
    minimum_confidence: Mapped[str] = mapped_column(String(20), nullable=False, server_default="MEDIUM")
    allow_assisted_verification: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    requires_evidence: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE", index=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    approved_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VehicleVerificationReviewTaskModel(Base):
    __tablename__ = "vehicle_verification_review_tasks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    verification_domain: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, server_default="MEDIUM")
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="OPEN", index=True)
    assigned_to: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    source_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_verification_sources.id", ondelete="SET NULL"), nullable=True)
    related_verification_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_verifications.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completion_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
