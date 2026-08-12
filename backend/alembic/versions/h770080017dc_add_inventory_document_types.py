"""Add EUB, ADI, CRT document types and seed INVENTORY catalog (Phase 017).

Note: PUT, MOV, AJI, CNT, TRA are assumed to exist from the initial catalog seed
(Phase 011). Only the proposed codes EUB, ADI, CRT are inserted here.

Revision ID: h770080017dc
Revises: g660970016dc
Create Date: 2026-07-26 23:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'h770080017dc'
down_revision: Union[str, None] = 'g660970016dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert proposed inventory document types. Idempotent via ON CONFLICT DO NOTHING."""
    conn = op.get_bind()

    table_exists = sa.inspect(conn).has_table('document_types')

    if not table_exists:
        # Table not yet created — skip seed (will be applied after catalog migration)
        return

    conn.execute(
        sa.text(
            """
            INSERT INTO document_types (
                id, family_id, code, name, description, origin_type,
                owner_module, resource_type, operation_type, catalog_status,
                created_at, updated_at
            )
            VALUES
                (gen_random_uuid(), (SELECT id FROM document_families WHERE code = 'INVENTORY'), 'EUB', 'Etiqueta de Ubicación',
                 'Etiqueta física/visual de identificación de ubicación en almacén (PROPOSED — PENDING_PHASE_022)',
                 'INTERNAL_GENERATED', 'inventory', 'warehouse_location', 'create_location_label', 'ACTIVE', now(), now()),
                (gen_random_uuid(), (SELECT id FROM document_families WHERE code = 'INVENTORY'), 'ADI', 'Acta de Diferencia de Inventario',
                 'Registro de diferencias detectadas en conteos o conciliaciones internas (PROPOSED)',
                 'INTERNAL_GENERATED', 'inventory', 'inventory_difference', 'record_inventory_difference', 'ACTIVE', now(), now()),
                (gen_random_uuid(), (SELECT id FROM document_families WHERE code = 'INVENTORY'), 'CRT', 'Constancia de Recepción de Transferencia',
                 'Constancia que compara lo despachado vs recibido en transferencias entre almacenes (PROPOSED)',
                 'INTERNAL_GENERATED', 'inventory', 'inventory_transfer', 'receive_transfer', 'ACTIVE', now(), now())
            ON CONFLICT (code) DO NOTHING;
            """
        )
    )


def downgrade() -> None:
    """Remove the proposed inventory document types inserted in this migration."""
    conn = op.get_bind()

    table_exists = sa.inspect(conn).has_table('document_types')

    if table_exists:
        conn.execute(
            sa.text("DELETE FROM document_types WHERE code IN ('EUB', 'ADI', 'CRT')")
        )
