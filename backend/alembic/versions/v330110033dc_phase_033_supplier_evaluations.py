"""Phase 033 — Supplier Evaluation (Cuadro Comparativo de Ofertas - CCO).

Revision ID: v330110033dc
Revises: u300110030a
Create Date: 2026-07-30 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "v330110033dc"
down_revision: Union[str, None] = "v410110031dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. supplier_evaluation_templates
    op.create_table(
        "supplier_evaluation_templates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("normalized_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scope_type", sa.String(length=50), nullable=False, server_default="GENERAL"),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.Column("product_type", sa.String(length=50), nullable=True),
        sa.Column("purchase_type", sa.String(length=50), nullable=True),
        sa.Column("currency_policy", sa.String(length=50), nullable=False, server_default="SAME_CURRENCY_REQUIRED"),
        sa.Column("award_policy", sa.String(length=50), nullable=False, server_default="BEST_OVERALL_SCORE"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("active_version_id", sa.UUID(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("updated_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "normalized_code", name="uq_eval_template_org_code"),
    )
    op.create_index("ix_supplier_eval_templates_org", "supplier_evaluation_templates", ["organization_id"])

    # 2. supplier_evaluation_template_versions
    op.create_table(
        "supplier_evaluation_template_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("template_id", sa.UUID(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("score_scale_min", sa.Numeric(precision=10, scale=4), nullable=False, server_default="0.0000"),
        sa.Column("score_scale_max", sa.Numeric(precision=10, scale=4), nullable=False, server_default="100.0000"),
        sa.Column("passing_score", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("minimum_supplier_score", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("missing_data_policy", sa.String(length=50), nullable=False, server_default="ZERO_SCORE"),
        sa.Column("tie_policy", sa.String(length=50), nullable=False, server_default="HIGHER_TECHNICAL_SCORE"),
        sa.Column("award_policy", sa.String(length=50), nullable=False, server_default="BEST_OVERALL_SCORE"),
        sa.Column("currency_policy", sa.String(length=50), nullable=False, server_default="SAME_CURRENCY_REQUIRED"),
        sa.Column("rounding_scale", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("rounding_mode", sa.String(length=50), nullable=False, server_default="HALF_UP"),
        sa.Column("engine_version", sa.String(length=50), nullable=False, server_default="1.0.0"),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("validated_by", sa.UUID(), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activated_by", sa.UUID(), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["supplier_evaluation_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", "version_number", name="uq_eval_version_number"),
    )
    op.create_index("ix_supplier_eval_template_versions_tpl", "supplier_evaluation_template_versions", ["template_id"])

    # 3. evaluation_criterion_definitions
    op.create_table(
        "evaluation_criterion_definitions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("template_version_id", sa.UUID(), nullable=False),
        sa.Column("criterion_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("criterion_group", sa.String(length=50), nullable=False),
        sa.Column("scoring_method", sa.String(length=50), nullable=False),
        sa.Column("weight", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("mandatory", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("disqualifying", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("minimum_score", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("maximum_score", sa.Numeric(precision=10, scale=4), nullable=False, server_default="100.0000"),
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="AUTOMATIC"),
        sa.Column("evidence_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("manual_override_allowed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("missing_data_policy", sa.String(length=50), nullable=True),
        sa.Column("normalization_parameters", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True),
        sa.Column("rubric_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["template_version_id"], ["supplier_evaluation_template_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_eval_criterion_defs_ver", "evaluation_criterion_definitions", ["template_version_id"])

    # 4. quotation_evaluations
    op.create_table(
        "quotation_evaluations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("quotation_round_id", sa.UUID(), nullable=False),
        sa.Column("evaluation_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("template_id", sa.UUID(), nullable=False),
        sa.Column("template_version_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("evaluation_scope", sa.String(length=50), nullable=False, server_default="WHOLE_RESPONSE"),
        sa.Column("award_policy", sa.String(length=50), nullable=False, server_default="BEST_OVERALL_SCORE"),
        sa.Column("comparison_currency_code", sa.String(length=3), nullable=True),
        sa.Column("currency_conversion_policy", sa.String(length=50), nullable=False, server_default="SAME_CURRENCY_REQUIRED"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_by", sa.UUID(), nullable=True),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("calculated_by", sa.UUID(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.UUID(), nullable=True),
        sa.Column("decision_recorded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_recorded_by", sa.UUID(), nullable=True),
        sa.Column("active_run_id", sa.UUID(), nullable=True),
        sa.Column("active_decision_id", sa.UUID(), nullable=True),
        sa.Column("source_snapshot_hash", sa.String(length=64), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("updated_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quotation_round_id", "evaluation_number", name="uq_eval_round_number"),
    )
    op.create_index("ix_quotation_evaluations_org", "quotation_evaluations", ["organization_id"])
    op.create_index("ix_quotation_evaluations_round", "quotation_evaluations", ["quotation_round_id"])

    # 5. quotation_evaluation_candidates
    op.create_table(
        "quotation_evaluation_candidates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("evaluation_id", sa.UUID(), nullable=False),
        sa.Column("supplier_business_partner_id", sa.UUID(), nullable=False),
        sa.Column("invitation_id", sa.UUID(), nullable=False),
        sa.Column("response_id", sa.UUID(), nullable=False),
        sa.Column("response_revision_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("supplier_snapshot", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("response_snapshot_hash", sa.String(length=64), nullable=False),
        sa.Column("eligibility_status", sa.String(length=50), nullable=False, server_default="ELIGIBLE"),
        sa.Column("eligibility_reasons", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True),
        sa.Column("disqualification_status", sa.String(length=50), nullable=False, server_default="NOT_DISQUALIFIED"),
        sa.Column("disqualification_reason", sa.Text(), nullable=True),
        sa.Column("late_response", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="PEN"),
        sa.Column("completeness_status", sa.String(length=50), nullable=False, server_default="COMPLETE"),
        sa.Column("technical_compliance_status", sa.String(length=50), nullable=False, server_default="COMPLIANT"),
        sa.Column("document_compliance_status", sa.String(length=50), nullable=False, server_default="COMPLIANT"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["evaluation_id"], ["quotation_evaluations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quotation_eval_cands_eval", "quotation_evaluation_candidates", ["evaluation_id"])

    # 6. quotation_evaluation_runs
    op.create_table(
        "quotation_evaluation_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("evaluation_id", sa.UUID(), nullable=False),
        sa.Column("run_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("engine_version", sa.String(length=50), nullable=False, server_default="1.0.0"),
        sa.Column("template_version_id", sa.UUID(), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("output_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="COMPLETED"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_by", sa.UUID(), nullable=False),
        sa.Column("failure_code", sa.String(length=50), nullable=True),
        sa.Column("failure_summary", sa.Text(), nullable=True),
        sa.Column("candidate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ranked_candidate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["evaluation_id"], ["quotation_evaluations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evaluation_id", "run_number", name="uq_eval_run_number"),
    )
    op.create_index("ix_quotation_eval_runs_eval", "quotation_evaluation_runs", ["evaluation_id"])

    # 7. quotation_criterion_scores
    op.create_table(
        "quotation_criterion_scores",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("evaluation_run_id", sa.UUID(), nullable=False),
        sa.Column("candidate_id", sa.UUID(), nullable=False),
        sa.Column("criterion_definition_id", sa.UUID(), nullable=False),
        sa.Column("criterion_code", sa.String(length=50), nullable=False),
        sa.Column("raw_value", sa.String(length=255), nullable=True),
        sa.Column("normalized_value", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("normalized_score", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("weight_snapshot", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("weighted_score", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("scoring_method", sa.String(length=50), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="AUTOMATIC"),
        sa.Column("source_reference", sa.String(length=255), nullable=True),
        sa.Column("evidence_file_id", sa.UUID(), nullable=True),
        sa.Column("evidence_record_id", sa.UUID(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("calculation_details", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True),
        sa.Column("manual", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("manually_entered_by", sa.UUID(), nullable=True),
        sa.Column("manually_entered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("override_of_score_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["evaluation_run_id"], ["quotation_evaluation_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evaluation_run_id", "candidate_id", "criterion_definition_id", name="uq_eval_run_cand_crit"),
    )
    op.create_index("ix_quotation_crit_scores_run", "quotation_criterion_scores", ["evaluation_run_id"])
    op.create_index("ix_quotation_crit_scores_cand", "quotation_criterion_scores", ["candidate_id"])

    # 8. manual_evaluation_scores
    op.create_table(
        "manual_evaluation_scores",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("evaluation_id", sa.UUID(), nullable=False),
        sa.Column("candidate_id", sa.UUID(), nullable=False),
        sa.Column("criterion_id", sa.UUID(), nullable=False),
        sa.Column("raw_score", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("normalized_score", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("rubric_level_id", sa.UUID(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_file_id", sa.UUID(), nullable=True),
        sa.Column("evidence_record_id", sa.UUID(), nullable=True),
        sa.Column("entered_by", sa.UUID(), nullable=False),
        sa.Column("entered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="SUBMITTED"),
        sa.Column("reviewed_by", sa.UUID(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("supersedes_score_id", sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_manual_eval_scores_eval", "manual_evaluation_scores", ["evaluation_id"])
    op.create_index("ix_manual_eval_scores_cand", "manual_evaluation_scores", ["candidate_id"])

    # 9. quotation_candidate_evaluation_summaries
    op.create_table(
        "quotation_candidate_evaluation_summaries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("evaluation_run_id", sa.UUID(), nullable=False),
        sa.Column("candidate_id", sa.UUID(), nullable=False),
        sa.Column("eligible_line_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_line_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("coverage_percentage", sa.Numeric(precision=10, scale=4), nullable=False, server_default="100.0000"),
        sa.Column("comparable_total", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="PEN"),
        sa.Column("price_score", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("delivery_score", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("technical_score", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("quality_score", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("compliance_score", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("commercial_terms_score", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("risk_score", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("weighted_total_score", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("tie_group_id", sa.UUID(), nullable=True),
        sa.Column("disqualified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("warnings", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["evaluation_run_id"], ["quotation_evaluation_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evaluation_run_id", "candidate_id", name="uq_eval_summary_cand"),
    )
    op.create_index("ix_quotation_cand_summaries_run", "quotation_candidate_evaluation_summaries", ["evaluation_run_id"])

    # 10. quotation_evaluation_decisions
    op.create_table(
        "quotation_evaluation_decisions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("evaluation_id", sa.UUID(), nullable=False),
        sa.Column("evaluation_run_id", sa.UUID(), nullable=False),
        sa.Column("decision_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("decision_type", sa.String(length=50), nullable=False, server_default="RECOMMEND_SINGLE_SUPPLIER"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="RECORDED"),
        sa.Column("procurement_approval_status", sa.String(length=50), nullable=False, server_default="PENDING_PHASE_035"),
        sa.Column("selected_candidate_id", sa.UUID(), nullable=True),
        sa.Column("selected_response_id", sa.UUID(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("tie_resolution_reason", sa.Text(), nullable=True),
        sa.Column("exceptions", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True),
        sa.Column("total_selected_amount", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("currency_code", sa.String(length=3), nullable=True),
        sa.Column("decision_snapshot_hash", sa.String(length=64), nullable=False),
        sa.Column("recorded_by", sa.UUID(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("supersedes_decision_id", sa.UUID(), nullable=True),
        sa.Column("superseded_by_decision_id", sa.UUID(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["evaluation_id"], ["quotation_evaluations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quotation_eval_decisions_eval", "quotation_evaluation_decisions", ["evaluation_id"])

    # 11. quotation_evaluation_decision_lines
    op.create_table(
        "quotation_evaluation_decision_lines",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("decision_id", sa.UUID(), nullable=False),
        sa.Column("quotation_request_line_id", sa.UUID(), nullable=False),
        sa.Column("selected_candidate_id", sa.UUID(), nullable=False),
        sa.Column("selected_response_id", sa.UUID(), nullable=False),
        sa.Column("selected_response_line_id", sa.UUID(), nullable=False),
        sa.Column("selected_quantity", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("selected_unit_id", sa.UUID(), nullable=False),
        sa.Column("comparable_base_quantity", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("selected_unit_price", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("selected_currency_code", sa.String(length=3), nullable=False, server_default="PEN"),
        sa.Column("selected_line_total", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="SELECTED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["decision_id"], ["quotation_evaluation_decisions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quotation_eval_decision_lines_dec", "quotation_evaluation_decision_lines", ["decision_id"])


def downgrade() -> None:
    op.drop_table("quotation_evaluation_decision_lines")
    op.drop_table("quotation_evaluation_decisions")
    op.drop_table("quotation_candidate_evaluation_summaries")
    op.drop_table("manual_evaluation_scores")
    op.drop_table("quotation_criterion_scores")
    op.drop_table("quotation_evaluation_runs")
    op.drop_table("quotation_evaluation_candidates")
    op.drop_table("quotation_evaluations")
    op.drop_table("evaluation_criterion_definitions")
    op.drop_table("supplier_evaluation_template_versions")
    op.drop_table("supplier_evaluation_templates")
