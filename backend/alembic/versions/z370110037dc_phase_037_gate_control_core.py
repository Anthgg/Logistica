"""Phase 037 gate control core domain models and tables.

Revision ID: z370110037dc
Revises: y360110036dc
Create Date: 2026-07-31
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'z370110037dc'
down_revision: Union[str, Sequence[str], None] = 'y360110036dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table: warehouse_gates
    op.create_table(
        'warehouse_gates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('gate_type', sa.String(30), nullable=False, server_default='MAIN_ENTRY'),
        sa.Column('status', sa.String(30), nullable=False, server_default='ACTIVE'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('row_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'code', name='uq_warehouse_gates_org_code'),
        sa.CheckConstraint('row_version >= 1', name='ck_warehouse_gates_row_version_positive'),
    )
    op.create_index('ix_warehouse_gates_org', 'warehouse_gates', ['organization_id'])
    op.create_index('ix_warehouse_gates_warehouse', 'warehouse_gates', ['warehouse_id'])
    op.create_index('ix_warehouse_gates_status', 'warehouse_gates', ['status'])
    op.create_index('ix_warehouse_gates_type', 'warehouse_gates', ['gate_type'])

    # 2. Table: gate_control_records
    op.create_table(
        'gate_control_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_organizations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('record_code', sa.String(50), nullable=False),
        sa.Column('gate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouse_gates.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('reception_appointment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reception_appointments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('drivers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('guard_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('event_type', sa.String(30), nullable=False, server_default='CHECK_IN'),
        sa.Column('arrival_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('check_in_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('check_out_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('access_decision', sa.String(30), nullable=False, server_default='PENDING'),
        sa.Column('plate_observed', sa.String(20), nullable=False),
        sa.Column('seal_status', sa.String(30), nullable=False, server_default='NOT_APPLICABLE'),
        sa.Column('driver_dni_raw', sa.String(50), nullable=True),
        sa.Column('driver_license_raw', sa.String(50), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('document_instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document_instances.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='DRAFT'),
        sa.Column('row_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('organization_id', 'record_code', name='uq_gate_control_records_org_code'),
        sa.CheckConstraint('row_version >= 1', name='ck_gate_control_records_row_version_positive'),
        sa.CheckConstraint('check_out_at IS NULL OR check_in_at IS NULL OR check_out_at >= check_in_at', name='ck_gate_records_checkout_after_checkin'),
    )
    op.create_index('ix_gate_records_org', 'gate_control_records', ['organization_id'])
    op.create_index('ix_gate_records_gate', 'gate_control_records', ['gate_id'])
    op.create_index('ix_gate_records_appointment', 'gate_control_records', ['reception_appointment_id'])
    op.create_index('ix_gate_records_vehicle', 'gate_control_records', ['vehicle_id'])
    op.create_index('ix_gate_records_driver', 'gate_control_records', ['driver_id'])
    op.create_index('ix_gate_records_guard', 'gate_control_records', ['guard_user_id'])
    op.create_index('ix_gate_records_status', 'gate_control_records', ['status'])
    op.create_index('ix_gate_records_arrival', 'gate_control_records', ['arrival_at'])
    op.create_index('ix_gate_records_plate', 'gate_control_records', ['plate_observed'])

    # 3. Table: gate_control_history
    op.create_table(
        'gate_control_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('record_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('gate_control_records.id', ondelete='CASCADE'), nullable=False),
        sa.Column('previous_status', sa.String(50), nullable=True),
        sa.Column('new_status', sa.String(50), nullable=False),
        sa.Column('changed_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_gate_control_history_record', 'gate_control_history', ['record_id'])
    op.create_index('ix_gate_control_history_changed_by', 'gate_control_history', ['changed_by_user_id'])
    op.create_index('ix_gate_control_history_created', 'gate_control_history', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_gate_control_history_created', table_name='gate_control_history')
    op.drop_index('ix_gate_control_history_changed_by', table_name='gate_control_history')
    op.drop_index('ix_gate_control_history_record', table_name='gate_control_history')
    op.drop_table('gate_control_history')

    op.drop_index('ix_gate_records_plate', table_name='gate_control_records')
    op.drop_index('ix_gate_records_arrival', table_name='gate_control_records')
    op.drop_index('ix_gate_records_status', table_name='gate_control_records')
    op.drop_index('ix_gate_records_guard', table_name='gate_control_records')
    op.drop_index('ix_gate_records_driver', table_name='gate_control_records')
    op.drop_index('ix_gate_records_vehicle', table_name='gate_control_records')
    op.drop_index('ix_gate_records_appointment', table_name='gate_control_records')
    op.drop_index('ix_gate_records_gate', table_name='gate_control_records')
    op.drop_index('ix_gate_records_org', table_name='gate_control_records')
    op.drop_table('gate_control_records')

    op.drop_index('ix_warehouse_gates_type', table_name='warehouse_gates')
    op.drop_index('ix_warehouse_gates_status', table_name='warehouse_gates')
    op.drop_index('ix_warehouse_gates_warehouse', table_name='warehouse_gates')
    op.drop_index('ix_warehouse_gates_org', table_name='warehouse_gates')
    op.drop_table('warehouse_gates')
