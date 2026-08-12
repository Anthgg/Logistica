"""phase 025 business partners master data

Revision ID: p270110025dc
Revises: o260110024dc
Create Date: 2026-07-28 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'p270110025dc'
down_revision = 'o260110024dc'
branch_labels = None
depends_on = None


def upgrade():
    # 1. business_partners
    op.create_table(
        'business_partners',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('partner_code', sa.String(length=30), nullable=False),
        sa.Column('normalized_partner_code', sa.String(length=30), nullable=False),
        sa.Column('legal_name', sa.String(length=200), nullable=False),
        sa.Column('trade_name', sa.String(length=200), nullable=True),
        sa.Column('person_type', sa.String(length=20), server_default='LEGAL_ENTITY', nullable=False),
        sa.Column('country_code', sa.String(length=3), server_default='PE', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='DRAFT', nullable=False),
        sa.Column('lifecycle_status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('risk_status', sa.String(length=20), server_default='NOT_EVALUATED', nullable=False),
        sa.Column('compliance_status', sa.String(length=20), server_default='NOT_EVALUATED', nullable=False),
        sa.Column('active_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('row_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('archived_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'normalized_partner_code', name='uq_partners_org_norm_code'),
    )
    op.create_index('ix_business_partners_org_id', 'business_partners', ['organization_id'])
    op.create_index('ix_business_partners_norm_code', 'business_partners', ['normalized_partner_code'])
    op.create_index('ix_business_partners_legal_name', 'business_partners', ['legal_name'])

    # 2. business_partner_versions
    op.create_table(
        'business_partner_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_partner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partners.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('legal_name', sa.String(length=200), nullable=False),
        sa.Column('trade_name', sa.String(length=200), nullable=True),
        sa.Column('person_type', sa.String(length=20), nullable=False),
        sa.Column('snapshot_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('business_partner_id', 'version', name='uq_partner_versions_partner_ver'),
    )

    # 3. business_partner_aliases
    op.create_table(
        'business_partner_aliases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_partner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partners.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alias_type', sa.String(length=30), nullable=False),
        sa.Column('previous_value', sa.String(length=200), nullable=False),
        sa.Column('current_value', sa.String(length=200), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 4. business_partner_roles
    op.create_table(
        'business_partner_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_partner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partners.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_type', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('business_partner_id', 'role_type', name='uq_partner_roles_partner_role'),
    )

    # 5. supplier_profiles
    op.create_table(
        'supplier_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_partner_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partner_roles.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('supplier_category', sa.String(length=50), nullable=True),
        sa.Column('supplies_goods', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('supplies_services', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('quality_inspection_required', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 6. customer_profiles
    op.create_table(
        'customer_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_partner_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partner_roles.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('customer_type', sa.String(length=50), server_default='STANDARD', nullable=False),
        sa.Column('requires_delivery_appointment', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 7. carrier_profiles
    op.create_table(
        'carrier_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_partner_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partner_roles.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('transport_mode', sa.String(length=30), server_default='ROAD', nullable=False),
        sa.Column('own_fleet', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('third_party_fleet', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('refrigerated_transport', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('hazardous_authorized', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 8. business_partner_identifiers
    op.create_table(
        'business_partner_identifiers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('business_partner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partners.id', ondelete='CASCADE'), nullable=False),
        sa.Column('identifier_type', sa.String(length=30), nullable=False),
        sa.Column('country_code', sa.String(length=3), server_default='PE', nullable=False),
        sa.Column('value', sa.String(length=50), nullable=False),
        sa.Column('normalized_value', sa.String(length=50), nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('verification_status', sa.String(length=30), server_default='NOT_VERIFIED', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'identifier_type', 'normalized_value', name='uq_partner_identifiers_org_type_val'),
    )
    op.create_index('ix_partner_identifiers_norm_val', 'business_partner_identifiers', ['normalized_value'])

    # 9. business_partner_addresses
    op.create_table(
        'business_partner_addresses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_partner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partners.id', ondelete='CASCADE'), nullable=False),
        sa.Column('address_type', sa.String(length=30), server_default='FISCAL', nullable=False),
        sa.Column('label', sa.String(length=100), nullable=True),
        sa.Column('address_line_1', sa.String(length=200), nullable=False),
        sa.Column('address_line_2', sa.String(length=200), nullable=True),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('province', sa.String(length=100), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('country_code', sa.String(length=3), server_default='PE', nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_delivery_address', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_billing_address', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_partner_addresses_partner_id', 'business_partner_addresses', ['business_partner_id'])

    # 10. business_partner_contacts
    op.create_table(
        'business_partner_contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_partner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partners.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contact_type', sa.String(length=30), server_default='GENERAL', nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=False),
        sa.Column('position_title', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=150), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('is_primary', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_partner_contacts_partner_id', 'business_partner_contacts', ['business_partner_id'])

    # 11. business_partner_operational_settings
    op.create_table(
        'business_partner_operational_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_partner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partners.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('default_currency_code', sa.String(length=3), server_default='PEN', nullable=False),
        sa.Column('default_language', sa.String(length=10), server_default='es', nullable=False),
        sa.Column('default_timezone', sa.String(length=50), server_default='America/Lima', nullable=False),
        sa.Column('requires_appointment', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('receiving_hours_notes', sa.Text(), nullable=True),
        sa.Column('delivery_hours_notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 12. business_partner_evaluation_templates
    op.create_table(
        'business_partner_evaluation_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('role_type', sa.String(length=30), nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=20), server_default='1.0.0', nullable=False),
        sa.Column('criteria_schema', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('score_scale', sa.Numeric(precision=5, scale=2), server_default='100.00', nullable=False),
        sa.Column('passing_score', sa.Numeric(precision=5, scale=2), server_default='70.00', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'code', 'version', name='uq_eval_templates_org_code_ver'),
    )

    # 13. business_partner_evaluations
    op.create_table(
        'business_partner_evaluations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_partner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partners.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_type', sa.String(length=30), nullable=False),
        sa.Column('evaluation_type', sa.String(length=30), server_default='PERIODIC', nullable=False),
        sa.Column('total_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('risk_level', sa.String(length=20), server_default='LOW', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='APPROVED', nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('evaluator_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_partner_evaluations_partner_id', 'business_partner_evaluations', ['business_partner_id'])

    # 14. business_partner_evaluation_criteria
    op.create_table(
        'business_partner_evaluation_criteria',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('evaluation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partner_evaluations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('criterion_code', sa.String(length=50), nullable=False),
        sa.Column('criterion_name', sa.String(length=100), nullable=False),
        sa.Column('weight', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('weighted_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('observations', sa.Text(), nullable=True),
    )

    # 15. business_partner_document_requirements
    op.create_table(
        'business_partner_document_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('role_type', sa.String(length=30), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('required', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('blocking', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('requires_expiration', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('warning_days_before_expiration', sa.Integer(), server_default='30', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'role_type', 'document_type', name='uq_doc_reqs_org_role_doctype'),
    )

    # 16. business_partner_documents
    op.create_table(
        'business_partner_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_partner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partners.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_type', sa.String(length=30), nullable=True),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('document_number', sa.String(length=50), nullable=True),
        sa.Column('issuer', sa.String(length=100), nullable=True),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_status', sa.String(length=30), server_default='NOT_VERIFIED', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('file_reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_partner_documents_partner_id', 'business_partner_documents', ['business_partner_id'])


def downgrade():
    op.drop_table('business_partner_documents')
    op.drop_table('business_partner_document_requirements')
    op.drop_table('business_partner_evaluation_criteria')
    op.drop_table('business_partner_evaluations')
    op.drop_table('business_partner_evaluation_templates')
    op.drop_table('business_partner_operational_settings')
    op.drop_table('business_partner_contacts')
    op.drop_table('business_partner_addresses')
    op.drop_table('business_partner_identifiers')
    op.drop_table('carrier_profiles')
    op.drop_table('customer_profiles')
    op.drop_table('supplier_profiles')
    op.drop_table('business_partner_roles')
    op.drop_table('business_partner_aliases')
    op.drop_table('business_partner_versions')
    op.drop_table('business_partners')
