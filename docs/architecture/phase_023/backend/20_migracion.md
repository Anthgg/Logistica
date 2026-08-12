# 20 — Script DDL y Migración Alembic (`n250110023dc_phase_023_product_catalog.py`)

## 1. Definición de la Migración Alembic

La migración `n250110023dc_phase_023_product_catalog.py` aplica la creación transaccional del esquema de base de datos relacional para el Catálogo de Productos (10 tablas, tipos enumerados, índices B-Tree y restricciones de clave foránea).

---

## 2. Código Fuente de la Migración Python Alembic

```python
"""Phase 023: Product Catalog Master Data Management

Revision ID: n250110023dc
Revises: n250110022dc
Create Date: 2026-07-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'n250110023dc'
down_revision = 'n250110022dc'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Crear Enum Types
    product_type_enum = postgresql.ENUM(
        'RAW_MATERIAL', 'WORK_IN_PROGRESS', 'FINISHED_GOOD', 'MERCHANDISE',
        'SUPPLY', 'PACKAGING', 'SERVICE', 'ASSET',
        name='product_type_enum'
    )
    product_type_enum.create(op.get_bind(), checkfirst=True)

    product_status_enum = postgresql.ENUM(
        'DRAFT', 'ACTIVE', 'INACTIVE', 'SUSPENDED', 'DISCONTINUED', 'BLOCKED', 'ARCHIVED',
        name='product_status_enum'
    )
    product_status_enum.create(op.get_bind(), checkfirst=True)

    identifier_type_enum = postgresql.ENUM(
        'GTIN_8', 'GTIN_12', 'GTIN_13', 'GTIN_14', 'INTERNAL_BARCODE', 'QR_CODE', 'CUSTOM_CODE',
        name='identifier_type_enum'
    )
    identifier_type_enum.create(op.get_bind(), checkfirst=True)

    tracking_mode_enum = postgresql.ENUM(
        'NONE', 'LOT', 'SERIAL', 'LOT_AND_SERIAL',
        name='tracking_mode_enum'
    )
    tracking_mode_enum.create(op.get_bind(), checkfirst=True)

    expiration_control_type_enum = postgresql.ENUM(
        'NOT_APPLICABLE', 'OPTIONAL', 'MANDATORY', 'DERIVED_FROM_LOT',
        name='expiration_control_type_enum'
    )
    expiration_control_type_enum.create(op.get_bind(), checkfirst=True)

    constraint_severity_enum = postgresql.ENUM(
        'HARD_BLOCK', 'WARNING_ONLY',
        name='constraint_severity_enum'
    )
    constraint_severity_enum.create(op.get_bind(), checkfirst=True)

    # 2. Crear Tabla product_categories
    op.create_table(
        'product_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('hierarchy_path', sa.String(length=500), nullable=False),
        sa.Column('depth', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['product_categories.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'code', name='uq_categories_org_code'),
        sa.CheckConstraint('depth >= 1 AND depth <= 5', name='chk_category_depth')
    )
    op.create_index('idx_categories_org_parent', 'product_categories', ['organization_id', 'parent_id'])
    op.create_index('idx_categories_path', 'product_categories', ['organization_id', 'hierarchy_path'])

    # 3. Crear Tabla product_brands
    op.create_table(
        'product_brands',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('normalized_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website_url', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'normalized_name', name='uq_brands_org_normalized_name')
    )
    op.create_index('idx_brands_org_lookup', 'product_brands', ['organization_id', 'normalized_name'])

    # 4. Crear Tabla Principal products
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sku', sa.String(length=50), nullable=False),
        sa.Column('normalized_sku', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('product_type', product_type_enum, nullable=False, server_default='FINISHED_GOOD'),
        sa.Column('status', product_status_enum, nullable=False, server_default='DRAFT'),
        sa.Column('base_unit_code', sa.String(length=20), nullable=False, server_default='UND'),
        sa.Column('is_hazmat', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('requires_cold_chain', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_fragile', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('row_version', sa.BigInteger(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['brand_id'], ['product_brands.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['category_id'], ['product_categories.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'sku', name='uq_products_org_sku'),
        sa.UniqueConstraint('organization_id', 'normalized_sku', name='uq_products_org_normalized_sku')
    )
    op.create_index('idx_products_brand', 'products', ['brand_id'])
    op.create_index('idx_products_category', 'products', ['category_id'])
    op.create_index('idx_products_normalized_sku', 'products', ['organization_id', 'normalized_sku'])
    op.create_index('idx_products_org_status', 'products', ['organization_id', 'status'])

    # 5. Crear Tabla product_sku_aliases
    op.create_table(
        'product_sku_aliases',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alias_sku', sa.String(length=50), nullable=False),
        sa.Column('normalized_alias_sku', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'normalized_alias_sku', name='uq_sku_aliases_org_normalized')
    )
    op.create_index('idx_sku_aliases_lookup', 'product_sku_aliases', ['organization_id', 'normalized_alias_sku'])
    op.create_index('idx_sku_aliases_product', 'product_sku_aliases', ['product_id'])

    # 6. Crear Tabla product_versions
    op.create_table(
        'product_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('payload_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('change_reason', sa.String(length=255), nullable=True),
        sa.Column('effective_start', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('effective_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', 'version_number', name='uq_product_version_num')
    )
    op.create_index('idx_product_versions_hash', 'product_versions', ['content_hash'])
    op.create_index('idx_product_versions_lookup', 'product_versions', ['product_id', 'version_number'])

    # 7. Crear Tabla product_identifiers
    op.create_table(
        'product_identifiers',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('identifier_type', identifier_type_enum, nullable=False),
        sa.Column('raw_value', sa.String(length=100), nullable=False),
        sa.Column('normalized_value', sa.String(length=100), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'normalized_value', name='uq_identifiers_org_value')
    )
    op.create_index('idx_identifiers_lookup', 'product_identifiers', ['organization_id', 'normalized_value'])
    op.create_index('idx_identifiers_product', 'product_identifiers', ['product_id'])

    # 8. Crear Tabla product_physical_profiles
    op.create_table(
        'product_physical_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('net_weight_kg', sa.Numeric(precision=14, scale=4), server_default='0.0000', nullable=False),
        sa.Column('gross_weight_kg', sa.Numeric(precision=14, scale=4), server_default='0.0000', nullable=False),
        sa.Column('length_cm', sa.Numeric(precision=14, scale=4), server_default='0.0000', nullable=False),
        sa.Column('width_cm', sa.Numeric(precision=14, scale=4), server_default='0.0000', nullable=False),
        sa.Column('height_cm', sa.Numeric(precision=14, scale=4), server_default='0.0000', nullable=False),
        sa.Column('calculated_volume_m3', sa.Numeric(precision=14, scale=4), server_default='0.0000', nullable=False),
        sa.Column('override_volume_m3', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('is_stackable', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('max_stacking_layers', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', name='uq_physical_profile_product'),
        sa.CheckConstraint('gross_weight_kg >= net_weight_kg', name='chk_net_gross_weight'),
        sa.CheckConstraint('length_cm >= 0 AND width_cm >= 0 AND height_cm >= 0', name='chk_positive_dimensions')
    )

    # 9. Crear Tabla product_tracking_policies
    op.create_table(
        'product_tracking_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tracking_mode', tracking_mode_enum, server_default='NONE', nullable=False),
        sa.Column('expiration_control', expiration_control_type_enum, server_default='NOT_APPLICABLE', nullable=False),
        sa.Column('requires_serial_on_receipt', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('requires_serial_on_dispatch', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('lot_number_mask', sa.String(length=50), nullable=True),
        sa.Column('serial_number_mask', sa.String(length=50), nullable=True),
        sa.Column('total_shelf_life_days', sa.Integer(), nullable=True),
        sa.Column('minimum_shelf_life_days', sa.Integer(), nullable=True),
        sa.Column('outbound_min_shelf_life_days', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', name='uq_tracking_policy_product')
    )

    # 10. Crear Tabla product_storage_conditions
    op.create_table(
        'product_storage_conditions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('min_temperature_celsius', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('max_temperature_celsius', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('min_humidity_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('max_humidity_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('requires_refrigeration', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('requires_freezing', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_hazmat', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('hazmat_class', sa.String(length=20), nullable=True),
        sa.Column('un_number', sa.String(length=10), nullable=True),
        sa.Column('is_fragile', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('requires_darkness', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('severity', constraint_severity_enum, server_default='HARD_BLOCK', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', name='uq_storage_condition_product')
    )

    # 11. Crear Tabla product_handling_conditions
    op.create_table(
        'product_handling_conditions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requires_two_persons', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('requires_forklift', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('orientation_instruction', sa.String(length=50), nullable=True),
        sa.Column('max_tilting_degrees', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('required_ppe', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('safety_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', name='uq_handling_condition_product')
    )

def downgrade() -> None:
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

    op.execute('DROP TYPE IF EXISTS constraint_severity_enum;')
    op.execute('DROP TYPE IF EXISTS expiration_control_type_enum;')
    op.execute('DROP TYPE IF EXISTS tracking_mode_enum;')
    op.execute('DROP TYPE IF EXISTS identifier_type_enum;')
    op.execute('DROP TYPE IF EXISTS product_status_enum;')
    op.execute('DROP TYPE IF EXISTS product_type_enum;')
```
