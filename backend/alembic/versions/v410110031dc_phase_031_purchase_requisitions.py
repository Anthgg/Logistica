"""Phase 031 - Purchase Requisitions & Cost Centers

Revision ID: v410110031dc
Revises: u320110030dc
Create Date: 2026-07-29 02:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'v410110031dc'
down_revision = 'u320110030dc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. cost_centers
    op.create_table(
        'cost_centers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_branches.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('normalized_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('responsible_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('parent_cost_center_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cost_centers.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('row_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('organization_id', 'normalized_code', name='uq_cost_centers_org_normalized_code'),
        sa.CheckConstraint('parent_cost_center_id != id', name='ck_cost_center_no_self_parent'),
    )
    op.create_index('ix_cost_centers_org_code', 'cost_centers', ['organization_id', 'normalized_code'])
    op.create_index('ix_cost_centers_status', 'cost_centers', ['organization_id', 'status'])

    # 2. purchase_requisitions
    op.create_table(
        'purchase_requisitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_branches.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('requisition_code', sa.String(length=60), nullable=True),
        sa.Column('normalized_requisition_code', sa.String(length=60), nullable=True),
        sa.Column('document_instance_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('document_series_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('requester_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requester_name_snapshot', sa.String(length=200), nullable=False),
        sa.Column('requester_area', sa.String(length=150), nullable=True),
        sa.Column('cost_center_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cost_centers.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('cost_center_snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='NORMAL'),
        sa.Column('required_date', sa.Date(), nullable=False),
        sa.Column('destination_warehouse_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('delivery_location_description', sa.Text(), nullable=True),
        sa.Column('justification', sa.Text(), nullable=False),
        sa.Column('business_purpose', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DRAFT'),
        sa.Column('current_revision_number', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('active_revision_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('submitted_revision_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_revision_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('returned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('returned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('withdrawn_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('withdrawn_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_decision_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('row_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('organization_id', 'normalized_requisition_code', name='uq_purchase_req_org_code'),
    )
    op.create_index('ix_pr_org_status', 'purchase_requisitions', ['organization_id', 'status'])
    op.create_index('ix_pr_requester', 'purchase_requisitions', ['organization_id', 'requester_user_id'])
    op.create_index('ix_pr_cost_center', 'purchase_requisitions', ['organization_id', 'cost_center_id'])
    op.create_index('ix_pr_required_date', 'purchase_requisitions', ['organization_id', 'required_date'])

    # 3. purchase_requisition_revisions
    op.create_table(
        'purchase_requisition_revisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('requisition_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_requisitions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('revision_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='EDITABLE'),
        sa.Column('branch_snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('requester_snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('cost_center_snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('required_date', sa.Date(), nullable=False),
        sa.Column('destination_snapshot', postgresql.JSONB(), nullable=True),
        sa.Column('justification', sa.Text(), nullable=False),
        sa.Column('business_purpose', sa.Text(), nullable=True),
        sa.Column('line_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_requested_base_quantity', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('created_from_revision_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('frozen_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('requisition_id', 'revision_number', name='uq_purchase_req_revision_number'),
    )
    op.create_index('ix_prr_requisition_status', 'purchase_requisition_revisions', ['requisition_id', 'status'])

    # 4. purchase_requisition_lines
    op.create_table(
        'purchase_requisition_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('requisition_revision_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_requisition_revisions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('product_versions.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('sku_snapshot', sa.String(length=50), nullable=False),
        sa.Column('product_name_snapshot', sa.String(length=200), nullable=False),
        sa.Column('product_description_snapshot', sa.Text(), nullable=True),
        sa.Column('requested_quantity', sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column('requested_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('base_quantity', sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column('base_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('conversion_rule_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('conversion_factor_snapshot', sa.Numeric(precision=38, scale=18), nullable=True),
        sa.Column('required_date', sa.Date(), nullable=True),
        sa.Column('destination_warehouse_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('line_justification', sa.Text(), nullable=True),
        sa.Column('specifications', postgresql.JSONB(), nullable=True),
        sa.Column('manufacturer_reference', sa.String(length=200), nullable=True),
        sa.Column('preferred_brand_reference', sa.String(length=200), nullable=True),
        sa.Column('priority_override', sa.String(length=20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('row_version', sa.Integer(), nullable=False, server_default='1'),
        sa.UniqueConstraint('requisition_revision_id', 'line_number', name='uq_purchase_req_line_number'),
        sa.CheckConstraint('requested_quantity > 0', name='ck_prl_requested_qty_positive'),
        sa.CheckConstraint('base_quantity > 0', name='ck_prl_base_qty_positive'),
    )
    op.create_index('ix_prl_revision_status', 'purchase_requisition_lines', ['requisition_revision_id', 'status'])
    op.create_index('ix_prl_product', 'purchase_requisition_lines', ['product_id'])

    # 5. purchase_requisition_decisions
    op.create_table(
        'purchase_requisition_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('requisition_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_requisitions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('revision_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_requisition_revisions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('decision_type', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('decided_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('conditions', postgresql.JSONB(), nullable=True),
        sa.Column('approval_policy_code', sa.String(length=50), nullable=False, server_default='SINGLE_STEP_BASIC'),
        sa.Column('approval_policy_version', sa.String(length=20), nullable=False, server_default='1.0.0'),
        sa.Column('step_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_final', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('previous_decision_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_prd_requisition_final', 'purchase_requisition_decisions', ['requisition_id', 'is_final'])
    op.create_index('ix_prd_decided_by', 'purchase_requisition_decisions', ['decided_by'])

    # 6. purchase_requisition_comments
    op.create_table(
        'purchase_requisition_comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('requisition_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_requisitions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('revision_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('comment_type', sa.String(length=30), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('visibility', sa.String(length=40), nullable=False, server_default='INTERNAL'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
    )
    op.create_index('ix_prc_requisition_type', 'purchase_requisition_comments', ['requisition_id', 'comment_type'])

    # 7. purchase_requisition_duplicate_candidates
    op.create_table(
        'purchase_requisition_duplicate_candidates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_requisition_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_requisitions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_requisition_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_requisitions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('score', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('detection_method', sa.String(length=50), nullable=False, server_default='HEURISTIC_BASIC'),
        sa.Column('override_justification', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('purchase_requisition_duplicate_candidates')
    op.drop_table('purchase_requisition_comments')
    op.drop_table('purchase_requisition_decisions')
    op.drop_table('purchase_requisition_lines')
    op.drop_table('purchase_requisition_revisions')
    op.drop_table('purchase_requisition_requisitions')
    op.drop_table('cost_centers')
