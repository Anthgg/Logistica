"""Phase 027 — Master Vehicle Management Migration.

Revision ID: r300110027dc
Revises: q280110026dc
Create Date: 2026-07-28 17:35:00.000000

Creates 13 tables for Phase 027:
  1. vehicles
  2. vehicle_versions
  3. vehicle_aliases
  4. vehicle_plate_assignments
  5. vehicle_makes
  6. vehicle_models
  7. vehicle_capacity_profiles
  8. vehicle_dimensions
  9. vehicle_ownership_assignments
  10. vehicle_carrier_assignments
  11. vehicle_documents
  12. vehicle_document_requirements
  13. vehicle_operational_restrictions
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'r300110027dc'
down_revision: Union[str, None] = 'q280110026dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. vehicle_makes
    op.create_table(
        'vehicle_makes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('normalized_name', sa.String(length=100), nullable=False, index=True),
        sa.Column('country_code', sa.String(length=3), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('system_defined', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 2. vehicle_models
    op.create_table(
        'vehicle_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('make_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_makes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('normalized_name', sa.String(length=100), nullable=False, index=True),
        sa.Column('vehicle_type', sa.String(length=50), nullable=True),
        sa.Column('body_type', sa.String(length=50), nullable=True),
        sa.Column('production_start_year', sa.Integer(), nullable=True),
        sa.Column('production_end_year', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('system_defined', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 3. vehicles
    op.create_table(
        'vehicles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vehicle_code', sa.String(length=50), nullable=False),
        sa.Column('normalized_vehicle_code', sa.String(length=50), nullable=False),
        sa.Column('display_plate', sa.String(length=20), nullable=False),
        sa.Column('normalized_plate', sa.String(length=20), nullable=False, index=True),
        sa.Column('vin', sa.String(length=30), nullable=True),
        sa.Column('normalized_vin', sa.String(length=30), nullable=True, index=True),
        sa.Column('chassis_number', sa.String(length=50), nullable=True),
        sa.Column('engine_number', sa.String(length=50), nullable=True),
        sa.Column('make_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_makes.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_models.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('manufacturing_year', sa.Integer(), nullable=True),
        sa.Column('model_year', sa.Integer(), nullable=True),
        sa.Column('vehicle_type', sa.String(length=50), nullable=False, server_default='HEAVY_TRUCK'),
        sa.Column('body_type', sa.String(length=50), nullable=False, server_default='CLOSED_BOX'),
        sa.Column('configuration_type', sa.String(length=50), nullable=True),
        sa.Column('fuel_type', sa.String(length=30), nullable=True, server_default='DIESEL'),
        sa.Column('transmission_type', sa.String(length=30), nullable=True, server_default='MANUAL'),
        sa.Column('axle_count', sa.Integer(), nullable=True),
        sa.Column('wheel_count', sa.Integer(), nullable=True),
        sa.Column('color', sa.String(length=50), nullable=True),
        sa.Column('country_of_registration_code', sa.String(length=3), nullable=False, server_default='PE'),
        sa.Column('registration_jurisdiction', sa.String(length=100), nullable=True),
        sa.Column('lifecycle_status', sa.String(length=30), nullable=False, server_default='DRAFT'),
        sa.Column('operational_status', sa.String(length=30), nullable=False, server_default='UNAVAILABLE'),
        sa.Column('compliance_status', sa.String(length=30), nullable=False, server_default='PENDING_REVIEW'),
        sa.Column('ownership_type', sa.String(length=30), nullable=False, server_default='OWNED'),
        sa.Column('current_owner_assignment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('current_carrier_assignment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('active_capacity_profile_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('active_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('suspended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('suspended_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('suspension_reason', sa.Text(), nullable=True),
        sa.Column('retired_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retired_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('retirement_reason', sa.Text(), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('archive_reason', sa.Text(), nullable=True),
        sa.Column('row_version', sa.Integer(), nullable=False, server_default=sa.text('1')),
    )
    op.create_index('uix_vehicle_org_code', 'vehicles', ['organization_id', 'normalized_vehicle_code'], unique=True)
    op.create_index('ix_vehicle_org_plate', 'vehicles', ['organization_id', 'normalized_plate'])

    # 4. vehicle_versions
    op.create_table(
        'vehicle_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'),
        sa.Column('vehicle_code', sa.String(length=50), nullable=False),
        sa.Column('plate_snapshot', sa.String(length=20), nullable=False),
        sa.Column('vin_snapshot', sa.String(length=30), nullable=True),
        sa.Column('make_snapshot', sa.String(length=100), nullable=False),
        sa.Column('model_snapshot', sa.String(length=100), nullable=False),
        sa.Column('vehicle_type', sa.String(length=50), nullable=False),
        sa.Column('body_type', sa.String(length=50), nullable=False),
        sa.Column('capacity_snapshot', postgresql.JSONB(), nullable=True),
        sa.Column('dimensions_snapshot', postgresql.JSONB(), nullable=True),
        sa.Column('ownership_snapshot', postgresql.JSONB(), nullable=True),
        sa.Column('carrier_snapshot', postgresql.JSONB(), nullable=True),
        sa.Column('document_compliance_snapshot', postgresql.JSONB(), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('uix_vehicle_version_ver', 'vehicle_versions', ['vehicle_id', 'version'], unique=True)

    # 5. vehicle_aliases
    op.create_table(
        'vehicle_aliases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alias_type', sa.String(length=30), nullable=False),  # PLATE, VEHICLE_CODE, LEGACY_CODE, FLEET_NUMBER
        sa.Column('previous_value', sa.String(length=100), nullable=False),
        sa.Column('current_value', sa.String(length=100), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 6. vehicle_plate_assignments
    op.create_table(
        'vehicle_plate_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('display_plate', sa.String(length=20), nullable=False),
        sa.Column('normalized_plate', sa.String(length=20), nullable=False, index=True),
        sa.Column('country_code', sa.String(length=3), nullable=False, server_default='PE'),
        sa.Column('jurisdiction', sa.String(length=100), nullable=True),
        sa.Column('assignment_type', sa.String(length=30), nullable=False, server_default='INITIAL'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='CURRENT'),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('source_type', sa.String(length=30), nullable=False, server_default='DECLARED'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 7. vehicle_capacity_profiles
    op.create_table(
        'vehicle_capacity_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('maximum_gross_weight_value', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('maximum_gross_weight_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('tare_weight_value', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('tare_weight_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('maximum_payload_value', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('maximum_payload_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('maximum_volume_value', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('maximum_volume_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('pallet_position_count', sa.Integer(), nullable=True),
        sa.Column('maximum_unit_count', sa.Integer(), nullable=True),
        sa.Column('passenger_count', sa.Integer(), nullable=True),
        sa.Column('axle_count', sa.Integer(), nullable=True),
        sa.Column('source_type', sa.String(length=30), nullable=False, server_default='DECLARED'),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('verified_status', sa.String(length=30), nullable=False, server_default='NOT_VERIFIED'),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 8. vehicle_dimensions
    op.create_table(
        'vehicle_dimensions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('external_length_value', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('external_width_value', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('external_height_value', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('internal_length_value', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('internal_width_value', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('internal_height_value', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('dimension_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('calculated_internal_volume', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('reported_internal_volume', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('source_type', sa.String(length=30), nullable=False, server_default='DECLARED'),
        sa.Column('measured_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_status', sa.String(length=30), nullable=False, server_default='NOT_VERIFIED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 9. vehicle_ownership_assignments
    op.create_table(
        'vehicle_ownership_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('owner_type', sa.String(length=30), nullable=False),  # INTERNAL_ORGANIZATION, BUSINESS_PARTNER
        sa.Column('owner_organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('owner_business_partner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partners.id', ondelete='SET NULL'), nullable=True),
        sa.Column('ownership_type', sa.String(length=30), nullable=False, server_default='OWNED'),
        sa.Column('contract_reference', sa.String(length=100), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='CURRENT'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 10. vehicle_carrier_assignments
    op.create_table(
        'vehicle_carrier_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('carrier_business_partner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partners.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('carrier_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_partner_roles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('assignment_type', sa.String(length=30), nullable=False, server_default='OWN_FLEET'),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='CURRENT'),
        sa.Column('authorization_reference', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 11. vehicle_documents
    op.create_table(
        'vehicle_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),  # SOAT, TECHNICAL_INSPECTION, REGISTRATION_CARD, etc.
        sa.Column('document_number', sa.String(length=100), nullable=True),
        sa.Column('issuer', sa.String(length=150), nullable=True),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('verification_status', sa.String(length=30), nullable=False, server_default='NOT_VERIFIED'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('file_reference_id', sa.String(length=255), nullable=True),
        sa.Column('source_type', sa.String(length=30), nullable=False, server_default='DECLARED'),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 12. vehicle_document_requirements
    op.create_table(
        'vehicle_document_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vehicle_type', sa.String(length=50), nullable=True),
        sa.Column('body_type', sa.String(length=50), nullable=True),
        sa.Column('ownership_type', sa.String(length=30), nullable=True),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('required', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('blocking', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('requires_expiration', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('warning_days_before_expiration', sa.Integer(), nullable=False, server_default=sa.text('30')),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 13. vehicle_operational_restrictions
    op.create_table(
        'vehicle_operational_restrictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('restriction_type', sa.String(length=50), nullable=False),  # MAINTENANCE, MANUAL_BLOCK, SAFETY_REVIEW
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('estimated_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('vehicle_operational_restrictions')
    op.drop_table('vehicle_document_requirements')
    op.drop_table('vehicle_documents')
    op.drop_table('vehicle_carrier_assignments')
    op.drop_table('vehicle_ownership_assignments')
    op.drop_table('vehicle_dimensions')
    op.drop_table('vehicle_capacity_profiles')
    op.drop_table('vehicle_plate_assignments')
    op.drop_table('vehicle_aliases')
    op.drop_table('vehicle_versions')
    op.drop_table('vehicles')
    op.drop_table('vehicle_models')
    op.drop_table('vehicle_makes')
