"""Phase 041 — Quality Inspection Plans

Revision ID: dd500110041dc
Revises: bb400110040dc
Create Date: 2026-08-02 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "dd500110041dc"
down_revision: Union[str, Sequence[str], None] = "bb400110040dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    QTY = {"precision": 38, "scale": 18}

    op.create_table(
        "quality_inspection_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("plan_code", sa.String(80), nullable=False),
        sa.Column("plan_name", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("plan_family", sa.String(40), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("current_version_number", sa.Integer, nullable=False, server_default="0"),
        sa.Column("active_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_global", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("row_version", sa.Integer, nullable=False, server_default=sa.text("1")),
    )
    op.create_unique_constraint("uq_qip_org_code", "quality_inspection_plans", ["organization_id", "plan_code"])
    op.create_index("ix_qip_org", "quality_inspection_plans", ["organization_id"])
    op.create_index("ix_qip_family", "quality_inspection_plans", ["plan_family"])
    op.create_index("ix_qip_status", "quality_inspection_plans", ["status"])
    op.create_index("ix_qip_active_version", "quality_inspection_plans", ["active_version_id"])
    op.create_index("ix_qip_updated", "quality_inspection_plans", ["updated_at"])

    op.create_table(
        "quality_inspection_plan_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quality_inspection_plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("change_summary", sa.Text, nullable=True),
        sa.Column("plan_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("validation_errors", postgresql.JSONB, nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scheduled_activation_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("row_version", sa.Integer, nullable=False, server_default=sa.text("1")),
    )
    op.create_unique_constraint("uq_qip_version_number", "quality_inspection_plan_versions", ["plan_id", "version_number"])
    op.create_index("ix_qip_ver_plan", "quality_inspection_plan_versions", ["plan_id"])
    op.create_index("ix_qip_ver_status", "quality_inspection_plan_versions", ["status"])
    op.create_index("ix_qip_ver_number", "quality_inspection_plan_versions", ["version_number"])

    op.create_table(
        "quality_plan_scopes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quality_inspection_plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quality_inspection_plan_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("scope_type", sa.String(30), nullable=False),
        sa.Column("scope_product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scope_product_name", sa.String(300), nullable=True),
        sa.Column("scope_category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scope_category_name", sa.String(200), nullable=True),
        sa.Column("scope_warehouse_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scope_warehouse_name", sa.String(200), nullable=True),
        sa.Column("scope_branch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scope_branch_name", sa.String(200), nullable=True),
        sa.Column("resolution_specificity", sa.String(40), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_qip_scope_plan", "quality_plan_scopes", ["plan_id"])
    op.create_index("ix_qip_scope_product", "quality_plan_scopes", ["scope_product_id"])
    op.create_index("ix_qip_scope_category", "quality_plan_scopes", ["scope_category_id"])
    op.create_index("ix_qip_scope_warehouse", "quality_plan_scopes", ["scope_warehouse_id"])
    op.create_index("ix_qip_scope_branch", "quality_plan_scopes", ["scope_branch_id"])

    op.create_table(
        "quality_control_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quality_inspection_plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quality_inspection_plan_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("scope_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quality_plan_scopes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("control_type", sa.String(60), nullable=False),
        sa.Column("control_code", sa.String(80), nullable=False),
        sa.Column("control_name", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_mandatory", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_blocking", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("applies_to_all_units", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("applies_to_sample", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("configuration_json", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_qcd_plan", "quality_control_definitions", ["plan_id"])
    op.create_index("ix_qcd_version", "quality_control_definitions", ["version_id"])
    op.create_index("ix_qcd_type", "quality_control_definitions", ["control_type"])
    op.create_index("ix_qcd_scope", "quality_control_definitions", ["scope_id"])

    op.create_table(
        "quality_tolerance_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("control_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quality_control_definitions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tolerance_type", sa.String(40), nullable=False),
        sa.Column("min_value", sa.Numeric(**QTY), nullable=True),
        sa.Column("max_value", sa.Numeric(**QTY), nullable=True),
        sa.Column("target_value", sa.Numeric(**QTY), nullable=True),
        sa.Column("absolute_deviation", sa.Numeric(**QTY), nullable=True),
        sa.Column("percentage_deviation", sa.Numeric(**QTY), nullable=True),
        sa.Column("valid_options", postgresql.JSONB, nullable=True),
        sa.Column("default_value", postgresql.JSONB, nullable=True),
        sa.Column("unit_code", sa.String(20), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_qtd_control", "quality_tolerance_definitions", ["control_id"])
    op.create_index("ix_qtd_type", "quality_tolerance_definitions", ["tolerance_type"])

    op.create_table(
        "quality_sampling_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("control_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quality_control_definitions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sampling_type", sa.String(40), nullable=False),
        sa.Column("fixed_count", sa.Integer, nullable=True),
        sa.Column("percentage", sa.Numeric(**QTY), nullable=True),
        sa.Column("minimum_count", sa.Integer, nullable=True),
        sa.Column("package_level", sa.String(40), nullable=True),
        sa.Column("lot_level", sa.String(40), nullable=True),
        sa.Column("custom_formula", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_qsp_control", "quality_sampling_plans", ["control_id"])
    op.create_index("ix_qsp_type", "quality_sampling_plans", ["sampling_type"])

    op.create_table(
        "quality_certificate_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("control_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quality_control_definitions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("certificate_type", sa.String(60), nullable=False),
        sa.Column("document_type_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_mandatory", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("validity_days", sa.Integer, nullable=True),
        sa.Column("requires_signature", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("metadata_schema", postgresql.JSONB, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_qcr_control", "quality_certificate_requirements", ["control_id"])
    op.create_index("ix_qcr_type", "quality_certificate_requirements", ["certificate_type"])

    op.create_table(
        "quality_control_applicability_conditions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("control_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quality_control_definitions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("condition_type", sa.String(40), nullable=False),
        sa.Column("condition_field", sa.String(120), nullable=False),
        sa.Column("condition_operator", sa.String(20), nullable=False),
        sa.Column("condition_value", postgresql.JSONB, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_qcac_control", "quality_control_applicability_conditions", ["control_id"])

    op.create_table(
        "quality_plan_reference_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quality_inspection_plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quality_inspection_plan_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("file_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reference_type", sa.String(40), nullable=False, server_default="MANUAL"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("linked_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("content_hash", sa.String(64), nullable=True),
    )
    op.create_index("ix_qprf_plan", "quality_plan_reference_files", ["plan_id"])
    op.create_index("ix_qprf_version", "quality_plan_reference_files", ["version_id"])
    op.create_index("ix_qprf_file", "quality_plan_reference_files", ["file_asset_id"])

    op.create_table(
        "quality_plan_usage_projection",
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quality_inspection_plans.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_scopes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_controls", sa.Integer, nullable=False, server_default="0"),
        sa.Column("mandatory_controls", sa.Integer, nullable=False, server_default="0"),
        sa.Column("blocking_controls", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_tolerances", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_sampling_plans", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_certificate_requirements", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_reference_files", sa.Integer, nullable=False, server_default="0"),
        sa.Column("resolved_for_products", sa.Integer, nullable=False, server_default="0"),
        sa.Column("resolved_for_categories", sa.Integer, nullable=False, server_default="0"),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("quality_plan_usage_projection")
    op.drop_table("quality_plan_reference_files")
    op.drop_table("quality_control_applicability_conditions")
    op.drop_table("quality_certificate_requirements")
    op.drop_table("quality_sampling_plans")
    op.drop_table("quality_tolerance_definitions")
    op.drop_table("quality_control_definitions")
    op.drop_table("quality_plan_scopes")
    op.drop_table("quality_inspection_plan_versions")
    op.drop_table("quality_inspection_plans")
