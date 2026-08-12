"""phase_035_procurement_approvals

Revision ID: x350110035dc
Revises: w340110034dc
Create Date: 2026-07-31 00:52:00.000000

Phase 035 — Implementar Aprobaciones de Compras (Backend).
Creates 17 tables for procurement approval engine, policies, versions,
conditions, step definitions, escalation rules, requests, exchange rate snapshots,
step instances, assignments, decisions, information requests, delegations,
emergency overrides, audit seals, integrity events, notification jobs,
and migration records.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "x350110035dc"
down_revision: Union[str, None] = "w340110034dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. procurement_approval_policies
    op.create_table(
        "procurement_approval_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("normalized_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("subject_type", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="DRAFT"),
        sa.Column("active_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("effective_scope", sa.String(length=50), nullable=False, server_default="ORGANIZATION"),
        sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("organization_id", "normalized_code", name="uq_proc_appr_policy_org_code"),
        sa.CheckConstraint("status IN ('DRAFT', 'ACTIVE', 'INACTIVE', 'ARCHIVED')", name="ck_proc_appr_policy_status"),
        sa.CheckConstraint("priority >= 1 AND priority <= 9999", name="ck_proc_appr_policy_priority"),
    )
    op.create_index("ix_proc_appr_pol_org", "procurement_approval_policies", ["organization_id"])
    op.create_index("ix_proc_appr_pol_subject", "procurement_approval_policies", ["subject_type"])
    op.create_index("ix_proc_appr_pol_status", "procurement_approval_policies", ["status"])

    # 2. procurement_approval_policy_versions
    op.create_table(
        "procurement_approval_policy_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement_approval_policies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="DRAFT"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("matching_mode", sa.String(length=30), nullable=False, server_default="ALL_GROUPS"),
        sa.Column("mixed_category_strategy", sa.String(length=40), nullable=False, server_default="MOST_RESTRICTIVE_UNION"),
        sa.Column("amount_currency_policy", sa.String(length=40), nullable=False, server_default="SUBJECT_CURRENCY"),
        sa.Column("separation_of_duties_policy", sa.String(length=50), nullable=False, server_default="CREATOR_CANNOT_BE_SOLE_APPROVER"),
        sa.Column("default_step_deadline_hours", sa.Integer(), nullable=True),
        sa.Column("escalation_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("delegation_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("compiler_version", sa.String(length=20), nullable=False, server_default="1.0.0"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("validated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("policy_id", "version_number", name="uq_proc_appr_version_policy_num"),
        sa.CheckConstraint("status IN ('DRAFT', 'VALIDATED', 'ACTIVE', 'RETIRED', 'ARCHIVED')", name="ck_proc_appr_version_status"),
    )
    op.create_index("ix_proc_appr_ver_policy", "procurement_approval_policy_versions", ["policy_id"])
    op.create_index("ix_proc_appr_ver_status", "procurement_approval_policy_versions", ["status"])

    # 3. approval_policy_conditions
    op.create_table(
        "approval_policy_conditions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("policy_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement_approval_policy_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("condition_group", sa.String(length=20), nullable=False, server_default="ALL"),
        sa.Column("field_code", sa.String(length=50), nullable=False),
        sa.Column("operator", sa.String(length=30), nullable=False),
        sa.Column("value_type", sa.String(length=20), nullable=False, server_default="STRING"),
        sa.Column("value_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_proc_appr_cond_version", "approval_policy_conditions", ["policy_version_id"])

    # 4. approval_policy_step_definitions
    op.create_table(
        "approval_policy_step_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("policy_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement_approval_policy_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("execution_mode", sa.String(length=20), nullable=False, server_default="SEQUENTIAL"),
        sa.Column("completion_mode", sa.String(length=30), nullable=False, server_default="ALL"),
        sa.Column("minimum_approvals", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("required_approvals", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("approver_source_type", sa.String(length=50), nullable=False),
        sa.Column("approver_source_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("permission_required", sa.String(length=100), nullable=False, server_default="logistics.purchase_orders.approve"),
        sa.Column("step_up_level", sa.String(length=20), nullable=False, server_default="HIGH"),
        sa.Column("deadline_hours", sa.Integer(), nullable=True),
        sa.Column("allow_delegation", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("allow_abstention", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("allow_return", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("allow_request_information", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("distinct_from_creator", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("distinct_from_requester", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("distinct_from_previous_steps", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_proc_appr_stepdef_version", "approval_policy_step_definitions", ["policy_version_id"])

    # 5. approval_escalation_rules
    op.create_table(
        "approval_escalation_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("step_definition_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("approval_policy_step_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trigger_after_hours", sa.Integer(), nullable=False),
        sa.Column("repeat_every_hours", sa.Integer(), nullable=True),
        sa.Column("maximum_repeats", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("action_type", sa.String(length=30), nullable=False),
        sa.Column("target_source_type", sa.String(length=50), nullable=False),
        sa.Column("target_source_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("preserve_original_assignment", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_proc_appr_escal_step", "approval_escalation_rules", ["step_definition_id"])

    # 6. procurement_approval_requests
    op.create_table(
        "procurement_approval_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_code", sa.String(length=50), nullable=False),
        sa.Column("subject_type", sa.String(length=50), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("subject_code", sa.String(length=100), nullable=True),
        sa.Column("subject_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("subject_snapshot_hash", sa.String(length=64), nullable=False),
        sa.Column("policy_resolution_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("compiled_chain", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("chain_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="CREATED"),
        sa.Column("current_sequence", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("amount", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("comparison_amount", sa.Numeric(precision=28, scale=10), nullable=True),
        sa.Column("comparison_currency_code", sa.String(length=3), nullable=True),
        sa.Column("cost_center_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("category_snapshots", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("branch_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("requester_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requester_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("creator_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("creator_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("final_decision", sa.String(length=30), nullable=True),
        sa.Column("final_decision_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("final_decision_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("supersedes_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("superseded_by_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("return_reason", sa.Text(), nullable=True),
        sa.Column("audit_seal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint("status IN ('CREATED', 'RESOLVING', 'READY', 'IN_PROGRESS', 'WAITING_INFORMATION', 'APPROVED', 'REJECTED', 'RETURNED_FOR_CHANGES', 'CANCELLED', 'EXPIRED', 'SUPERSEDED', 'FAILED', 'ARCHIVED')", name="ck_proc_appr_req_status"),
        sa.CheckConstraint("amount >= 0", name="ck_proc_appr_req_amount_ge_zero"),
    )
    op.create_index("ix_proc_appr_req_org", "procurement_approval_requests", ["organization_id"])
    op.create_index("ix_proc_appr_req_code", "procurement_approval_requests", ["request_code"])
    op.create_index("ix_proc_appr_req_subject", "procurement_approval_requests", ["subject_type", "subject_id"])
    op.create_index("ix_proc_appr_req_status", "procurement_approval_requests", ["status"])

    # 7. approval_exchange_rate_snapshots
    op.create_table(
        "approval_exchange_rate_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("approval_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement_approval_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_currency", sa.String(length=3), nullable=False),
        sa.Column("target_currency", sa.String(length=3), nullable=False),
        sa.Column("rate", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False, server_default="SYSTEM_OFFICIAL_RATE"),
        sa.Column("source_reference", sa.String(length=100), nullable=True),
        sa.Column("source_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.CheckConstraint("rate > 0", name="ck_proc_appr_rate_gt_zero"),
    )

    # 8. approval_step_instances
    op.create_table(
        "approval_step_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("approval_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement_approval_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_code", sa.String(length=50), nullable=False),
        sa.Column("name_snapshot", sa.String(length=150), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("execution_mode", sa.String(length=20), nullable=False, server_default="SEQUENTIAL"),
        sa.Column("completion_mode", sa.String(length=30), nullable=False, server_default="ALL"),
        sa.Column("minimum_approvals", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("required_approvals", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completion_result", sa.String(length=30), nullable=True),
        sa.Column("escalation_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_proc_appr_stepinst_req", "approval_step_instances", ["approval_request_id"])
    op.create_index("ix_proc_appr_stepinst_status", "approval_step_instances", ["status"])

    # 9. approval_assignments
    op.create_table(
        "approval_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("approval_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement_approval_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_instance_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("approval_step_instances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_approver_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("effective_approver_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approver_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("assignment_source_type", sa.String(length=50), nullable=False),
        sa.Column("assignment_source_reference", sa.String(length=100), nullable=True),
        sa.Column("delegation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ASSIGNED"),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_proc_appr_assign_req", "approval_assignments", ["approval_request_id"])
    op.create_index("ix_proc_appr_assign_step", "approval_assignments", ["step_instance_id"])
    op.create_index("ix_proc_appr_assign_effective_user", "approval_assignments", ["effective_approver_user_id"])
    op.create_index("ix_proc_appr_assign_status", "approval_assignments", ["status"])

    # 10. approval_decisions
    op.create_table(
        "approval_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("approval_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement_approval_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_instance_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("approval_step_instances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("approval_assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("decision_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="RECORDED"),
        sa.Column("decided_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approver_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("acting_on_behalf_of_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("delegation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("step_up_assurance_level", sa.String(length=20), nullable=False, server_default="HIGH"),
        sa.Column("decision_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("request_snapshot_hash", sa.String(length=64), nullable=False),
        sa.Column("step_snapshot_hash", sa.String(length=64), nullable=False),
        sa.Column("previous_event_hash", sa.String(length=64), nullable=True),
        sa.Column("decision_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_proc_appr_dec_req", "approval_decisions", ["approval_request_id"])
    op.create_index("ix_proc_appr_dec_step", "approval_decisions", ["step_instance_id"])
    op.create_index("ix_proc_appr_dec_user", "approval_decisions", ["decided_by_user_id"])

    # 11. approval_information_requests
    op.create_table(
        "approval_information_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("approval_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement_approval_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("answered_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # 12. approval_delegations
    op.create_table(
        "approval_delegations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("delegator_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("delegate_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scope_type", sa.String(length=30), nullable=False, server_default="ALL_APPROVALS"),
        sa.Column("subject_types", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("cost_center_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("category_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revoked_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("delegator_user_id <> delegate_user_id", name="ck_proc_appr_delegation_distinct"),
        sa.CheckConstraint("valid_from < valid_until", name="ck_proc_appr_delegation_dates"),
    )
    op.create_index("ix_proc_appr_del_org", "approval_delegations", ["organization_id"])
    op.create_index("ix_proc_appr_del_delegator", "approval_delegations", ["delegator_user_id"])
    op.create_index("ix_proc_appr_del_delegate", "approval_delegations", ["delegate_user_id"])

    # 13. approval_emergency_overrides
    op.create_table(
        "approval_emergency_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("approval_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement_approval_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("override_type", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("incident_reference", sa.String(length=100), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("affected_rules", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("audit_seal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="APPLIED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("requested_by <> approved_by", name="ck_proc_appr_override_distinct"),
    )

    # 14. approval_audit_seals
    op.create_table(
        "approval_audit_seals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approval_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement_approval_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject_type", sa.String(length=50), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("subject_snapshot_hash", sa.String(length=64), nullable=False),
        sa.Column("policy_versions_hash", sa.String(length=64), nullable=False),
        sa.Column("chain_hash", sa.String(length=64), nullable=False),
        sa.Column("decisions_hash", sa.String(length=64), nullable=False),
        sa.Column("event_chain_hash", sa.String(length=64), nullable=False),
        sa.Column("final_status", sa.String(length=30), nullable=False),
        sa.Column("final_decision", sa.String(length=30), nullable=False),
        sa.Column("sealed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("sealed_by_service", sa.String(length=100), nullable=False, server_default="ProcurementApprovalEngine"),
        sa.Column("hash_algorithm", sa.String(length=20), nullable=False, server_default="SHA-256"),
        sa.Column("canonicalization_version", sa.String(length=20), nullable=False, server_default="1.0.0"),
        sa.Column("seal_hash", sa.String(length=64), nullable=False),
        sa.Column("signature_algorithm", sa.String(length=50), nullable=True),
        sa.Column("signature_value", sa.Text(), nullable=True),
        sa.Column("kms_key_reference", sa.String(length=255), nullable=True),
        sa.Column("kms_key_version", sa.String(length=100), nullable=True),
        sa.Column("verification_status", sa.String(length=30), nullable=False, server_default="HASH_VERIFIED"),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_proc_appr_seal_org", "approval_audit_seals", ["organization_id"])
    op.create_index("ix_proc_appr_seal_req", "approval_audit_seals", ["approval_request_id"])

    # 15. approval_integrity_events
    op.create_table(
        "approval_integrity_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("approval_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement_approval_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("actor_reference", sa.String(length=100), nullable=False),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("previous_event_hash", sa.String(length=64), nullable=True),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.Column("correlation_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("approval_request_id", "sequence_number", name="uq_proc_appr_integrity_seq"),
    )
    op.create_index("ix_proc_appr_event_req", "approval_integrity_events", ["approval_request_id"])

    # 16. approval_notification_jobs
    op.create_table(
        "approval_notification_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("approval_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("recipient_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # 17. approval_migration_records
    op.create_table(
        "approval_migration_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("purchase_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("previous_approval_status", sa.String(length=50), nullable=False),
        sa.Column("migration_action", sa.String(length=50), nullable=False),
        sa.Column("new_approval_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("migrated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("approval_migration_records")
    op.drop_table("approval_notification_jobs")
    op.drop_table("approval_integrity_events")
    op.drop_table("approval_audit_seals")
    op.drop_table("approval_emergency_overrides")
    op.drop_table("approval_delegations")
    op.drop_table("approval_information_requests")
    op.drop_table("approval_decisions")
    op.drop_table("approval_assignments")
    op.drop_table("approval_step_instances")
    op.drop_table("approval_exchange_rate_snapshots")
    op.drop_table("procurement_approval_requests")
    op.drop_table("approval_escalation_rules")
    op.drop_table("approval_policy_step_definitions")
    op.drop_table("approval_policy_conditions")
    op.drop_table("procurement_approval_policy_versions")
    op.drop_table("procurement_approval_policies")
