"""phase 024 units and conversions engine

Revision ID: o260110024dc
Revises: n250110023dc
Create Date: 2026-07-28 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'o260110024dc'
down_revision = 'n250110023dc'
branch_labels = None
depends_on = None


def upgrade():
    # 1. measurement_dimensions
    op.create_table(
        'measurement_dimensions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(length=30), nullable=False, unique=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('canonical_unit_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('supports_fractional_quantities', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('default_precision', sa.Integer(), server_default='4', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('system_defined', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 2. units_of_measure
    op.create_table(
        'units_of_measure',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('dimension_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('measurement_dimensions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('normalized_code', sa.String(length=30), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('plural_name', sa.String(length=100), nullable=True),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('unit_scope', sa.String(length=20), server_default='SYSTEM', nullable=False),
        sa.Column('unit_kind', sa.String(length=20), server_default='BASE', nullable=False),
        sa.Column('decimal_precision', sa.Integer(), server_default='4', nullable=False),
        sa.Column('minimum_increment', sa.Numeric(precision=38, scale=18), nullable=True),
        sa.Column('integer_only', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_canonical', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('system_defined', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('active_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('row_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'normalized_code', name='uq_units_org_norm_code'),
    )
    op.create_index('ix_units_organization_id', 'units_of_measure', ['organization_id'])
    op.create_index('ix_units_dimension_id', 'units_of_measure', ['dimension_id'])
    op.create_index('ix_units_norm_code', 'units_of_measure', ['normalized_code'])

    # Foreign key for canonical unit in dimensions
    op.create_foreign_key('fk_dimensions_canonical_unit_id', 'measurement_dimensions', 'units_of_measure', ['canonical_unit_id'], ['id'], ondelete='SET NULL')

    # 3. unit_of_measure_versions
    op.create_table(
        'unit_of_measure_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('dimension_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('precision', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('unit_id', 'version', name='uq_unit_versions_unit_version'),
    )

    # 4. unit_conversion_rules
    op.create_table(
        'unit_conversion_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=True),
        sa.Column('source_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('target_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('conversion_scope', sa.String(length=20), server_default='SYSTEM', nullable=False),
        sa.Column('multiplier', sa.Numeric(precision=38, scale=18), nullable=False),
        sa.Column('multiplier_numerator', sa.Numeric(precision=38, scale=18), nullable=True),
        sa.Column('multiplier_denominator', sa.Numeric(precision=38, scale=18), nullable=True),
        sa.Column('allows_inverse', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('precision', sa.Integer(), server_default='4', nullable=False),
        sa.Column('rounding_policy', sa.String(length=30), server_default='HALF_UP', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('version', sa.String(length=20), server_default='1.0.0', nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_conversion_rules_source', 'unit_conversion_rules', ['source_unit_id'])
    op.create_index('ix_conversion_rules_target', 'unit_conversion_rules', ['target_unit_id'])
    op.create_index('ix_conversion_rules_product', 'unit_conversion_rules', ['product_id'])
    op.create_index('ix_conversion_rules_scope', 'unit_conversion_rules', ['conversion_scope'])

    # 5. product_unit_configurations
    op.create_table(
        'product_unit_configurations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('base_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('purchase_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('reception_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('storage_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('picking_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('dispatch_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('count_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('version', sa.String(length=20), server_default='1.0.0', nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 6. product_unit_configuration_versions
    op.create_table(
        'product_unit_configuration_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('configuration_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('product_unit_configurations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('configuration_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 7. product_packaging_definitions
    op.create_table(
        'product_packaging_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('packaging_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('contained_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('units_of_measure.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('contained_quantity', sa.Numeric(precision=38, scale=18), nullable=False),
        sa.Column('level_order', sa.Integer(), nullable=False),
        sa.Column('package_type', sa.String(length=30), server_default='BOX', nullable=False),
        sa.Column('gross_weight', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('version', sa.String(length=20), server_default='1.0.0', nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('product_id', 'packaging_unit_id', name='uq_product_pkg_prod_unit'),
    )
    op.create_index('ix_product_packaging_product_id', 'product_packaging_definitions', ['product_id'])


def downgrade():
    op.drop_table('product_packaging_definitions')
    op.drop_table('product_unit_configuration_versions')
    op.drop_table('product_unit_configurations')
    op.drop_table('unit_conversion_rules')
    op.drop_table('unit_of_measure_versions')
    op.drop_constraint('fk_dimensions_canonical_unit_id', 'measurement_dimensions', type_='foreignkey')
    op.drop_table('units_of_measure')
    op.drop_table('measurement_dimensions')
