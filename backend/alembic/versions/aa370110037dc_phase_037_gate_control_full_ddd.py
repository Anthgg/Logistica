"""Phase 037 Gate Control — Full DDD schema (replaces z370110037dc stub tables).

This migration:
1. Drops the stub tables from z370110037dc (gate_control_records, gate_control_history).
2. Drops the stub warehouse_gates and recreates it with the full schema.
3. Creates all Phase 037 DDD tables:
   - warehouse_gates (full schema)
   - gate_verification_policies
   - gate_verification_policy_versions
   - gate_verification_check_definitions
   - gate_check_ins
   - gate_check_in_revisions
   - gate_vehicle_inspections
   - gate_driver_inspections
   - gate_presented_documents
   - gate_seal_inspections
   - gate_photo_evidence
   - gate_verification_check_results
   - gate_verification_exceptions
   - gate_entry_decisions
   - gate_check_in_holds
   - gate_check_in_time_corrections
   - gate_check_in_correction_requests
   - gate_check_in_package_jobs

Revision ID: aa370110037dc
Revises: z370110037dc
Create Date: 2026-08-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "aa370110037dc"
down_revision: Union[str, Sequence[str], None] = "z370110037dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ──────────────────────────────────────────────────────────────────────
    # Step 1: Drop stub tables from z370110037dc
    # ──────────────────────────────────────────────────────────────────────
    op.drop_table("gate_control_history")
    op.drop_table("gate_control_records")
    op.drop_table("warehouse_gates")

    # ──────────────────────────────────────────────────────────────────────
    # Step 2: warehouse_gates (full schema)
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "warehouse_gates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "branch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("logistics_branches.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "warehouse_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("warehouses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("normalized_code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("gate_type", sa.String(40), nullable=False, server_default="VEHICLE_ENTRY"),
        sa.Column("direction_policy", sa.String(40), nullable=False, server_default="ENTRY_ONLY"),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column(
            "active_verification_policy_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.UniqueConstraint("warehouse_id", "normalized_code", name="uq_warehouse_gate_code"),
        sa.CheckConstraint("row_version >= 1", name="ck_warehouse_gate_row_version"),
    )
    op.create_index("ix_warehouse_gates_org", "warehouse_gates", ["organization_id"])
    op.create_index("ix_warehouse_gates_warehouse", "warehouse_gates", ["warehouse_id"])
    op.create_index("ix_warehouse_gates_status", "warehouse_gates", ["status"])

    # ──────────────────────────────────────────────────────────────────────
    # Step 3: gate_verification_policies
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_verification_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scope_type", sa.String(40), nullable=False, server_default="ORGANIZATION"),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("gate_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("active_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.CheckConstraint("row_version >= 1", name="ck_gate_policy_row_version"),
    )
    op.create_index("ix_gate_policies_org", "gate_verification_policies", ["organization_id"])
    op.create_index("ix_gate_policies_status", "gate_verification_policies", ["status"])

    # ──────────────────────────────────────────────────────────────────────
    # Step 4: gate_verification_policy_versions
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_verification_policy_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "policy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("gate_verification_policies.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("late_tolerance_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("early_tolerance_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("walk_in_allowed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "photo_requirements",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("seal_requirement", sa.String(20), nullable=False, server_default="REQUIRED"),
        sa.Column(
            "document_requirements",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "vehicle_mismatch_policy", sa.String(20), nullable=False, server_default="BLOCK"
        ),
        sa.Column(
            "driver_mismatch_policy", sa.String(20), nullable=False, server_default="BLOCK"
        ),
        sa.Column(
            "license_expired_policy", sa.String(20), nullable=False, server_default="BLOCK"
        ),
        sa.Column(
            "verification_expired_policy", sa.String(20), nullable=False, server_default="BLOCK"
        ),
        sa.Column(
            "missing_document_policy", sa.String(20), nullable=False, server_default="WARN"
        ),
        sa.Column(
            "broken_seal_policy", sa.String(20), nullable=False, server_default="BLOCK"
        ),
        sa.Column(
            "decision_matrix",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("validated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("activated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "policy_id", "version_number", name="uq_gate_policy_version_number"
        ),
    )
    op.create_index(
        "ix_gate_policy_versions_policy",
        "gate_verification_policy_versions",
        ["policy_id"],
    )
    op.create_index(
        "ix_gate_policy_versions_status",
        "gate_verification_policy_versions",
        ["status"],
    )

    # ──────────────────────────────────────────────────────────────────────
    # Step 5: gate_verification_check_definitions
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_verification_check_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "policy_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("gate_verification_policy_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("check_code", sa.String(60), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("blocking_on_fail", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("requires_photo", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("requires_document", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "requires_comment_on_fail", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "allow_supervisor_override", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("override_step_up_level", sa.String(20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "policy_version_id", "check_code", name="uq_gate_check_def_code"
        ),
    )
    op.create_index(
        "ix_gate_check_defs_version",
        "gate_verification_check_definitions",
        ["policy_version_id"],
    )

    # ──────────────────────────────────────────────────────────────────────
    # Step 6: gate_check_ins (aggregate root)
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_check_ins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "branch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("logistics_branches.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "warehouse_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("warehouses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "gate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("warehouse_gates.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("appointment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("arrival_notice_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("appointment_code_snapshot", sa.String(40), nullable=True),
        sa.Column("check_in_code", sa.String(40), nullable=True),
        sa.Column("normalized_check_in_code", sa.String(40), nullable=True),
        sa.Column("document_instance_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="CREATED"),
        sa.Column("source_type", sa.String(40), nullable=False, server_default="APPOINTMENT"),
        sa.Column(
            "arrival_classification",
            sa.String(40),
            nullable=False,
            server_default="TIME_NOT_CLASSIFIED",
        ),
        # Server clock only — never from client
        sa.Column("arrived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("gate_timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("check_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("check_completed_at", sa.DateTime(timezone=True), nullable=True),
        # Session-derived guard — never from payload
        sa.Column("guard_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "guard_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("supervisor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "supplier_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "carrier_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "expected_transport_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "observed_transport_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "verification_policy_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "verification_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("decision", sa.String(50), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("entry_authorized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("entry_authorized_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("entry_denied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("entry_denied_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("hold_reason", sa.Text(), nullable=True),
        sa.Column("exception_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_check_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warning_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_revision_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("active_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("audit_seal_hash", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.CheckConstraint("exception_count >= 0", name="ck_gate_check_in_exceptions"),
        sa.CheckConstraint("failed_check_count >= 0", name="ck_gate_check_in_failed"),
        sa.CheckConstraint("warning_count >= 0", name="ck_gate_check_in_warnings"),
        sa.CheckConstraint("row_version >= 1", name="ck_gate_check_in_row_version"),
    )
    op.create_index("ix_gate_check_ins_org", "gate_check_ins", ["organization_id"])
    op.create_index("ix_gate_check_ins_warehouse", "gate_check_ins", ["warehouse_id"])
    op.create_index("ix_gate_check_ins_gate", "gate_check_ins", ["gate_id"])
    op.create_index("ix_gate_check_ins_appointment", "gate_check_ins", ["appointment_id"])
    op.create_index("ix_gate_check_ins_status", "gate_check_ins", ["status"])
    op.create_index("ix_gate_check_ins_decision", "gate_check_ins", ["decision"])
    op.create_index("ix_gate_check_ins_arrived_at", "gate_check_ins", ["arrived_at"])
    op.create_index("ix_gate_check_ins_guard", "gate_check_ins", ["guard_user_id"])
    op.create_index("ix_gate_check_ins_completed_at", "gate_check_ins", ["check_completed_at"])

    # ──────────────────────────────────────────────────────────────────────
    # Step 7: gate_check_in_revisions
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_check_in_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "gate_check_in_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("gate_check_ins.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="EDITABLE"),
        sa.Column("appointment_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("expected_transport_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("observed_transport_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("document_inspection_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("seal_inspection_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("photo_evidence_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("checklist_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("decision_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("gate_check_in_id", "revision_number", name="uq_gate_revision_number"),
    )
    op.create_index("ix_gate_revisions_check_in", "gate_check_in_revisions", ["gate_check_in_id"])

    # ──────────────────────────────────────────────────────────────────────
    # Step 8: gate_vehicle_inspections
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_vehicle_inspections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gate_check_in_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("expected_vehicle_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expected_plate", sa.String(20), nullable=True),
        sa.Column("expected_plate_normalized", sa.String(20), nullable=True),
        sa.Column("expected_vehicle_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("observed_vehicle_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("observed_plate", sa.String(20), nullable=True),
        sa.Column("observed_plate_normalized", sa.String(20), nullable=True),
        sa.Column("observed_vehicle_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("plate_match_status", sa.String(30), nullable=False, server_default="MANUAL_REVIEW"),
        sa.Column("vehicle_match_status", sa.String(30), nullable=False, server_default="UNCONFIRMED"),
        sa.Column("operational_status", sa.String(30), nullable=True),
        sa.Column("verification_status", sa.String(30), nullable=True),
        sa.Column("verification_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_expiration", sa.DateTime(timezone=True), nullable=True),
        sa.Column("visual_condition", sa.String(40), nullable=True),
        sa.Column("inspection_result", sa.String(30), nullable=False, server_default="NOT_VERIFIED"),
        sa.Column("exception_reason", sa.Text(), nullable=True),
        sa.Column("capture_method", sa.String(40), nullable=False, server_default="MANUAL_ENTRY"),
        sa.Column("inspected_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inspected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_gate_vehicle_insp_check_in", "gate_vehicle_inspections", ["gate_check_in_id"])
    op.create_index("ix_gate_vehicle_insp_observed_plate", "gate_vehicle_inspections", ["observed_plate_normalized"])
    op.create_index("ix_gate_vehicle_insp_observed_vehicle", "gate_vehicle_inspections", ["observed_vehicle_id"])

    # ──────────────────────────────────────────────────────────────────────
    # Step 9: gate_driver_inspections
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_driver_inspections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gate_check_in_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("expected_driver_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expected_driver_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("observed_driver_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("observed_name_snapshot", sa.String(160), nullable=True),
        sa.Column("observed_document_type", sa.String(20), nullable=True),
        # Encrypted — application layer. No plaintext.
        sa.Column("observed_document_number_encrypted", sa.Text(), nullable=True),
        sa.Column("observed_document_number_hash", sa.String(64), nullable=True),
        sa.Column("observed_document_number_redacted", sa.String(20), nullable=True),
        sa.Column("license_number_encrypted", sa.Text(), nullable=True),
        sa.Column("license_number_hash", sa.String(64), nullable=True),
        sa.Column("license_number_redacted", sa.String(20), nullable=True),
        sa.Column("license_category", sa.String(20), nullable=True),
        sa.Column("license_expiration", sa.DateTime(timezone=True), nullable=True),
        sa.Column("driver_match_status", sa.String(40), nullable=False, server_default="MANUAL_REVIEW"),
        sa.Column("license_status", sa.String(30), nullable=False, server_default="NOT_VERIFIED"),
        sa.Column("carrier_match_status", sa.String(30), nullable=False, server_default="NOT_VERIFIED"),
        sa.Column("restriction_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("inspection_result", sa.String(30), nullable=False, server_default="NOT_VERIFIED"),
        sa.Column("exception_reason", sa.Text(), nullable=True),
        sa.Column("inspected_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inspected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_gate_driver_insp_check_in", "gate_driver_inspections", ["gate_check_in_id"])
    op.create_index("ix_gate_driver_insp_observed_driver", "gate_driver_inspections", ["observed_driver_id"])

    # ──────────────────────────────────────────────────────────────────────
    # Step 10: gate_presented_documents
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_presented_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gate_check_in_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_transport_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("document_kind", sa.String(40), nullable=False),
        sa.Column("expected_reference", sa.String(120), nullable=True),
        sa.Column("observed_series", sa.String(20), nullable=True),
        sa.Column("observed_number", sa.String(30), nullable=True),
        sa.Column("observed_reference_normalized", sa.String(120), nullable=True),
        sa.Column("presentation_status", sa.String(30), nullable=False, server_default="NOT_PRESENTED"),
        sa.Column("comparison_status", sa.String(30), nullable=False, server_default="REQUIRES_REVIEW"),
        sa.Column("verification_status", sa.String(30), nullable=False, server_default="NOT_VERIFIED"),
        sa.Column("verification_source", sa.String(60), nullable=True),
        sa.Column("inspected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("inspected_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_gate_presented_docs_check_in", "gate_presented_documents", ["gate_check_in_id"])

    # ──────────────────────────────────────────────────────────────────────
    # Step 11: gate_seal_inspections
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_seal_inspections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gate_check_in_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("seal_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("expected_seal_number", sa.String(80), nullable=True),
        sa.Column("expected_seal_number_hash", sa.String(64), nullable=True),
        sa.Column("observed_seal_number", sa.String(80), nullable=True),
        sa.Column("observed_seal_number_hash", sa.String(64), nullable=True),
        sa.Column("seal_match_status", sa.String(30), nullable=False, server_default="NOT_APPLICABLE"),
        sa.Column("physical_status", sa.String(30), nullable=False, server_default="NOT_APPLICABLE"),
        sa.Column("inspection_result", sa.String(30), nullable=False, server_default="PASS"),
        sa.Column("photo_file_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("exception_reason", sa.Text(), nullable=True),
        sa.Column("inspected_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inspected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_gate_seal_insp_check_in", "gate_seal_inspections", ["gate_check_in_id"])
    op.create_index("ix_gate_seal_insp_observed_hash", "gate_seal_inspections", ["observed_seal_number_hash"])

    # ──────────────────────────────────────────────────────────────────────
    # Step 12: gate_photo_evidence
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_photo_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gate_check_in_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("evidence_type", sa.String(40), nullable=False),
        sa.Column("file_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("captured_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_reference_hash", sa.String(64), nullable=True),
        sa.Column("source_type", sa.String(30), nullable=False, server_default="FILE_UPLOAD"),
        sa.Column("classification", sa.String(30), nullable=False, server_default="RESTRICTED"),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("metadata_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_gate_photo_evidence_check_in", "gate_photo_evidence", ["gate_check_in_id"])

    # ──────────────────────────────────────────────────────────────────────
    # Step 13: gate_verification_check_results
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_verification_check_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gate_check_in_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("check_definition_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("check_code", sa.String(60), nullable=False),
        sa.Column("result", sa.String(30), nullable=False, server_default="NOT_VERIFIED"),
        sa.Column("observed_value", sa.Text(), nullable=True),
        sa.Column("expected_value", sa.Text(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("evidence_file_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("blocking", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("override_status", sa.String(20), nullable=False, server_default="NOT_REQUIRED"),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("override_requested_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("override_approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("checked_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("gate_check_in_id", "check_code", name="uq_gate_check_result_code"),
    )
    op.create_index("ix_gate_check_results_check_in", "gate_verification_check_results", ["gate_check_in_id"])
    op.create_index("ix_gate_check_results_result", "gate_verification_check_results", ["result"])
    op.create_index("ix_gate_check_results_blocking", "gate_verification_check_results", ["blocking"])

    # ──────────────────────────────────────────────────────────────────────
    # Step 14: gate_verification_exceptions
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_verification_exceptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gate_check_in_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("check_result_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("exception_type", sa.String(40), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="REQUESTED"),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_gate_exceptions_check_in", "gate_verification_exceptions", ["gate_check_in_id"])
    op.create_index("ix_gate_exceptions_status", "gate_verification_exceptions", ["status"])
    op.create_index("ix_gate_exceptions_type", "gate_verification_exceptions", ["exception_type"])

    # ──────────────────────────────────────────────────────────────────────
    # Step 15: gate_entry_decisions (append-only)
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_entry_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gate_check_in_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("decision_type", sa.String(40), nullable=False),
        sa.Column("decision_reason", sa.Text(), nullable=False),
        sa.Column("conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("blocking_checks", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("approved_exceptions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("denied_exceptions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("decided_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("supervisor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("step_up_assurance_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("decision_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_gate_decisions_check_in", "gate_entry_decisions", ["gate_check_in_id"])

    # ──────────────────────────────────────────────────────────────────────
    # Step 16: gate_check_in_holds
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_check_in_holds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gate_check_in_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("hold_reason", sa.Text(), nullable=False),
        sa.Column("hold_started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("held_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_gate_holds_check_in", "gate_check_in_holds", ["gate_check_in_id"])

    # ──────────────────────────────────────────────────────────────────────
    # Step 17: gate_check_in_time_corrections
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_check_in_time_corrections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gate_check_in_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("original_arrived_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("proposed_arrived_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="REQUESTED"),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_gate_time_corrections_check_in", "gate_check_in_time_corrections", ["gate_check_in_id"])

    # ──────────────────────────────────────────────────────────────────────
    # Step 18: gate_check_in_correction_requests
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_check_in_correction_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gate_check_in_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("field_code", sa.String(60), nullable=False),
        sa.Column("original_value_hash", sa.String(64), nullable=True),
        sa.Column("proposed_value", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="REQUESTED"),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_gate_corrections_check_in", "gate_check_in_correction_requests", ["gate_check_in_id"])

    # ──────────────────────────────────────────────────────────────────────
    # Step 19: gate_check_in_package_jobs
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "gate_check_in_package_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gate_check_in_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_gate_package_jobs_check_in", "gate_check_in_package_jobs", ["gate_check_in_id"])


def downgrade() -> None:
    op.drop_table("gate_check_in_package_jobs")
    op.drop_table("gate_check_in_correction_requests")
    op.drop_table("gate_check_in_time_corrections")
    op.drop_table("gate_check_in_holds")
    op.drop_table("gate_entry_decisions")
    op.drop_table("gate_verification_exceptions")
    op.drop_table("gate_verification_check_results")
    op.drop_table("gate_photo_evidence")
    op.drop_table("gate_seal_inspections")
    op.drop_table("gate_presented_documents")
    op.drop_table("gate_driver_inspections")
    op.drop_table("gate_vehicle_inspections")
    op.drop_table("gate_check_in_revisions")
    op.drop_table("gate_check_ins")
    op.drop_table("gate_verification_check_definitions")
    op.drop_table("gate_verification_policy_versions")
    op.drop_table("gate_verification_policies")
    op.drop_table("warehouse_gates")

    # Re-create stub tables from z370110037dc
    op.create_table(
        "warehouse_gates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gate_type", sa.String(30), nullable=False, server_default="MAIN_ENTRY"),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "gate_control_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("record_code", sa.String(50), nullable=False),
        sa.Column("gate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("guard_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False, server_default="CHECK_IN"),
        sa.Column("arrival_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "gate_control_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("new_status", sa.String(50), nullable=False),
        sa.Column("changed_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("change_reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
