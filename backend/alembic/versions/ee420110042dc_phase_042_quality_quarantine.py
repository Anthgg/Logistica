"""Phase 042 — Quality Quarantine and Release.

Revision ID: ee420110042dc
Revises: dd500110041dc
Create Date: 2026-08-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "ee420110042dc"
down_revision = "dd500110041dc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. inbound_inventory_disposition_allocations
    op.create_table(
        "inbound_inventory_disposition_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("inbound_receipt_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("inbound_receipt_revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inbound_received_line_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("expected_line_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("purchase_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("purchase_order_line_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("supplier_business_partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("product_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sku_snapshot", sa.String(120), nullable=True),
        sa.Column("product_name_snapshot", sa.String(500), nullable=True),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("source_quantity", sa.Numeric(38, 18), nullable=True),
        sa.Column("source_unit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_base_quantity", sa.Numeric(38, 18), nullable=True),
        sa.Column("allocation_status", sa.String(50), nullable=False, server_default="PENDING_QUALITY_ASSESSMENT"),
        sa.Column("availability_class", sa.String(50), nullable=False, server_default="UNKNOWN"),
        sa.Column("quality_status", sa.String(50), nullable=False, server_default="NOT_ASSESSED"),
        sa.Column("parent_allocation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("root_allocation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("split_sequence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("lot_observation_ids", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("serial_observation_ids", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("expiration_observation_ids", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("difference_case_ids", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("quarantine_case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("quality_inspection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("quality_decision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("physical_quarantine_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("released_for_putaway_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
        sa.CheckConstraint("quantity > 0", name="ck_disposition_alloc_qty_positive"),
        sa.CheckConstraint("base_quantity > 0", name="ck_disposition_alloc_base_qty_positive"),
        sa.CheckConstraint("row_version >= 1", name="ck_disposition_alloc_row_version"),
    )
    op.create_index("ix_disp_alloc_receipt_line", "inbound_inventory_disposition_allocations", ["inbound_receipt_id", "inbound_received_line_id"])

    # 2. inventory_disposition_splits
    op.create_table(
        "inventory_disposition_splits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_allocation_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("split_reason", sa.String(60), nullable=False),
        sa.Column("original_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("original_base_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("first_child_allocation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("second_child_allocation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("content_hash", sa.String(64), nullable=True),
    )

    # 3. quality_quarantine_cases
    op.create_table(
        "quality_quarantine_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("quarantine_code", sa.String(80), nullable=False),
        sa.Column("normalized_quarantine_code", sa.String(80), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("source_reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("inbound_receipt_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("difference_case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("product_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="DRAFT"),
        sa.Column("severity", sa.String(20), nullable=False, server_default="LOW"),
        sa.Column("quarantine_reason", sa.String(300), nullable=True),
        sa.Column("reason_description", sa.Text, nullable=True),
        sa.Column("active_inspection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("quality_result", sa.String(50), nullable=True),
        sa.Column("quality_decision_status", sa.String(50), nullable=False, server_default="NONE"),
        sa.Column("release_status", sa.String(50), nullable=False, server_default="NONE"),
        sa.Column("physical_segregation_status", sa.String(50), nullable=False, server_default="NOT_REQUIRED"),
        sa.Column("quarantine_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("responsible_quality_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_reviewer_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("active_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("current_revision_number", sa.Integer, nullable=False, server_default="0"),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opened_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
        sa.UniqueConstraint("organization_id", "normalized_quarantine_code", name="uq_quarantine_code"),
        sa.CheckConstraint("row_version >= 1", name="ck_quarantine_row_version"),
    )
    op.create_index("ix_quarantine_status", "quality_quarantine_cases", ["status"])
    op.create_index("ix_quarantine_severity", "quality_quarantine_cases", ["severity"])
    op.create_index("ix_quarantine_opened", "quality_quarantine_cases", ["opened_at"])

    # 4. quality_quarantine_case_revisions
    op.create_table(
        "quality_quarantine_case_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("quarantine_case_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("revision_number", sa.Integer, nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="EDITABLE"),
        sa.Column("source_snapshot", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("inspection_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("decision_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("release_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_from_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("change_reason", sa.Text, nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("quarantine_case_id", "revision_number", name="uq_quarantine_revision"),
    )

    # 5. quarantine_zone_configurations
    op.create_table(
        "quarantine_zone_configurations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("warehouse_location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("allowed_product_categories", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("temperature_capabilities", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("hazardous_declared_capable", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("maximum_capacity_reference", sa.Numeric(38, 18), nullable=True),
        sa.Column("capacity_unit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("instructions", sa.Text, nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
        sa.UniqueConstraint("organization_id", "code", name="uq_quarantine_zone_code"),
        sa.CheckConstraint("row_version >= 1", name="ck_quarantine_zone_row_version"),
    )

    # 6. quarantine_placement_confirmations
    op.create_table(
        "quarantine_placement_confirmations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("quarantine_case_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("allocation_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("quarantine_zone_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("placement_status", sa.String(40), nullable=False, server_default="PENDING"),
        sa.Column("scanned_location_code", sa.String(50), nullable=True),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("confirmed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("observation", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 7. quality_inspections
    op.create_table(
        "quality_inspections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inspection_code", sa.String(80), nullable=False),
        sa.Column("quarantine_case_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("allocation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inbound_receipt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("difference_case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("product_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("plan_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("plan_resolution_hash", sa.String(64), nullable=True),
        sa.Column("inspection_snapshot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="CREATED"),
        sa.Column("overall_result", sa.String(50), nullable=False, server_default="NOT_CALCULATED"),
        sa.Column("sample_size", sa.Integer, nullable=True),
        sa.Column("sample_unit", sa.String(30), nullable=True),
        sa.Column("required_control_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completed_control_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed_control_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("warning_control_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("evidence_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
        sa.UniqueConstraint("organization_id", "inspection_code", name="uq_inspection_code"),
        sa.CheckConstraint("row_version >= 1", name="ck_inspection_row_version"),
    )
    op.create_index("ix_inspection_product", "quality_inspections", ["product_id"])
    op.create_index("ix_inspection_status", "quality_inspections", ["status"])
    op.create_index("ix_inspection_result", "quality_inspections", ["overall_result"])

    # 8. quality_inspection_snapshots
    op.create_table(
        "quality_inspection_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("inspection_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("plan_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("plan_version_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("resolution_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("product_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("receipt_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("difference_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("allocation_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("quantity_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("lot_observations_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("serial_observations_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("expiration_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("controls_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("tolerances_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("sampling_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("certificates_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("evidence_requirements_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("instructions_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("responsibilities_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("applicability_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 9. quality_inspection_controls
    op.create_table(
        "quality_inspection_controls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("inspection_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("source_control_definition_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("control_code", sa.String(80), nullable=False),
        sa.Column("name_snapshot", sa.String(300), nullable=False),
        sa.Column("description_snapshot", sa.Text, nullable=True),
        sa.Column("control_type", sa.String(60), nullable=False, index=True),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("required", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("blocking_on_fail", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("result_value_type", sa.String(30), nullable=True),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tolerance_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("evidence_requirements_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("instructions_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("applicability_result", sa.String(30), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="NOT_STARTED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("row_version", sa.Integer, nullable=False, server_default="1"),
        sa.CheckConstraint("order_index >= 0", name="ck_control_order_index"),
    )
    op.create_index("ix_control_inspection", "quality_inspection_controls", ["inspection_id"])
    op.create_index("ix_control_status", "quality_inspection_controls", ["status"])

    # 10. quality_inspection_control_results
    op.create_table(
        "quality_inspection_control_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("inspection_control_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("result_status", sa.String(40), nullable=False),
        sa.Column("boolean_value", sa.Boolean, nullable=True),
        sa.Column("decimal_value", sa.Numeric(38, 18), nullable=True),
        sa.Column("integer_value", sa.Integer, nullable=True),
        sa.Column("text_value", sa.Text, nullable=True),
        sa.Column("date_value", sa.DateTime(timezone=True), nullable=True),
        sa.Column("option_value", sa.String(200), nullable=True),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tolerance_evaluation", postgresql.JSONB, nullable=True),
        sa.Column("observation", sa.Text, nullable=True),
        sa.Column("evidence_complete", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("measured_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("superseded_by_result_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # 11. quality_measurements
    op.create_table(
        "quality_measurements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("inspection_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("inspection_control_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("measurement_type", sa.String(40), nullable=False),
        sa.Column("measured_value", sa.Numeric(38, 18), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("normalized_value", sa.Numeric(38, 18), nullable=True),
        sa.Column("normalized_unit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("conversion_rule_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tolerance_result", sa.String(40), nullable=True),
        sa.Column("device_reference", sa.String(200), nullable=True),
        sa.Column("calibration_reference", sa.String(200), nullable=True),
        sa.Column("sample_reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("measured_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_measurement_inspection", "quality_measurements", ["inspection_id"])
    op.create_index("ix_measurement_type", "quality_measurements", ["measurement_type"])

    # 12. quality_inspection_sample_sets
    op.create_table(
        "quality_inspection_sample_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("inspection_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("source_sampling_plan_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sampling_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("population_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("population_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("required_sample_size", sa.Integer, nullable=False),
        sa.Column("sample_unit", sa.String(30), nullable=True),
        sa.Column("selection_method", sa.String(40), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 13. quality_inspection_sample_references
    op.create_table(
        "quality_inspection_sample_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sample_set_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("sample_number", sa.Integer, nullable=False),
        sa.Column("source_reference_type", sa.String(40), nullable=False),
        sa.Column("inbound_received_line_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lot_observation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("serial_observation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("package_ordinal", sa.Integer, nullable=True),
        sa.Column("operator_reference", sa.String(200), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("selected_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 14. quality_certificate_reviews
    op.create_table(
        "quality_certificate_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("inspection_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("certificate_requirement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("requirement_code", sa.String(80), nullable=False),
        sa.Column("document_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("document_type_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("review_status", sa.String(40), nullable=False),
        sa.Column("issuer_observed", sa.String(300), nullable=True),
        sa.Column("issue_date_observed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expiration_date_observed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reference_number_observed", sa.String(200), nullable=True),
        sa.Column("metadata_match_status", sa.String(40), nullable=True),
        sa.Column("file_status", sa.String(40), nullable=True),
        sa.Column("observation", sa.Text, nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 15. quality_inspection_evidence_links
    op.create_table(
        "quality_inspection_evidence_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("inspection_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("inspection_control_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("file_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("evidence_type", sa.String(40), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("classification", sa.String(40), nullable=False, server_default="STANDARD"),
        sa.Column("linked_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 16. quality_disposition_decisions
    op.create_table(
        "quality_disposition_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("quarantine_case_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("inspection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("allocation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision_type", sa.String(60), nullable=False),
        sa.Column("decision_status", sa.String(40), nullable=False, server_default="PROPOSED"),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("reason_code", sa.String(60), nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("inspection_result_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("evidence_manifest_hash", sa.String(64), nullable=True),
        sa.Column("policy_version", sa.String(60), nullable=True),
        sa.Column("proposed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("proposed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("supersedes_decision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 17. quality_decision_approvals
    op.create_table(
        "quality_decision_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("approval_level", sa.Integer, nullable=False, server_default="1"),
        sa.Column("decision", sa.String(40), nullable=False),
        sa.Column("approver_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approver_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("policy_version", sa.String(60), nullable=True),
        sa.Column("step_up_assurance_summary", postgresql.JSONB, nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 18. quarantine_release_authorizations
    op.create_table(
        "quarantine_release_authorizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("quarantine_case_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("allocation_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("quality_decision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("release_type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="REQUESTED"),
        sa.Column("release_reason", sa.Text, nullable=True),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("step_up_assurance_summary", postgresql.JSONB, nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_release_case", "quarantine_release_authorizations", ["quarantine_case_id"])
    op.create_index("ix_release_allocation", "quarantine_release_authorizations", ["allocation_id"])
    op.create_index("ix_release_status", "quarantine_release_authorizations", ["status"])

    # 19. quarantine_rejection_authorizations
    op.create_table(
        "quarantine_rejection_authorizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("quarantine_case_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("allocation_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("quality_decision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rejection_type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("reason_code", sa.String(60), nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="REQUESTED"),
        sa.Column("future_disposition_recommendation", sa.String(60), nullable=True),
        sa.Column("evidence_manifest_hash", sa.String(64), nullable=True),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_rejection_case", "quarantine_rejection_authorizations", ["quarantine_case_id"])
    op.create_index("ix_rejection_allocation", "quarantine_rejection_authorizations", ["allocation_id"])
    op.create_index("ix_rejection_status", "quarantine_rejection_authorizations", ["status"])

    # 20. quality_reinspection_requests
    op.create_table(
        "quality_reinspection_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("quarantine_case_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("previous_inspection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("required_controls", postgresql.JSONB, nullable=True),
        sa.Column("additional_evidence_required", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("new_inspection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="REQUESTED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 21. quality_disposition_events
    op.create_table(
        "quality_disposition_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quarantine_case_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("allocation_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("inspection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sequence_number", sa.Integer, nullable=False),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=True),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("base_quantity", sa.Numeric(38, 18), nullable=True),
        sa.Column("previous_status", sa.String(50), nullable=True),
        sa.Column("new_status", sa.String(50), nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("previous_event_hash", sa.String(64), nullable=True),
        sa.Column("event_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("quarantine_case_id", "sequence_number", name="uq_disposition_event_seq"),
    )
    op.create_index("ix_disposition_event_case", "quality_disposition_events", ["quarantine_case_id"])
    op.create_index("ix_disposition_event_allocation", "quality_disposition_events", ["allocation_id"])
    op.create_index("ix_disposition_event_type", "quality_disposition_events", ["event_type"])

    # 22. inbound_quality_availability_projection
    op.create_table(
        "inbound_quality_availability_projection",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inbound_receipt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("allocation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("availability_class", sa.String(50), nullable=False),
        sa.Column("quality_status", sa.String(50), nullable=False),
        sa.Column("quarantine_case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("inspection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("physical_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("released_for_putaway_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_quality_status", sa.String(30), nullable=False, server_default="PARTIAL"),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("projection_version", sa.Integer, nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("organization_id", "warehouse_id", "inbound_receipt_id", "product_id", "allocation_id"),
    )
    op.create_index("ix_projection_warehouse", "inbound_quality_availability_projection", ["warehouse_id"])
    op.create_index("ix_projection_product", "inbound_quality_availability_projection", ["product_id"])
    op.create_index("ix_projection_availability", "inbound_quality_availability_projection", ["availability_class"])


def downgrade() -> None:
    tables = [
        "inbound_quality_availability_projection",
        "quality_disposition_events",
        "quality_reinspection_requests",
        "quarantine_rejection_authorizations",
        "quarantine_release_authorizations",
        "quality_decision_approvals",
        "quality_disposition_decisions",
        "quality_inspection_evidence_links",
        "quality_certificate_reviews",
        "quality_inspection_sample_references",
        "quality_inspection_sample_sets",
        "quality_measurements",
        "quality_inspection_control_results",
        "quality_inspection_controls",
        "quality_inspection_snapshots",
        "quality_inspections",
        "quarantine_placement_confirmations",
        "quarantine_zone_configurations",
        "quality_quarantine_case_revisions",
        "quality_quarantine_cases",
        "inventory_disposition_splits",
        "inbound_inventory_disposition_allocations",
    ]
    for t in tables:
        op.drop_table(t)
