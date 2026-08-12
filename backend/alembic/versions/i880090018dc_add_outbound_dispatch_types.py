"""Add CPR document type and seed outbound/dispatch catalog (Phase 018).

Revision ID: i880090018dc
Revises: h770080017dc
Create Date: 2026-07-26 23:15:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'i880090018dc'
down_revision: Union[str, None] = 'h770080017dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert CPR document type. Idempotent via ON CONFLICT DO NOTHING."""
    conn = op.get_bind()

    table_exists = sa.inspect(conn).has_table('document_types')

    if not table_exists:
        # Table not yet created — skip seed
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
                (gen_random_uuid(), (SELECT id FROM document_families WHERE code = 'DISPATCH'), 'CPR', 'Control de Precinto',
                 'Registro detallado del estado y verificación de precintos colocados en vehículos de carga (PROPOSED — PENDING_PHASE_058)',
                 'INTERNAL_GENERATED', 'dispatch', 'seal_control', 'create_seal_control', 'ACTIVE', now(), now())
            ON CONFLICT (code) DO NOTHING;
            """
        )
    )


def downgrade() -> None:
    """Remove CPR document type inserted in this migration."""
    conn = op.get_bind()

    table_exists = sa.inspect(conn).has_table('document_types')

    if table_exists:
        conn.execute(
            sa.text("DELETE FROM document_types WHERE code = 'CPR'")
        )
