"""Phase 005.1 — contador transaccional de códigos de entidad.

Crea `entity_code_counters`, la fila que se bloquea con ``SELECT … FOR UPDATE`` para
reservar el siguiente código de organización, sede o almacén sin condiciones de
carrera.

No toca las columnas geográficas de `warehouses`: `district`, `province` y
`department` ya eran nullable en base de datos; lo que cambió en F005.1 es el
contrato de entrada y la derivación en el servicio, no el esquema. Eliminarlas
requiere una fase de limpieza de datos aparte.

Revision ID: jl480110048dk
Revises: ik470110047dk
"""

import sqlalchemy as sa
from alembic import op

revision = "jl480110048dk"
down_revision = "ik470110047dk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entity_code_counters",
        sa.Column("entity_type", sa.String(length=30), primary_key=True),
        sa.Column("next_value", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Misma postura que las tablas nuevas de fases anteriores.
        op.execute("ALTER TABLE entity_code_counters ENABLE ROW LEVEL SECURITY;")

    # Los contadores arrancan por encima de lo ya existente para que un código
    # generado nunca choque con uno heredado. Se cuentan las filas actuales en vez
    # de fijar un número: la base de desarrollo y la de producción no coinciden.
    op.execute(
        """
        INSERT INTO entity_code_counters (entity_type, next_value)
        VALUES
            ('organization', (SELECT COALESCE(COUNT(*), 0) + 1 FROM logistics_organizations)),
            ('branch',       (SELECT COALESCE(COUNT(*), 0) + 1 FROM logistics_branches)),
            ('warehouse',    (SELECT COALESCE(COUNT(*), 0) + 1 FROM warehouses))
        ON CONFLICT (entity_type) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("entity_code_counters")
