"""Add APC and CEP document types and seed purchasing templates catalog (Phase 015).

Revision ID: f550860015dc
Revises: e440750014dc
Create Date: 2026-07-26 22:20:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f550860015dc'
down_revision: Union[str, None] = 'e440750014dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Insert Document Types APC and CEP into document_types if present
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
                (
                    gen_random_uuid(),
                    (SELECT id FROM document_families WHERE code = 'PURCHASING'),
                    'APC', 'Aprobación de Compra',
                    'Dictamen formal de aprobación presupuestal y operativa de compra',
                    'INTERNAL_GENERATED', 'purchasing', 'purchase_order',
                    'approve_purchase_order', 'ACTIVE', now(), now()
                ),
                (
                    gen_random_uuid(),
                    (SELECT id FROM document_families WHERE code = 'PURCHASING'),
                    'CEP', 'Constancia de Envío al Proveedor',
                    'Evidencia técnica de notificación y envío de documentos a proveedores',
                    'INTERNAL_GENERATED', 'purchasing', 'purchase_order',
                    'notify_supplier', 'ACTIVE', now(), now()
                )
            ON CONFLICT (code) DO NOTHING;
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM document_types WHERE code IN ('APC', 'CEP');"))
