"""Phase 004 — corrige server_default entrecomillados y normaliza warehouse_type.

La revisión ``a2f27fd9a6c0`` declaró los defaults como cadenas Python que ya contenían
comillas (``server_default="'active'"``). SQLAlchemy las volvió a citar, así que el DDL
aplicado fue ``DEFAULT '''active'''`` y el valor por defecto real incluye apóstrofos.

En ``logistics_organizations`` y ``logistics_branches`` el fallo quedó latente porque el
``default=`` del ORM siempre aporta el valor y el default del servidor no llega a usarse.
En ``warehouses.warehouse_type`` sí se activó: las filas sembradas quedaron con el valor
literal ``'general'``, apóstrofos incluidos, que no pertenece a ningún validador real.

No se modifica la revisión histórica ya aplicada: se corrige hacia delante.

Revision ID: hj460110046dk
Revises: gj450510045vr

La baseline de Supabase (``gj450510045vr``) se integró en main antes que F004, así
que esta revisión cuelga de ella. Encadenarlas mantiene una sola cabeza de Alembic:
con ambas colgando de ``gi450410045dk`` el grafo tendría dos.
"""

from alembic import op
import sqlalchemy as sa


revision = "hj460110046dk"
down_revision = "gj450510045vr"
branch_labels = None
depends_on = None


# (tabla, columna, default correcto, default corrupto que dejó a2f27fd9a6c0)
_QUOTED_DEFAULTS = [
    ("logistics_organizations", "status", "active"),
    ("logistics_organizations", "timezone", "America/Lima"),
    ("logistics_branches", "status", "active"),
    ("logistics_branches", "timezone", "America/Lima"),
    ("warehouses", "warehouse_type", "general"),
]


def upgrade() -> None:
    for table, column, correct in _QUOTED_DEFAULTS:
        op.alter_column(
            table,
            column,
            existing_type=sa.String(),
            existing_nullable=False,
            server_default=sa.text(f"'{correct}'"),
        )

    # Normalización de datos: solo las filas demostrablemente corruptas, es decir las
    # que empiezan y terminan con apóstrofo. No es un replace indiscriminado sobre
    # cualquier cadena: un valor legítimo nunca lleva comillas dentro del dato.
    op.execute(
        sa.text(
            """
            UPDATE warehouses
               SET warehouse_type = btrim(warehouse_type, '''')
             WHERE warehouse_type LIKE '''%'
               AND warehouse_type LIKE '%'''
            """
        )
    )


def downgrade() -> None:
    # Se restauran los defaults entrecomillados tal y como estaban, para que el
    # downgrade sea fiel al estado anterior. Los datos normalizados no se vuelven a
    # corromper a propósito.
    for table, column, correct in _QUOTED_DEFAULTS:
        op.alter_column(
            table,
            column,
            existing_type=sa.String(),
            existing_nullable=False,
            server_default=sa.text(f"'''{correct}'''"),
        )
