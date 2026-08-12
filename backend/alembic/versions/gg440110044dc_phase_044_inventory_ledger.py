"""Phase 044 — Inventory ledger (append-only book).

Revision ID: gg440110044dc
Revises: ff430110043dc
Create Date: 2026-08-02 00:00:00.000000
"""

from __future__ import annotations

import re
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import context, op

revision: str = "gg440110044dc"
down_revision: str | Sequence[str] | None = "ff430110043dc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _legacy_index_name(index_name: str) -> str | None:
    match = re.fullmatch(r"ix_inventory_movements_([A-Za-z0-9_]+)", index_name)
    if match is None:
        return None
    return f"ix_inventory_movements_legacy_{match.group(1)}"


def upgrade() -> None:
    # The pre-Phase-044 model used the same physical table name. Preserve it
    # verbatim before creating the append-only canonical ledger table.
    if not context.is_offline_mode():
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        table_names = set(inspector.get_table_names())
        if "inventory_movements" in table_names and "inventory_movements_legacy" not in table_names:
            legacy_columns = {
                column["name"] for column in inspector.get_columns("inventory_movements")
            }
            if {"previous_stock", "resulting_stock"} & legacy_columns and not {
                "ledger_sequence",
                "movement_hash",
            }.issubset(legacy_columns):
                op.rename_table("inventory_movements", "inventory_movements_legacy")

        # PostgreSQL keeps secondary index names when a table is renamed.
        # Move those schema-global names out of the canonical table namespace
        # before creating the Phase 044 inventory_movements replacement.
        inspector = sa.inspect(bind)
        if "inventory_movements_legacy" in set(inspector.get_table_names()):
            for index in inspector.get_indexes("inventory_movements_legacy"):
                current_name = index.get("name")
                legacy_name = (
                    _legacy_index_name(current_name) if current_name else None
                )
                if legacy_name:
                    op.execute(
                        sa.text(
                            f'ALTER INDEX IF EXISTS "{current_name}" '
                            f'RENAME TO "{legacy_name}"'
                        )
                    )

    # 1. inventory_ledger_partitions
    op.create_table(
        "inventory_ledger_partitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("partition_key", sa.String(120), nullable=False, index=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("fiscal_year", sa.Integer, nullable=True),
        sa.Column("current_sequence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_movement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_movement_hash", sa.String(64), nullable=True),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "organization_id", "partition_key", name="uq_inventory_ledger_partition_key"
        ),
        sa.CheckConstraint(
            "current_sequence >= 0", name="ck_inventory_ledger_partition_sequence_nonnegative"
        ),
    )

    # 2. inventory_positions
    op.create_table(
        "inventory_positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column(
            "warehouse_location_id", postgresql.UUID(as_uuid=True), nullable=True, index=True
        ),
        sa.Column("boundary_type", sa.String(40), nullable=False, index=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("product_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ownership_type", sa.String(30), nullable=False, server_default="OWNED"),
        sa.Column("owner_business_partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("availability_state", sa.String(30), nullable=False, server_default="UNKNOWN"),
        sa.Column("quality_state", sa.String(30), nullable=False, server_default="UNKNOWN"),
        sa.Column("transit_state", sa.String(30), nullable=False, server_default="NOT_IN_TRANSIT"),
        sa.Column("damage_state", sa.String(30), nullable=False, server_default="NORMAL"),
        sa.Column(
            "expiration_state", sa.String(30), nullable=False, server_default="NOT_APPLICABLE"
        ),
        sa.Column("tracking_reference_type", sa.String(30), nullable=True),
        sa.Column("tracking_reference_hash", sa.String(64), nullable=True),
        sa.Column("handling_unit_reference_hash", sa.String(64), nullable=True),
        sa.Column("dimension_key", sa.String(255), nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "organization_id", "dimension_key", name="uq_inventory_position_dimension_key"
        ),
    )

    # 3. inventory_external_boundaries
    op.create_table(
        "inventory_external_boundaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("boundary_kind", sa.String(40), nullable=False, index=True),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("normalized_code", sa.String(80), nullable=False, index=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("business_partner_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "organization_id", "normalized_code", name="uq_inventory_external_boundary_code"
        ),
    )

    # 4. inventory_movement_posting_requests
    op.create_table(
        "inventory_movement_posting_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("request_key", sa.String(128), nullable=False, index=True),
        sa.Column("source_system", sa.String(60), nullable=False),
        sa.Column(
            "source_module", sa.String(60), nullable=False, server_default="INVENTORY_LEDGER"
        ),
        sa.Column("source_event_type", sa.String(80), nullable=False),
        sa.Column("source_event_id", sa.String(120), nullable=False),
        sa.Column("source_event_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column(
            "payload", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("status", sa.String(30), nullable=False, server_default="RECEIVED", index=True),
        sa.Column("validation_result", postgresql.JSONB, nullable=True),
        sa.Column(
            "resulting_movement_id", postgresql.UUID(as_uuid=True), nullable=True, index=True
        ),
        sa.Column("failure_code", sa.String(80), nullable=True),
        sa.Column("failure_detail_safe", sa.String(500), nullable=True),
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("requested_by_service", sa.String(100), nullable=True),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
        sa.UniqueConstraint(
            "organization_id",
            "source_system",
            "source_event_type",
            "source_event_id",
            "source_event_version",
            name="uq_inventory_posting_request_source_event",
        ),
    )

    # 5. inventory_movements
    op.create_table(
        "inventory_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("warehouse_scope_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("movement_code", sa.String(80), nullable=False),
        sa.Column("normalized_movement_code", sa.String(80), nullable=False, index=True),
        sa.Column("ledger_partition_key", sa.String(120), nullable=False, index=True),
        sa.Column("ledger_sequence", sa.Integer, nullable=False, index=True),
        sa.Column("movement_type", sa.String(60), nullable=False, index=True),
        sa.Column("movement_family", sa.String(40), nullable=False, index=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="POSTED", index=True),
        sa.Column("source_system", sa.String(60), nullable=False),
        sa.Column("source_event_type", sa.String(80), nullable=False),
        sa.Column("source_event_id", sa.String(120), nullable=False, index=True),
        sa.Column("source_event_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("source_document_type", sa.String(40), nullable=True),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("source_document_code", sa.String(80), nullable=True, index=True),
        sa.Column("source_reference_snapshot", postgresql.JSONB, nullable=True),
        sa.Column(
            "posting_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column(
            "posted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
        sa.Column("posted_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("posted_by_service", sa.String(100), nullable=True),
        sa.Column("reason_code", sa.String(60), nullable=True),
        sa.Column("reason_description", sa.Text, nullable=True),
        sa.Column("line_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_base_quantity_reference", sa.Numeric(38, 18), nullable=True),
        sa.Column("currency_code", sa.String(3), nullable=True),
        sa.Column(
            "valuation_status", sa.String(30), nullable=False, server_default="NOT_APPLICABLE"
        ),
        sa.Column("previous_movement_hash", sa.String(64), nullable=True, index=True),
        sa.Column("movement_hash", sa.String(64), nullable=False, index=True),
        sa.Column(
            "canonicalization_version", sa.String(20), nullable=False, server_default="1.0.0"
        ),
        sa.Column("schema_version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column(
            "compensation_for_movement_id", postgresql.UUID(as_uuid=True), nullable=True, index=True
        ),
        sa.Column(
            "compensated_by_movement_id", postgresql.UUID(as_uuid=True), nullable=True, index=True
        ),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "organization_id", "normalized_movement_code", name="uq_inventory_movement_code"
        ),
        sa.UniqueConstraint(
            "ledger_partition_key",
            "ledger_sequence",
            name="uq_inventory_movement_partition_sequence",
        ),
        sa.CheckConstraint("ledger_sequence >= 1", name="ck_inventory_movement_sequence_positive"),
        sa.CheckConstraint("line_count >= 0", name="ck_inventory_movement_line_count_nonnegative"),
    )

    # 6. inventory_movement_lines
    op.create_table(
        "inventory_movement_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "inventory_movement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inventory_movements.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("line_number", sa.Integer, nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("product_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "product_snapshot",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("base_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversion_rule_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("conversion_snapshot", postgresql.JSONB, nullable=True),
        sa.Column(
            "source_position_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inventory_positions.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "destination_position_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inventory_positions.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
        sa.Column("source_position_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("destination_position_snapshot", postgresql.JSONB, nullable=True),
        sa.Column(
            "source_external_boundary_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inventory_external_boundaries.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "destination_external_boundary_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inventory_external_boundaries.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
        sa.Column("source_external_boundary_kind", sa.String(40), nullable=True),
        sa.Column("destination_external_boundary_kind", sa.String(40), nullable=True),
        sa.Column("quantity_direction", sa.String(30), nullable=False),
        sa.Column("reason_code", sa.String(60), nullable=True),
        sa.Column("traceability_reference_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("cost_reference_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("metadata_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "inventory_movement_id", "line_number", name="uq_inventory_movement_line_number"
        ),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_movement_line_quantity_positive"),
        sa.CheckConstraint(
            "base_quantity > 0", name="ck_inventory_movement_line_base_quantity_positive"
        ),
        sa.CheckConstraint(
            "(source_position_id IS NOT NULL AND source_external_boundary_id IS NULL AND source_external_boundary_kind IS NULL) OR "
            "(source_position_id IS NULL AND (source_external_boundary_id IS NOT NULL OR source_external_boundary_kind IS NOT NULL))",
            name="ck_inventory_movement_line_source_boundary",
        ),
        sa.CheckConstraint(
            "(destination_position_id IS NOT NULL AND destination_external_boundary_id IS NULL AND destination_external_boundary_kind IS NULL) OR "
            "(destination_position_id IS NULL AND (destination_external_boundary_id IS NOT NULL OR destination_external_boundary_kind IS NOT NULL))",
            name="ck_inventory_movement_line_destination_boundary",
        ),
    )

    # 7. inventory_movement_source_references
    op.create_table(
        "inventory_movement_source_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "movement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inventory_movements.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("source_system", sa.String(60), nullable=False),
        sa.Column("source_module", sa.String(60), nullable=False),
        sa.Column("source_event_type", sa.String(80), nullable=False),
        sa.Column("source_event_id", sa.String(120), nullable=False, index=True),
        sa.Column("source_event_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("source_document_type", sa.String(40), nullable=True),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("source_document_code", sa.String(80), nullable=True),
        sa.Column("source_entity_type", sa.String(60), nullable=False),
        sa.Column("source_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("source_occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("adapter_name", sa.String(80), nullable=False),
        sa.Column("adapter_version", sa.String(20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "ix_inventory_movement_source_event",
        "inventory_movement_source_references",
        ["source_system", "source_event_type", "source_event_id"],
    )

    # 8. inventory_movement_compensation_requests
    op.create_table(
        "inventory_movement_compensation_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "original_movement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inventory_movements.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("reason_code", sa.String(60), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column(
            "evidence_file_ids",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("status", sa.String(30), nullable=False, server_default="REQUESTED", index=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column(
            "resulting_movement_id", postgresql.UUID(as_uuid=True), nullable=True, index=True
        ),
        sa.Column("risk_level", sa.String(20), nullable=False, server_default="HIGH"),
        sa.Column("separation_of_duties_check", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
        sa.CheckConstraint(
            "row_version >= 1", name="ck_inventory_compensation_request_row_version"
        ),
    )

    # 9. inventory_ledger_checkpoints
    op.create_table(
        "inventory_ledger_checkpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("ledger_partition_key", sa.String(120), nullable=False, index=True),
        sa.Column("from_sequence", sa.Integer, nullable=False),
        sa.Column("to_sequence", sa.Integer, nullable=False),
        sa.Column("movement_count", sa.Integer, nullable=False),
        sa.Column("first_hash", sa.String(64), nullable=True),
        sa.Column("last_hash", sa.String(64), nullable=True),
        sa.Column("manifest_hash", sa.String(64), nullable=False),
        sa.Column(
            "verification_status",
            sa.String(20),
            nullable=False,
            server_default="VERIFYING",
            index=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by_service", sa.String(100), nullable=True),
        sa.Column("algorithm_version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "ledger_partition_key",
            "from_sequence",
            "to_sequence",
            name="uq_inventory_ledger_checkpoint_range",
        ),
        sa.CheckConstraint("from_sequence >= 1", name="ck_inventory_ledger_checkpoint_from_seq"),
        sa.CheckConstraint(
            "to_sequence >= from_sequence",
            name="ck_inventory_ledger_checkpoint_range_order",
        ),
        sa.CheckConstraint(
            "movement_count >= 0", name="ck_inventory_ledger_checkpoint_count_nonneg"
        ),
    )

    # 10. inventory_ledger_reconciliation_jobs
    op.create_table(
        "inventory_ledger_reconciliation_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("scope", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(20), nullable=False, server_default="QUEUED", index=True),
        sa.Column("triggered_by", sa.String(30), nullable=False, server_default="SCHEDULED"),
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_events_seen", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_movements_seen", sa.Integer, nullable=False, server_default="0"),
        sa.Column("issue_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("summary", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    # 11. inventory_ledger_reconciliation_results
    op.create_table(
        "inventory_ledger_reconciliation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inventory_ledger_reconciliation_jobs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("result_code", sa.String(60), nullable=False, index=True),
        sa.Column("source_system", sa.String(60), nullable=True),
        sa.Column("source_event_type", sa.String(80), nullable=True),
        sa.Column("source_event_id", sa.String(120), nullable=True, index=True),
        sa.Column("source_entity_type", sa.String(60), nullable=True),
        sa.Column("source_entity_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("movement_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("movement_code", sa.String(80), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column(
            "detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    # 12. inventory_kardex_export_jobs
    op.create_table(
        "inventory_kardex_export_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "filters", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("format", sa.String(20), nullable=False, server_default="CSV"),
        sa.Column("timezone", sa.String(60), nullable=False, server_default="UTC"),
        sa.Column("status", sa.String(20), nullable=False, server_default="QUEUED", index=True),
        sa.Column("initial_sequence", sa.Integer, nullable=True),
        sa.Column("final_sequence", sa.Integer, nullable=True),
        sa.Column("row_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("manifest_hash", sa.String(64), nullable=True),
        sa.Column(
            "warnings", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column("integrity_status", sa.String(20), nullable=False, server_default="UNKNOWN"),
        sa.Column(
            "requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    # 13. inventory_ledger_outbox_events
    op.create_table(
        "inventory_ledger_outbox_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("aggregate_type", sa.String(60), nullable=False, index=True),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("event_type", sa.String(80), nullable=False, index=True),
        sa.Column("event_version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column(
            "payload", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("correlation_id", sa.String(120), nullable=True, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING", index=True),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_table("inventory_ledger_outbox_events")
    op.drop_table("inventory_kardex_export_jobs")
    op.drop_table("inventory_ledger_reconciliation_results")
    op.drop_table("inventory_ledger_reconciliation_jobs")
    op.drop_table("inventory_ledger_checkpoints")
    op.drop_table("inventory_movement_compensation_requests")
    op.drop_index(
        "ix_inventory_movement_source_event", table_name="inventory_movement_source_references"
    )
    op.drop_table("inventory_movement_source_references")
    op.drop_table("inventory_movement_lines")
    op.drop_table("inventory_movements")
    op.drop_table("inventory_movement_posting_requests")
    op.drop_table("inventory_external_boundaries")
    op.drop_table("inventory_positions")
    op.drop_table("inventory_ledger_partitions")
    if not context.is_offline_mode():
        inspector = sa.inspect(op.get_bind())
        table_names = set(inspector.get_table_names())
        if "inventory_movements_legacy" in table_names and "inventory_movements" not in table_names:
            op.rename_table("inventory_movements_legacy", "inventory_movements")
