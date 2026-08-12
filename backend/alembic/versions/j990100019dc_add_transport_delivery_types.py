"""Add CVT and PAR document types and seed transport/delivery catalog (Phase 019).

Revision ID: j990100019dc
Revises: i880090018dc
Create Date: 2026-07-26 23:30:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'j990100019dc'
down_revision: Union[str, None] = 'i880090018dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert CVT and PAR document types. Idempotent via ON CONFLICT DO NOTHING."""
    conn = op.get_bind()

    table_exists = sa.inspect(conn).has_table('document_types')

    if not table_exists:
        return

    conn.execute(
        sa.text(
            """
            INSERT INTO document_types (
                id, code, name, short_name, description, family_id, origin_type,
                owner_module, resource_type, operation_type, catalog_status,
                is_system, is_official_external, supports_internal_number,
                supports_external_number, supports_series, supports_talonario,
                supports_preview, supports_issue, supports_download,
                supports_bulk_download, supports_reprint, supports_cancel,
                supports_public_verification, requires_qr, requires_signature,
                requires_reason_on_reprint, requires_reason_on_cancel, is_sensitive,
                display_order, created_at, updated_at
            ) VALUES (
                gen_random_uuid(), 'CVT', 'Control Vehicular de Transporte', 'Control Vehicular',
                'Checklist de estado vehicular antes del despacho (PROPOSED — PENDING_PHASE_027)',
                (SELECT id FROM document_families WHERE code = 'TRANSPORT' LIMIT 1), 'INTERNAL_GENERATED',
                'trips', 'vehicle_control', 'create_vehicle_control', 'ACTIVE',
                true, false, true, false, true, false, true, true, true, false, true, true, false, true, true, true, true, false, 30, now(), now()
            ) ON CONFLICT (code) DO NOTHING;
            """
        )
    )

    conn.execute(
        sa.text(
            """
            INSERT INTO document_types (
                id, code, name, short_name, description, family_id, origin_type,
                owner_module, resource_type, operation_type, catalog_status,
                is_system, is_official_external, supports_internal_number,
                supports_external_number, supports_series, supports_talonario,
                supports_preview, supports_issue, supports_download,
                supports_bulk_download, supports_reprint, supports_cancel,
                supports_public_verification, requires_qr, requires_signature,
                requires_reason_on_reprint, requires_reason_on_cancel, is_sensitive,
                display_order, created_at, updated_at
            ) VALUES (
                gen_random_uuid(), 'PAR', 'Constancia de Parada', 'Constancia Parada',
                'Registro de llegada y salida en parada durante la ruta (PROPOSED — PENDING_PHASE_064)',
                (SELECT id FROM document_families WHERE code = 'TRANSPORT' LIMIT 1), 'INTERNAL_GENERATED',
                'routes', 'stop_record', 'create_stop_record', 'ACTIVE',
                true, false, true, false, true, false, true, true, true, false, true, true, false, true, true, true, true, false, 31, now(), now()
            ) ON CONFLICT (code) DO NOTHING;
            """
        )
    )


def downgrade() -> None:
    """Remove the proposed document types inserted in this migration."""
    conn = op.get_bind()

    table_exists = sa.inspect(conn).has_table('document_types')

    if table_exists:
        conn.execute(
            sa.text("DELETE FROM document_types WHERE code IN ('CVT', 'PAR')")
        )
