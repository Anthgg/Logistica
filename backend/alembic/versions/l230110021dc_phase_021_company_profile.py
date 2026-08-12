"""add company profile tables phase 021

Revision ID: l230110021dc
Revises: k220110020dc
Create Date: 2026-07-27 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'l230110021dc'
down_revision = 'k220110020dc'
branch_labels = None
depends_on = None


def upgrade():
    # 1. organization_profiles
    op.create_table(
        'organization_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('legal_name', sa.String(length=256), nullable=False),
        sa.Column('trade_name', sa.String(length=256), nullable=True),
        sa.Column('ruc', sa.String(length=11), nullable=False),
        sa.Column('legal_entity_type', sa.String(length=64), nullable=True),
        sa.Column('economic_activity', sa.String(length=256), nullable=True),
        sa.Column('website', sa.String(length=256), nullable=True),
        sa.Column('primary_email', sa.String(length=128), nullable=True),
        sa.Column('primary_phone', sa.String(length=32), nullable=True),
        sa.Column('country_code', sa.String(length=2), server_default='PE', nullable=False),
        sa.Column('locale', sa.String(length=10), server_default='es-PE', nullable=False),
        sa.Column('timezone', sa.String(length=50), server_default='America/Lima', nullable=False),
        sa.Column('default_currency', sa.String(length=3), server_default='PEN', nullable=False),
        sa.Column('document_language', sa.String(length=10), server_default='es', nullable=False),
        sa.Column('profile_status', sa.String(length=32), server_default='DRAFT', nullable=False),
        sa.Column('active_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verification_status', sa.String(length=32), server_default='FORMAT_VALID', nullable=False),
        sa.Column('verification_source', sa.String(length=64), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', name='uq_org_profile_organization'),
        sa.UniqueConstraint('ruc', name='uq_org_profile_ruc'),
    )
    op.create_index('ix_org_profiles_org_id', 'organization_profiles', ['organization_id'])
    op.create_index('ix_org_profiles_ruc', 'organization_profiles', ['ruc'])

    # 2. organization_profile_versions
    op.create_table(
        'organization_profile_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='DRAFT', nullable=False),
        sa.Column('legal_name', sa.String(length=256), nullable=False),
        sa.Column('trade_name', sa.String(length=256), nullable=True),
        sa.Column('ruc', sa.String(length=11), nullable=False),
        sa.Column('institutional_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_profile_id'], ['organization_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_profile_id', 'version', name='uq_org_profile_ver'),
    )
    op.create_index('ix_org_prof_ver_profile_id', 'organization_profile_versions', ['organization_profile_id'])

    # Add FK from organization_profiles.active_version_id to organization_profile_versions.id
    op.create_foreign_key(
        'fk_org_profile_active_version',
        'organization_profiles',
        'organization_profile_versions',
        ['active_version_id'],
        ['id'],
        ondelete='SET NULL',
    )

    # 3. organization_addresses
    op.create_table(
        'organization_addresses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('address_type', sa.String(length=32), nullable=False),
        sa.Column('label', sa.String(length=128), nullable=False),
        sa.Column('address_line', sa.String(length=512), nullable=False),
        sa.Column('district', sa.String(length=128), nullable=True),
        sa.Column('province', sa.String(length=128), nullable=True),
        sa.Column('department', sa.String(length=128), nullable=True),
        sa.Column('postal_code', sa.String(length=32), nullable=True),
        sa.Column('country_code', sa.String(length=2), server_default='PE', nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_document_address', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('verification_status', sa.String(length=32), server_default='FORMAT_VALID', nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['branch_id'], ['logistics_branches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_org_addresses_org_id', 'organization_addresses', ['organization_id'])

    # 4. organization_contacts
    op.create_table(
        'organization_contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('contact_type', sa.String(length=32), nullable=False),
        sa.Column('label', sa.String(length=128), nullable=False),
        sa.Column('full_name', sa.String(length=256), nullable=True),
        sa.Column('position', sa.String(length=128), nullable=True),
        sa.Column('email', sa.String(length=128), nullable=True),
        sa.Column('phone', sa.String(length=32), nullable=True),
        sa.Column('extension', sa.String(length=16), nullable=True),
        sa.Column('website', sa.String(length=256), nullable=True),
        sa.Column('is_primary', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('show_in_documents', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('document_families', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['branch_id'], ['logistics_branches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_org_contacts_org_id', 'organization_contacts', ['organization_id'])

    # 5. organization_assets
    op.create_table(
        'organization_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_type', sa.String(length=32), nullable=False),
        sa.Column('filename', sa.String(length=256), nullable=False),
        sa.Column('mime_type', sa.String(length=64), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('storage_provider', sa.String(length=32), server_default='local', nullable=False),
        sa.Column('storage_key', sa.String(length=512), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('asset_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_org_assets_org_id', 'organization_assets', ['organization_id'])

    # 6. authorized_signers
    op.create_table(
        'authorized_signers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('full_name', sa.String(length=256), nullable=False),
        sa.Column('position_title', sa.String(length=128), nullable=False),
        sa.Column('department', sa.String(length=128), nullable=True),
        sa.Column('document_number_masked', sa.String(length=32), nullable=True),
        sa.Column('authorization_reference', sa.String(length=128), nullable=True),
        sa.Column('authorization_type', sa.String(length=64), server_default='LEGAL_REPRESENTATIVE', nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('signature_asset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('stamp_asset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('can_sign_all_branches', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('branch_scope', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('document_family_scope', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('document_type_scope', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('max_amount', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('currency_code', sa.String(length=3), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revocation_reason', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['signature_asset_id'], ['organization_assets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['stamp_asset_id'], ['organization_assets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_auth_signers_org_id', 'authorized_signers', ['organization_id'])

    # 7. organization_document_settings
    op.create_table(
        'organization_document_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('profile_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('document_logo_asset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('default_address_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('default_contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('show_ruc', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('show_trade_name', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('show_legal_name', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('show_address', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('show_contact', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('show_template_version', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('show_renderer_version', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('show_partial_hash', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('show_qr', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('show_page_number', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('confidentiality_text', sa.String(length=512), nullable=True),
        sa.Column('footer_text', sa.String(length=512), nullable=True),
        sa.Column('default_locale', sa.String(length=10), server_default='es-PE', nullable=False),
        sa.Column('default_timezone', sa.String(length=50), server_default='America/Lima', nullable=False),
        sa.Column('default_currency', sa.String(length=3), server_default='PEN', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['default_address_id'], ['organization_addresses.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['default_contact_id'], ['organization_contacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['document_logo_asset_id'], ['organization_assets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['profile_version_id'], ['organization_profile_versions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', name='uq_org_doc_settings_org'),
    )
    op.create_index('ix_org_doc_settings_org_id', 'organization_document_settings', ['organization_id'])

    # 8. organization_numbering_display_policies
    op.create_table(
        'organization_numbering_display_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('document_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code_standard_version', sa.String(length=32), server_default='1.0.0', nullable=False),
        sa.Column('document_site_code_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('display_pattern', sa.String(length=128), server_default='{TYPE}-{SITE}-{YEAR}-{SEQUENCE}', nullable=False),
        sa.Column('sequence_padding', sa.Integer(), server_default='6', nullable=False),
        sa.Column('show_internal_code', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('show_external_series', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('show_external_number', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['branch_id'], ['logistics_branches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['document_site_code_id'], ['document_site_codes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['document_type_id'], ['document_types.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_org_numb_policies_org_id', 'organization_numbering_display_policies', ['organization_id'])


def downgrade():
    op.drop_table('organization_numbering_display_policies')
    op.drop_table('organization_document_settings')
    op.drop_table('authorized_signers')
    op.drop_table('organization_assets')
    op.drop_table('organization_contacts')
    op.drop_table('organization_addresses')
    op.drop_constraint('fk_org_profile_active_version', 'organization_profiles', type_='foreignkey')
    op.drop_table('organization_profile_versions')
    op.drop_table('organization_profiles')
