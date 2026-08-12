# 15. DDL SQL y Script de Migración Alembic

## Archivo de Migración Alembic

* **Identificador de Migración:** `m240110022dc`
* **Nombre de Archivo:** `m240110022dc_phase_022_warehouses_locations.py`
* **Revisión Previa:** `m240110021dc` (Fase 021)

---

## Código Completo de la Migración

```python
"""Phase 022: Modelar Almacenes y Ubicaciones Jerárquicas

Revision ID: m240110022dc
Revises: m240110021dc
Create Date: 2026-07-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'm240110022dc'
down_revision = 'm240110021dc'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Extensión Modular de la tabla preexistente warehouses
    op.add_column('warehouses', sa.Column('establishment_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('warehouses', sa.Column('code', sa.String(length=32), nullable=True))
    op.add_column('warehouses', sa.Column('warehouse_type', sa.String(length=32), server_default='CENTRAL', nullable=False))
    op.add_column('warehouses', sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False))
    op.add_column('warehouses', sa.Column('total_area_sqm', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('warehouses', sa.Column('total_volume_cubic_meters', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('warehouses', sa.Column('max_weight_kg', sa.Numeric(precision=14, scale=2), nullable=True))
    op.add_column('warehouses', sa.Column('address_info', postgresql.JSONB(as_text=True), server_default='{}', nullable=False))
    op.add_column('warehouses', sa.Column('geo_coordinates', postgresql.JSONB(as_text=True), server_default='{}', nullable=False))
    op.add_column('warehouses', sa.Column('is_allow_picking', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('warehouses', sa.Column('is_allow_receiving', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('warehouses', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))

    # Backfill para registros preexistentes en warehouses
    op.execute("UPDATE warehouses SET code = 'ALM-PREV-' || SUBSTRING(id::text, 1, 8) WHERE code IS NULL")
    op.alter_column('warehouses', 'code', nullable=False)
    op.create_unique_constraint('uq_warehouse_org_code', 'warehouses', ['organization_id', 'code'])

    # 2. Tabla warehouse_locations
    op.create_table(
        'warehouse_locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouse_locations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('full_code', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('public_ref', sa.String(length=64), nullable=False, unique=True),
        sa.Column('location_type', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('hierarchy_path', sa.String(length=1024), nullable=False),
        sa.Column('depth', sa.Integer(), server_default='0', nullable=False),
        sa.Column('sequence_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_pickable', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_receivable', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_returnable', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_counted', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('attributes', postgresql.JSONB(as_text=True), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('warehouse_id', 'full_code', name='uq_location_wh_full_code'),
        sa.CheckConstraint('depth >= 0 AND depth <= 9', name='chk_location_depth')
    )
    op.create_index('idx_wh_loc_hierarchy_path', 'warehouse_locations', ['hierarchy_path'], postgresql_ops={'hierarchy_path': 'varchar_pattern_ops'})
    op.create_index('idx_wh_loc_org_wh', 'warehouse_locations', ['organization_id', 'warehouse_id', 'status'])

    # 3. Tabla warehouse_location_capacities
    op.create_table(
        'warehouse_location_capacities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouse_locations.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('max_weight_kg', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('max_volume_cubic_meters', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('usable_height_meters', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('usable_width_meters', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('usable_depth_meters', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('max_pallets', sa.Integer(), nullable=True),
        sa.Column('max_boxes', sa.Integer(), nullable=True),
        sa.Column('max_units', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False)
    )

    # 4. Tabla warehouse_location_restrictions
    op.create_table(
        'warehouse_location_restrictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouse_locations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('restriction_type', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=32), server_default='HARD_BLOCK', nullable=False),
        sa.Column('min_temperature_celsius', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('max_temperature_celsius', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('max_humidity_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('requires_hazmat_license', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('allowed_hazmat_classes', postgresql.JSONB(as_text=True), server_default='[]', nullable=False),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False)
    )

    # 5. Tabla warehouse_location_code_aliases
    op.create_table(
        'warehouse_location_code_aliases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouse_locations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('old_full_code', sa.String(length=255), nullable=False),
        sa.Column('moved_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False)
    )
    op.create_index('idx_wh_loc_alias_old_code', 'warehouse_location_code_aliases', ['old_full_code'])

    # 6. Tablas de Layout 2D (warehouse_layout_versions y warehouse_layout_nodes)
    op.create_table(
        'warehouse_layout_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('canvas_dimensions', postgresql.JSONB(as_text=True), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('warehouse_id', 'version_number', name='uq_layout_wh_version')
    )

    op.create_table(
        'warehouse_layout_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('layout_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouse_layout_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouse_locations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('pos_x', sa.Numeric(precision=10, scale=2), server_default='0', nullable=False),
        sa.Column('pos_y', sa.Numeric(precision=10, scale=2), server_default='0', nullable=False),
        sa.Column('width', sa.Numeric(precision=10, scale=2), server_default='100', nullable=False),
        sa.Column('height', sa.Numeric(precision=10, scale=2), server_default='100', nullable=False),
        sa.Column('rotation_degrees', sa.Integer(), server_default='0', nullable=False),
        sa.Column('z_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('style_metadata', postgresql.JSONB(as_text=True), server_default='{}', nullable=False)
    )

    # 7. Tabla logistics_audit_events
    op.create_table(
        'logistics_audit_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouses.id'), nullable=True),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payload_before', postgresql.JSONB(as_text=True), nullable=True),
        sa.Column('payload_after', postgresql.JSONB(as_text=True), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False)
    )
    op.create_index('idx_audit_logistics_org_event', 'logistics_audit_events', ['organization_id', 'event_type', 'created_at'])

def downgrade():
    op.drop_table('logistics_audit_events')
    op.drop_table('warehouse_layout_nodes')
    op.drop_table('warehouse_layout_versions')
    op.drop_table('warehouse_location_code_aliases')
    op.drop_table('warehouse_location_restrictions')
    op.drop_table('warehouse_location_capacities')
    op.drop_table('warehouse_locations')
    
    op.drop_constraint('uq_warehouse_org_code', 'warehouses', type_='unique')
    op.drop_column('warehouses', 'updated_at')
    op.drop_column('warehouses', 'is_allow_receiving')
    op.drop_column('warehouses', 'is_allow_picking')
    op.drop_column('warehouses', 'geo_coordinates')
    op.drop_column('warehouses', 'address_info')
    op.drop_column('warehouses', 'max_weight_kg')
    op.drop_column('warehouses', 'total_volume_cubic_meters')
    op.drop_column('warehouses', 'total_area_sqm')
    op.drop_column('warehouses', 'status')
    op.drop_column('warehouses', 'warehouse_type')
    op.drop_column('warehouses', 'code')
    op.drop_column('warehouses', 'establishment_id')
```
