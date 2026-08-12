"""Add CIT, CPV, AREC, DIF, NC document types and seed inbound catalog (Phase 016).

Revision ID: g660970016dc
Revises: f550860015dc
Create Date: 2026-07-26 22:28:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'g660970016dc'
down_revision: Union[str, None] = 'f550860015dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Insert Document Types CIT, CPV, AREC, DIF, NC into document_types if present
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO document_types (
                id, family_id, code, name, description, origin_type,
                owner_module, resource_type, operation_type, catalog_status,
                created_at, updated_at
            )
            VALUES 
                (gen_random_uuid(), (SELECT id FROM document_families WHERE code = 'INBOUND'), 'CIT', 'Cita de Recepción', 'Programación de llegada de mercadería a sede y almacén', 'INTERNAL_GENERATED', 'inbound', 'inbound_appointment', 'create_appointment', 'ACTIVE', now(), now()),
                (gen_random_uuid(), (SELECT id FROM document_families WHERE code = 'INBOUND'), 'CPV', 'Control de Puerta Vehicular', 'Registro de ingreso/salida vehicular y conductor', 'INTERNAL_GENERATED', 'inbound', 'gate_entry', 'create_gate_entry', 'ACTIVE', now(), now()),
                (gen_random_uuid(), (SELECT id FROM document_families WHERE code = 'INBOUND'), 'AREC', 'Acta de Recepción', 'Registro de descarga, conteo y revisión inicial', 'INTERNAL_GENERATED', 'inbound', 'reception', 'create_reception', 'ACTIVE', now(), now()),
                (gen_random_uuid(), (SELECT id FROM document_families WHERE code = 'INBOUND'), 'DIF', 'Acta de Diferencias', 'Registro de faltantes, sobrantes y daños en recepción', 'INTERNAL_GENERATED', 'inbound', 'reception_difference', 'record_difference', 'ACTIVE', now(), now()),
                (gen_random_uuid(), (SELECT id FROM document_families WHERE code = 'QUALITY'), 'NC', 'No Conformidad', 'Informe de no conformidad y bloqueo de producto por calidad', 'INTERNAL_GENERATED', 'quality', 'non_conformity', 'create_non_conformity', 'ACTIVE', now(), now())
            ON CONFLICT (code) DO NOTHING;
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM document_types WHERE code IN ('CIT', 'CPV', 'AREC', 'DIF', 'NC');"))
