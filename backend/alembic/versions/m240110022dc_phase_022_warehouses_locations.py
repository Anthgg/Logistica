"""phase 022 warehouses and locations hierarchy

Revision ID: m240110022dc
Revises: l230110021dc
Create Date: 2026-07-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'm240110022dc'
down_revision = 'l230110021dc'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Extend warehouses table
    op.add_column('warehouses', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('warehouses', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('warehouses', sa.Column('address_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('warehouses', sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False))
    op.add_column('warehouses', sa.Column('layout_status', sa.String(length=20), server_default='DRAFT', nullable=False))
    op.add_column('warehouses', sa.Column('manager_user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('warehouses', sa.Column('operating_hours', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('warehouses', sa.Column('temperature_controlled', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('warehouses', sa.Column('hazardous_materials_allowed', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('warehouses', sa.Column('cross_dock_enabled', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('warehouses', sa.Column('receiving_enabled', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('warehouses', sa.Column('dispatch_enabled', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('warehouses', sa.Column('inventory_enabled', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('warehouses', sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('warehouses', sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True))

    op.create_foreign_key('fk_warehouses_organization_id', 'warehouses', 'logistics_organizations', ['organization_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key('fk_warehouses_address_id', 'warehouses', 'organization_addresses', ['address_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_warehouses_organization_id', 'warehouses', ['organization_id'])

    # 2. Create warehouse_locations
    op.create_table(
        'warehouse_locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('location_type', sa.String(length=30), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('full_code', sa.String(length=200), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('hierarchy_path', sa.String(length=500), nullable=False),
        sa.Column('depth', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('sequence_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'),
        sa.Column('usage_type', sa.String(length=30), nullable=False, server_default='GENERAL_STORAGE'),
        sa.Column('picking_priority', sa.Integer(), nullable=True),
        sa.Column('putaway_priority', sa.Integer(), nullable=True),
        sa.Column('is_pickable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_receivable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_dispatchable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_countable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_locked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('lock_reason', sa.String(length=255), nullable=True),
        sa.Column('layout_x', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('layout_y', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('layout_width', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('layout_height', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('layout_rotation', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('floor_index', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['branch_id'], ['logistics_branches.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_location_id'], ['warehouse_locations.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'full_code', name='uq_locations_org_full_code'),
    )
    op.create_index('ix_warehouse_locations_organization_id', 'warehouse_locations', ['organization_id'])
    op.create_index('ix_warehouse_locations_warehouse_id', 'warehouse_locations', ['warehouse_id'])
    op.create_index('ix_warehouse_locations_parent_location_id', 'warehouse_locations', ['parent_location_id'])
    op.create_index('ix_warehouse_locations_location_type', 'warehouse_locations', ['location_type'])
    op.create_index('ix_warehouse_locations_status', 'warehouse_locations', ['status'])
    op.create_index('ix_warehouse_locations_full_code', 'warehouse_locations', ['full_code'])
    op.create_index('ix_warehouse_locations_hierarchy_path', 'warehouse_locations', ['hierarchy_path'])

    # 3. Create warehouse_location_capacities
    op.create_table(
        'warehouse_location_capacities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('capacity_type', sa.String(length=30), nullable=False),
        sa.Column('maximum_value', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('unit_code', sa.String(length=20), nullable=False),
        sa.Column('warning_threshold', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('critical_threshold', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['location_id'], ['warehouse_locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_warehouse_location_capacities_location_id', 'warehouse_location_capacities', ['location_id'])

    # 4. Create warehouse_location_restrictions
    op.create_table(
        'warehouse_location_restrictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('restriction_type', sa.String(length=50), nullable=False),
        sa.Column('operator', sa.String(length=20), nullable=False, server_default='EQUALS'),
        sa.Column('value_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('is_blocking', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['location_id'], ['warehouse_locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_warehouse_location_restrictions_location_id', 'warehouse_location_restrictions', ['location_id'])

    # 5. Create warehouse_location_code_aliases
    op.create_table(
        'warehouse_location_code_aliases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('previous_full_code', sa.String(length=200), nullable=False),
        sa.Column('new_full_code', sa.String(length=200), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['location_id'], ['warehouse_locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_location_code_aliases_location_id', 'warehouse_location_code_aliases', ['location_id'])
    op.create_index('ix_location_code_aliases_prev_code', 'warehouse_location_code_aliases', ['previous_full_code'])

    # 6. Create warehouse_layout_versions
    op.create_table(
        'warehouse_layout_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('canvas_width', sa.Numeric(precision=10, scale=2), nullable=False, server_default='1000.00'),
        sa.Column('canvas_height', sa.Numeric(precision=10, scale=2), nullable=False, server_default='1000.00'),
        sa.Column('floor_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('warehouse_id', 'version', name='uq_warehouse_layout_version'),
    )
    op.create_index('ix_warehouse_layout_versions_warehouse_id', 'warehouse_layout_versions', ['warehouse_id'])

    # 7. Create warehouse_layout_nodes
    op.create_table(
        'warehouse_layout_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('layout_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('floor_index', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('x', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('y', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('width', sa.Numeric(precision=10, scale=2), nullable=False, server_default='100.00'),
        sa.Column('height', sa.Numeric(precision=10, scale=2), nullable=False, server_default='100.00'),
        sa.Column('rotation_degrees', sa.Numeric(precision=6, scale=2), nullable=False, server_default='0.00'),
        sa.Column('shape_type', sa.String(length=30), nullable=False, server_default='RECTANGLE'),
        sa.Column('z_index', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('label_position', sa.String(length=20), nullable=False, server_default='CENTER'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['warehouse_locations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['layout_version_id'], ['warehouse_layout_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_warehouse_layout_nodes_layout_version_id', 'warehouse_layout_nodes', ['layout_version_id'])
    op.create_index('ix_warehouse_layout_nodes_location_id', 'warehouse_layout_nodes', ['location_id'])

    # 8. Create warehouse_location_qr_versions
    op.create_table(
        'warehouse_location_qr_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('qr_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('public_reference', sa.String(length=100), nullable=False),
        sa.Column('payload_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revocation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['location_id'], ['warehouse_locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_reference', name='uq_location_qr_public_ref'),
    )
    op.create_index('ix_location_qr_versions_location_id', 'warehouse_location_qr_versions', ['location_id'])
    op.create_index('ix_location_qr_versions_public_ref', 'warehouse_location_qr_versions', ['public_reference'])


def downgrade():
    op.drop_table('warehouse_location_qr_versions')
    op.drop_table('warehouse_layout_nodes')
    op.drop_table('warehouse_layout_versions')
    op.drop_table('warehouse_location_code_aliases')
    op.drop_table('warehouse_location_restrictions')
    op.drop_table('warehouse_location_capacities')
    op.drop_table('warehouse_locations')

    op.drop_constraint('fk_warehouses_address_id', 'warehouses', type_='foreignkey')
    op.drop_constraint('fk_warehouses_organization_id', 'warehouses', type_='foreignkey')
    op.drop_index('ix_warehouses_organization_id', table_name='warehouses')
    op.drop_column('warehouses', 'updated_by')
    op.drop_column('warehouses', 'created_by')
    op.drop_column('warehouses', 'inventory_enabled')
    op.drop_column('warehouses', 'dispatch_enabled')
    op.drop_column('warehouses', 'receiving_enabled')
    op.drop_column('warehouses', 'cross_dock_enabled')
    op.drop_column('warehouses', 'hazardous_materials_allowed')
    op.drop_column('warehouses', 'temperature_controlled')
    op.drop_column('warehouses', 'operating_hours')
    op.drop_column('warehouses', 'manager_user_id')
    op.drop_column('warehouses', 'layout_status')
    op.drop_column('warehouses', 'status')
    op.drop_column('warehouses', 'address_id')
    op.drop_column('warehouses', 'description')
    op.drop_column('warehouses', 'organization_id')
