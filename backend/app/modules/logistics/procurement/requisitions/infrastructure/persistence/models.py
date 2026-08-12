"""ORM models for Purchase Requisitions module (Phase 031).

Tables created:
- purchase_requisitions
- purchase_requisition_revisions
- purchase_requisition_lines
- purchase_requisition_decisions
- purchase_requisition_comments
- purchase_requisition_duplicate_candidates
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship

from app.database.base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# SQLite compatibility for tests
try:
    JSON_TYPE = JSONB().with_variant(JSON(), "sqlite")
except Exception:  # pragma: no cover
    JSON_TYPE = JSON()  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# PurchaseRequisitionModel
# ---------------------------------------------------------------------------


class PurchaseRequisitionModel(Base):
    """Master record of a purchase requisition — lifecycle owner."""

    __tablename__ = "purchase_requisitions"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "normalized_requisition_code",
            name="uq_purchase_req_org_code",
        ),
        Index("ix_pr_org_status", "organization_id", "status"),
        Index("ix_pr_requester", "organization_id", "requester_user_id"),
        Index("ix_pr_cost_center", "organization_id", "cost_center_id"),
        Index("ix_pr_required_date", "organization_id", "required_date"),
        Index("ix_pr_submitted_at", "organization_id", "submitted_at"),
        Index("ix_pr_priority", "organization_id", "priority"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    branch_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_branches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Document number — assigned only on submit, not during preview
    requisition_code = Column(String(60), nullable=True)
    normalized_requisition_code = Column(String(60), nullable=True, index=True)
    document_instance_id = Column(PG_UUID(as_uuid=True), nullable=True)
    document_series_id = Column(PG_UUID(as_uuid=True), nullable=True)

    # Requester
    requester_user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    requester_name_snapshot = Column(String(200), nullable=False)
    requester_area = Column(String(150), nullable=True)

    # Cost center
    cost_center_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("cost_centers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    cost_center_snapshot = Column(JSON_TYPE, nullable=False)

    # Request details
    priority = Column(String(20), nullable=False, default="NORMAL", index=True)
    required_date = Column(Date, nullable=False, index=True)
    destination_warehouse_id = Column(PG_UUID(as_uuid=True), nullable=True, index=True)
    delivery_location_description = Column(Text, nullable=True)
    justification = Column(Text, nullable=False)
    business_purpose = Column(Text, nullable=True)

    # State machine
    status = Column(String(30), nullable=False, default="DRAFT", index=True)

    # Revision tracking
    current_revision_number = Column(Integer, nullable=False, default=0)
    active_revision_id = Column(PG_UUID(as_uuid=True), nullable=True)
    submitted_revision_id = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_revision_id = Column(PG_UUID(as_uuid=True), nullable=True)

    # Lifecycle timestamps and actors
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    submitted_by = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(PG_UUID(as_uuid=True), nullable=True)
    returned_at = Column(DateTime(timezone=True), nullable=True)
    returned_by = Column(PG_UUID(as_uuid=True), nullable=True)
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)
    withdrawn_by = Column(PG_UUID(as_uuid=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by = Column(PG_UUID(as_uuid=True), nullable=True)

    last_decision_id = Column(PG_UUID(as_uuid=True), nullable=True)

    # Audit
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=False)
    row_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    revisions = relationship(
        "PurchaseRequisitionRevisionModel",
        back_populates="requisition",
        cascade="all, delete-orphan",
        order_by="PurchaseRequisitionRevisionModel.revision_number",
    )
    decisions = relationship(
        "PurchaseRequisitionDecisionModel",
        back_populates="requisition",
        cascade="all, delete-orphan",
        order_by="PurchaseRequisitionDecisionModel.created_at",
    )
    comments = relationship(
        "PurchaseRequisitionCommentModel",
        back_populates="requisition",
        cascade="all, delete-orphan",
        order_by="PurchaseRequisitionCommentModel.created_at",
    )


# ---------------------------------------------------------------------------
# PurchaseRequisitionRevisionModel
# ---------------------------------------------------------------------------


class PurchaseRequisitionRevisionModel(Base):
    """Immutable snapshot of a requisition at a specific point in time."""

    __tablename__ = "purchase_requisition_revisions"
    __table_args__ = (
        UniqueConstraint(
            "requisition_id",
            "revision_number",
            name="uq_purchase_req_revision_number",
        ),
        Index("ix_prr_requisition_status", "requisition_id", "status"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    requisition_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_requisitions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    revision_number = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False, default="EDITABLE", index=True)

    # Immutable snapshots (captured at revision creation time)
    branch_snapshot = Column(JSON_TYPE, nullable=False)
    requester_snapshot = Column(JSON_TYPE, nullable=False)
    cost_center_snapshot = Column(JSON_TYPE, nullable=False)

    priority = Column(String(20), nullable=False)
    required_date = Column(Date, nullable=False)
    destination_snapshot = Column(JSON_TYPE, nullable=True)
    justification = Column(Text, nullable=False)
    business_purpose = Column(Text, nullable=True)

    line_count = Column(Integer, nullable=False, default=0)
    total_requested_base_quantity = Column(Numeric(18, 6), nullable=True)
    content_hash = Column(String(64), nullable=True)

    created_from_revision_id = Column(PG_UUID(as_uuid=True), nullable=True)
    change_summary = Column(Text, nullable=True)

    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    frozen_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    requisition = relationship("PurchaseRequisitionModel", back_populates="revisions")
    lines = relationship(
        "PurchaseRequisitionLineModel",
        back_populates="revision",
        cascade="all, delete-orphan",
        order_by="PurchaseRequisitionLineModel.line_number",
    )
    decisions = relationship(
        "PurchaseRequisitionDecisionModel",
        back_populates="revision",
        foreign_keys="PurchaseRequisitionDecisionModel.revision_id",
    )


# ---------------------------------------------------------------------------
# PurchaseRequisitionLineModel
# ---------------------------------------------------------------------------


class PurchaseRequisitionLineModel(Base):
    """Single product line within a purchase requisition revision."""

    __tablename__ = "purchase_requisition_lines"
    __table_args__ = (
        UniqueConstraint(
            "requisition_revision_id",
            "line_number",
            name="uq_purchase_req_line_number",
        ),
        CheckConstraint("requested_quantity > 0", name="ck_prl_requested_qty_positive"),
        CheckConstraint("base_quantity > 0", name="ck_prl_base_qty_positive"),
        Index("ix_prl_revision_status", "requisition_revision_id", "status"),
        Index("ix_prl_product", "product_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    requisition_revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_requisition_revisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number = Column(Integer, nullable=False)

    # Product reference (never free text)
    product_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    product_version_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("product_versions.id", ondelete="RESTRICT"),
        nullable=True,
    )

    # Immutable product snapshots (persist even if product changes later)
    sku_snapshot = Column(String(50), nullable=False)
    product_name_snapshot = Column(String(200), nullable=False)
    product_description_snapshot = Column(Text, nullable=True)

    # Quantities — always Decimal, never float
    requested_quantity = Column(Numeric(18, 6), nullable=False)
    requested_unit_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"),
        nullable=False,
    )
    base_quantity = Column(Numeric(18, 6), nullable=False)
    base_unit_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Conversion audit trail
    conversion_rule_id = Column(PG_UUID(as_uuid=True), nullable=True)
    conversion_factor_snapshot = Column(Numeric(38, 18), nullable=True)

    # Optional per-line details
    required_date = Column(Date, nullable=True)
    destination_warehouse_id = Column(PG_UUID(as_uuid=True), nullable=True)
    line_justification = Column(Text, nullable=True)
    specifications = Column(JSON_TYPE, nullable=True)
    manufacturer_reference = Column(String(200), nullable=True)
    preferred_brand_reference = Column(String(200), nullable=True)
    priority_override = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)

    status = Column(String(20), nullable=False, default="ACTIVE", index=True)

    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    row_version = Column(Integer, nullable=False, default=1)

    # Relationships
    revision = relationship("PurchaseRequisitionRevisionModel", back_populates="lines")


# ---------------------------------------------------------------------------
# PurchaseRequisitionDecisionModel
# ---------------------------------------------------------------------------


class PurchaseRequisitionDecisionModel(Base):
    """Immutable decision record — approve, reject, return, etc."""

    __tablename__ = "purchase_requisition_decisions"
    __table_args__ = (
        Index("ix_prd_requisition_final", "requisition_id", "is_final"),
        Index("ix_prd_decided_by", "decided_by"),
        Index("ix_prd_decided_at", "decided_at"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    requisition_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_requisitions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_requisition_revisions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    decision_type = Column(String(30), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="ACTIVE")

    decided_by = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    decided_at = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text, nullable=True)
    conditions = Column(JSON_TYPE, nullable=True)

    approval_policy_code = Column(String(50), nullable=False, default="SINGLE_STEP_BASIC")
    approval_policy_version = Column(String(20), nullable=False, default="1.0.0")
    step_number = Column(Integer, nullable=False, default=1)
    is_final = Column(Boolean, nullable=False, default=False, index=True)
    previous_decision_id = Column(PG_UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    requisition = relationship("PurchaseRequisitionModel", back_populates="decisions")
    revision = relationship(
        "PurchaseRequisitionRevisionModel",
        back_populates="decisions",
        foreign_keys=[revision_id],
    )


# ---------------------------------------------------------------------------
# PurchaseRequisitionCommentModel
# ---------------------------------------------------------------------------


class PurchaseRequisitionCommentModel(Base):
    """Comments and notes attached to a purchase requisition."""

    __tablename__ = "purchase_requisition_comments"
    __table_args__ = (
        Index("ix_prc_requisition_type", "requisition_id", "comment_type"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    requisition_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_requisitions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    revision_id = Column(PG_UUID(as_uuid=True), nullable=True)
    comment_type = Column(String(30), nullable=False)
    body = Column(Text, nullable=False)
    visibility = Column(String(40), nullable=False, default="INTERNAL")

    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    edited_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")

    # Relationships
    requisition = relationship("PurchaseRequisitionModel", back_populates="comments")


# ---------------------------------------------------------------------------
# PurchaseRequisitionDuplicateCandidateModel
# ---------------------------------------------------------------------------


class PurchaseRequisitionDuplicateCandidateModel(Base):
    """Detected potential duplicate pairs — advisory only, never blocking."""

    __tablename__ = "purchase_requisition_duplicate_candidates"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_requisition_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_requisitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_requisition_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_requisitions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    score = Column(Numeric(5, 4), nullable=False)
    detection_method = Column(String(50), nullable=False, default="HEURISTIC_BASIC")
    override_justification = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
