"""Phase 036 arrival notices and reception scheduling.

Revision ID: y360110036dc
Revises: x350110035dc
Create Date: 2026-07-31
"""

import importlib.util
from pathlib import Path
from typing import Sequence, Union
from uuid import uuid4
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision: str = 'y360110036dc'
down_revision: Union[str, Sequence[str], None] = 'x350110035dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DRIVER_TABLES = {
    "drivers",
    "driver_versions",
    "driver_identity_documents",
    "driver_licenses",
    "driver_license_categories",
    "driver_license_category_assignments",
    "driver_license_restrictions",
    "driver_license_vehicle_type_rules",
    "driver_carrier_assignments",
    "driver_contacts",
    "driver_emergency_contacts",
    "driver_photos",
    "driver_documents",
    "driver_document_requirements",
    "driver_operational_restrictions",
    "driver_user_account_links",
}


def _ensure_phase_029_driver_schema() -> None:
    """Repair databases stamped past Phase 029 without its physical tables."""
    present = _DRIVER_TABLES.intersection(sa.inspect(op.get_bind()).get_table_names())
    if present == _DRIVER_TABLES:
        return
    if present:
        missing = ", ".join(sorted(_DRIVER_TABLES - present))
        raise RuntimeError(f"Partial Phase 029 driver schema; missing: {missing}")

    migration_path = Path(__file__).with_name("t310110029dc_phase_029_drivers.py")
    spec = importlib.util.spec_from_file_location("phase_029_driver_schema_repair", migration_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the Phase 029 driver migration")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.upgrade()


def _seed_phase_036_rbac(bind) -> None:
    from app.modules.logistics.rbac.permission_catalog import (
        PHASE_036_PERMISSIONS,
        ROLE_PERMISSION_MATRIX,
    )

    permissions = sa.table(
        "logistics_permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String()),
        sa.column("resource", sa.String()),
        sa.column("action", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
        sa.column("category", sa.String()),
        sa.column("risk_level", sa.String()),
        sa.column("is_sensitive", sa.Boolean()),
        sa.column("requires_reason", sa.Boolean()),
        sa.column("requires_step_up", sa.Boolean()),
        sa.column("is_system", sa.Boolean()),
        sa.column("status", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    roles = sa.table(
        "logistics_roles",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String()),
    )
    role_permissions = sa.table(
        "logistics_role_permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
        sa.column("effect", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    for definition in PHASE_036_PERMISSIONS:
        statement = postgresql.insert(permissions).values(
            id=uuid4(),
            code=definition["code"],
            resource=definition["resource"],
            action=definition["action"],
            name=definition["name"],
            description=definition["description"],
            category=definition["category"],
            risk_level=str(definition["risk_level"]),
            is_sensitive=definition.get("is_sensitive", False),
            requires_reason=definition.get("requires_reason", False),
            requires_step_up=definition.get("requires_step_up", False),
            is_system=True,
            status="active",
            created_at=sa.func.now(),
            updated_at=sa.func.now(),
        )
        bind.execute(
            statement.on_conflict_do_update(
                index_elements=[permissions.c.code],
                set_={
                    "risk_level": statement.excluded.risk_level,
                    "is_sensitive": statement.excluded.is_sensitive,
                    "requires_reason": statement.excluded.requires_reason,
                    "requires_step_up": statement.excluded.requires_step_up,
                    "updated_at": sa.func.now(),
                },
            )
        )
    role_ids = dict(bind.execute(sa.select(roles.c.code, roles.c.id)).all())
    phase_codes = {item["code"] for item in PHASE_036_PERMISSIONS}
    permission_ids = dict(
        bind.execute(
            sa.select(permissions.c.code, permissions.c.id).where(
                permissions.c.code.in_(phase_codes)
            )
        ).all()
    )
    for role_code, codes in ROLE_PERMISSION_MATRIX.items():
        role_id = role_ids.get(role_code)
        if role_id is None:
            continue
        for code in set(codes) & phase_codes:
            statement = postgresql.insert(role_permissions).values(
                id=uuid4(),
                role_id=role_id,
                permission_id=permission_ids[code],
                effect="allow",
                created_at=sa.func.now(),
            )
            bind.execute(
                statement.on_conflict_do_nothing(
                    index_elements=[
                        role_permissions.c.role_id,
                        role_permissions.c.permission_id,
                    ]
                )
            )


def upgrade() -> None:
    _ensure_phase_029_driver_schema()
    op.create_table('arrival_notice_outbox_events', sa.Column('id', sa.UUID(), nullable=False), sa.Column('organization_id', sa.UUID(), nullable=False), sa.Column('aggregate_type', sa.String(length=60), nullable=False), sa.Column('aggregate_id', sa.UUID(), nullable=False), sa.Column('event_type', sa.String(length=120), nullable=False), sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column('deduplication_key', sa.String(length=180), nullable=False), sa.Column('status', sa.String(length=30), nullable=False), sa.Column('attempt_count', sa.Integer(), nullable=False), sa.Column('available_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True), sa.Column('last_error', sa.Text(), nullable=True), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='RESTRICT'), sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('organization_id', 'deduplication_key', name='uq_arrival_outbox_dedupe'))
    with op.batch_alter_table('arrival_notice_outbox_events', schema=None) as batch_op:
        batch_op.create_index('ix_arrival_outbox_aggregate', ['aggregate_type', 'aggregate_id'], unique=False)
        batch_op.create_index('ix_arrival_outbox_status_available', ['status', 'available_at'], unique=False)
    op.create_table('arrival_notices', sa.Column('id', sa.UUID(), nullable=False), sa.Column('organization_id', sa.UUID(), nullable=False), sa.Column('branch_id', sa.UUID(), nullable=False), sa.Column('warehouse_id', sa.UUID(), nullable=False), sa.Column('supplier_business_partner_id', sa.UUID(), nullable=False), sa.Column('supplier_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column('carrier_business_partner_id', sa.UUID(), nullable=True), sa.Column('carrier_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True), sa.Column('submission_channel', sa.String(length=40), nullable=False), sa.Column('external_reference', sa.String(length=160), nullable=True), sa.Column('status', sa.String(length=40), nullable=False), sa.Column('appointment_status', sa.String(length=40), nullable=False), sa.Column('source_type', sa.String(length=40), nullable=False), sa.Column('current_revision_number', sa.Integer(), nullable=False), sa.Column('active_revision_id', sa.UUID(), nullable=True), sa.Column('confirmed_revision_id', sa.UUID(), nullable=True), sa.Column('appointment_id', sa.UUID(), nullable=True), sa.Column('expected_arrival_date', sa.Date(), nullable=False), sa.Column('expected_arrival_timezone', sa.String(length=64), nullable=False), sa.Column('total_purchase_orders', sa.Integer(), nullable=False), sa.Column('total_lines', sa.Integer(), nullable=False), sa.Column('expected_pallet_count', sa.Integer(), nullable=False), sa.Column('expected_package_count', sa.Integer(), nullable=False), sa.Column('expected_loose_item_count', sa.Integer(), nullable=True), sa.Column('expected_gross_weight', sa.Numeric(precision=28, scale=10), nullable=False), sa.Column('normalized_gross_weight', sa.Numeric(precision=28, scale=10), nullable=True), sa.Column('weight_unit_id', sa.UUID(), nullable=False), sa.Column('normalized_weight_unit_id', sa.UUID(), nullable=True), sa.Column('transport_mode', sa.String(length=50), nullable=False), sa.Column('special_handling_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column('comments', sa.Text(), nullable=True), sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True), sa.Column('submitted_by', sa.UUID(), nullable=True), sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True), sa.Column('confirmed_by', sa.UUID(), nullable=True), sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True), sa.Column('cancelled_by', sa.UUID(), nullable=True), sa.Column('cancellation_reason', sa.Text(), nullable=True), sa.Column('window_elapsed_at', sa.DateTime(timezone=True), nullable=True), sa.Column('created_by', sa.UUID(), nullable=False), sa.Column('updated_by', sa.UUID(), nullable=True), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.Column('row_version', sa.Integer(), nullable=False), sa.CheckConstraint('current_revision_number >= 1', name='ck_arrival_notice_revision_positive'), sa.CheckConstraint('expected_gross_weight >= 0', name='ck_arrival_notice_weight_non_negative'), sa.CheckConstraint('expected_loose_item_count IS NULL OR expected_loose_item_count >= 0', name='ck_arrival_notice_loose_non_negative'), sa.CheckConstraint('expected_package_count >= 0', name='ck_arrival_notice_packages_non_negative'), sa.CheckConstraint('expected_pallet_count >= 0', name='ck_arrival_notice_pallets_non_negative'), sa.CheckConstraint('row_version >= 1', name='ck_arrival_notice_row_version_positive'), sa.ForeignKeyConstraint(['branch_id'], ['logistics_branches.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['carrier_business_partner_id'], ['business_partners.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['normalized_weight_unit_id'], ['units_of_measure.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['supplier_business_partner_id'], ['business_partners.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['weight_unit_id'], ['units_of_measure.id'], ondelete='RESTRICT'), sa.PrimaryKeyConstraint('id'))
    with op.batch_alter_table('arrival_notices', schema=None) as batch_op:
        batch_op.create_index('ix_arrival_notices_carrier', ['carrier_business_partner_id'], unique=False)
        batch_op.create_index('ix_arrival_notices_expected_date', ['expected_arrival_date'], unique=False)
        batch_op.create_index('ix_arrival_notices_org', ['organization_id'], unique=False)
        batch_op.create_index('ix_arrival_notices_status', ['status'], unique=False)
        batch_op.create_index('ix_arrival_notices_supplier', ['supplier_business_partner_id'], unique=False)
        batch_op.create_index('ix_arrival_notices_updated', ['updated_at'], unique=False)
        batch_op.create_index('ix_arrival_notices_warehouse', ['warehouse_id'], unique=False)
    op.create_table('warehouse_reception_calendars', sa.Column('id', sa.UUID(), nullable=False), sa.Column('organization_id', sa.UUID(), nullable=False), sa.Column('warehouse_id', sa.UUID(), nullable=False), sa.Column('name', sa.String(length=160), nullable=False), sa.Column('timezone', sa.String(length=64), nullable=False), sa.Column('slot_duration_minutes', sa.Integer(), nullable=False), sa.Column('booking_horizon_days', sa.Integer(), nullable=False), sa.Column('minimum_advance_minutes', sa.Integer(), nullable=False), sa.Column('maximum_advance_days', sa.Integer(), nullable=False), sa.Column('cancellation_cutoff_minutes', sa.Integer(), nullable=False), sa.Column('reschedule_cutoff_minutes', sa.Integer(), nullable=False), sa.Column('hold_duration_minutes', sa.Integer(), nullable=False), sa.Column('maximum_hold_refreshes', sa.Integer(), nullable=False), sa.Column('default_max_concurrent_appointments', sa.Integer(), nullable=False), sa.Column('default_max_pallets_per_slot', sa.Integer(), nullable=True), sa.Column('default_max_packages_per_slot', sa.Integer(), nullable=True), sa.Column('default_max_weight_per_slot', sa.Numeric(precision=28, scale=10), nullable=True), sa.Column('weight_unit_id', sa.UUID(), nullable=True), sa.Column('status', sa.String(length=20), nullable=False), sa.Column('created_by', sa.UUID(), nullable=False), sa.Column('updated_by', sa.UUID(), nullable=True), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.Column('row_version', sa.Integer(), nullable=False), sa.CheckConstraint('booking_horizon_days >= 0', name='ck_reception_calendar_horizon'), sa.CheckConstraint('default_max_concurrent_appointments > 0', name='ck_reception_calendar_max_concurrent'), sa.CheckConstraint('maximum_advance_days >= 0', name='ck_reception_calendar_max_advance'), sa.CheckConstraint('minimum_advance_minutes >= 0', name='ck_reception_calendar_min_advance'), sa.CheckConstraint('slot_duration_minutes > 0', name='ck_reception_calendar_slot_duration'), sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['weight_unit_id'], ['units_of_measure.id'], ondelete='RESTRICT'), sa.PrimaryKeyConstraint('id'))
    with op.batch_alter_table('warehouse_reception_calendars', schema=None) as batch_op:
        batch_op.create_index('ix_reception_calendars_org', ['organization_id'], unique=False)
        batch_op.create_index('ix_reception_calendars_status', ['status'], unique=False)
        batch_op.create_index('ix_reception_calendars_warehouse', ['warehouse_id'], unique=False)
        batch_op.create_index('uq_reception_calendar_active_warehouse', ['warehouse_id'], unique=True, postgresql_where=sa.text("status = 'ACTIVE'"))
    op.create_table('arrival_notice_revisions', sa.Column('id', sa.UUID(), nullable=False), sa.Column('arrival_notice_id', sa.UUID(), nullable=False), sa.Column('revision_number', sa.Integer(), nullable=False), sa.Column('status', sa.String(length=30), nullable=False), sa.Column('supplier_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column('carrier_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True), sa.Column('warehouse_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column('purchase_order_snapshots', postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column('transport_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column('document_references_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column('expected_load_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column('proposed_window', postgresql.JSONB(astext_type=sa.Text()), nullable=True), sa.Column('special_requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column('comments', sa.Text(), nullable=True), sa.Column('content_hash', sa.String(length=64), nullable=True), sa.Column('created_from_revision_id', sa.UUID(), nullable=True), sa.Column('change_summary', sa.Text(), nullable=True), sa.Column('created_by', sa.UUID(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True), sa.Column('frozen_at', sa.DateTime(timezone=True), nullable=True), sa.CheckConstraint('revision_number >= 1', name='ck_arrival_notice_revision_number_positive'), sa.ForeignKeyConstraint(['arrival_notice_id'], ['arrival_notices.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['created_from_revision_id'], ['arrival_notice_revisions.id'], ondelete='RESTRICT'), sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('arrival_notice_id', 'revision_number', name='uq_arrival_notice_revision_number'))
    with op.batch_alter_table('arrival_notice_revisions', schema=None) as batch_op:
        batch_op.create_index('ix_arrival_notice_revisions_notice', ['arrival_notice_id'], unique=False)
        batch_op.create_index('ix_arrival_notice_revisions_status', ['status'], unique=False)
    op.create_table('reception_appointment_holds', sa.Column('id', sa.UUID(), nullable=False), sa.Column('organization_id', sa.UUID(), nullable=False), sa.Column('warehouse_id', sa.UUID(), nullable=False), sa.Column('calendar_id', sa.UUID(), nullable=False), sa.Column('arrival_notice_id', sa.UUID(), nullable=False), sa.Column('slot_start', sa.DateTime(timezone=True), nullable=False), sa.Column('slot_end', sa.DateTime(timezone=True), nullable=False), sa.Column('expected_pallet_count', sa.Integer(), nullable=False), sa.Column('expected_package_count', sa.Integer(), nullable=False), sa.Column('expected_weight', sa.Numeric(precision=28, scale=10), nullable=False), sa.Column('weight_unit_id', sa.UUID(), nullable=False), sa.Column('status', sa.String(length=20), nullable=False), sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False), sa.Column('refresh_count', sa.Integer(), nullable=False), sa.Column('created_by', sa.UUID(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.CheckConstraint('expected_package_count >= 0', name='ck_reception_hold_packages'), sa.CheckConstraint('expected_pallet_count >= 0', name='ck_reception_hold_pallets'), sa.CheckConstraint('expected_weight >= 0', name='ck_reception_hold_weight'), sa.CheckConstraint('slot_start < slot_end', name='ck_reception_hold_slot_order'), sa.ForeignKeyConstraint(['arrival_notice_id'], ['arrival_notices.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['calendar_id'], ['warehouse_reception_calendars.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['weight_unit_id'], ['units_of_measure.id'], ondelete='RESTRICT'), sa.PrimaryKeyConstraint('id'))
    with op.batch_alter_table('reception_appointment_holds', schema=None) as batch_op:
        batch_op.create_index('ix_reception_holds_expires', ['expires_at'], unique=False)
        batch_op.create_index('ix_reception_holds_slot', ['slot_start', 'slot_end'], unique=False)
        batch_op.create_index('ix_reception_holds_status', ['status'], unique=False)
        batch_op.create_index('ix_reception_holds_warehouse', ['warehouse_id'], unique=False)
        batch_op.create_index('uq_reception_hold_active_notice', ['arrival_notice_id'], unique=True, postgresql_where=sa.text("status = 'ACTIVE'"))
    op.create_table('warehouse_reception_blackouts', sa.Column('id', sa.UUID(), nullable=False), sa.Column('calendar_id', sa.UUID(), nullable=False), sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False), sa.Column('ends_at', sa.DateTime(timezone=True), nullable=False), sa.Column('reason_code', sa.String(length=40), nullable=False), sa.Column('reason', sa.Text(), nullable=False), sa.Column('affects_all_appointments', sa.Boolean(), nullable=False), sa.Column('status', sa.String(length=20), nullable=False), sa.Column('created_by', sa.UUID(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.CheckConstraint('starts_at < ends_at', name='ck_reception_blackout_time_order'), sa.ForeignKeyConstraint(['calendar_id'], ['warehouse_reception_calendars.id'], ondelete='CASCADE'), sa.PrimaryKeyConstraint('id'))
    with op.batch_alter_table('warehouse_reception_blackouts', schema=None) as batch_op:
        batch_op.create_index('ix_reception_blackouts_calendar', ['calendar_id'], unique=False)
        batch_op.create_index('ix_reception_blackouts_range', ['starts_at', 'ends_at'], unique=False)
        batch_op.create_index('ix_reception_blackouts_status', ['status'], unique=False)
    op.create_table('warehouse_reception_operating_windows', sa.Column('id', sa.UUID(), nullable=False), sa.Column('calendar_id', sa.UUID(), nullable=False), sa.Column('day_of_week', sa.Integer(), nullable=False), sa.Column('start_local_time', sa.Time(), nullable=False), sa.Column('end_local_time', sa.Time(), nullable=False), sa.Column('effective_from', sa.Date(), nullable=False), sa.Column('effective_to', sa.Date(), nullable=True), sa.Column('max_concurrent_appointments', sa.Integer(), nullable=True), sa.Column('max_pallets', sa.Integer(), nullable=True), sa.Column('max_packages', sa.Integer(), nullable=True), sa.Column('max_weight', sa.Numeric(precision=28, scale=10), nullable=True), sa.Column('status', sa.String(length=20), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.CheckConstraint('day_of_week >= 0 AND day_of_week <= 6', name='ck_reception_window_weekday'), sa.CheckConstraint('effective_to IS NULL OR effective_to >= effective_from', name='ck_reception_window_effective_dates'), sa.CheckConstraint('max_concurrent_appointments IS NULL OR max_concurrent_appointments > 0', name='ck_reception_window_concurrent'), sa.CheckConstraint('start_local_time < end_local_time', name='ck_reception_window_time_order'), sa.ForeignKeyConstraint(['calendar_id'], ['warehouse_reception_calendars.id'], ondelete='CASCADE'), sa.PrimaryKeyConstraint('id'))
    with op.batch_alter_table('warehouse_reception_operating_windows', schema=None) as batch_op:
        batch_op.create_index('ix_reception_windows_calendar_day', ['calendar_id', 'day_of_week'], unique=False)
    op.create_table('arrival_notice_driver_references', sa.Column('id', sa.UUID(), nullable=False), sa.Column('revision_id', sa.UUID(), nullable=False), sa.Column('driver_id', sa.UUID(), nullable=True), sa.Column('full_name_snapshot', sa.String(length=300), nullable=False), sa.Column('document_type_snapshot', sa.String(length=30), nullable=True), sa.Column('document_number_redacted_snapshot', sa.String(length=80), nullable=True), sa.Column('license_number_redacted_snapshot', sa.String(length=80), nullable=True), sa.Column('license_category_snapshot', sa.String(length=120), nullable=True), sa.Column('license_expiration_snapshot', sa.Date(), nullable=True), sa.Column('contact_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True), sa.Column('source_type', sa.String(length=50), nullable=False), sa.Column('exception_reason', sa.Text(), nullable=True), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['revision_id'], ['arrival_notice_revisions.id'], ondelete='CASCADE'), sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('revision_id', name='uq_arrival_notice_driver_revision'))
    with op.batch_alter_table('arrival_notice_driver_references', schema=None) as batch_op:
        batch_op.create_index('ix_arrival_notice_driver_id', ['driver_id'], unique=False)
    op.create_table('arrival_notice_purchase_order_references', sa.Column('id', sa.UUID(), nullable=False), sa.Column('arrival_notice_revision_id', sa.UUID(), nullable=False), sa.Column('purchase_order_id', sa.UUID(), nullable=False), sa.Column('purchase_order_revision_id', sa.UUID(), nullable=False), sa.Column('purchase_order_code', sa.String(length=60), nullable=False), sa.Column('supplier_business_partner_id', sa.UUID(), nullable=False), sa.Column('currency_code', sa.String(length=3), nullable=False), sa.Column('source_snapshot_hash', sa.String(length=64), nullable=False), sa.Column('status', sa.String(length=30), nullable=False), sa.Column('linked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.ForeignKeyConstraint(['arrival_notice_revision_id'], ['arrival_notice_revisions.id'], ondelete='CASCADE'), sa.ForeignKeyConstraint(['purchase_order_id'], ['po_purchase_orders.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['purchase_order_revision_id'], ['po_purchase_order_revisions.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['supplier_business_partner_id'], ['business_partners.id'], ondelete='RESTRICT'), sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('arrival_notice_revision_id', 'purchase_order_id', name='uq_arrival_notice_revision_po'))
    with op.batch_alter_table('arrival_notice_purchase_order_references', schema=None) as batch_op:
        batch_op.create_index('ix_arrival_notice_po_ref_po', ['purchase_order_id'], unique=False)
        batch_op.create_index('ix_arrival_notice_po_ref_revision', ['arrival_notice_revision_id'], unique=False)
    op.create_table('arrival_notice_transport_documents', sa.Column('id', sa.UUID(), nullable=False), sa.Column('revision_id', sa.UUID(), nullable=False), sa.Column('document_kind', sa.String(length=50), nullable=False), sa.Column('issuer_business_partner_id', sa.UUID(), nullable=True), sa.Column('issuer_tax_identifier_snapshot', sa.String(length=40), nullable=True), sa.Column('series', sa.String(length=40), nullable=True), sa.Column('number', sa.String(length=80), nullable=False), sa.Column('normalized_reference', sa.String(length=140), nullable=False), sa.Column('issue_date', sa.Date(), nullable=True), sa.Column('document_date', sa.Date(), nullable=True), sa.Column('transport_reference', sa.String(length=160), nullable=True), sa.Column('verification_status', sa.String(length=50), nullable=False), sa.Column('verification_source', sa.String(length=80), nullable=True), sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True), sa.Column('file_asset_id', sa.UUID(), nullable=True), sa.Column('notes', sa.Text(), nullable=True), sa.Column('status', sa.String(length=20), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.ForeignKeyConstraint(['file_asset_id'], ['file_assets.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['issuer_business_partner_id'], ['business_partners.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['revision_id'], ['arrival_notice_revisions.id'], ondelete='CASCADE'), sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('revision_id', 'document_kind', 'normalized_reference', name='uq_arrival_transport_doc_reference'))
    with op.batch_alter_table('arrival_notice_transport_documents', schema=None) as batch_op:
        batch_op.create_index('ix_arrival_transport_docs_file', ['file_asset_id'], unique=False)
        batch_op.create_index('ix_arrival_transport_docs_reference', ['normalized_reference'], unique=False)
        batch_op.create_index('ix_arrival_transport_docs_revision', ['revision_id'], unique=False)
    op.create_table('arrival_notice_vehicle_references', sa.Column('id', sa.UUID(), nullable=False), sa.Column('revision_id', sa.UUID(), nullable=False), sa.Column('vehicle_id', sa.UUID(), nullable=True), sa.Column('plate_snapshot', sa.String(length=20), nullable=False), sa.Column('normalized_plate', sa.String(length=20), nullable=False), sa.Column('vehicle_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True), sa.Column('source_type', sa.String(length=50), nullable=False), sa.Column('verification_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column('verification_date', sa.DateTime(timezone=True), nullable=True), sa.Column('verification_expiration', sa.DateTime(timezone=True), nullable=True), sa.Column('exception_reason', sa.Text(), nullable=True), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.ForeignKeyConstraint(['revision_id'], ['arrival_notice_revisions.id'], ondelete='CASCADE'), sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='RESTRICT'), sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('revision_id', name='uq_arrival_notice_vehicle_revision'))
    with op.batch_alter_table('arrival_notice_vehicle_references', schema=None) as batch_op:
        batch_op.create_index('ix_arrival_notice_vehicle_id', ['vehicle_id'], unique=False)
        batch_op.create_index('ix_arrival_notice_vehicle_plate', ['normalized_plate'], unique=False)
    op.create_table('arrival_notice_expected_lines', sa.Column('id', sa.UUID(), nullable=False), sa.Column('arrival_notice_revision_id', sa.UUID(), nullable=False), sa.Column('purchase_order_reference_id', sa.UUID(), nullable=False), sa.Column('purchase_order_line_id', sa.UUID(), nullable=False), sa.Column('purchase_order_schedule_line_id', sa.UUID(), nullable=True), sa.Column('line_number', sa.Integer(), nullable=False), sa.Column('product_id', sa.UUID(), nullable=True), sa.Column('product_version_id', sa.UUID(), nullable=True), sa.Column('sku_snapshot', sa.String(length=120), nullable=True), sa.Column('product_name_snapshot', sa.String(length=500), nullable=False), sa.Column('expected_quantity', sa.Numeric(precision=28, scale=10), nullable=False), sa.Column('expected_unit_id', sa.UUID(), nullable=False), sa.Column('expected_base_quantity', sa.Numeric(precision=28, scale=10), nullable=False), sa.Column('base_unit_id', sa.UUID(), nullable=False), sa.Column('conversion_rule_id', sa.UUID(), nullable=True), sa.Column('conversion_factor_snapshot', sa.Numeric(precision=28, scale=10), nullable=True), sa.Column('expected_package_count', sa.Integer(), nullable=True), sa.Column('expected_pallet_count', sa.Integer(), nullable=True), sa.Column('supplier_lot_reference', sa.String(length=120), nullable=True), sa.Column('supplier_expiration_reference', sa.Date(), nullable=True), sa.Column('notes', sa.Text(), nullable=True), sa.Column('status', sa.String(length=20), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.CheckConstraint('expected_base_quantity > 0', name='ck_arrival_expected_line_base_qty_positive'), sa.CheckConstraint('expected_package_count IS NULL OR expected_package_count >= 0', name='ck_arrival_expected_line_packages_non_negative'), sa.CheckConstraint('expected_pallet_count IS NULL OR expected_pallet_count >= 0', name='ck_arrival_expected_line_pallets_non_negative'), sa.CheckConstraint('expected_quantity > 0', name='ck_arrival_expected_line_qty_positive'), sa.ForeignKeyConstraint(['arrival_notice_revision_id'], ['arrival_notice_revisions.id'], ondelete='CASCADE'), sa.ForeignKeyConstraint(['base_unit_id'], ['units_of_measure.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['conversion_rule_id'], ['unit_conversion_rules.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['expected_unit_id'], ['units_of_measure.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['purchase_order_line_id'], ['po_purchase_order_lines.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['purchase_order_reference_id'], ['arrival_notice_purchase_order_references.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['purchase_order_schedule_line_id'], ['po_delivery_schedule_lines.id'], ondelete='RESTRICT'), sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('arrival_notice_revision_id', 'purchase_order_line_id', name='uq_arrival_notice_revision_po_line'))
    with op.batch_alter_table('arrival_notice_expected_lines', schema=None) as batch_op:
        batch_op.create_index('ix_arrival_expected_line_po_line', ['purchase_order_line_id'], unique=False)
        batch_op.create_index('ix_arrival_expected_line_product', ['product_id'], unique=False)
        batch_op.create_index('ix_arrival_expected_line_revision', ['arrival_notice_revision_id'], unique=False)
    op.create_table('reception_appointments', sa.Column('id', sa.UUID(), nullable=False), sa.Column('organization_id', sa.UUID(), nullable=False), sa.Column('branch_id', sa.UUID(), nullable=False), sa.Column('warehouse_id', sa.UUID(), nullable=False), sa.Column('calendar_id', sa.UUID(), nullable=False), sa.Column('arrival_notice_id', sa.UUID(), nullable=False), sa.Column('arrival_notice_revision_id', sa.UUID(), nullable=False), sa.Column('appointment_code', sa.String(length=80), nullable=True), sa.Column('normalized_appointment_code', sa.String(length=80), nullable=True), sa.Column('document_instance_id', sa.UUID(), nullable=True), sa.Column('document_series_id', sa.UUID(), nullable=True), sa.Column('status', sa.String(length=40), nullable=False), sa.Column('slot_start', sa.DateTime(timezone=True), nullable=False), sa.Column('slot_end', sa.DateTime(timezone=True), nullable=False), sa.Column('timezone', sa.String(length=64), nullable=False), sa.Column('expected_pallet_count', sa.Integer(), nullable=False), sa.Column('expected_package_count', sa.Integer(), nullable=False), sa.Column('expected_gross_weight', sa.Numeric(precision=28, scale=10), nullable=False), sa.Column('weight_unit_id', sa.UUID(), nullable=False), sa.Column('vehicle_reference_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True), sa.Column('driver_reference_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True), sa.Column('supplier_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column('carrier_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True), sa.Column('contact_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True), sa.Column('special_requirements_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column('confirmation_notes', sa.Text(), nullable=True), sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True), sa.Column('confirmed_by', sa.UUID(), nullable=True), sa.Column('rescheduled_from_appointment_id', sa.UUID(), nullable=True), sa.Column('reschedule_reason', sa.Text(), nullable=True), sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True), sa.Column('cancelled_by', sa.UUID(), nullable=True), sa.Column('cancellation_reason', sa.Text(), nullable=True), sa.Column('window_elapsed_at', sa.DateTime(timezone=True), nullable=True), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.Column('row_version', sa.Integer(), nullable=False), sa.CheckConstraint('expected_gross_weight >= 0', name='ck_reception_appointment_weight'), sa.CheckConstraint('expected_package_count >= 0', name='ck_reception_appointment_packages'), sa.CheckConstraint('expected_pallet_count >= 0', name='ck_reception_appointment_pallets'), sa.CheckConstraint('row_version >= 1', name='ck_reception_appointment_row_version'), sa.CheckConstraint('slot_start < slot_end', name='ck_reception_appointment_slot_order'), sa.ForeignKeyConstraint(['arrival_notice_id'], ['arrival_notices.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['arrival_notice_revision_id'], ['arrival_notice_revisions.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['branch_id'], ['logistics_branches.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['calendar_id'], ['warehouse_reception_calendars.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['document_instance_id'], ['document_instances.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['document_series_id'], ['document_series.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['rescheduled_from_appointment_id'], ['reception_appointments.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['weight_unit_id'], ['units_of_measure.id'], ondelete='RESTRICT'), sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('organization_id', 'normalized_appointment_code', name='uq_reception_appointment_org_code'))
    with op.batch_alter_table('reception_appointments', schema=None) as batch_op:
        batch_op.create_index('ix_reception_appointments_code', ['normalized_appointment_code'], unique=False)
        batch_op.create_index('ix_reception_appointments_notice', ['arrival_notice_id'], unique=False)
        batch_op.create_index('ix_reception_appointments_org', ['organization_id'], unique=False)
        batch_op.create_index('ix_reception_appointments_slot', ['slot_start', 'slot_end'], unique=False)
        batch_op.create_index('ix_reception_appointments_status', ['status'], unique=False)
        batch_op.create_index('ix_reception_appointments_warehouse', ['warehouse_id'], unique=False)
    op.create_table('inbound_expected_quantity_allocations', sa.Column('id', sa.UUID(), nullable=False), sa.Column('organization_id', sa.UUID(), nullable=False), sa.Column('arrival_notice_id', sa.UUID(), nullable=False), sa.Column('expected_line_id', sa.UUID(), nullable=False), sa.Column('purchase_order_line_id', sa.UUID(), nullable=False), sa.Column('purchase_order_schedule_line_id', sa.UUID(), nullable=True), sa.Column('allocated_quantity', sa.Numeric(precision=28, scale=10), nullable=False), sa.Column('allocated_unit_id', sa.UUID(), nullable=False), sa.Column('allocated_base_quantity', sa.Numeric(precision=28, scale=10), nullable=False), sa.Column('status', sa.String(length=30), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.Column('released_at', sa.DateTime(timezone=True), nullable=True), sa.Column('release_reason', sa.Text(), nullable=True), sa.CheckConstraint('allocated_base_quantity > 0', name='ck_inbound_allocation_base_qty_positive'), sa.CheckConstraint('allocated_quantity > 0', name='ck_inbound_allocation_qty_positive'), sa.ForeignKeyConstraint(['allocated_unit_id'], ['units_of_measure.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['arrival_notice_id'], ['arrival_notices.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['expected_line_id'], ['arrival_notice_expected_lines.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['purchase_order_line_id'], ['po_purchase_order_lines.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['purchase_order_schedule_line_id'], ['po_delivery_schedule_lines.id'], ondelete='RESTRICT'), sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('expected_line_id', name='uq_inbound_allocation_expected_line'))
    with op.batch_alter_table('inbound_expected_quantity_allocations', schema=None) as batch_op:
        batch_op.create_index('ix_inbound_allocations_notice', ['arrival_notice_id'], unique=False)
        batch_op.create_index('ix_inbound_allocations_org', ['organization_id'], unique=False)
        batch_op.create_index('ix_inbound_allocations_po_line', ['purchase_order_line_id'], unique=False)
        batch_op.create_index('ix_inbound_allocations_status', ['status'], unique=False)
    op.create_table('reception_appointment_history', sa.Column('id', sa.UUID(), nullable=False), sa.Column('appointment_id', sa.UUID(), nullable=False), sa.Column('organization_id', sa.UUID(), nullable=False), sa.Column('event_type', sa.String(length=80), nullable=False), sa.Column('previous_status', sa.String(length=40), nullable=True), sa.Column('new_status', sa.String(length=40), nullable=True), sa.Column('previous_slot', postgresql.JSONB(astext_type=sa.Text()), nullable=True), sa.Column('new_slot', postgresql.JSONB(astext_type=sa.Text()), nullable=True), sa.Column('reason', sa.Text(), nullable=True), sa.Column('actor_user_id', sa.UUID(), nullable=True), sa.Column('metadata_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.ForeignKeyConstraint(['appointment_id'], ['reception_appointments.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='RESTRICT'), sa.PrimaryKeyConstraint('id'))
    with op.batch_alter_table('reception_appointment_history', schema=None) as batch_op:
        batch_op.create_index('ix_reception_appointment_history_appointment', ['appointment_id', 'created_at'], unique=False)
    op.create_table('reception_appointment_package_jobs', sa.Column('id', sa.UUID(), nullable=False), sa.Column('organization_id', sa.UUID(), nullable=False), sa.Column('appointment_id', sa.UUID(), nullable=False), sa.Column('idempotency_key', sa.String(length=128), nullable=False), sa.Column('request_hash', sa.String(length=64), nullable=False), sa.Column('status', sa.String(length=30), nullable=False), sa.Column('file_asset_id', sa.UUID(), nullable=True), sa.Column('artifact_id', sa.UUID(), nullable=True), sa.Column('manifest', postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column('attempt_count', sa.Integer(), nullable=False), sa.Column('available_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True), sa.Column('last_error', sa.Text(), nullable=True), sa.Column('created_by', sa.UUID(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.ForeignKeyConstraint(['appointment_id'], ['reception_appointments.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['artifact_id'], ['document_artifacts.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['file_asset_id'], ['file_assets.id'], ondelete='RESTRICT'), sa.ForeignKeyConstraint(['organization_id'], ['logistics_organizations.id'], ondelete='RESTRICT'), sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('organization_id', 'idempotency_key', name='uq_reception_package_job_idempotency'))
    with op.batch_alter_table('reception_appointment_package_jobs', schema=None) as batch_op:
        batch_op.create_index('ix_reception_package_jobs_appointment', ['appointment_id'], unique=False)
        batch_op.create_index('ix_reception_package_jobs_status', ['status', 'available_at'], unique=False)
    op.create_foreign_key(
        "fk_arrival_notice_active_revision",
        "arrival_notices",
        "arrival_notice_revisions",
        ["active_revision_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_arrival_notice_confirmed_revision",
        "arrival_notices",
        "arrival_notice_revisions",
        ["confirmed_revision_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_arrival_notice_appointment",
        "arrival_notices",
        "reception_appointments",
        ["appointment_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    _seed_phase_036_rbac(op.get_bind())

def downgrade() -> None:
    from app.modules.logistics.rbac.permission_catalog import PHASE_036_PERMISSIONS

    phase_codes = [item["code"] for item in PHASE_036_PERMISSIONS]
    op.execute(
        sa.text(
            "DELETE FROM logistics_permissions WHERE code = ANY(:codes)"
        ).bindparams(
            sa.bindparam(
                "codes",
                value=phase_codes,
                type_=postgresql.ARRAY(sa.String()),
            )
        )
    )
    op.drop_constraint(
        "fk_arrival_notice_appointment",
        "arrival_notices",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_arrival_notice_confirmed_revision",
        "arrival_notices",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_arrival_notice_active_revision",
        "arrival_notices",
        type_="foreignkey",
    )
    with op.batch_alter_table('reception_appointment_package_jobs', schema=None) as batch_op:
        batch_op.drop_index('ix_reception_package_jobs_status')
        batch_op.drop_index('ix_reception_package_jobs_appointment')
    op.drop_table('reception_appointment_package_jobs')
    with op.batch_alter_table('reception_appointment_history', schema=None) as batch_op:
        batch_op.drop_index('ix_reception_appointment_history_appointment')
    op.drop_table('reception_appointment_history')
    with op.batch_alter_table('inbound_expected_quantity_allocations', schema=None) as batch_op:
        batch_op.drop_index('ix_inbound_allocations_status')
        batch_op.drop_index('ix_inbound_allocations_po_line')
        batch_op.drop_index('ix_inbound_allocations_org')
        batch_op.drop_index('ix_inbound_allocations_notice')
    op.drop_table('inbound_expected_quantity_allocations')
    with op.batch_alter_table('reception_appointments', schema=None) as batch_op:
        batch_op.drop_index('ix_reception_appointments_warehouse')
        batch_op.drop_index('ix_reception_appointments_status')
        batch_op.drop_index('ix_reception_appointments_slot')
        batch_op.drop_index('ix_reception_appointments_org')
        batch_op.drop_index('ix_reception_appointments_notice')
        batch_op.drop_index('ix_reception_appointments_code')
    op.drop_table('reception_appointments')
    with op.batch_alter_table('arrival_notice_expected_lines', schema=None) as batch_op:
        batch_op.drop_index('ix_arrival_expected_line_revision')
        batch_op.drop_index('ix_arrival_expected_line_product')
        batch_op.drop_index('ix_arrival_expected_line_po_line')
    op.drop_table('arrival_notice_expected_lines')
    with op.batch_alter_table('arrival_notice_vehicle_references', schema=None) as batch_op:
        batch_op.drop_index('ix_arrival_notice_vehicle_plate')
        batch_op.drop_index('ix_arrival_notice_vehicle_id')
    op.drop_table('arrival_notice_vehicle_references')
    with op.batch_alter_table('arrival_notice_transport_documents', schema=None) as batch_op:
        batch_op.drop_index('ix_arrival_transport_docs_revision')
        batch_op.drop_index('ix_arrival_transport_docs_reference')
        batch_op.drop_index('ix_arrival_transport_docs_file')
    op.drop_table('arrival_notice_transport_documents')
    with op.batch_alter_table('arrival_notice_purchase_order_references', schema=None) as batch_op:
        batch_op.drop_index('ix_arrival_notice_po_ref_revision')
        batch_op.drop_index('ix_arrival_notice_po_ref_po')
    op.drop_table('arrival_notice_purchase_order_references')
    with op.batch_alter_table('arrival_notice_driver_references', schema=None) as batch_op:
        batch_op.drop_index('ix_arrival_notice_driver_id')
    op.drop_table('arrival_notice_driver_references')
    with op.batch_alter_table('warehouse_reception_operating_windows', schema=None) as batch_op:
        batch_op.drop_index('ix_reception_windows_calendar_day')
    op.drop_table('warehouse_reception_operating_windows')
    with op.batch_alter_table('warehouse_reception_blackouts', schema=None) as batch_op:
        batch_op.drop_index('ix_reception_blackouts_status')
        batch_op.drop_index('ix_reception_blackouts_range')
        batch_op.drop_index('ix_reception_blackouts_calendar')
    op.drop_table('warehouse_reception_blackouts')
    with op.batch_alter_table('reception_appointment_holds', schema=None) as batch_op:
        batch_op.drop_index('uq_reception_hold_active_notice', postgresql_where=sa.text("status = 'ACTIVE'"))
        batch_op.drop_index('ix_reception_holds_warehouse')
        batch_op.drop_index('ix_reception_holds_status')
        batch_op.drop_index('ix_reception_holds_slot')
        batch_op.drop_index('ix_reception_holds_expires')
    op.drop_table('reception_appointment_holds')
    with op.batch_alter_table('arrival_notice_revisions', schema=None) as batch_op:
        batch_op.drop_index('ix_arrival_notice_revisions_status')
        batch_op.drop_index('ix_arrival_notice_revisions_notice')
    op.drop_table('arrival_notice_revisions')
    with op.batch_alter_table('warehouse_reception_calendars', schema=None) as batch_op:
        batch_op.drop_index('uq_reception_calendar_active_warehouse', postgresql_where=sa.text("status = 'ACTIVE'"))
        batch_op.drop_index('ix_reception_calendars_warehouse')
        batch_op.drop_index('ix_reception_calendars_status')
        batch_op.drop_index('ix_reception_calendars_org')
    op.drop_table('warehouse_reception_calendars')
    with op.batch_alter_table('arrival_notices', schema=None) as batch_op:
        batch_op.drop_index('ix_arrival_notices_warehouse')
        batch_op.drop_index('ix_arrival_notices_updated')
        batch_op.drop_index('ix_arrival_notices_supplier')
        batch_op.drop_index('ix_arrival_notices_status')
        batch_op.drop_index('ix_arrival_notices_org')
        batch_op.drop_index('ix_arrival_notices_expected_date')
        batch_op.drop_index('ix_arrival_notices_carrier')
    op.drop_table('arrival_notices')
    with op.batch_alter_table('arrival_notice_outbox_events', schema=None) as batch_op:
        batch_op.drop_index('ix_arrival_outbox_status_available')
        batch_op.drop_index('ix_arrival_outbox_aggregate')
    op.drop_table('arrival_notice_outbox_events')
