"""Phase 043 — Putaway (22 tables).

Revision ID: ff430110043dc
Revises: ee420110042dc
Create Date: 2026-08-02 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "ff430110043dc"
down_revision: Union[str, Sequence[str], None] = "ee420110042dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. putaway_policies
    op.create_table(
        "putaway_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("normalized_code", sa.String(50), nullable=False, index=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT", index=True),
        sa.Column("active_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
        sa.UniqueConstraint("organization_id", "normalized_code", name="uq_putaway_policies_org_code"),
        sa.CheckConstraint("row_version >= 1", name="ck_putaway_policies_row_version"),
    )

    # 2. putaway_policy_versions
    op.create_table(
        "putaway_policy_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("putaway_policies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_to", sa.DateTime(timezone=True)),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True)),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True)),
        sa.Column("product_category_id", postgresql.UUID(as_uuid=True)),
        sa.Column("product_id", postgresql.UUID(as_uuid=True)),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("capacity_weight", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("rotation_weight", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("picking_proximity_weight", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("consolidation_weight", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("fragmentation_penalty_weight", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("travel_cost_weight", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("manual_override_allowed", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("partial_putaway_allowed", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("split_destination_allowed", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("reservation_expiration_minutes", sa.Integer, nullable=False, server_default="30"),
        sa.Column("maximum_candidate_count", sa.Integer, nullable=False, server_default="50"),
        sa.Column("minimum_score", sa.Numeric(5, 2)),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("validated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("activated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("activated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("policy_id", "version_number", name="uq_putaway_policy_versions_policy_version"),
    )

    # 3. storage_compatibility_rules
    op.create_table(
        "storage_compatibility_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("policy_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("putaway_policy_versions.id", ondelete="SET NULL"), index=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True)),
        sa.Column("location_type", sa.String(30)),
        sa.Column("product_id", postgresql.UUID(as_uuid=True)),
        sa.Column("product_category_id", postgresql.UUID(as_uuid=True)),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("action", sa.String(20), nullable=False, server_default="ALLOW"),
        sa.Column("required_value", postgresql.JSONB),
        sa.Column("severity", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("reason", sa.Text),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_to", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Index("ix_storage_compat_warehouse_type", "warehouse_id", "rule_type"),
    )

    # 4. warehouse_location_capacity_profiles
    op.create_table(
        "warehouse_location_capacity_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("warehouse_location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouse_locations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("capacity_type", sa.String(30), nullable=False),
        sa.Column("maximum_value", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("safety_margin_value", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("reservation_limit_value", sa.Numeric(14, 4)),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_to", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
        sa.CheckConstraint("maximum_value > 0", name="ck_capacity_profiles_max_positive"),
    )

    # 5. putaway_location_capacity_projection
    op.create_table(
        "putaway_location_capacity_projection",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("capacity_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("capacity_type", sa.String(30), nullable=False),
        sa.Column("maximum_value", sa.Numeric(14, 4), nullable=False),
        sa.Column("safety_margin_value", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("operational_occupied_value", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("active_reserved_value", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("projected_free_value", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("data_quality_status", sa.String(30), nullable=False, server_default="MISSING_BASELINE"),
        sa.Column("last_placement_at", sa.DateTime(timezone=True)),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("projection_version", sa.Integer, nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("organization_id", "warehouse_id", "location_id", "capacity_profile_id"),
    )

    # 6. warehouse_location_proximity_profiles
    op.create_table(
        "warehouse_location_proximity_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("source_location_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("target_zone_id", postgresql.UUID(as_uuid=True)),
        sa.Column("target_location_id", postgresql.UUID(as_uuid=True)),
        sa.Column("metric_type", sa.String(40), nullable=False),
        sa.Column("metric_value", sa.Numeric(14, 4), nullable=False),
        sa.Column("metric_unit", sa.String(20), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False, server_default="MANUAL_MEASUREMENT"),
        sa.Column("measured_at", sa.DateTime(timezone=True)),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_to", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Index("ix_proximity_source_target", "source_location_id", "target_zone_id"),
    )

    # 7. putaway_recommendation_runs
    op.create_table(
        "putaway_recommendation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("source_allocation_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("policy_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="CREATED", index=True),
        sa.Column("requested_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("requested_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_base_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("candidate_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("eligible_candidate_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("source_snapshot_hash", sa.String(64)),
        sa.Column("input_hash", sa.String(64)),
        sa.Column("scoring_version", sa.String(20)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 8. putaway_location_candidates
    op.create_table(
        "putaway_location_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("recommendation_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("putaway_recommendation_runs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("rank", sa.Integer, nullable=False),
        sa.Column("compatible", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("capacity_available", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("capacity_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("rotation_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("picking_proximity_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("consolidation_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("fragmentation_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("travel_cost_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("penalty_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("total_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("capacity_snapshot", postgresql.JSONB),
        sa.Column("compatibility_snapshot", postgresql.JSONB),
        sa.Column("proximity_snapshot", postgresql.JSONB),
        sa.Column("rotation_snapshot", postgresql.JSONB),
        sa.Column("explanation", postgresql.JSONB),
        sa.Column("status", sa.String(20), nullable=False, server_default="CANDIDATE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Index("ix_candidate_total_score", "recommendation_run_id", "total_score"),
    )

    # 9. putaway_orders
    op.create_table(
        "putaway_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("order_code", sa.String(80), nullable=False),
        sa.Column("normalized_order_code", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT", index=True),
        sa.Column("source_type", sa.String(30), nullable=False, server_default="QUALITY_RELEASE"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("task_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completed_task_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("exception_task_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("document_instance_id", postgresql.UUID(as_uuid=True)),
        sa.Column("issued_at", sa.DateTime(timezone=True)),
        sa.Column("issued_by", postgresql.UUID(as_uuid=True)),
        sa.Column("assigned_team_id", postgresql.UUID(as_uuid=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("cancellation_reason", sa.Text),
        sa.Column("active_revision_id", postgresql.UUID(as_uuid=True)),
        sa.Column("current_revision_number", sa.Integer, nullable=False, server_default="0"),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
        sa.UniqueConstraint("organization_id", "normalized_order_code", name="uq_putaway_orders_org_code"),
        sa.CheckConstraint("row_version >= 1", name="ck_putaway_orders_row_version"),
    )

    # 10. putaway_order_revisions
    op.create_table(
        "putaway_order_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("putaway_order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("putaway_orders.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("revision_number", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="EDITABLE"),
        sa.Column("source_allocations_snapshot", postgresql.JSONB),
        sa.Column("recommendation_snapshot", postgresql.JSONB),
        sa.Column("tasks_snapshot", postgresql.JSONB),
        sa.Column("reservation_snapshot", postgresql.JSONB),
        sa.Column("document_snapshot", postgresql.JSONB),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("created_from_revision_id", postgresql.UUID(as_uuid=True)),
        sa.Column("change_reason", sa.Text),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("frozen_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("putaway_order_id", "revision_number", name="uq_putaway_order_revisions_order_number"),
    )

    # 11. putaway_tasks
    op.create_table(
        "putaway_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("putaway_order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("putaway_orders.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("task_number", sa.String(50), nullable=False),
        sa.Column("source_allocation_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("recommendation_run_id", postgresql.UUID(as_uuid=True)),
        sa.Column("recommended_location_id", postgresql.UUID(as_uuid=True)),
        sa.Column("selected_location_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("source_stage_location_id", postgresql.UUID(as_uuid=True)),
        sa.Column("status", sa.String(40), nullable=False, server_default="CREATED", index=True),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("assignment_status", sa.String(20), nullable=False, server_default="UNASSIGNED"),
        sa.Column("assigned_user_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("assigned_team_id", postgresql.UUID(as_uuid=True)),
        sa.Column("assigned_at", sa.DateTime(timezone=True)),
        sa.Column("required_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("required_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("required_base_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("placed_quantity", sa.Numeric(38, 18), nullable=False, server_default="0"),
        sa.Column("placed_unit_id", postgresql.UUID(as_uuid=True)),
        sa.Column("placed_base_quantity", sa.Numeric(38, 18), nullable=False, server_default="0"),
        sa.Column("remaining_quantity", sa.Numeric(38, 18), nullable=False, server_default="0"),
        sa.Column("remaining_base_quantity", sa.Numeric(38, 18), nullable=False, server_default="0"),
        sa.Column("scan_policy", sa.String(40), nullable=False, server_default="PRODUCT_THEN_LOCATION"),
        sa.Column("expected_product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column("quality_release_hash", sa.String(64)),
        sa.Column("location_reservation_id", postgresql.UUID(as_uuid=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("paused_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("exception_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
        sa.UniqueConstraint("putaway_order_id", "task_number", name="uq_putaway_tasks_order_number"),
        sa.CheckConstraint("required_quantity > 0", name="ck_putaway_tasks_req_qty_positive"),
        sa.CheckConstraint("row_version >= 1", name="ck_putaway_tasks_row_version"),
    )

    # 12. putaway_task_destinations
    op.create_table(
        "putaway_task_destinations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_number", sa.Integer, nullable=False),
        sa.Column("recommended_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("reservation_id", postgresql.UUID(as_uuid=True)),
        sa.Column("status", sa.String(30), nullable=False, server_default="PLANNED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 13. putaway_task_assignments
    op.create_table(
        "putaway_task_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("assignment_type", sa.String(20), nullable=False, server_default="USER"),
        sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("team_id", postgresql.UUID(as_uuid=True)),
        sa.Column("status", sa.String(20), nullable=False, server_default="ASSIGNED"),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("declined_at", sa.DateTime(timezone=True)),
        sa.Column("decline_reason", sa.Text),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 14. putaway_location_reservations
    op.create_table(
        "putaway_location_reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source_allocation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("capacity_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reserved_value", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reserved_base_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE", index=True),
        sa.Column("reserved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True)),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("cancellation_reason", sa.Text),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Index("ix_reservation_expires", "status", "expires_at"),
    )

    # 15. putaway_execution_sessions
    op.create_table(
        "putaway_execution_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("operator_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_reference_hash", sa.String(64)),
        sa.Column("scanner_type", sa.String(30), nullable=False, server_default="HANDHELD_TERMINAL"),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("paused_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("client_session_reference", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
    )

    # 16. putaway_scan_events
    op.create_table(
        "putaway_scan_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("execution_session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("putaway_execution_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("client_scan_id", sa.String(200), nullable=False),
        sa.Column("server_sequence", sa.Integer, nullable=False),
        sa.Column("scan_type", sa.String(30), nullable=False),
        sa.Column("raw_code_encrypted", sa.Text),
        sa.Column("normalized_code", sa.String(200), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("symbology", sa.String(30)),
        sa.Column("resolution_status", sa.String(20), nullable=False, server_default="RECORDED"),
        sa.Column("resolved_product_id", postgresql.UUID(as_uuid=True)),
        sa.Column("resolved_location_id", postgresql.UUID(as_uuid=True)),
        sa.Column("validation_status", sa.String(30)),
        sa.Column("expected_value_hash", sa.String(64)),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("operator_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="RECORDED"),
        sa.Column("duplicate_of_event_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("execution_session_id", "client_scan_id", name="uq_putaway_scan_events_session_client"),
        sa.Index("ix_scan_event_code_hash", "code_hash"),
        sa.Index("ix_scan_event_type_received", "scan_type", "received_at"),
    )

    # 17. putaway_placement_confirmations
    op.create_table(
        "putaway_placement_confirmations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source_allocation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("product_scan_event_id", postgresql.UUID(as_uuid=True)),
        sa.Column("location_scan_event_id", postgresql.UUID(as_uuid=True)),
        sa.Column("reservation_id", postgresql.UUID(as_uuid=True)),
        sa.Column("confirmation_status", sa.String(30), nullable=False, server_default="CONFIRMED"),
        sa.Column("confirmed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("evidence_file_id", postgresql.UUID(as_uuid=True)),
        sa.Column("observation", sa.Text),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("quantity > 0", name="ck_placement_qty_positive"),
        sa.CheckConstraint("base_quantity > 0", name="ck_placement_base_qty_positive"),
        sa.Index("ix_placement_location_product", "location_id", "source_allocation_id"),
    )

    # 18. putaway_location_overrides
    op.create_table(
        "putaway_location_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("recommended_location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("selected_location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommended_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("selected_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("reason_code", sa.String(30), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True)),
        sa.Column("step_up_assurance_summary", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 19. putaway_task_exceptions
    op.create_table(
        "putaway_task_exceptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("exception_type", sa.String(40), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("product_scan_event_id", postgresql.UUID(as_uuid=True)),
        sa.Column("location_scan_event_id", postgresql.UUID(as_uuid=True)),
        sa.Column("location_id", postgresql.UUID(as_uuid=True)),
        sa.Column("quantity", sa.Numeric(38, 18)),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True)),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("evidence_file_ids", postgresql.JSONB, server_default="[]"),
        sa.Column("status", sa.String(30), nullable=False, server_default="OPEN", index=True),
        sa.Column("detected_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("resolution", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 20. putaway_task_pauses
    op.create_table(
        "putaway_task_pauses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("putaway_tasks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("pause_reason", sa.String(30), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("paused_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resumed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 21. operational_inventory_placements
    op.create_table(
        "operational_inventory_placements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("source_allocation_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("putaway_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("putaway_task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("placement_confirmation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("product_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("quality_release_hash", sa.String(64)),
        sa.Column("observed_lot_references", postgresql.JSONB, server_default="[]"),
        sa.Column("observed_serial_references", postgresql.JSONB, server_default="[]"),
        sa.Column("expiration_observations", postgresql.JSONB, server_default="[]"),
        sa.Column("status", sa.String(40), nullable=False, server_default="PLACED_PENDING_MOVEMENT_LEDGER"),
        sa.Column("placed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("placed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("quantity > 0", name="ck_operational_placement_qty"),
        sa.CheckConstraint("base_quantity > 0", name="ck_operational_placement_base_qty"),
        sa.Index("ix_operational_placement_location_product", "location_id", "product_id"),
    )

    # 22. putaway_location_placement_projection
    op.create_table(
        "putaway_location_placement_projection",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=False, server_default="0"),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_quantity", sa.Numeric(38, 18), nullable=False, server_default="0"),
        sa.Column("placement_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("active_reservation_value", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("operational_capacity_used", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("operational_capacity_free", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("data_quality_status", sa.String(30), nullable=False, server_default="MISSING_BASELINE"),
        sa.Column("last_putaway_at", sa.DateTime(timezone=True)),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("projection_version", sa.Integer, nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("organization_id", "warehouse_id", "location_id", "product_id"),
    )


def downgrade() -> None:
    tables_to_drop = [
        "putaway_location_placement_projection",
        "operational_inventory_placements",
        "putaway_task_pauses",
        "putaway_task_exceptions",
        "putaway_location_overrides",
        "putaway_placement_confirmations",
        "putaway_scan_events",
        "putaway_execution_sessions",
        "putaway_location_reservations",
        "putaway_task_assignments",
        "putaway_task_destinations",
        "putaway_tasks",
        "putaway_order_revisions",
        "putaway_orders",
        "putaway_location_candidates",
        "putaway_recommendation_runs",
        "warehouse_location_proximity_profiles",
        "putaway_location_capacity_projection",
        "warehouse_location_capacity_profiles",
        "storage_compatibility_rules",
        "putaway_policy_versions",
        "putaway_policies",
    ]
    for table in tables_to_drop:
        op.drop_table(table)
