"""Phase 043 — Putaway ORM models (22 tables)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4, UUID

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def _uuid() -> UUID:
    return uuid4()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# =============================================================================
# 1. PutawayPolicy
# =============================================================================
class PutawayPolicyModel(Base):
    __tablename__ = "putaway_policies"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    normalized_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", index=True)
    active_version_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    row_version: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)

    versions: Mapped[list["PutawayPolicyVersionModel"]] = relationship(back_populates="policy", cascade="all, delete-orphan")

    __table_args__ = (
        sa.UniqueConstraint("organization_id", "normalized_code", name="uq_putaway_policies_org_code"),
        CheckConstraint("row_version >= 1", name="ck_putaway_policies_row_version"),
    )


# =============================================================================
# 2. PutawayPolicyVersion
# =============================================================================
class PutawayPolicyVersionModel(Base):
    __tablename__ = "putaway_policy_versions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    policy_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("putaway_policies.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")
    effective_from: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    effective_to: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    warehouse_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    branch_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    product_category_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    product_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    priority: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    capacity_weight: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False, default=Decimal("0"))
    rotation_weight: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False, default=Decimal("0"))
    picking_proximity_weight: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False, default=Decimal("0"))
    consolidation_weight: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False, default=Decimal("0"))
    fragmentation_penalty_weight: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False, default=Decimal("0"))
    travel_cost_weight: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False, default=Decimal("0"))
    manual_override_allowed: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    partial_putaway_allowed: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    split_destination_allowed: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    reservation_expiration_minutes: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=30)
    maximum_candidate_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=50)
    minimum_score: Mapped[Decimal | None] = mapped_column(sa.Numeric(5, 2))
    content_hash: Mapped[str | None] = mapped_column(String(64))
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    validated_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    activated_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    activated_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))

    policy: Mapped["PutawayPolicyModel"] = relationship(back_populates="versions")

    __table_args__ = (
        sa.UniqueConstraint("policy_id", "version_number", name="uq_putaway_policy_versions_policy_version"),
    )


# =============================================================================
# 3. StorageCompatibilityRule
# =============================================================================
class StorageCompatibilityRuleModel(Base):
    __tablename__ = "storage_compatibility_rules"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    policy_version_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("putaway_policy_versions.id", ondelete="SET NULL"), index=True)
    warehouse_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    location_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    location_type: Mapped[str | None] = mapped_column(String(30))
    product_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    product_category_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False, default="ALLOW")
    required_value: Mapped[dict | None] = mapped_column(JSONB)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    reason: Mapped[str | None] = mapped_column(Text)
    effective_from: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    effective_to: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())

    __table_args__ = (
        Index("ix_storage_compat_warehouse_type", "warehouse_id", "rule_type"),
    )


# =============================================================================
# 4. WarehouseLocationCapacityProfile
# =============================================================================
class WarehouseLocationCapacityProfileModel(Base):
    __tablename__ = "warehouse_location_capacity_profiles"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    warehouse_location_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("warehouse_locations.id", ondelete="CASCADE"), nullable=False, index=True)
    capacity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    maximum_value: Mapped[Decimal] = mapped_column(sa.Numeric(14, 4), nullable=False)
    unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    safety_margin_value: Mapped[Decimal] = mapped_column(sa.Numeric(14, 4), nullable=False, default=Decimal("0"))
    reservation_limit_value: Mapped[Decimal | None] = mapped_column(sa.Numeric(14, 4))
    effective_from: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    effective_to: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    row_version: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)

    __table_args__ = (
        CheckConstraint("maximum_value > 0", name="ck_capacity_profiles_max_positive"),
    )


# =============================================================================
# 5. PutawayLocationCapacityProjection
# =============================================================================
class PutawayLocationCapacityProjectionModel(Base):
    __tablename__ = "putaway_location_capacity_projection"

    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    warehouse_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    location_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    capacity_profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    capacity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    maximum_value: Mapped[Decimal] = mapped_column(sa.Numeric(14, 4), nullable=False)
    safety_margin_value: Mapped[Decimal] = mapped_column(sa.Numeric(14, 4), nullable=False, default=Decimal("0"))
    operational_occupied_value: Mapped[Decimal] = mapped_column(sa.Numeric(14, 4), nullable=False, default=Decimal("0"))
    active_reserved_value: Mapped[Decimal] = mapped_column(sa.Numeric(14, 4), nullable=False, default=Decimal("0"))
    projected_free_value: Mapped[Decimal] = mapped_column(sa.Numeric(14, 4), nullable=False, default=Decimal("0"))
    unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    data_quality_status: Mapped[str] = mapped_column(String(30), nullable=False, default="MISSING_BASELINE")
    last_placement_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    calculated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    projection_version: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)

    __table_args__ = (
        sa.PrimaryKeyConstraint("organization_id", "warehouse_id", "location_id", "capacity_profile_id"),
        Index("ix_capacity_projection_location", "location_id"),
    )


# =============================================================================
# 6. WarehouseLocationProximityProfile
# =============================================================================
class WarehouseLocationProximityProfileModel(Base):
    __tablename__ = "warehouse_location_proximity_profiles"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    warehouse_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    source_location_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    target_zone_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    target_location_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    metric_type: Mapped[str] = mapped_column(String(40), nullable=False)
    metric_value: Mapped[Decimal] = mapped_column(sa.Numeric(14, 4), nullable=False)
    metric_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, default="MANUAL_MEASUREMENT")
    measured_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    effective_from: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    effective_to: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())

    __table_args__ = (
        Index("ix_proximity_source_target", "source_location_id", "target_zone_id"),
    )


# =============================================================================
# 7. PutawayRecommendationRun
# =============================================================================
class PutawayRecommendationRunModel(Base):
    __tablename__ = "putaway_recommendation_runs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    warehouse_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    source_allocation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    policy_version_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="CREATED", index=True)
    requested_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False)
    requested_unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    requested_base_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False)
    candidate_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    eligible_candidate_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    source_snapshot_hash: Mapped[str | None] = mapped_column(String(64))
    input_hash: Mapped[str | None] = mapped_column(String(64))
    scoring_version: Mapped[str | None] = mapped_column(String(20))
    started_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())

    candidates: Mapped[list["PutawayLocationCandidateModel"]] = relationship(back_populates="recommendation_run", cascade="all, delete-orphan")


# =============================================================================
# 8. PutawayLocationCandidate
# =============================================================================
class PutawayLocationCandidateModel(Base):
    __tablename__ = "putaway_location_candidates"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    recommendation_run_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("putaway_recommendation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    rank: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    compatible: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    capacity_available: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    capacity_score: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False, default=Decimal("0"))
    rotation_score: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False, default=Decimal("0"))
    picking_proximity_score: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False, default=Decimal("0"))
    consolidation_score: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False, default=Decimal("0"))
    fragmentation_score: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False, default=Decimal("0"))
    travel_cost_score: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False, default=Decimal("0"))
    penalty_score: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False, default=Decimal("0"))
    total_score: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False, default=Decimal("0"))
    capacity_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    compatibility_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    proximity_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    rotation_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    explanation: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="CANDIDATE")
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())

    recommendation_run: Mapped["PutawayRecommendationRunModel"] = relationship(back_populates="candidates")

    __table_args__ = (
        Index("ix_candidate_total_score", "recommendation_run_id", "total_score"),
    )


# =============================================================================
# 9. PutawayOrder
# =============================================================================
class PutawayOrderModel(Base):
    __tablename__ = "putaway_orders"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    branch_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    warehouse_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    order_code: Mapped[str] = mapped_column(String(80), nullable=False)
    normalized_order_code: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT", index=True)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default="QUALITY_RELEASE")
    priority: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    task_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    completed_task_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    exception_task_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    document_instance_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    issued_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    issued_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    assigned_team_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    started_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    active_revision_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    current_revision_number: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    row_version: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)

    __table_args__ = (
        sa.UniqueConstraint("organization_id", "normalized_order_code", name="uq_putaway_orders_org_code"),
        CheckConstraint("row_version >= 1", name="ck_putaway_orders_row_version"),
    )


# =============================================================================
# 10. PutawayOrderRevision
# =============================================================================
class PutawayOrderRevisionModel(Base):
    __tablename__ = "putaway_order_revisions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    putaway_order_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("putaway_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    revision_number: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="EDITABLE")
    source_allocations_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    recommendation_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    tasks_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    reservation_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    document_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    created_from_revision_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    change_reason: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    frozen_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))

    __table_args__ = (
        sa.UniqueConstraint("putaway_order_id", "revision_number", name="uq_putaway_order_revisions_order_number"),
    )


# =============================================================================
# 11. PutawayTask
# =============================================================================
class PutawayTaskModel(Base):
    __tablename__ = "putaway_tasks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    warehouse_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    putaway_order_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("putaway_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    task_number: Mapped[str] = mapped_column(String(50), nullable=False)
    source_allocation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    recommendation_run_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    recommended_location_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    selected_location_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), index=True)
    source_stage_location_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="CREATED", index=True)
    priority: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    assignment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="UNASSIGNED")
    assigned_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), index=True)
    assigned_team_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    assigned_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    required_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False)
    required_unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    required_base_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False)
    placed_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False, default=Decimal("0"))
    placed_unit_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    placed_base_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False, default=Decimal("0"))
    remaining_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False, default=Decimal("0"))
    remaining_base_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False, default=Decimal("0"))
    scan_policy: Mapped[str] = mapped_column(String(40), nullable=False, default="PRODUCT_THEN_LOCATION")
    expected_product_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    product_version_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    quality_release_hash: Mapped[str | None] = mapped_column(String(64))
    location_reservation_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    started_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    paused_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    exception_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    row_version: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)

    __table_args__ = (
        sa.UniqueConstraint("putaway_order_id", "task_number", name="uq_putaway_tasks_order_number"),
        CheckConstraint("required_quantity > 0", name="ck_putaway_tasks_req_qty_positive"),
        CheckConstraint("row_version >= 1", name="ck_putaway_tasks_row_version"),
    )


# =============================================================================
# 12. PutawayTaskDestination
# =============================================================================
class PutawayTaskDestinationModel(Base):
    __tablename__ = "putaway_task_destinations"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    sequence_number: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    recommended_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False)
    unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    base_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False)
    reservation_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PLANNED")
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


# =============================================================================
# 13. PutawayTaskAssignment
# =============================================================================
class PutawayTaskAssignmentModel(Base):
    __tablename__ = "putaway_task_assignments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_type: Mapped[str] = mapped_column(String(20), nullable=False, default="USER")
    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    team_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ASSIGNED")
    assigned_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    accepted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    declined_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    decline_reason: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


# =============================================================================
# 14. PutawayLocationReservation
# =============================================================================
class PutawayLocationReservationModel(Base):
    __tablename__ = "putaway_location_reservations"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    warehouse_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    location_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    source_allocation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    capacity_profile_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    reserved_value: Mapped[Decimal] = mapped_column(sa.Numeric(14, 4), nullable=False)
    unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    reserved_base_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)
    reserved_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    row_version: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())

    __table_args__ = (
        Index("ix_reservation_expires", "status", "expires_at"),
    )


# =============================================================================
# 15. PutawayExecutionSession
# =============================================================================
class PutawayExecutionSessionModel(Base):
    __tablename__ = "putaway_execution_sessions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    operator_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    device_reference_hash: Mapped[str | None] = mapped_column(String(64))
    scanner_type: Mapped[str] = mapped_column(String(30), nullable=False, default="HANDHELD_TERMINAL")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    started_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    last_activity_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    paused_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    client_session_reference: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    row_version: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)


# =============================================================================
# 16. PutawayScanEvent
# =============================================================================
class PutawayScanEventModel(Base):
    __tablename__ = "putaway_scan_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    warehouse_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    execution_session_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("putaway_execution_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    client_scan_id: Mapped[str] = mapped_column(String(200), nullable=False)
    server_sequence: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    scan_type: Mapped[str] = mapped_column(String(30), nullable=False)
    raw_code_encrypted: Mapped[str | None] = mapped_column(Text)
    normalized_code: Mapped[str] = mapped_column(String(200), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    symbology: Mapped[str | None] = mapped_column(String(30))
    resolution_status: Mapped[str] = mapped_column(String(20), nullable=False, default="RECORDED")
    resolved_product_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    resolved_location_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    validation_status: Mapped[str | None] = mapped_column(String(30))
    expected_value_hash: Mapped[str | None] = mapped_column(String(64))
    received_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    operator_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="RECORDED")
    duplicate_of_event_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())

    __table_args__ = (
        sa.UniqueConstraint("execution_session_id", "client_scan_id", name="uq_putaway_scan_events_session_client"),
        Index("ix_scan_event_code_hash", "code_hash"),
        Index("ix_scan_event_type_received", "scan_type", "received_at"),
    )


# =============================================================================
# 17. PutawayPlacementConfirmation
# =============================================================================
class PutawayPlacementConfirmationModel(Base):
    __tablename__ = "putaway_placement_confirmations"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    warehouse_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    source_allocation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    location_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False)
    unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    base_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False)
    product_scan_event_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    location_scan_event_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    reservation_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    confirmation_status: Mapped[str] = mapped_column(String(30), nullable=False, default="CONFIRMED")
    confirmed_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    confirmed_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    evidence_file_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    observation: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_placement_qty_positive"),
        CheckConstraint("base_quantity > 0", name="ck_placement_base_qty_positive"),
        Index("ix_placement_location_product", "location_id", "source_allocation_id"),
    )


# =============================================================================
# 18. PutawayLocationOverride
# =============================================================================
class PutawayLocationOverrideModel(Base):
    __tablename__ = "putaway_location_overrides"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    recommended_location_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    selected_location_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    recommendation_run_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    recommended_score: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False)
    selected_score: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    approved_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    step_up_assurance_summary: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


# =============================================================================
# 19. PutawayTaskException
# =============================================================================
class PutawayTaskExceptionModel(Base):
    __tablename__ = "putaway_task_exceptions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    exception_type: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    product_scan_event_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    location_scan_event_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    location_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    quantity: Mapped[Decimal | None] = mapped_column(sa.Numeric(38, 18))
    unit_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_file_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="OPEN", index=True)
    detected_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    resolved_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    resolved_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    resolution: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


# =============================================================================
# 20. PutawayTaskPause
# =============================================================================
class PutawayTaskPauseModel(Base):
    __tablename__ = "putaway_task_pauses"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    pause_reason: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    paused_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    paused_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    resumed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


# =============================================================================
# 21. OperationalInventoryPlacement
# =============================================================================
class OperationalInventoryPlacementModel(Base):
    __tablename__ = "operational_inventory_placements"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    warehouse_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    location_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    source_allocation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    putaway_order_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    putaway_task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    placement_confirmation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    product_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    product_version_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False)
    unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    base_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False)
    quality_release_hash: Mapped[str | None] = mapped_column(String(64))
    observed_lot_references: Mapped[list | None] = mapped_column(JSONB, default=list)
    observed_serial_references: Mapped[list | None] = mapped_column(JSONB, default=list)
    expiration_observations: Mapped[list | None] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="PLACED_PENDING_MOVEMENT_LEDGER")
    placed_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    placed_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_operational_placement_qty"),
        CheckConstraint("base_quantity > 0", name="ck_operational_placement_base_qty"),
        Index("ix_operational_placement_location_product", "location_id", "product_id"),
    )


# =============================================================================
# 22. PutawayLocationPlacementProjection
# =============================================================================
class PutawayLocationPlacementProjectionModel(Base):
    __tablename__ = "putaway_location_placement_projection"

    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    warehouse_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    location_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    product_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False, default=Decimal("0"))
    unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    base_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(38, 18), nullable=False, default=Decimal("0"))
    placement_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    active_reservation_value: Mapped[Decimal] = mapped_column(sa.Numeric(14, 4), nullable=False, default=Decimal("0"))
    operational_capacity_used: Mapped[Decimal] = mapped_column(sa.Numeric(14, 4), nullable=False, default=Decimal("0"))
    operational_capacity_free: Mapped[Decimal] = mapped_column(sa.Numeric(14, 4), nullable=False, default=Decimal("0"))
    data_quality_status: Mapped[str] = mapped_column(String(30), nullable=False, default="MISSING_BASELINE")
    last_putaway_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    calculated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    projection_version: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)

    __table_args__ = (
        sa.PrimaryKeyConstraint("organization_id", "warehouse_id", "location_id", "product_id"),
    )
