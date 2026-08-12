"""Phase 029 - Driver Master Data

Revision ID: t310110029dc
Revises: s290110028dc
Create Date: 2026-07-29 00:36:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 't310110029dc'
down_revision = 't290110029po'
branch_labels = None
depends_on = None


def upgrade():
    # 1. drivers
    op.create_table(
        'drivers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('driver_code', sa.String(30), nullable=False),
        sa.Column('normalized_driver_code', sa.String(30), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('middle_name', sa.String(100), nullable=True),
        sa.Column('paternal_last_name', sa.String(100), nullable=False),
        sa.Column('maternal_last_name', sa.String(100), nullable=True),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('nationality_country_code', sa.String(3), nullable=False, server_default='PE'),
        sa.Column('primary_identity_document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('primary_license_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('current_carrier_assignment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('primary_contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('current_photo_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('lifecycle_status', sa.String(20), nullable=False, server_default='DRAFT'),
        sa.Column('compliance_status', sa.String(30), nullable=False, server_default='NOT_EVALUATED'),
        sa.Column('eligibility_status', sa.String(30), nullable=False, server_default='NOT_EVALUATED'),
        sa.Column('active_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_link_status', sa.String(20), nullable=False, server_default='NOT_LINKED'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('row_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('suspended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('suspended_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('suspension_reason', sa.Text(), nullable=True),
        sa.Column('blocked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('blocked_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('block_reason', sa.Text(), nullable=True),
        sa.Column('retired_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retired_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('retirement_reason', sa.Text(), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('archive_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'normalized_driver_code', name='uq_drivers_org_code'),
    )
    op.create_index('ix_drivers_org', 'drivers', ['organization_id'])
    op.create_index('ix_drivers_norm_code', 'drivers', ['normalized_driver_code'])
    op.create_index('ix_drivers_display_name', 'drivers', ['display_name'])
    op.create_index('ix_drivers_lifecycle', 'drivers', ['lifecycle_status'])

    # 2. driver_versions
    op.create_table(
        'driver_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drivers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('identity_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('license_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('categories_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('carrier_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('contact_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('photo_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('restrictions_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('compliance_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('eligibility_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('driver_id', 'version', name='uq_driver_versions_num'),
    )
    op.create_index('ix_driver_versions_driver', 'driver_versions', ['driver_id'])

    # 3. driver_identity_documents
    op.create_table(
        'driver_identity_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drivers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_type', sa.String(20), nullable=False, server_default='DNI'),
        sa.Column('country_code', sa.String(3), nullable=False, server_default='PE'),
        sa.Column('value', sa.String(50), nullable=False),
        sa.Column('normalized_value', sa.String(50), nullable=False),
        sa.Column('masked_value', sa.String(50), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('verification_status', sa.String(30), nullable=False, server_default='NOT_VERIFIED'),
        sa.Column('verification_source', sa.String(50), nullable=True),
        sa.Column('issued_at', sa.Date(), nullable=True),
        sa.Column('expires_at', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'document_type', 'normalized_value', name='uq_driver_id_docs_org_val'),
    )
    op.create_index('ix_driver_id_docs_norm_val', 'driver_identity_documents', ['normalized_value'])

    # 4. driver_licenses
    op.create_table(
        'driver_licenses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drivers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('country_code', sa.String(3), nullable=False, server_default='PE'),
        sa.Column('issuing_authority', sa.String(100), nullable=False, server_default='MTC'),
        sa.Column('license_number', sa.String(50), nullable=False),
        sa.Column('normalized_license_number', sa.String(50), nullable=False),
        sa.Column('masked_license_number', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='DRAFT'),
        sa.Column('verification_status', sa.String(30), nullable=False, server_default='NOT_VERIFIED'),
        sa.Column('verification_source', sa.String(50), nullable=True),
        sa.Column('issued_at', sa.Date(), nullable=True),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('expires_at', sa.Date(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('suspension_start', sa.Date(), nullable=True),
        sa.Column('suspension_end', sa.Date(), nullable=True),
        sa.Column('primary_license', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('file_reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_reference', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('row_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'issuing_authority', 'normalized_license_number', name='uq_driver_licenses_org_auth_num'),
    )
    op.create_index('ix_driver_licenses_norm_num', 'driver_licenses', ['normalized_license_number'])
    op.create_index('ix_driver_licenses_expires', 'driver_licenses', ['expires_at'])

    # 5. driver_license_categories
    op.create_table(
        'driver_license_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('country_code', sa.String(3), nullable=False, server_default='PE'),
        sa.Column('jurisdiction_code', sa.String(10), nullable=True),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('normalized_code', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_group', sa.String(50), nullable=True),
        sa.Column('minimum_age', sa.Integer(), nullable=True),
        sa.Column('hierarchy_level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('system_defined', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version', sa.String(20), nullable=False, server_default='1.0.0'),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_to', sa.Date(), nullable=True),
        sa.Column('legal_reference', sa.String(200), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('country_code', 'normalized_code', name='uq_driver_license_cats_country_code'),
    )

    # 6. driver_license_category_assignments
    op.create_table(
        'driver_license_category_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('driver_license_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('driver_licenses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('driver_license_categories.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('expires_at', sa.Date(), nullable=False),
        sa.Column('restrictions_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('source_type', sa.String(30), nullable=False, server_default='MANUAL_ENTRY'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 7. driver_license_restrictions
    op.create_table(
        'driver_license_restrictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('driver_license_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('driver_licenses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('restriction_code', sa.String(30), nullable=False),
        sa.Column('restriction_type', sa.String(40), nullable=False, server_default='LICENSE_ANNOTATION'),
        sa.Column('description', sa.String(250), nullable=False),
        sa.Column('source_type', sa.String(30), nullable=False, server_default='LICENSE_ANNOTATION'),
        sa.Column('severity', sa.String(20), nullable=False, server_default='MEDIUM'),
        sa.Column('blocking', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('expires_at', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 8. driver_license_vehicle_type_rules
    op.create_table(
        'driver_license_vehicle_type_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('jurisdiction_code', sa.String(10), nullable=False, server_default='PE'),
        sa.Column('license_category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('driver_license_categories.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('vehicle_type', sa.String(50), nullable=False),
        sa.Column('body_type', sa.String(50), nullable=True),
        sa.Column('allowed', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('requires_additional_certificate', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_to', sa.Date(), nullable=True),
        sa.Column('legal_reference', sa.String(200), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 9. driver_carrier_assignments
    op.create_table(
        'driver_carrier_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drivers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('carrier_business_partner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partners.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('carrier_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partner_roles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('assignment_type', sa.String(30), nullable=False, server_default='INTERNAL'),
        sa.Column('employment_reference', sa.String(100), nullable=True),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='CURRENT'),
        sa.Column('authorization_reference', sa.String(100), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 10. driver_contacts
    op.create_table(
        'driver_contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drivers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contact_type', sa.String(20), nullable=False, server_default='PERSONAL'),
        sa.Column('email', sa.String(150), nullable=True),
        sa.Column('phone', sa.String(30), nullable=True),
        sa.Column('mobile_phone', sa.String(30), nullable=True),
        sa.Column('country_calling_code', sa.String(5), nullable=True, server_default='+51'),
        sa.Column('address_line', sa.String(250), nullable=True),
        sa.Column('district', sa.String(100), nullable=True),
        sa.Column('province', sa.String(100), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('country_code', sa.String(3), nullable=False, server_default='PE'),
        sa.Column('preferred_channel', sa.String(20), nullable=True, server_default='PHONE'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 11. driver_emergency_contacts
    op.create_table(
        'driver_emergency_contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drivers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=False),
        sa.Column('relationship_label', sa.String(50), nullable=False),
        sa.Column('phone', sa.String(30), nullable=False),
        sa.Column('alternate_phone', sa.String(30), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('consent_status', sa.String(20), nullable=False, server_default='GRANTED'),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 12. driver_photos
    op.create_table(
        'driver_photos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drivers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('photo_type', sa.String(30), nullable=False, server_default='PROFILE'),
        sa.Column('file_reference_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('captured_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_type', sa.String(30), nullable=False, server_default='INTERNAL_CAPTURE'),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('mime_type', sa.String(50), nullable=True, server_default='image/jpeg'),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('retention_policy', sa.String(50), nullable=False, server_default='STANDARD_5_YEARS'),
        sa.Column('consent_reference', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revocation_reason', sa.Text(), nullable=True),
    )

    # 13. driver_documents
    op.create_table(
        'driver_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drivers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('document_number', sa.String(50), nullable=True),
        sa.Column('issuer', sa.String(150), nullable=True),
        sa.Column('issued_at', sa.Date(), nullable=True),
        sa.Column('valid_from', sa.Date(), nullable=True),
        sa.Column('expires_at', sa.Date(), nullable=True),
        sa.Column('verification_status', sa.String(30), nullable=False, server_default='NOT_VERIFIED'),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('file_reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_type', sa.String(30), nullable=False, server_default='MANUAL_UPLOAD'),
        sa.Column('source_reference', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 14. driver_document_requirements
    op.create_table(
        'driver_document_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('carrier_category_scope', sa.String(50), nullable=True),
        sa.Column('vehicle_type_scope', sa.String(50), nullable=True),
        sa.Column('operation_type_scope', sa.String(50), nullable=True),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('blocking', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('requires_expiration', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('warning_days_before_expiration', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('minimum_verification_status', sa.String(30), nullable=False, server_default='METADATA_REVIEWED'),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_to', sa.Date(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 15. driver_operational_restrictions
    op.create_table(
        'driver_operational_restrictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drivers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('restriction_type', sa.String(40), nullable=False, server_default='MANUAL_BLOCK'),
        sa.Column('source_type', sa.String(30), nullable=False, server_default='ADMINISTRATIVE'),
        sa.Column('severity', sa.String(20), nullable=False, server_default='CRITICAL'),
        sa.Column('blocking', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('description', sa.String(250), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revocation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 16. driver_user_account_links
    op.create_table(
        'driver_user_account_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drivers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='LINKED'),
        sa.Column('linked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('linked_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revocation_reason', sa.Text(), nullable=True),
        sa.UniqueConstraint('driver_id', 'user_id', name='uq_driver_user_link'),
    )


def downgrade():
    op.drop_table('driver_user_account_links')
    op.drop_table('driver_operational_restrictions')
    op.drop_table('driver_document_requirements')
    op.drop_table('driver_documents')
    op.drop_table('driver_photos')
    op.drop_table('driver_emergency_contacts')
    op.drop_table('driver_contacts')
    op.drop_table('driver_carrier_assignments')
    op.drop_table('driver_license_vehicle_type_rules')
    op.drop_table('driver_license_restrictions')
    op.drop_table('driver_license_category_assignments')
    op.drop_table('driver_license_categories')
    op.drop_table('driver_licenses')
    op.drop_table('driver_identity_documents')
    op.drop_table('driver_versions')
    op.drop_table('drivers')
