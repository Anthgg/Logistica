"""phase 023 product catalog master data

Revision ID: n250110023dc
Revises: m240110022dc
Create Date: 2026-07-28 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'n250110023dc'
down_revision = 'm240110022dc'
branch_labels = None
depends_on = None


def upgrade():
    # 1. product_categories
    op.create_table(
        'product_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('parent_category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('product_categories.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('hierarchy_path', sa.String(length=500), nullable=False),
        sa.Column('depth', sa.Integer(), server_default='1', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('default_tracking_policy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('default_storage_condition_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'code', name='uq_product_categories_org_code'),
    )
    op.create_index('ix_product_categories_organization_id', 'product_categories', ['organization_id'])
    op.create_index('ix_product_categories_parent_id', 'product_categories', ['parent_category_id'])
    op.create_index('ix_product_categories_hierarchy_path', 'product_categories', ['hierarchy_path'])

    # 2. product_brands
    op.create_table(
        'product_brands',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('normalized_name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('manufacturer_name', sa.String(length=200), nullable=True),
        sa.Column('country_code', sa.String(length=2), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'code', name='uq_product_brands_org_code'),
        sa.UniqueConstraint('organization_id', 'normalized_name', name='uq_product_brands_org_norm_name'),
    )
    op.create_index('ix_product_brands_organization_id', 'product_brands', ['organization_id'])

    # 3. products
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('sku', sa.String(length=50), nullable=False),
        sa.Column('normalized_sku', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('short_name', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('product_categories.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('product_brands.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('product_type', sa.String(length=30), server_default='PHYSICAL_GOOD', nullable=False),
        sa.Column('base_unit_code', sa.String(length=20), server_default='UND', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='DRAFT', nullable=False),
        sa.Column('lifecycle_status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('tracking_policy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('physical_profile_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('default_storage_condition_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tax_category_reference', sa.String(length=50), nullable=True),
        sa.Column('manufacturer_reference', sa.String(length=100), nullable=True),
        sa.Column('country_of_origin_code', sa.String(length=2), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),
        sa.Column('external_description', sa.Text(), nullable=True),
        sa.Column('active_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('archived_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('archive_reason', sa.Text(), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('row_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'normalized_sku', name='uq_products_org_normalized_sku'),
    )
    op.create_index('ix_products_organization_id', 'products', ['organization_id'])
    op.create_index('ix_products_normalized_sku', 'products', ['normalized_sku'])
    op.create_index('ix_products_category_id', 'products', ['category_id'])
    op.create_index('ix_products_brand_id', 'products', ['brand_id'])
    op.create_index('ix_products_status', 'products', ['status'])

    # 4. product_sku_aliases
    op.create_table(
        'product_sku_aliases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('previous_sku', sa.String(length=50), nullable=False),
        sa.Column('current_sku', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_product_sku_aliases_product_id', 'product_sku_aliases', ['product_id'])
    op.create_index('ix_product_sku_aliases_prev_sku', 'product_sku_aliases', ['previous_sku'])

    # 5. product_versions
    op.create_table(
        'product_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='DRAFT', nullable=False),
        sa.Column('sku_snapshot', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('brand_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('product_type', sa.String(length=30), nullable=False),
        sa.Column('base_unit_code', sa.String(length=20), nullable=False),
        sa.Column('tracking_policy_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('physical_profile_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('storage_conditions_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('handling_conditions_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('identifiers_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('product_id', 'version', name='uq_product_versions_product_version'),
    )
    op.create_index('ix_product_versions_product_id', 'product_versions', ['product_id'])

    # 6. product_identifiers
    op.create_table(
        'product_identifiers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('identifier_type', sa.String(length=30), nullable=False),
        sa.Column('value', sa.String(length=100), nullable=False),
        sa.Column('normalized_value', sa.String(length=100), nullable=False),
        sa.Column('symbology', sa.String(length=30), nullable=True),
        sa.Column('issuer', sa.String(length=100), nullable=True),
        sa.Column('is_primary', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_status', sa.String(length=30), server_default='NOT_VERIFIED', nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('organization_id', 'normalized_value', name='uq_product_identifiers_org_norm_val'),
    )
    op.create_index('ix_product_identifiers_organization_id', 'product_identifiers', ['organization_id'])
    op.create_index('ix_product_identifiers_product_id', 'product_identifiers', ['product_id'])
    op.create_index('ix_product_identifiers_norm_val', 'product_identifiers', ['normalized_value'])

    # 7. product_physical_profiles
    op.create_table(
        'product_physical_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('net_weight_value', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('net_weight_unit', sa.String(length=20), nullable=True),
        sa.Column('gross_weight_value', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('gross_weight_unit', sa.String(length=20), nullable=True),
        sa.Column('length_value', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('width_value', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('height_value', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('dimension_unit', sa.String(length=20), nullable=True),
        sa.Column('volume_value', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('volume_unit', sa.String(length=20), nullable=True),
        sa.Column('density_value', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('density_unit', sa.String(length=20), nullable=True),
        sa.Column('measurement_source', sa.String(length=30), server_default='MANUAL', nullable=False),
        sa.Column('measured_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('product_id', name='uq_product_physical_profiles_product_id'),
    )

    # 8. product_tracking_policies
    op.create_table(
        'product_tracking_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tracking_type', sa.String(length=30), server_default='NONE', nullable=False),
        sa.Column('lot_control', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('serial_control', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('expiration_control', sa.String(length=30), server_default='NONE', nullable=False),
        sa.Column('manufacturing_date_control', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('best_before_control', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('minimum_shelf_life_days', sa.Integer(), nullable=True),
        sa.Column('total_shelf_life_days', sa.Integer(), nullable=True),
        sa.Column('serial_quantity_rule', sa.String(length=40), server_default='NOT_APPLICABLE', nullable=False),
        sa.Column('lot_uniqueness_scope', sa.String(length=30), server_default='PRODUCT', nullable=False),
        sa.Column('allow_mixed_lots', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('allow_mixed_expiration_dates', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('require_supplier_lot', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('require_manufacturer_serial', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('product_id', name='uq_product_tracking_policies_product_id'),
    )

    # 9. product_storage_conditions
    op.create_table(
        'product_storage_conditions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('condition_type', sa.String(length=40), nullable=False),
        sa.Column('minimum_value', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('maximum_value', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('unit_code', sa.String(length=20), nullable=True),
        sa.Column('required', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('severity', sa.String(length=20), server_default='HARD_BLOCK', nullable=False),
        sa.Column('handling_instruction', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_product_storage_conditions_product_id', 'product_storage_conditions', ['product_id'])

    # 10. product_handling_conditions
    op.create_table(
        'product_handling_conditions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('condition_type', sa.String(length=40), nullable=False),
        sa.Column('instruction', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), server_default='WARNING_ONLY', nullable=False),
        sa.Column('required_equipment', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_product_handling_conditions_product_id', 'product_handling_conditions', ['product_id'])


def downgrade():
    op.drop_table('product_handling_conditions')
    op.drop_table('product_storage_conditions')
    op.drop_table('product_tracking_policies')
    op.drop_table('product_physical_profiles')
    op.drop_table('product_identifiers')
    op.drop_table('product_versions')
    op.drop_table('product_sku_aliases')
    op.drop_table('products')
    op.drop_table('product_brands')
    op.drop_table('product_categories')
