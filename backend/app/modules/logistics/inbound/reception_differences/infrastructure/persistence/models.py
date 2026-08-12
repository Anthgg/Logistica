"""Phase 040 persistence. Reception difference cases, items, evidence, responsibility, reviews, approvals."""

from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.database.base import Base

QTY = {"precision": 38, "scale": 18}


class ReceptionDifferenceCaseModel(Base):
    __tablename__ = "reception_difference_cases"
    __table_args__ = (
        UniqueConstraint("organization_id", "normalized_case_code", name="uq_diff_case_org_code"),
        Index("ix_diff_case_org", "organization_id"),
        Index("ix_diff_case_warehouse", "warehouse_id"),
        Index("ix_diff_case_receipt", "inbound_receipt_id"),
        Index("ix_diff_case_supplier", "supplier_business_partner_id"),
        Index("ix_diff_case_carrier", "carrier_business_partner_id"),
        Index("ix_diff_case_status", "status"),
        Index("ix_diff_case_severity", "severity"),
        Index("ix_diff_case_responsibility", "responsibility_status"),
        Index("ix_diff_case_issued", "issued_at"),
        Index("ix_diff_case_updated", "updated_at"),
        CheckConstraint("row_version >= 1", name="ck_diff_case_row_version"),
    )
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    branch_id = Column(PG_UUID(as_uuid=True), nullable=False)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    case_code = Column(String(80), nullable=False)
    normalized_case_code = Column(String(80), nullable=False)
    inbound_receipt_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_receipts.id", ondelete="RESTRICT"), nullable=False)
    inbound_receipt_revision_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_receipt_revisions.id", ondelete="RESTRICT"), nullable=False)
    unloading_operation_id = Column(PG_UUID(as_uuid=True), nullable=True)
    gate_check_in_id = Column(PG_UUID(as_uuid=True), nullable=True)
    appointment_id = Column(PG_UUID(as_uuid=True), nullable=True)
    arrival_notice_id = Column(PG_UUID(as_uuid=True), nullable=True)
    supplier_business_partner_id = Column(PG_UUID(as_uuid=True), nullable=True)
    supplier_snapshot = Column(JSONB, nullable=False, default=dict)
    carrier_business_partner_id = Column(PG_UUID(as_uuid=True), nullable=True)
    carrier_snapshot = Column(JSONB, nullable=True)
    status = Column(String(40), nullable=False, default="DRAFT")
    source_type = Column(String(40), nullable=False, default="RECEIPT_CANDIDATES")
    severity = Column(String(20), nullable=False, default="LOW")
    item_count = Column(Integer, nullable=False, default=0)
    open_item_count = Column(Integer, nullable=False, default=0)
    critical_item_count = Column(Integer, nullable=False, default=0)
    evidence_count = Column(Integer, nullable=False, default=0)
    proposed_responsible_party_type = Column(String(40), nullable=True)
    proposed_responsible_party_id = Column(PG_UUID(as_uuid=True), nullable=True)
    responsibility_status = Column(String(40), nullable=False, default="UNDETERMINED")
    active_revision_id = Column(PG_UUID(as_uuid=True), nullable=True)
    current_revision_number = Column(Integer, nullable=False, default=0)
    document_instance_id = Column(PG_UUID(as_uuid=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True))
    submitted_by = Column(PG_UUID(as_uuid=True))
    reviewed_at = Column(DateTime(timezone=True))
    reviewed_by = Column(PG_UUID(as_uuid=True))
    approved_at = Column(DateTime(timezone=True))
    approved_by = Column(PG_UUID(as_uuid=True))
    issued_at = Column(DateTime(timezone=True))
    issued_by = Column(PG_UUID(as_uuid=True))
    acknowledged_at = Column(DateTime(timezone=True))
    disputed_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    cancellation_reason = Column(Text)
    content_hash = Column(String(64))
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    row_version = Column(Integer, nullable=False, server_default=text("1"))


class ReceptionDifferenceCaseRevisionModel(Base):
    __tablename__ = "reception_difference_case_revisions"
    __table_args__ = (
        UniqueConstraint("difference_case_id", "revision_number", name="uq_diff_case_revision_number"),
    )
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    difference_case_id = Column(PG_UUID(as_uuid=True), ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False, index=True)
    revision_number = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False, default="EDITABLE")
    source_snapshot = Column(JSONB, nullable=False, default=dict)
    difference_items_snapshot = Column(JSONB, nullable=True)
    evidence_manifest_snapshot = Column(JSONB, nullable=True)
    responsibility_snapshot = Column(JSONB, nullable=True)
    review_snapshot = Column(JSONB, nullable=True)
    approval_snapshot = Column(JSONB, nullable=True)
    acknowledgement_snapshot = Column(JSONB, nullable=True)
    content_hash = Column(String(64))
    completion_snapshot = Column(JSONB, nullable=True)
    created_from_revision_id = Column(PG_UUID(as_uuid=True))
    change_reason = Column(Text)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    submitted_at = Column(DateTime(timezone=True))
    frozen_at = Column(DateTime(timezone=True))


class ReceptionDifferenceItemModel(Base):
    __tablename__ = "reception_difference_items"
    __table_args__ = (
        UniqueConstraint("case_revision_id", "item_number", name="uq_diff_item_revision_number"),
        Index("ix_diff_item_case", "difference_case_id"),
        Index("ix_diff_item_candidate", "source_candidate_id"),
        Index("ix_diff_item_type", "difference_type"),
        Index("ix_diff_item_category", "category"),
        Index("ix_diff_item_severity", "severity"),
        Index("ix_diff_item_product", "product_id"),
        Index("ix_diff_item_po_line", "purchase_order_line_id"),
        Index("ix_diff_item_status", "status"),
        CheckConstraint("row_version >= 1", name="ck_diff_item_row_version"),
    )
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    difference_case_id = Column(PG_UUID(as_uuid=True), ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False, index=True)
    case_revision_id = Column(PG_UUID(as_uuid=True), ForeignKey("reception_difference_case_revisions.id", ondelete="RESTRICT"), nullable=False)
    item_number = Column(Integer, nullable=False)
    source_candidate_id = Column(PG_UUID(as_uuid=True), nullable=True)
    difference_type = Column(String(60), nullable=False)
    category = Column(String(30), nullable=False)
    severity = Column(String(20), nullable=False, default="LOW")
    status = Column(String(30), nullable=False, default="OPEN")
    purchase_order_id = Column(PG_UUID(as_uuid=True), nullable=True)
    purchase_order_line_id = Column(PG_UUID(as_uuid=True), nullable=True)
    expected_line_id = Column(PG_UUID(as_uuid=True), nullable=True)
    received_line_id = Column(PG_UUID(as_uuid=True), nullable=True)
    product_id = Column(PG_UUID(as_uuid=True), nullable=True)
    product_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    sku_snapshot = Column(String(120), nullable=True)
    product_name_snapshot = Column(String(500), nullable=True)
    expected_quantity = Column(Numeric(**QTY), nullable=True)
    expected_unit_id = Column(PG_UUID(as_uuid=True), nullable=True)
    expected_base_quantity = Column(Numeric(**QTY), nullable=True)
    observed_quantity = Column(Numeric(**QTY), nullable=True)
    observed_unit_id = Column(PG_UUID(as_uuid=True), nullable=True)
    observed_base_quantity = Column(Numeric(**QTY), nullable=True)
    difference_quantity = Column(Numeric(**QTY), nullable=True)
    difference_unit_id = Column(PG_UUID(as_uuid=True), nullable=True)
    difference_base_quantity = Column(Numeric(**QTY), nullable=True)
    lot_observation_id = Column(PG_UUID(as_uuid=True), nullable=True)
    serial_observation_id = Column(PG_UUID(as_uuid=True), nullable=True)
    expiration_observation_id = Column(PG_UUID(as_uuid=True), nullable=True)
    transport_document_id = Column(PG_UUID(as_uuid=True), nullable=True)
    gate_seal_inspection_id = Column(PG_UUID(as_uuid=True), nullable=True)
    unloading_seal_opening_event_id = Column(PG_UUID(as_uuid=True), nullable=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    detection_source = Column(String(40), nullable=False, default="RECEIPT_CANDIDATES")
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    detected_by_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    detected_by_service = Column(String(120), nullable=True)
    requires_evidence = Column(Boolean, nullable=False, default=True)
    requires_responsibility = Column(Boolean, nullable=False, default=True)
    requires_quality_review = Column(Boolean, nullable=False, default=False)
    future_quarantine_recommended = Column(Boolean, nullable=False, default=False)
    future_claim_recommended = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    row_version = Column(Integer, nullable=False, server_default=text("1"))


class ReceptionDamageDetailModel(Base):
    __tablename__ = "reception_damage_details"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    difference_item_id = Column(PG_UUID(as_uuid=True), ForeignKey("reception_difference_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    damage_scope = Column(String(40), nullable=False)
    damage_type = Column(String(40), nullable=False)
    affected_quantity = Column(Numeric(**QTY), nullable=True)
    unit_id = Column(PG_UUID(as_uuid=True), nullable=True)
    affected_base_quantity = Column(Numeric(**QTY), nullable=True)
    packaging_level = Column(String(40), nullable=True)
    visual_description = Column(Text, nullable=True)
    functional_impact_declared = Column(Text, nullable=True)
    safety_concern = Column(Boolean, nullable=False, default=False)
    contamination_concern = Column(Boolean, nullable=False, default=False)
    temperature_concern = Column(Boolean, nullable=False, default=False)
    evidence_required = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReceptionDifferenceEvidenceLinkModel(Base):
    __tablename__ = "reception_difference_evidence_links"
    __table_args__ = (
        Index("ix_diff_evidence_case", "difference_case_id"),
        Index("ix_diff_evidence_item", "difference_item_id"),
        Index("ix_diff_evidence_file", "file_asset_id"),
    )
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    difference_case_id = Column(PG_UUID(as_uuid=True), ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False)
    difference_item_id = Column(PG_UUID(as_uuid=True), ForeignKey("reception_difference_items.id", ondelete="SET NULL"), nullable=True)
    evidence_record_id = Column(PG_UUID(as_uuid=True), nullable=True)
    file_asset_id = Column(PG_UUID(as_uuid=True), nullable=False)
    file_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    evidence_type = Column(String(40), nullable=False)
    source_type = Column(String(40), nullable=False, default="UPLOAD")
    classification = Column(String(40), nullable=False, default="STANDARD")
    description = Column(Text, nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=True)
    linked_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    linked_by = Column(PG_UUID(as_uuid=True), nullable=False)
    content_hash = Column(String(64), nullable=True)
    status = Column(String(30), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReceptionDifferenceResponsiblePartyModel(Base):
    __tablename__ = "reception_difference_responsible_parties"
    __table_args__ = (
        Index("ix_diff_resp_case", "difference_case_id"),
        Index("ix_diff_resp_type", "party_type"),
        Index("ix_diff_resp_status", "responsibility_status"),
    )
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    difference_case_id = Column(PG_UUID(as_uuid=True), ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False)
    difference_item_id = Column(PG_UUID(as_uuid=True), ForeignKey("reception_difference_items.id", ondelete="SET NULL"), nullable=True)
    party_type = Column(String(40), nullable=False)
    business_partner_id = Column(PG_UUID(as_uuid=True), nullable=True)
    user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    organization_unit_id = Column(PG_UUID(as_uuid=True), nullable=True)
    responsible_snapshot = Column(JSONB, nullable=False, default=dict)
    responsibility_role = Column(String(30), nullable=False, default="UNDETERMINED")
    responsibility_status = Column(String(40), nullable=False, default="PROPOSED")
    proposed_by = Column(PG_UUID(as_uuid=True), nullable=False)
    proposed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reviewed_by = Column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(PG_UUID(as_uuid=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    disputed_by = Column(PG_UUID(as_uuid=True), nullable=True)
    disputed_at = Column(DateTime(timezone=True), nullable=True)
    dispute_reason = Column(Text, nullable=True)
    allocation_percentage = Column(Numeric(**QTY), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReceptionDifferenceReviewModel(Base):
    __tablename__ = "reception_difference_reviews"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    difference_case_id = Column(PG_UUID(as_uuid=True), ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False, index=True)
    review_type = Column(String(40), nullable=False)
    status = Column(String(30), nullable=False, default="PENDING")
    reviewer_user_id = Column(PG_UUID(as_uuid=True), nullable=False)
    reviewer_snapshot = Column(JSONB, nullable=False, default=dict)
    findings = Column(Text, nullable=True)
    blocking_issues = Column(JSONB, nullable=True)
    requested_changes = Column(JSONB, nullable=True)
    recommendation = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReceptionDifferenceApprovalModel(Base):
    __tablename__ = "reception_difference_approvals"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    difference_case_id = Column(PG_UUID(as_uuid=True), ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False, index=True)
    approval_level = Column(Integer, nullable=False, default=1)
    approver_user_id = Column(PG_UUID(as_uuid=True), nullable=False)
    approver_snapshot = Column(JSONB, nullable=False, default=dict)
    decision = Column(String(40), nullable=False)
    reason = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    policy_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    step_up_assurance_summary = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReceptionDifferenceAcknowledgementModel(Base):
    __tablename__ = "reception_difference_acknowledgements"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    difference_case_id = Column(PG_UUID(as_uuid=True), ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False, index=True)
    party_type = Column(String(40), nullable=False)
    business_partner_id = Column(PG_UUID(as_uuid=True), nullable=True)
    external_actor_id = Column(PG_UUID(as_uuid=True), nullable=True)
    acknowledgement_type = Column(String(40), nullable=False)
    statement = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="ACTIVE")
    acknowledged_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    evidence_file_id = Column(PG_UUID(as_uuid=True), nullable=True)
    source_channel = Column(String(40), nullable=False, default="INTERNAL")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReceptionDifferenceFollowUpRecommendationModel(Base):
    __tablename__ = "reception_difference_follow_up_recommendations"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id = Column(PG_UUID(as_uuid=True), ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False, index=True)
    item_id = Column(PG_UUID(as_uuid=True), ForeignKey("reception_difference_items.id", ondelete="SET NULL"), nullable=True)
    recommendation_type = Column(String(60), nullable=False)
    reason = Column(Text, nullable=True)
    priority = Column(String(20), nullable=False, default="MEDIUM")
    status = Column(String(30), nullable=False, default="PENDING")
    target_module = Column(String(60), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReceptionDifferenceDocumentPackageModel(Base):
    __tablename__ = "reception_difference_document_packages"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    difference_case_id = Column(PG_UUID(as_uuid=True), ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False, index=True)
    package_type = Column(String(30), nullable=False, default="DIF_PACKAGE")
    status = Column(String(30), nullable=False, default="PENDING")
    file_asset_id = Column(PG_UUID(as_uuid=True), nullable=True)
    content_hash = Column(String(64), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True))


class ReceptionDifferenceMetricsProjectionModel(Base):
    __tablename__ = "reception_difference_metrics_projection"
    case_id = Column(PG_UUID(as_uuid=True), ForeignKey("reception_difference_cases.id", ondelete="CASCADE"), primary_key=True)
    organization_id = Column(PG_UUID(as_uuid=True), nullable=False)
    warehouse_id = Column(PG_UUID(as_uuid=True), nullable=False)
    total_items = Column(Integer, nullable=False, default=0)
    critical_items = Column(Integer, nullable=False, default=0)
    quantity_items = Column(Integer, nullable=False, default=0)
    product_items = Column(Integer, nullable=False, default=0)
    condition_items = Column(Integer, nullable=False, default=0)
    identification_items = Column(Integer, nullable=False, default=0)
    documentation_items = Column(Integer, nullable=False, default=0)
    seal_items = Column(Integer, nullable=False, default=0)
    evidence_count = Column(Integer, nullable=False, default=0)
    photo_count = Column(Integer, nullable=False, default=0)
    responsible_parties_count = Column(Integer, nullable=False, default=0)
    calculated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


PHASE_040_TABLES = (
    "reception_difference_cases",
    "reception_difference_case_revisions",
    "reception_difference_items",
    "reception_damage_details",
    "reception_difference_evidence_links",
    "reception_difference_responsible_parties",
    "reception_difference_reviews",
    "reception_difference_approvals",
    "reception_difference_acknowledgements",
    "reception_difference_follow_up_recommendations",
    "reception_difference_document_packages",
    "reception_difference_metrics_projection",
)
