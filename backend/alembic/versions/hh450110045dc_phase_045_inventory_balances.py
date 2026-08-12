"""Phase 045 — Inventory balances materialized projection tables.

Revision ID: hh450110045dc
Revises: gl440610044rb
Create Date: 2026-08-11 22:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "hh450110045dc"
down_revision: str | Sequence[str] | None = "gl440610044rb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. inventory_position_balances
    op.create_table(
        "inventory_position_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("warehouse_location_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("inventory_position_id", postgresql.UUID(as_uuid=True), unique=True, nullable=False, index=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("product_version_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("base_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=False, server_default="0", index=True),
        sa.Column("availability_state", sa.String(50), nullable=False, server_default="UNKNOWN", index=True),
        sa.Column("quality_state", sa.String(50), nullable=False, server_default="UNKNOWN", index=True),
        sa.Column("transit_state", sa.String(50), nullable=False, server_default="NOT_IN_TRANSIT", index=True),
        sa.Column("damage_state", sa.String(50), nullable=False, server_default="NORMAL", index=True),
        sa.Column("expiration_state", sa.String(50), nullable=False, server_default="NOT_APPLICABLE", index=True),
        sa.Column("ownership_type", sa.String(50), nullable=False, server_default="OWNED"),
        sa.Column("owner_business_partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tracking_reference_type", sa.String(50), nullable=True),
        sa.Column("tracking_reference_hash", sa.String(64), nullable=True),
        sa.Column("handling_unit_reference_hash", sa.String(64), nullable=True),
        sa.Column("dimension_key", sa.String(64), nullable=False, index=True),
        sa.Column("last_applied_ledger_partition_key", sa.String(120), nullable=False),
        sa.Column("last_applied_ledger_sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_applied_movement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_applied_movement_hash", sa.String(64), nullable=True),
        sa.Column("balance_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("data_quality_status", sa.String(50), nullable=False, server_default="PROJECTION_CURRENT"),
        sa.Column("reconciliation_status", sa.String(50), nullable=False, server_default="RECONCILED", index=True),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
    )

    # 2. inventory_balance_deltas
    op.create_table(
        "inventory_balance_deltas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("ledger_partition_key", sa.String(120), nullable=False, index=True),
        sa.Column("ledger_sequence", sa.Integer(), nullable=False, index=True),
        sa.Column("movement_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("movement_line_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("delta_type", sa.String(50), nullable=False),
        sa.Column("delta_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("base_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("movement_hash", sa.String(64), nullable=False),
        sa.Column("materialization_key", sa.String(128), unique=True, nullable=False),
        sa.Column("applied_status", sa.String(50), nullable=False, server_default="PENDING", index=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("balance_before", sa.Numeric(38, 18), nullable=True),
        sa.Column("balance_after", sa.Numeric(38, 18), nullable=True),
        sa.Column("consumer_version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 3. inventory_balance_projection_cursors
    op.create_table(
        "inventory_balance_projection_cursors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ledger_partition_key", sa.String(120), nullable=False, index=True),
        sa.Column("last_applied_sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_applied_movement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_applied_hash", sa.String(64), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="CURRENT", index=True),
        sa.Column("lag_movement_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lag_seconds", sa.Numeric(12, 3), nullable=False, server_default="0.000"),
        sa.Column("last_success_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(50), nullable=True),
        sa.Column("consumer_version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("organization_id", "ledger_partition_key", name="uq_cursor_org_partition"),
    )

    # 4. inventory_balance_formula_definitions
    op.create_table(
        "inventory_balance_formula_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("metric_code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("dimension_family", sa.String(50), nullable=False),
        sa.Column("aggregation_type", sa.String(50), nullable=False, server_default="SUM"),
        sa.Column("mutually_exclusive_group", sa.String(50), nullable=True),
        sa.Column("overlap_allowed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("active_version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 5. inventory_balance_formula_versions
    op.create_table(
        "inventory_balance_formula_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "formula_definition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inventory_balance_formula_definitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("expression_rules", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 6. inventory_balance_checkpoints
    op.create_table(
        "inventory_balance_checkpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("ledger_partition_key", sa.String(120), nullable=False, index=True),
        sa.Column("checkpoint_sequence", sa.Integer(), nullable=False),
        sa.Column("checkpoint_movement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("checkpoint_movement_hash", sa.String(64), nullable=False),
        sa.Column("balance_manifest_hash", sa.String(64), nullable=False),
        sa.Column("position_count", sa.Integer(), nullable=False),
        sa.Column("total_product_count", sa.Integer(), nullable=False),
        sa.Column("formula_version_set", sa.String(100), nullable=False, server_default="1.0.0"),
        sa.Column("projection_version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="VALID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("ledger_partition_key", "checkpoint_sequence", name="uq_balance_checkpoint_partition_seq"),
    )

    # 7. inventory_balance_rebuild_jobs
    op.create_table(
        "inventory_balance_rebuild_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("rebuild_mode", sa.String(50), nullable=False),
        sa.Column("target_warehouse_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_position_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_partition_key", sa.String(120), nullable=True),
        sa.Column("as_of_sequence", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING", index=True),
        sa.Column("positions_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("movements_replayed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("differences_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("initiated_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_up_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 8. inventory_balance_rebuild_differences
    op.create_table(
        "inventory_balance_rebuild_differences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "rebuild_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inventory_balance_rebuild_jobs.id"),
            nullable=False,
        ),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("current_projected_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("replayed_ledger_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("difference_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 9. inventory_balance_reconciliation_jobs
    op.create_table(
        "inventory_balance_reconciliation_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING", index=True),
        sa.Column("total_positions_audited", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_differences_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("initiated_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 10. inventory_balance_reconciliation_differences
    op.create_table(
        "inventory_balance_reconciliation_differences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "reconciliation_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inventory_balance_reconciliation_jobs.id"),
            nullable=False,
        ),
        sa.Column("difference_type", sa.String(50), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("projected_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("replay_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("difference_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expected_sequence", sa.Integer(), nullable=False),
        sa.Column("actual_sequence", sa.Integer(), nullable=False),
        sa.Column("resolution_status", sa.String(50), nullable=False, server_default="OPEN", index=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 11. inventory_balance_export_jobs
    op.create_table(
        "inventory_balance_export_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("format", sa.String(10), nullable=False),
        sa.Column("filter_params", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING"),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("inventory_balance_export_jobs")
    op.drop_table("inventory_balance_reconciliation_differences")
    op.drop_table("inventory_balance_reconciliation_jobs")
    op.drop_table("inventory_balance_rebuild_differences")
    op.drop_table("inventory_balance_rebuild_jobs")
    op.drop_table("inventory_balance_checkpoints")
    op.drop_table("inventory_balance_formula_versions")
    op.drop_table("inventory_balance_formula_definitions")
    op.drop_table("inventory_balance_projection_cursors")
    op.drop_table("inventory_balance_deltas")
    op.drop_table("inventory_position_balances")
