"""SQLAlchemy 2.0 ORM models for Phase 037 — Gate Control.

These tables intentionally contain NO:
  - dock_id / dock assignment
  - unload_started_at / unload_completed_at
  - received_quantity / accepted_quantity / rejected_quantity
  - stock movement or inventory fields
  - lot, serial or pallet references

Server-authoritative clock is used for arrived_at.
Guard identity is derived from the authenticated session (guard_user_id),
never from a request payload field.
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.database.base import Base


# ─────────────────────────────────────────────────────────────────────────────
# WarehouseGate
# ─────────────────────────────────────────────────────────────────────────────

class WarehouseGateModel(Base):
    """Physical access point at a warehouse (Phase 037).

    NOT a dock / unloading bay. A gate is where vehicles arrive and
    the guard performs the identity / document verification.
    """

    __tablename__ = "warehouse_gates"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint("warehouse_id", "normalized_code", name="uq_warehouse_gate_code"),
        CheckConstraint("row_version >= 1", name="ck_warehouse_gate_row_version"),
        Index("ix_warehouse_gates_org", "organization_id"),
        Index("ix_warehouse_gates_warehouse", "warehouse_id"),
        Index("ix_warehouse_gates_status", "status"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    branch_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_branches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    warehouse_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code = Column(String(30), nullable=False)
    normalized_code = Column(String(30), nullable=False)
    name = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    gate_type = Column(String(40), nullable=False, default="VEHICLE_ENTRY")
    direction_policy = Column(String(40), nullable=False, default="ENTRY_ONLY")
    timezone = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT")
    active_verification_policy_version_id = Column(
        PG_UUID(as_uuid=True), nullable=True
    )
    instructions = Column(Text, nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    row_version = Column(Integer, nullable=False, server_default=text("1"))


# ─────────────────────────────────────────────────────────────────────────────
# Verification Policy
# ─────────────────────────────────────────────────────────────────────────────

class GateVerificationPolicyModel(Base):
    __tablename__ = "gate_verification_policies"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint("row_version >= 1", name="ck_gate_policy_row_version"),
        Index("ix_gate_policies_org", "organization_id"),
        Index("ix_gate_policies_status", "status"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code = Column(String(40), nullable=False)
    name = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    scope_type = Column(String(40), nullable=False, default="ORGANIZATION")
    warehouse_id = Column(PG_UUID(as_uuid=True), nullable=True)
    gate_id = Column(PG_UUID(as_uuid=True), nullable=True)
    status = Column(String(20), nullable=False, default="DRAFT")
    active_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    row_version = Column(Integer, nullable=False, server_default=text("1"))


class GateVerificationPolicyVersionModel(Base):
    __tablename__ = "gate_verification_policy_versions"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint(
            "policy_id", "version_number", name="uq_gate_policy_version_number"
        ),
        Index("ix_gate_policy_versions_policy", "policy_id"),
        Index("ix_gate_policy_versions_status", "status"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    policy_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_verification_policies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version_number = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT")
    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    late_tolerance_minutes = Column(Integer, nullable=False, default=30)
    early_tolerance_minutes = Column(Integer, nullable=False, default=60)
    walk_in_allowed = Column(Boolean, nullable=False, default=False)
    photo_requirements = Column(JSONB, nullable=False, default=dict)
    seal_requirement = Column(String(20), nullable=False, default="REQUIRED")
    document_requirements = Column(JSONB, nullable=False, default=dict)
    vehicle_mismatch_policy = Column(String(20), nullable=False, default="BLOCK")
    driver_mismatch_policy = Column(String(20), nullable=False, default="BLOCK")
    license_expired_policy = Column(String(20), nullable=False, default="BLOCK")
    verification_expired_policy = Column(String(20), nullable=False, default="BLOCK")
    missing_document_policy = Column(String(20), nullable=False, default="WARN")
    broken_seal_policy = Column(String(20), nullable=False, default="BLOCK")
    decision_matrix = Column(JSONB, nullable=False, default=dict)
    content_hash = Column(String(64), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    validated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    activated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class GateVerificationCheckDefinitionModel(Base):
    __tablename__ = "gate_verification_check_definitions"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint(
            "policy_version_id", "check_code", name="uq_gate_check_def_code"
        ),
        Index("ix_gate_check_defs_version", "policy_version_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    policy_version_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_verification_policy_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    check_code = Column(String(60), nullable=False)
    name = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(30), nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    required = Column(Boolean, nullable=False, default=True)
    blocking_on_fail = Column(Boolean, nullable=False, default=False)
    requires_photo = Column(Boolean, nullable=False, default=False)
    requires_document = Column(Boolean, nullable=False, default=False)
    requires_comment_on_fail = Column(Boolean, nullable=False, default=True)
    allow_supervisor_override = Column(Boolean, nullable=False, default=False)
    override_step_up_level = Column(String(20), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ─────────────────────────────────────────────────────────────────────────────
# GateCheckIn  (aggregate root)
# ─────────────────────────────────────────────────────────────────────────────

class GateCheckInModel(Base):
    """Central aggregate for vehicle check-in at a warehouse gate.

    IMPORTANT — fields intentionally absent:
      dock_id, unload_started_at, unload_completed_at,
      received_quantity, stock movement, lot, serial, pallet.
    """

    __tablename__ = "gate_check_ins"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint("exception_count >= 0", name="ck_gate_check_in_exceptions"),
        CheckConstraint("failed_check_count >= 0", name="ck_gate_check_in_failed"),
        CheckConstraint("warning_count >= 0", name="ck_gate_check_in_warnings"),
        CheckConstraint("row_version >= 1", name="ck_gate_check_in_row_version"),
        Index("ix_gate_check_ins_org", "organization_id"),
        Index("ix_gate_check_ins_warehouse", "warehouse_id"),
        Index("ix_gate_check_ins_gate", "gate_id"),
        Index("ix_gate_check_ins_appointment", "appointment_id"),
        Index("ix_gate_check_ins_status", "status"),
        Index("ix_gate_check_ins_decision", "decision"),
        Index("ix_gate_check_ins_arrived_at", "arrived_at"),
        Index("ix_gate_check_ins_guard", "guard_user_id"),
        Index("ix_gate_check_ins_completed_at", "check_completed_at"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    branch_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_branches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    warehouse_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    gate_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouse_gates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    appointment_id = Column(PG_UUID(as_uuid=True), nullable=True)
    arrival_notice_id = Column(PG_UUID(as_uuid=True), nullable=True)
    appointment_code_snapshot = Column(String(40), nullable=True)
    check_in_code = Column(String(40), nullable=True)
    normalized_check_in_code = Column(String(40), nullable=True)
    document_instance_id = Column(PG_UUID(as_uuid=True), nullable=True)
    status = Column(String(50), nullable=False, default="CREATED")
    source_type = Column(String(40), nullable=False, default="APPOINTMENT")
    arrival_classification = Column(String(40), nullable=False, default="TIME_NOT_CLASSIFIED")
    # Server clock — not accepted from client
    arrived_at = Column(DateTime(timezone=True), nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=True)
    gate_timezone = Column(String(64), nullable=False, default="UTC")
    check_started_at = Column(DateTime(timezone=True), nullable=True)
    verification_completed_at = Column(DateTime(timezone=True), nullable=True)
    decision_at = Column(DateTime(timezone=True), nullable=True)
    check_completed_at = Column(DateTime(timezone=True), nullable=True)
    # Guard resolved from authenticated session — never from payload
    guard_user_id = Column(PG_UUID(as_uuid=True), nullable=False)
    guard_snapshot = Column(JSONB, nullable=False, default=dict)
    supervisor_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    supplier_snapshot = Column(JSONB, nullable=True)
    carrier_snapshot = Column(JSONB, nullable=True)
    expected_transport_snapshot = Column(JSONB, nullable=True)
    observed_transport_snapshot = Column(JSONB, nullable=True)
    verification_policy_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    verification_summary = Column(JSONB, nullable=True)
    decision = Column(String(50), nullable=True)
    decision_reason = Column(Text, nullable=True)
    entry_authorized_at = Column(DateTime(timezone=True), nullable=True)
    entry_authorized_by = Column(PG_UUID(as_uuid=True), nullable=True)
    entry_denied_at = Column(DateTime(timezone=True), nullable=True)
    entry_denied_by = Column(PG_UUID(as_uuid=True), nullable=True)
    hold_reason = Column(Text, nullable=True)
    exception_count = Column(Integer, nullable=False, default=0)
    failed_check_count = Column(Integer, nullable=False, default=0)
    warning_count = Column(Integer, nullable=False, default=0)
    current_revision_number = Column(Integer, nullable=False, default=1)
    active_revision_id = Column(PG_UUID(as_uuid=True), nullable=True)
    audit_seal_hash = Column(String(64), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    row_version = Column(Integer, nullable=False, server_default=text("1"))


class GateCheckInRevisionModel(Base):
    __tablename__ = "gate_check_in_revisions"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint(
            "gate_check_in_id", "revision_number", name="uq_gate_revision_number"
        ),
        Index("ix_gate_revisions_check_in", "gate_check_in_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    gate_check_in_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_check_ins.id", ondelete="RESTRICT"),
        nullable=False,
    )
    revision_number = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="EDITABLE")
    appointment_snapshot = Column(JSONB, nullable=True)
    expected_transport_snapshot = Column(JSONB, nullable=True)
    observed_transport_snapshot = Column(JSONB, nullable=True)
    document_inspection_snapshot = Column(JSONB, nullable=True)
    seal_inspection_snapshot = Column(JSONB, nullable=True)
    photo_evidence_snapshot = Column(JSONB, nullable=True)
    checklist_snapshot = Column(JSONB, nullable=True)
    decision_snapshot = Column(JSONB, nullable=True)
    content_hash = Column(String(64), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    frozen_at = Column(DateTime(timezone=True), nullable=True)


# ─────────────────────────────────────────────────────────────────────────────
# Inspections
# ─────────────────────────────────────────────────────────────────────────────

class GateVehicleInspectionModel(Base):
    __tablename__ = "gate_vehicle_inspections"
    __allow_unmapped__ = True
    __table_args__ = (
        Index("ix_gate_vehicle_insp_check_in", "gate_check_in_id"),
        Index("ix_gate_vehicle_insp_observed_plate", "observed_plate_normalized"),
        Index("ix_gate_vehicle_insp_observed_vehicle", "observed_vehicle_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    gate_check_in_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_check_ins.id", ondelete="RESTRICT"),
        nullable=False,
    )
    expected_vehicle_id = Column(PG_UUID(as_uuid=True), nullable=True)
    expected_plate = Column(String(20), nullable=True)
    expected_plate_normalized = Column(String(20), nullable=True)
    expected_vehicle_snapshot = Column(JSONB, nullable=True)
    observed_vehicle_id = Column(PG_UUID(as_uuid=True), nullable=True)
    observed_plate = Column(String(20), nullable=True)
    observed_plate_normalized = Column(String(20), nullable=True)
    observed_vehicle_snapshot = Column(JSONB, nullable=True)
    plate_match_status = Column(String(30), nullable=False, default="MANUAL_REVIEW")
    vehicle_match_status = Column(String(30), nullable=False, default="UNCONFIRMED")
    operational_status = Column(String(30), nullable=True)
    verification_status = Column(String(30), nullable=True)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    verification_expiration = Column(DateTime(timezone=True), nullable=True)
    visual_condition = Column(String(40), nullable=True)
    inspection_result = Column(String(30), nullable=False, default="NOT_VERIFIED")
    exception_reason = Column(Text, nullable=True)
    capture_method = Column(String(40), nullable=False, default="MANUAL_ENTRY")
    inspected_by = Column(PG_UUID(as_uuid=True), nullable=False)
    inspected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class GateDriverInspectionModel(Base):
    __tablename__ = "gate_driver_inspections"
    __allow_unmapped__ = True
    __table_args__ = (
        Index("ix_gate_driver_insp_check_in", "gate_check_in_id"),
        Index("ix_gate_driver_insp_observed_driver", "observed_driver_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    gate_check_in_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_check_ins.id", ondelete="RESTRICT"),
        nullable=False,
    )
    expected_driver_id = Column(PG_UUID(as_uuid=True), nullable=True)
    expected_driver_snapshot = Column(JSONB, nullable=True)
    observed_driver_id = Column(PG_UUID(as_uuid=True), nullable=True)
    observed_name_snapshot = Column(String(160), nullable=True)
    observed_document_type = Column(String(20), nullable=True)
    # Encrypted at application layer; never stored as plaintext
    observed_document_number_encrypted = Column(Text, nullable=True)
    observed_document_number_hash = Column(String(64), nullable=True)
    observed_document_number_redacted = Column(String(20), nullable=True)
    license_number_encrypted = Column(Text, nullable=True)
    license_number_hash = Column(String(64), nullable=True)
    license_number_redacted = Column(String(20), nullable=True)
    license_category = Column(String(20), nullable=True)
    license_expiration = Column(DateTime(timezone=True), nullable=True)
    driver_match_status = Column(String(40), nullable=False, default="MANUAL_REVIEW")
    license_status = Column(String(30), nullable=False, default="NOT_VERIFIED")
    carrier_match_status = Column(String(30), nullable=False, default="NOT_VERIFIED")
    restriction_summary = Column(JSONB, nullable=True)
    inspection_result = Column(String(30), nullable=False, default="NOT_VERIFIED")
    exception_reason = Column(Text, nullable=True)
    inspected_by = Column(PG_UUID(as_uuid=True), nullable=False)
    inspected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class GatePresentedDocumentModel(Base):
    __tablename__ = "gate_presented_documents"
    __allow_unmapped__ = True
    __table_args__ = (
        Index("ix_gate_presented_docs_check_in", "gate_check_in_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    gate_check_in_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_check_ins.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_transport_document_id = Column(PG_UUID(as_uuid=True), nullable=True)
    document_kind = Column(String(40), nullable=False)
    expected_reference = Column(String(120), nullable=True)
    observed_series = Column(String(20), nullable=True)
    observed_number = Column(String(30), nullable=True)
    observed_reference_normalized = Column(String(120), nullable=True)
    presentation_status = Column(String(30), nullable=False, default="NOT_PRESENTED")
    comparison_status = Column(String(30), nullable=False, default="REQUIRES_REVIEW")
    verification_status = Column(String(30), nullable=False, default="NOT_VERIFIED")
    verification_source = Column(String(60), nullable=True)
    inspected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    inspected_by = Column(PG_UUID(as_uuid=True), nullable=False)
    file_asset_id = Column(PG_UUID(as_uuid=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class GateSealInspectionModel(Base):
    __tablename__ = "gate_seal_inspections"
    __allow_unmapped__ = True
    __table_args__ = (
        Index("ix_gate_seal_insp_check_in", "gate_check_in_id"),
        Index("ix_gate_seal_insp_observed_hash", "observed_seal_number_hash"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    gate_check_in_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_check_ins.id", ondelete="RESTRICT"),
        nullable=False,
    )
    seal_required = Column(Boolean, nullable=False, default=False)
    expected_seal_number = Column(String(80), nullable=True)
    expected_seal_number_hash = Column(String(64), nullable=True)
    observed_seal_number = Column(String(80), nullable=True)
    observed_seal_number_hash = Column(String(64), nullable=True)
    seal_match_status = Column(String(30), nullable=False, default="NOT_APPLICABLE")
    physical_status = Column(String(30), nullable=False, default="NOT_APPLICABLE")
    inspection_result = Column(String(30), nullable=False, default="PASS")
    photo_file_asset_id = Column(PG_UUID(as_uuid=True), nullable=True)
    exception_reason = Column(Text, nullable=True)
    inspected_by = Column(PG_UUID(as_uuid=True), nullable=False)
    inspected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


# ─────────────────────────────────────────────────────────────────────────────
# Photo Evidence
# ─────────────────────────────────────────────────────────────────────────────

class GatePhotoEvidenceModel(Base):
    """References to file assets captured during gate check-in.

    Photos are stored via FileAsset. No base64 data stored here.
    Signed/presigned URLs are generated on demand and NEVER persisted.
    """

    __tablename__ = "gate_photo_evidence"
    __allow_unmapped__ = True
    __table_args__ = (
        Index("ix_gate_photo_evidence_check_in", "gate_check_in_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    gate_check_in_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_check_ins.id", ondelete="RESTRICT"),
        nullable=False,
    )
    evidence_type = Column(String(40), nullable=False)
    file_asset_id = Column(PG_UUID(as_uuid=True), nullable=False)
    file_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    captured_by = Column(PG_UUID(as_uuid=True), nullable=False)
    device_reference_hash = Column(String(64), nullable=True)
    source_type = Column(String(30), nullable=False, default="FILE_UPLOAD")
    classification = Column(String(30), nullable=False, default="RESTRICTED")
    content_hash = Column(String(64), nullable=False)
    metadata_summary = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


# ─────────────────────────────────────────────────────────────────────────────
# Checklist Results & Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class GateVerificationCheckResultModel(Base):
    __tablename__ = "gate_verification_check_results"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint(
            "gate_check_in_id", "check_code", name="uq_gate_check_result_code"
        ),
        Index("ix_gate_check_results_check_in", "gate_check_in_id"),
        Index("ix_gate_check_results_result", "result"),
        Index("ix_gate_check_results_blocking", "blocking"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    gate_check_in_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_check_ins.id", ondelete="RESTRICT"),
        nullable=False,
    )
    check_definition_id = Column(PG_UUID(as_uuid=True), nullable=True)
    check_code = Column(String(60), nullable=False)
    result = Column(String(30), nullable=False, default="NOT_VERIFIED")
    observed_value = Column(Text, nullable=True)
    expected_value = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    evidence_file_ids = Column(JSONB, nullable=True)
    blocking = Column(Boolean, nullable=False, default=False)
    override_status = Column(String(20), nullable=False, default="NOT_REQUIRED")
    override_reason = Column(Text, nullable=True)
    override_requested_by = Column(PG_UUID(as_uuid=True), nullable=True)
    override_approved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    checked_by = Column(PG_UUID(as_uuid=True), nullable=False)
    checked_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class GateVerificationExceptionModel(Base):
    __tablename__ = "gate_verification_exceptions"
    __allow_unmapped__ = True
    __table_args__ = (
        Index("ix_gate_exceptions_check_in", "gate_check_in_id"),
        Index("ix_gate_exceptions_status", "status"),
        Index("ix_gate_exceptions_type", "exception_type"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    gate_check_in_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_check_ins.id", ondelete="RESTRICT"),
        nullable=False,
    )
    check_result_id = Column(PG_UUID(as_uuid=True), nullable=True)
    exception_type = Column(String(40), nullable=False)
    risk_level = Column(String(20), nullable=False, default="MEDIUM")
    reason = Column(Text, nullable=False)
    evidence_file_id = Column(PG_UUID(as_uuid=True), nullable=True)
    status = Column(String(20), nullable=False, default="REQUESTED")
    requested_by = Column(PG_UUID(as_uuid=True), nullable=False)
    reviewed_by = Column(PG_UUID(as_uuid=True), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    decision_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


# ─────────────────────────────────────────────────────────────────────────────
# Entry Decision (append-only)
# ─────────────────────────────────────────────────────────────────────────────

class GateEntryDecisionModel(Base):
    """Immutable, append-only record of each gate entry decision.

    No UPDATE or DELETE on this table. Decisions are commands, not state.
    """

    __tablename__ = "gate_entry_decisions"
    __allow_unmapped__ = True
    __table_args__ = (
        Index("ix_gate_decisions_check_in", "gate_check_in_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    gate_check_in_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_check_ins.id", ondelete="RESTRICT"),
        nullable=False,
    )
    decision_type = Column(String(40), nullable=False)
    decision_reason = Column(Text, nullable=False)
    conditions = Column(JSONB, nullable=True)
    blocking_checks = Column(JSONB, nullable=True)
    warnings = Column(JSONB, nullable=True)
    approved_exceptions = Column(JSONB, nullable=True)
    denied_exceptions = Column(JSONB, nullable=True)
    # Resolved from authenticated session — never from payload
    decided_by = Column(PG_UUID(as_uuid=True), nullable=False)
    decided_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    supervisor_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    step_up_assurance_summary = Column(JSONB, nullable=True)
    decision_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


# ─────────────────────────────────────────────────────────────────────────────
# Hold, Time Correction, Correction Requests, Package Jobs
# ─────────────────────────────────────────────────────────────────────────────

class GateCheckInHoldModel(Base):
    __tablename__ = "gate_check_in_holds"
    __allow_unmapped__ = True
    __table_args__ = (
        Index("ix_gate_holds_check_in", "gate_check_in_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    gate_check_in_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_check_ins.id", ondelete="RESTRICT"),
        nullable=False,
    )
    hold_reason = Column(Text, nullable=False)
    hold_started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    held_by = Column(PG_UUID(as_uuid=True), nullable=False)
    review_required = Column(Boolean, nullable=False, default=True)
    deadline_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class GateCheckInTimeCorrectionModel(Base):
    __tablename__ = "gate_check_in_time_corrections"
    __allow_unmapped__ = True
    __table_args__ = (
        Index("ix_gate_time_corrections_check_in", "gate_check_in_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    gate_check_in_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_check_ins.id", ondelete="RESTRICT"),
        nullable=False,
    )
    original_arrived_at = Column(DateTime(timezone=True), nullable=False)
    proposed_arrived_at = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text, nullable=False)
    evidence_file_id = Column(PG_UUID(as_uuid=True), nullable=True)
    status = Column(String(20), nullable=False, default="REQUESTED")
    requested_by = Column(PG_UUID(as_uuid=True), nullable=False)
    approved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)


class GateCheckInCorrectionRequestModel(Base):
    __tablename__ = "gate_check_in_correction_requests"
    __allow_unmapped__ = True
    __table_args__ = (
        Index("ix_gate_corrections_check_in", "gate_check_in_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    gate_check_in_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_check_ins.id", ondelete="RESTRICT"),
        nullable=False,
    )
    field_code = Column(String(60), nullable=False)
    original_value_hash = Column(String(64), nullable=True)
    proposed_value = Column(Text, nullable=True)
    reason = Column(Text, nullable=False)
    evidence_file_id = Column(PG_UUID(as_uuid=True), nullable=True)
    status = Column(String(20), nullable=False, default="REQUESTED")
    requested_by = Column(PG_UUID(as_uuid=True), nullable=False)
    reviewed_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    decided_at = Column(DateTime(timezone=True), nullable=True)


class GateCheckInPackageJobModel(Base):
    __tablename__ = "gate_check_in_package_jobs"
    __allow_unmapped__ = True
    __table_args__ = (
        Index("ix_gate_package_jobs_check_in", "gate_check_in_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    gate_check_in_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("gate_check_ins.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status = Column(String(20), nullable=False, default="PENDING")
    requested_by = Column(PG_UUID(as_uuid=True), nullable=False)
    file_asset_id = Column(PG_UUID(as_uuid=True), nullable=True)
    error_detail = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


__all__ = [
    "WarehouseGateModel",
    "GateVerificationPolicyModel",
    "GateVerificationPolicyVersionModel",
    "GateVerificationCheckDefinitionModel",
    "GateCheckInModel",
    "GateCheckInRevisionModel",
    "GateVehicleInspectionModel",
    "GateDriverInspectionModel",
    "GatePresentedDocumentModel",
    "GateSealInspectionModel",
    "GatePhotoEvidenceModel",
    "GateVerificationCheckResultModel",
    "GateVerificationExceptionModel",
    "GateEntryDecisionModel",
    "GateCheckInHoldModel",
    "GateCheckInTimeCorrectionModel",
    "GateCheckInCorrectionRequestModel",
    "GateCheckInPackageJobModel",
]
