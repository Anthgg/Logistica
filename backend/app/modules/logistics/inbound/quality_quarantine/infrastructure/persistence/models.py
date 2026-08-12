"""Phase 042 — Quality Quarantine ORM models (22 tables)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


def _uuid() -> object:
    return uuid4()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# 1. InboundInventoryDispositionAllocation
# ---------------------------------------------------------------------------

class InboundInventoryDispositionAllocationModel(Base):
    __tablename__ = "inbound_inventory_disposition_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    inbound_receipt_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    inbound_receipt_revision_id = Column(UUID(as_uuid=True), nullable=False)
    inbound_received_line_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    expected_line_id = Column(UUID(as_uuid=True), nullable=True)
    purchase_order_id = Column(UUID(as_uuid=True), nullable=True)
    purchase_order_line_id = Column(UUID(as_uuid=True), nullable=True)
    supplier_business_partner_id = Column(UUID(as_uuid=True), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_version_id = Column(UUID(as_uuid=True), nullable=True)
    sku_snapshot = Column(String(120), nullable=True)
    product_name_snapshot = Column(String(500), nullable=True)
    quantity = Column(Numeric(38, 18), nullable=False)
    unit_id = Column(UUID(as_uuid=True), nullable=False)
    base_quantity = Column(Numeric(38, 18), nullable=False)
    source_quantity = Column(Numeric(38, 18), nullable=True)
    source_unit_id = Column(UUID(as_uuid=True), nullable=True)
    source_base_quantity = Column(Numeric(38, 18), nullable=True)
    allocation_status = Column(String(50), nullable=False, default="PENDING_QUALITY_ASSESSMENT")
    availability_class = Column(String(50), nullable=False, default="UNKNOWN")
    quality_status = Column(String(50), nullable=False, default="NOT_ASSESSED")
    parent_allocation_id = Column(UUID(as_uuid=True), nullable=True)
    root_allocation_id = Column(UUID(as_uuid=True), nullable=False)
    split_sequence = Column(Integer, nullable=False, default=0)
    lot_observation_ids = Column(JSONB, nullable=False, default=list)
    serial_observation_ids = Column(JSONB, nullable=False, default=list)
    expiration_observation_ids = Column(JSONB, nullable=False, default=list)
    difference_case_ids = Column(JSONB, nullable=False, default=list)
    quarantine_case_id = Column(UUID(as_uuid=True), nullable=True)
    quality_inspection_id = Column(UUID(as_uuid=True), nullable=True)
    quality_decision_id = Column(UUID(as_uuid=True), nullable=True)
    physical_quarantine_location_id = Column(UUID(as_uuid=True), nullable=True)
    released_for_putaway_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    row_version = Column(Integer, nullable=False, server_default="1")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_disposition_alloc_qty_positive"),
        CheckConstraint("base_quantity > 0", name="ck_disposition_alloc_base_qty_positive"),
        CheckConstraint("row_version >= 1", name="ck_disposition_alloc_row_version"),
        Index("ix_disp_alloc_receipt_line", "inbound_receipt_id", "inbound_received_line_id"),
    )


# ---------------------------------------------------------------------------
# 2. InventoryDispositionSplit
# ---------------------------------------------------------------------------

class InventoryDispositionSplitModel(Base):
    __tablename__ = "inventory_disposition_splits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    source_allocation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    split_reason = Column(String(60), nullable=False)
    original_quantity = Column(Numeric(38, 18), nullable=False)
    original_base_quantity = Column(Numeric(38, 18), nullable=False)
    first_child_allocation_id = Column(UUID(as_uuid=True), nullable=False)
    second_child_allocation_id = Column(UUID(as_uuid=True), nullable=False)
    requested_by = Column(UUID(as_uuid=True), nullable=False)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    content_hash = Column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_split_source", "source_allocation_id"),
    )


# ---------------------------------------------------------------------------
# 3. QualityQuarantineCase
# ---------------------------------------------------------------------------

class QualityQuarantineCaseModel(Base):
    __tablename__ = "quality_quarantine_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    quarantine_code = Column(String(80), nullable=False)
    normalized_quarantine_code = Column(String(80), nullable=False)
    source_type = Column(String(40), nullable=False)
    source_reference_id = Column(UUID(as_uuid=True), nullable=True)
    inbound_receipt_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    difference_case_id = Column(UUID(as_uuid=True), nullable=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_version_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(50), nullable=False, default="DRAFT")
    severity = Column(String(20), nullable=False, default="LOW")
    quarantine_reason = Column(String(300), nullable=True)
    reason_description = Column(Text, nullable=True)
    active_inspection_id = Column(UUID(as_uuid=True), nullable=True)
    quality_result = Column(String(50), nullable=True)
    quality_decision_status = Column(String(50), nullable=False, default="NONE")
    release_status = Column(String(50), nullable=False, default="NONE")
    physical_segregation_status = Column(String(50), nullable=False, default="NOT_REQUIRED")
    quarantine_location_id = Column(UUID(as_uuid=True), nullable=True)
    responsible_quality_user_id = Column(UUID(as_uuid=True), nullable=True)
    assigned_reviewer_user_id = Column(UUID(as_uuid=True), nullable=True)
    active_revision_id = Column(UUID(as_uuid=True), nullable=True)
    current_revision_number = Column(Integer, nullable=False, default=0)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    opened_by = Column(UUID(as_uuid=True), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    decided_by = Column(UUID(as_uuid=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    released_by = Column(UUID(as_uuid=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(UUID(as_uuid=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    content_hash = Column(String(64), nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    row_version = Column(Integer, nullable=False, server_default="1")

    __table_args__ = (
        UniqueConstraint("organization_id", "normalized_quarantine_code", name="uq_quarantine_code"),
        CheckConstraint("row_version >= 1", name="ck_quarantine_row_version"),
        Index("ix_quarantine_status", "status"),
        Index("ix_quarantine_severity", "severity"),
        Index("ix_quarantine_opened", "opened_at"),
    )


# ---------------------------------------------------------------------------
# 4. QualityQuarantineCaseRevision
# ---------------------------------------------------------------------------

class QualityQuarantineCaseRevisionModel(Base):
    __tablename__ = "quality_quarantine_case_revisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    quarantine_case_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    revision_number = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False, default="EDITABLE")
    source_snapshot = Column(JSONB, nullable=False, default=dict)
    inspection_snapshot = Column(JSONB, nullable=True)
    decision_snapshot = Column(JSONB, nullable=True)
    release_snapshot = Column(JSONB, nullable=True)
    content_hash = Column(String(64), nullable=True)
    created_from_revision_id = Column(UUID(as_uuid=True), nullable=True)
    change_reason = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    frozen_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("quarantine_case_id", "revision_number", name="uq_quarantine_revision"),
    )


# ---------------------------------------------------------------------------
# 5. QuarantineZoneConfiguration
# ---------------------------------------------------------------------------

class QuarantineZoneConfigurationModel(Base):
    __tablename__ = "quarantine_zone_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    warehouse_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    warehouse_location_id = Column(UUID(as_uuid=True), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    status = Column(String(30), nullable=False, default="ACTIVE")
    allowed_product_categories = Column(JSONB, nullable=False, default=list)
    temperature_capabilities = Column(JSONB, nullable=False, default=dict)
    hazardous_declared_capable = Column(Boolean, nullable=False, default=False)
    maximum_capacity_reference = Column(Numeric(38, 18), nullable=True)
    capacity_unit_id = Column(UUID(as_uuid=True), nullable=True)
    priority = Column(Integer, nullable=False, default=0)
    instructions = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    row_version = Column(Integer, nullable=False, server_default="1")

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_quarantine_zone_code"),
        CheckConstraint("row_version >= 1", name="ck_quarantine_zone_row_version"),
    )


# ---------------------------------------------------------------------------
# 6. QuarantinePlacementConfirmation
# ---------------------------------------------------------------------------

class QuarantinePlacementConfirmationModel(Base):
    __tablename__ = "quarantine_placement_confirmations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    quarantine_case_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    allocation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    quarantine_zone_id = Column(UUID(as_uuid=True), nullable=False)
    warehouse_location_id = Column(UUID(as_uuid=True), nullable=False)
    placement_status = Column(String(40), nullable=False, default="PENDING")
    scanned_location_code = Column(String(50), nullable=True)
    quantity = Column(Numeric(38, 18), nullable=False)
    unit_id = Column(UUID(as_uuid=True), nullable=False)
    base_quantity = Column(Numeric(38, 18), nullable=False)
    confirmed_by = Column(UUID(as_uuid=True), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    evidence_file_id = Column(UUID(as_uuid=True), nullable=True)
    observation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        Index("ix_placement_case", "quarantine_case_id"),
        Index("ix_placement_allocation", "allocation_id"),
    )


# ---------------------------------------------------------------------------
# 7. QualityInspection
# ---------------------------------------------------------------------------

class QualityInspectionModel(Base):
    __tablename__ = "quality_inspections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), nullable=False)
    inspection_code = Column(String(80), nullable=False)
    quarantine_case_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    allocation_id = Column(UUID(as_uuid=True), nullable=False)
    inbound_receipt_id = Column(UUID(as_uuid=True), nullable=False)
    difference_case_id = Column(UUID(as_uuid=True), nullable=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_version_id = Column(UUID(as_uuid=True), nullable=True)
    plan_id = Column(UUID(as_uuid=True), nullable=True)
    plan_version_id = Column(UUID(as_uuid=True), nullable=True)
    plan_resolution_hash = Column(String(64), nullable=True)
    inspection_snapshot_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String(30), nullable=False, default="CREATED")
    overall_result = Column(String(50), nullable=False, default="NOT_CALCULATED")
    sample_size = Column(Integer, nullable=True)
    sample_unit = Column(String(30), nullable=True)
    required_control_count = Column(Integer, nullable=False, default=0)
    completed_control_count = Column(Integer, nullable=False, default=0)
    failed_control_count = Column(Integer, nullable=False, default=0)
    warning_control_count = Column(Integer, nullable=False, default=0)
    evidence_count = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    started_by = Column(UUID(as_uuid=True), nullable=True)
    paused_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    content_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    row_version = Column(Integer, nullable=False, server_default="1")

    __table_args__ = (
        UniqueConstraint("organization_id", "inspection_code", name="uq_inspection_code"),
        CheckConstraint("row_version >= 1", name="ck_inspection_row_version"),
        Index("ix_inspection_product", "product_id"),
        Index("ix_inspection_status", "status"),
        Index("ix_inspection_result", "overall_result"),
    )


# ---------------------------------------------------------------------------
# 8. QualityInspectionSnapshot
# ---------------------------------------------------------------------------

class QualityInspectionSnapshotModel(Base):
    __tablename__ = "quality_inspection_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    inspection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    plan_snapshot = Column(JSONB, nullable=True)
    plan_version_snapshot = Column(JSONB, nullable=True)
    resolution_snapshot = Column(JSONB, nullable=True)
    product_snapshot = Column(JSONB, nullable=True)
    receipt_snapshot = Column(JSONB, nullable=True)
    difference_snapshot = Column(JSONB, nullable=True)
    allocation_snapshot = Column(JSONB, nullable=True)
    quantity_snapshot = Column(JSONB, nullable=True)
    lot_observations_snapshot = Column(JSONB, nullable=True)
    serial_observations_snapshot = Column(JSONB, nullable=True)
    expiration_snapshot = Column(JSONB, nullable=True)
    controls_snapshot = Column(JSONB, nullable=True)
    tolerances_snapshot = Column(JSONB, nullable=True)
    sampling_snapshot = Column(JSONB, nullable=True)
    certificates_snapshot = Column(JSONB, nullable=True)
    evidence_requirements_snapshot = Column(JSONB, nullable=True)
    instructions_snapshot = Column(JSONB, nullable=True)
    responsibilities_snapshot = Column(JSONB, nullable=True)
    applicability_snapshot = Column(JSONB, nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=False)
    content_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


# ---------------------------------------------------------------------------
# 9. QualityInspectionControl
# ---------------------------------------------------------------------------

class QualityInspectionControlModel(Base):
    __tablename__ = "quality_inspection_controls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    inspection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    source_control_definition_id = Column(UUID(as_uuid=True), nullable=True)
    control_code = Column(String(80), nullable=False)
    name_snapshot = Column(String(300), nullable=False)
    description_snapshot = Column(Text, nullable=True)
    control_type = Column(String(60), nullable=False, index=True)
    order_index = Column(Integer, nullable=False, default=0)
    required = Column(Boolean, nullable=False, default=True)
    blocking_on_fail = Column(Boolean, nullable=False, default=False)
    result_value_type = Column(String(30), nullable=True)
    unit_id = Column(UUID(as_uuid=True), nullable=True)
    tolerance_snapshot = Column(JSONB, nullable=True)
    evidence_requirements_snapshot = Column(JSONB, nullable=True)
    instructions_snapshot = Column(JSONB, nullable=True)
    applicability_result = Column(String(30), nullable=True)
    status = Column(String(30), nullable=False, default="NOT_STARTED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    row_version = Column(Integer, nullable=False, server_default="1")

    __table_args__ = (
        CheckConstraint("order_index >= 0", name="ck_control_order_index"),
        Index("ix_control_inspection", "inspection_id"),
        Index("ix_control_status", "status"),
    )


# ---------------------------------------------------------------------------
# 10. QualityInspectionControlResult
# ---------------------------------------------------------------------------

class QualityInspectionControlResultModel(Base):
    __tablename__ = "quality_inspection_control_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    inspection_control_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    result_status = Column(String(40), nullable=False)
    boolean_value = Column(Boolean, nullable=True)
    decimal_value = Column(Numeric(38, 18), nullable=True)
    integer_value = Column(Integer, nullable=True)
    text_value = Column(Text, nullable=True)
    date_value = Column(DateTime(timezone=True), nullable=True)
    option_value = Column(String(200), nullable=True)
    unit_id = Column(UUID(as_uuid=True), nullable=True)
    tolerance_evaluation = Column(JSONB, nullable=True)
    observation = Column(Text, nullable=True)
    evidence_complete = Column(Boolean, nullable=False, default=False)
    measured_by = Column(UUID(as_uuid=True), nullable=False)
    measured_at = Column(DateTime(timezone=True), nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    source = Column(String(40), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    superseded_by_result_id = Column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index("ix_control_result_control", "inspection_control_id"),
    )


# ---------------------------------------------------------------------------
# 11. QualityMeasurement
# ---------------------------------------------------------------------------

class QualityMeasurementModel(Base):
    __tablename__ = "quality_measurements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    inspection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    inspection_control_id = Column(UUID(as_uuid=True), nullable=False)
    measurement_type = Column(String(40), nullable=False)
    measured_value = Column(Numeric(38, 18), nullable=False)
    unit_id = Column(UUID(as_uuid=True), nullable=False)
    normalized_value = Column(Numeric(38, 18), nullable=True)
    normalized_unit_id = Column(UUID(as_uuid=True), nullable=True)
    conversion_rule_id = Column(UUID(as_uuid=True), nullable=True)
    tolerance_result = Column(String(40), nullable=True)
    device_reference = Column(String(200), nullable=True)
    calibration_reference = Column(String(200), nullable=True)
    sample_reference_id = Column(UUID(as_uuid=True), nullable=True)
    measured_by = Column(UUID(as_uuid=True), nullable=False)
    measured_at = Column(DateTime(timezone=True), nullable=False)
    evidence_file_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(30), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        Index("ix_measurement_inspection", "inspection_id"),
        Index("ix_measurement_type", "measurement_type"),
    )


# ---------------------------------------------------------------------------
# 12. QualityInspectionSampleSet
# ---------------------------------------------------------------------------

class QualityInspectionSampleSetModel(Base):
    __tablename__ = "quality_inspection_sample_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    inspection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    source_sampling_plan_id = Column(UUID(as_uuid=True), nullable=True)
    sampling_snapshot = Column(JSONB, nullable=True)
    population_quantity = Column(Numeric(38, 18), nullable=False)
    population_unit_id = Column(UUID(as_uuid=True), nullable=False)
    required_sample_size = Column(Integer, nullable=False)
    sample_unit = Column(String(30), nullable=True)
    selection_method = Column(String(40), nullable=True)
    status = Column(String(30), nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


# ---------------------------------------------------------------------------
# 13. QualityInspectionSampleReference
# ---------------------------------------------------------------------------

class QualityInspectionSampleReferenceModel(Base):
    __tablename__ = "quality_inspection_sample_references"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    sample_set_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    sample_number = Column(Integer, nullable=False)
    source_reference_type = Column(String(40), nullable=False)
    inbound_received_line_id = Column(UUID(as_uuid=True), nullable=True)
    lot_observation_id = Column(UUID(as_uuid=True), nullable=True)
    serial_observation_id = Column(UUID(as_uuid=True), nullable=True)
    package_ordinal = Column(Integer, nullable=True)
    operator_reference = Column(String(200), nullable=True)
    status = Column(String(30), nullable=False, default="PENDING")
    selected_by = Column(UUID(as_uuid=True), nullable=True)
    selected_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


# ---------------------------------------------------------------------------
# 14. QualityCertificateReview
# ---------------------------------------------------------------------------

class QualityCertificateReviewModel(Base):
    __tablename__ = "quality_certificate_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    inspection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    certificate_requirement_id = Column(UUID(as_uuid=True), nullable=True)
    requirement_code = Column(String(80), nullable=False)
    document_file_id = Column(UUID(as_uuid=True), nullable=True)
    document_type_id = Column(UUID(as_uuid=True), nullable=True)
    review_status = Column(String(40), nullable=False)
    issuer_observed = Column(String(300), nullable=True)
    issue_date_observed = Column(DateTime(timezone=True), nullable=True)
    expiration_date_observed = Column(DateTime(timezone=True), nullable=True)
    reference_number_observed = Column(String(200), nullable=True)
    metadata_match_status = Column(String(40), nullable=True)
    file_status = Column(String(40), nullable=True)
    observation = Column(Text, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


# ---------------------------------------------------------------------------
# 15. QualityInspectionEvidenceLink
# ---------------------------------------------------------------------------

class QualityInspectionEvidenceLinkModel(Base):
    __tablename__ = "quality_inspection_evidence_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    inspection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    inspection_control_id = Column(UUID(as_uuid=True), nullable=True)
    result_id = Column(UUID(as_uuid=True), nullable=True)
    file_asset_id = Column(UUID(as_uuid=True), nullable=False)
    file_version_id = Column(UUID(as_uuid=True), nullable=True)
    evidence_type = Column(String(40), nullable=False)
    description = Column(Text, nullable=True)
    classification = Column(String(40), nullable=False, default="STANDARD")
    linked_by = Column(UUID(as_uuid=True), nullable=False)
    linked_at = Column(DateTime(timezone=True), nullable=False)
    content_hash = Column(String(64), nullable=True)
    status = Column(String(30), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


# ---------------------------------------------------------------------------
# 16. QualityDispositionDecision
# ---------------------------------------------------------------------------

class QualityDispositionDecisionModel(Base):
    __tablename__ = "quality_disposition_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    quarantine_case_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    inspection_id = Column(UUID(as_uuid=True), nullable=True)
    allocation_id = Column(UUID(as_uuid=True), nullable=False)
    decision_type = Column(String(60), nullable=False)
    decision_status = Column(String(40), nullable=False, default="PROPOSED")
    quantity = Column(Numeric(38, 18), nullable=False)
    unit_id = Column(UUID(as_uuid=True), nullable=False)
    base_quantity = Column(Numeric(38, 18), nullable=False)
    reason_code = Column(String(60), nullable=True)
    reason = Column(Text, nullable=True)
    inspection_result_snapshot = Column(JSONB, nullable=True)
    evidence_manifest_hash = Column(String(64), nullable=True)
    policy_version = Column(String(60), nullable=True)
    proposed_by = Column(UUID(as_uuid=True), nullable=False)
    proposed_at = Column(DateTime(timezone=True), nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    supersedes_decision_id = Column(UUID(as_uuid=True), nullable=True)
    content_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


# ---------------------------------------------------------------------------
# 17. QualityDecisionApproval
# ---------------------------------------------------------------------------

class QualityDecisionApprovalModel(Base):
    __tablename__ = "quality_decision_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    decision_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    approval_level = Column(Integer, nullable=False, default=1)
    decision = Column(String(40), nullable=False)
    approver_user_id = Column(UUID(as_uuid=True), nullable=False)
    approver_snapshot = Column(JSONB, nullable=True)
    reason = Column(Text, nullable=True)
    policy_version = Column(String(60), nullable=True)
    step_up_assurance_summary = Column(JSONB, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


# ---------------------------------------------------------------------------
# 18. QuarantineReleaseAuthorization
# ---------------------------------------------------------------------------

class QuarantineReleaseAuthorizationModel(Base):
    __tablename__ = "quarantine_release_authorizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    quarantine_case_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    allocation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    quality_decision_id = Column(UUID(as_uuid=True), nullable=False)
    release_type = Column(String(20), nullable=False)
    quantity = Column(Numeric(38, 18), nullable=False)
    unit_id = Column(UUID(as_uuid=True), nullable=False)
    base_quantity = Column(Numeric(38, 18), nullable=False)
    status = Column(String(40), nullable=False, default="REQUESTED")
    release_reason = Column(Text, nullable=True)
    requested_by = Column(UUID(as_uuid=True), nullable=False)
    requested_at = Column(DateTime(timezone=True), nullable=False)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    executed_by = Column(UUID(as_uuid=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    step_up_assurance_summary = Column(JSONB, nullable=True)
    content_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        Index("ix_release_case", "quarantine_case_id"),
        Index("ix_release_allocation", "allocation_id"),
        Index("ix_release_status", "status"),
    )


# ---------------------------------------------------------------------------
# 19. QuarantineRejectionAuthorization
# ---------------------------------------------------------------------------

class QuarantineRejectionAuthorizationModel(Base):
    __tablename__ = "quarantine_rejection_authorizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    quarantine_case_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    allocation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    quality_decision_id = Column(UUID(as_uuid=True), nullable=False)
    rejection_type = Column(String(20), nullable=False)
    quantity = Column(Numeric(38, 18), nullable=False)
    unit_id = Column(UUID(as_uuid=True), nullable=False)
    base_quantity = Column(Numeric(38, 18), nullable=False)
    reason_code = Column(String(60), nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(40), nullable=False, default="REQUESTED")
    future_disposition_recommendation = Column(String(60), nullable=True)
    evidence_manifest_hash = Column(String(64), nullable=True)
    requested_by = Column(UUID(as_uuid=True), nullable=False)
    requested_at = Column(DateTime(timezone=True), nullable=False)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    executed_by = Column(UUID(as_uuid=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    content_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        Index("ix_rejection_case", "quarantine_case_id"),
        Index("ix_rejection_allocation", "allocation_id"),
        Index("ix_rejection_status", "status"),
    )


# ---------------------------------------------------------------------------
# 20. QualityReinspectionRequest
# ---------------------------------------------------------------------------

class QualityReinspectionRequestModel(Base):
    __tablename__ = "quality_reinspection_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    quarantine_case_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    previous_inspection_id = Column(UUID(as_uuid=True), nullable=False)
    reason = Column(Text, nullable=False)
    required_controls = Column(JSONB, nullable=True)
    additional_evidence_required = Column(Boolean, nullable=False, default=False)
    requested_by = Column(UUID(as_uuid=True), nullable=False)
    requested_at = Column(DateTime(timezone=True), nullable=False)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    new_inspection_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(30), nullable=False, default="REQUESTED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


# ---------------------------------------------------------------------------
# 21. QualityDispositionEvent
# ---------------------------------------------------------------------------

class QualityDispositionEventModel(Base):
    __tablename__ = "quality_disposition_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), nullable=False)
    quarantine_case_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    allocation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    inspection_id = Column(UUID(as_uuid=True), nullable=True)
    decision_id = Column(UUID(as_uuid=True), nullable=True)
    sequence_number = Column(Integer, nullable=False)
    event_type = Column(String(60), nullable=False)
    event_at = Column(DateTime(timezone=True), nullable=False)
    actor_user_id = Column(UUID(as_uuid=True), nullable=False)
    actor_snapshot = Column(JSONB, nullable=True)
    quantity = Column(Numeric(38, 18), nullable=True)
    unit_id = Column(UUID(as_uuid=True), nullable=True)
    base_quantity = Column(Numeric(38, 18), nullable=True)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    reason = Column(Text, nullable=True)
    correlation_id = Column(UUID(as_uuid=True), nullable=True)
    previous_event_hash = Column(String(64), nullable=True)
    event_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("quarantine_case_id", "sequence_number", name="uq_disposition_event_seq"),
        Index("ix_disposition_event_case", "quarantine_case_id"),
        Index("ix_disposition_event_allocation", "allocation_id"),
        Index("ix_disposition_event_type", "event_type"),
    )


# ---------------------------------------------------------------------------
# 22. InboundQualityAvailabilityProjection
# ---------------------------------------------------------------------------

class InboundQualityAvailabilityProjectionModel(Base):
    __tablename__ = "inbound_quality_availability_projection"

    organization_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    warehouse_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    inbound_receipt_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    product_version_id = Column(UUID(as_uuid=True), nullable=True)
    allocation_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    quantity = Column(Numeric(38, 18), nullable=False)
    unit_id = Column(UUID(as_uuid=True), nullable=False)
    base_quantity = Column(Numeric(38, 18), nullable=False)
    availability_class = Column(String(50), nullable=False)
    quality_status = Column(String(50), nullable=False)
    quarantine_case_id = Column(UUID(as_uuid=True), nullable=True)
    inspection_id = Column(UUID(as_uuid=True), nullable=True)
    decision_id = Column(UUID(as_uuid=True), nullable=True)
    physical_location_id = Column(UUID(as_uuid=True), nullable=True)
    released_for_putaway_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    data_quality_status = Column(String(30), nullable=False, default="PARTIAL")
    calculated_at = Column(DateTime(timezone=True), nullable=False)
    projection_version = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        Index("ix_projection_warehouse", "warehouse_id"),
        Index("ix_projection_product", "product_id"),
        Index("ix_projection_availability", "availability_class"),
    )


# ---------------------------------------------------------------------------
# Table tuple for Alembic
# ---------------------------------------------------------------------------

PHASE_042_TABLES = (
    "inbound_inventory_disposition_allocations",
    "inventory_disposition_splits",
    "quality_quarantine_cases",
    "quality_quarantine_case_revisions",
    "quarantine_zone_configurations",
    "quarantine_placement_confirmations",
    "quality_inspections",
    "quality_inspection_snapshots",
    "quality_inspection_controls",
    "quality_inspection_control_results",
    "quality_measurements",
    "quality_inspection_sample_sets",
    "quality_inspection_sample_references",
    "quality_certificate_reviews",
    "quality_inspection_evidence_links",
    "quality_disposition_decisions",
    "quality_decision_approvals",
    "quarantine_release_authorizations",
    "quarantine_rejection_authorizations",
    "quality_reinspection_requests",
    "quality_disposition_events",
    "inbound_quality_availability_projection",
)
