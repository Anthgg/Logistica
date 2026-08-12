"""Phase 040 reception differences.

Revision ID: bb400110040dc
Revises: ac390110039dc
Deployment remains an explicit operational action; the migration itself is safe
to apply through the normal Alembic chain.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.database.base import Base
from app.models import registry as _registry  # noqa: F401
from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.models import PHASE_040_TABLES

revision: str = "bb400110040dc"
down_revision: Union[str, Sequence[str], None] = "ac390110039dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    QTY = {"precision": 38, "scale": 18}

    # reception_difference_cases
    op.create_table(
        "reception_difference_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("case_code", sa.String(80), nullable=False),
        sa.Column("normalized_case_code", sa.String(80), nullable=False),
        sa.Column("inbound_receipt_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inbound_receipts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("inbound_receipt_revision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inbound_receipt_revisions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("unloading_operation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("gate_check_in_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("appointment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("arrival_notice_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("supplier_business_partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("supplier_snapshot", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("carrier_business_partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("carrier_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="DRAFT"),
        sa.Column("source_type", sa.String(40), nullable=False, server_default="RECEIPT_CANDIDATES"),
        sa.Column("severity", sa.String(20), nullable=False, server_default="LOW"),
        sa.Column("item_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("open_item_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("critical_item_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("evidence_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("proposed_responsible_party_type", sa.String(40), nullable=True),
        sa.Column("proposed_responsible_party_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("responsibility_status", sa.String(40), nullable=False, server_default="UNDETERMINED"),
        sa.Column("active_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("current_revision_number", sa.Integer, nullable=False, server_default="0"),
        sa.Column("document_instance_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issued_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disputed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.Text, nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("row_version", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.UniqueConstraint("organization_id", "normalized_case_code", name="uq_diff_case_org_code"),
        sa.CheckConstraint("row_version >= 1", name="ck_diff_case_row_version"),
    )
    op.create_index("ix_diff_case_org", "reception_difference_cases", ["organization_id"])
    op.create_index("ix_diff_case_warehouse", "reception_difference_cases", ["warehouse_id"])
    op.create_index("ix_diff_case_receipt", "reception_difference_cases", ["inbound_receipt_id"])
    op.create_index("ix_diff_case_supplier", "reception_difference_cases", ["supplier_business_partner_id"])
    op.create_index("ix_diff_case_carrier", "reception_difference_cases", ["carrier_business_partner_id"])
    op.create_index("ix_diff_case_status", "reception_difference_cases", ["status"])
    op.create_index("ix_diff_case_severity", "reception_difference_cases", ["severity"])
    op.create_index("ix_diff_case_responsibility", "reception_difference_cases", ["responsibility_status"])
    op.create_index("ix_diff_case_issued", "reception_difference_cases", ["issued_at"])
    op.create_index("ix_diff_case_updated", "reception_difference_cases", ["updated_at"])

    # reception_difference_case_revisions
    op.create_table(
        "reception_difference_case_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("difference_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("revision_number", sa.Integer, nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="EDITABLE"),
        sa.Column("source_snapshot", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("difference_items_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("evidence_manifest_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("responsibility_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("review_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("approval_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("acknowledgement_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_from_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("change_reason", sa.Text, nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("difference_case_id", "revision_number", name="uq_diff_case_revision_number"),
    )
    op.create_index("ix_diff_case_rev_case", "reception_difference_case_revisions", ["difference_case_id"])

    # reception_difference_items
    op.create_table(
        "reception_difference_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("difference_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("case_revision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reception_difference_case_revisions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("item_number", sa.Integer, nullable=False),
        sa.Column("source_candidate_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("difference_type", sa.String(60), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="LOW"),
        sa.Column("status", sa.String(30), nullable=False, server_default="OPEN"),
        sa.Column("purchase_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("purchase_order_line_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expected_line_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("received_line_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sku_snapshot", sa.String(120), nullable=True),
        sa.Column("product_name_snapshot", sa.String(500), nullable=True),
        sa.Column("expected_quantity", sa.Numeric(**QTY), nullable=True),
        sa.Column("expected_unit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expected_base_quantity", sa.Numeric(**QTY), nullable=True),
        sa.Column("observed_quantity", sa.Numeric(**QTY), nullable=True),
        sa.Column("observed_unit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("observed_base_quantity", sa.Numeric(**QTY), nullable=True),
        sa.Column("difference_quantity", sa.Numeric(**QTY), nullable=True),
        sa.Column("difference_unit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("difference_base_quantity", sa.Numeric(**QTY), nullable=True),
        sa.Column("lot_observation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("serial_observation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expiration_observation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("transport_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("gate_seal_inspection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("unloading_seal_opening_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("detection_source", sa.String(40), nullable=False, server_default="RECEIPT_CANDIDATES"),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("detected_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("detected_by_service", sa.String(120), nullable=True),
        sa.Column("requires_evidence", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("requires_responsibility", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("requires_quality_review", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("future_quarantine_recommended", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("future_claim_recommended", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("row_version", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.UniqueConstraint("case_revision_id", "item_number", name="uq_diff_item_revision_number"),
        sa.CheckConstraint("row_version >= 1", name="ck_diff_item_row_version"),
    )
    op.create_index("ix_diff_item_case", "reception_difference_items", ["difference_case_id"])
    op.create_index("ix_diff_item_candidate", "reception_difference_items", ["source_candidate_id"])
    op.create_index("ix_diff_item_type", "reception_difference_items", ["difference_type"])
    op.create_index("ix_diff_item_category", "reception_difference_items", ["category"])
    op.create_index("ix_diff_item_severity", "reception_difference_items", ["severity"])
    op.create_index("ix_diff_item_product", "reception_difference_items", ["product_id"])
    op.create_index("ix_diff_item_po_line", "reception_difference_items", ["purchase_order_line_id"])
    op.create_index("ix_diff_item_status", "reception_difference_items", ["status"])

    # reception_damage_details
    op.create_table(
        "reception_damage_details",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("difference_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reception_difference_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("damage_scope", sa.String(40), nullable=False),
        sa.Column("damage_type", sa.String(40), nullable=False),
        sa.Column("affected_quantity", sa.Numeric(**QTY), nullable=True),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("affected_base_quantity", sa.Numeric(**QTY), nullable=True),
        sa.Column("packaging_level", sa.String(40), nullable=True),
        sa.Column("visual_description", sa.Text, nullable=True),
        sa.Column("functional_impact_declared", sa.Text, nullable=True),
        sa.Column("safety_concern", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("contamination_concern", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("temperature_concern", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("evidence_required", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_diff_damage_item", "reception_damage_details", ["difference_item_id"])

    # reception_difference_evidence_links
    op.create_table(
        "reception_difference_evidence_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("difference_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("difference_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reception_difference_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("evidence_record_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("file_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("evidence_type", sa.String(40), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False, server_default="UPLOAD"),
        sa.Column("classification", sa.String(40), nullable=False, server_default="STANDARD"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("linked_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_diff_evidence_case", "reception_difference_evidence_links", ["difference_case_id"])
    op.create_index("ix_diff_evidence_item", "reception_difference_evidence_links", ["difference_item_id"])
    op.create_index("ix_diff_evidence_file", "reception_difference_evidence_links", ["file_asset_id"])

    # reception_difference_responsible_parties
    op.create_table(
        "reception_difference_responsible_parties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("difference_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("difference_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reception_difference_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("party_type", sa.String(40), nullable=False),
        sa.Column("business_partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("organization_unit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("responsible_snapshot", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("responsibility_role", sa.String(30), nullable=False, server_default="UNDETERMINED"),
        sa.Column("responsibility_status", sa.String(40), nullable=False, server_default="PROPOSED"),
        sa.Column("proposed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("proposed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disputed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("disputed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dispute_reason", sa.Text, nullable=True),
        sa.Column("allocation_percentage", sa.Numeric(**QTY), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_diff_resp_case", "reception_difference_responsible_parties", ["difference_case_id"])
    op.create_index("ix_diff_resp_type", "reception_difference_responsible_parties", ["party_type"])
    op.create_index("ix_diff_resp_status", "reception_difference_responsible_parties", ["responsibility_status"])

    # reception_difference_reviews
    op.create_table(
        "reception_difference_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("difference_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("review_type", sa.String(40), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("reviewer_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_snapshot", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("findings", sa.Text, nullable=True),
        sa.Column("blocking_issues", postgresql.JSONB, nullable=True),
        sa.Column("requested_changes", postgresql.JSONB, nullable=True),
        sa.Column("recommendation", sa.Text, nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_diff_review_case", "reception_difference_reviews", ["difference_case_id"])

    # reception_difference_approvals
    op.create_table(
        "reception_difference_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("difference_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("approval_level", sa.Integer, nullable=False, server_default="1"),
        sa.Column("approver_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approver_snapshot", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("decision", sa.String(40), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("policy_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("step_up_assurance_summary", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_diff_approval_case", "reception_difference_approvals", ["difference_case_id"])

    # reception_difference_acknowledgements
    op.create_table(
        "reception_difference_acknowledgements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("difference_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("party_type", sa.String(40), nullable=False),
        sa.Column("business_partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("external_actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("acknowledgement_type", sa.String(40), nullable=False),
        sa.Column("statement", sa.Text, nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("evidence_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_channel", sa.String(40), nullable=False, server_default="INTERNAL"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_diff_ack_case", "reception_difference_acknowledgements", ["difference_case_id"])

    # reception_difference_follow_up_recommendations
    op.create_table(
        "reception_difference_follow_up_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reception_difference_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recommendation_type", sa.String(60), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("target_module", sa.String(60), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_diff_followup_case", "reception_difference_follow_up_recommendations", ["case_id"])

    # reception_difference_document_packages
    op.create_table(
        "reception_difference_document_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("difference_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reception_difference_cases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("package_type", sa.String(30), nullable=False, server_default="DIF_PACKAGE"),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("file_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_diff_pkg_case", "reception_difference_document_packages", ["difference_case_id"])

    # reception_difference_metrics_projection
    op.create_table(
        "reception_difference_metrics_projection",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reception_difference_cases.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("critical_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("quantity_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("product_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("condition_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("identification_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("documentation_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("seal_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("evidence_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("photo_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("responsible_parties_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Seed DocumentType DIF if not exists
    op.execute("""
        INSERT INTO document_types (
            id, family_id, code, name, description, origin_type,
            owner_module, resource_type, operation_type, catalog_status,
            created_at, updated_at
        )
        SELECT gen_random_uuid(), (SELECT id FROM document_families WHERE code = 'INBOUND'), 'DIF', 'Acta de Diferencias', 'Documento oficial de formalización de diferencias de recepción', 'INTERNAL_GENERATED', 'inbound', 'reception_difference', 'record_difference', 'ACTIVE', now(), now()
        WHERE NOT EXISTS (SELECT 1 FROM document_types WHERE code = 'DIF');
    """)


def downgrade() -> None:
    op.drop_table("reception_difference_metrics_projection")
    op.drop_table("reception_difference_document_packages")
    op.drop_table("reception_difference_follow_up_recommendations")
    op.drop_table("reception_difference_acknowledgements")
    op.drop_table("reception_difference_approvals")
    op.drop_table("reception_difference_reviews")
    op.drop_table("reception_difference_responsible_parties")
    op.drop_table("reception_difference_evidence_links")
    op.drop_table("reception_damage_details")
    op.drop_table("reception_difference_items")
    op.drop_table("reception_difference_case_revisions")
    op.drop_table("reception_difference_cases")
