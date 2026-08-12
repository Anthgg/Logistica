# Migración de Base de Datos Alembic (DDL SQL)

## 1. Archivo de Migración `r300110027dc_phase_027_vehicles.py`

La migración de Alembic para la Fase 027 se encuentra ubicada en `src/backend/alembic/versions/r300110027dc_phase_027_vehicles.py`. Crea las 13 tablas relacionales con sus respectivas claves foráneas, restricciones de unicidad e índices B-Tree optimizados.

---

## 2. Extracto de Código DDL Python (Alembic)

```python
"""phase_027_vehicles

Revision ID: r300110027dc
Revises: r300110026dc
Create Date: 2026-07-28 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'r300110027dc'
down_revision = 'r300110026dc'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Marcas
    op.create_table(
        'logistics_vehicle_makes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(32), nullable=False, unique=True),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('origin', sa.String(16), nullable=False, server_default='ORGANIZATION'),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # 2. Modelos
    op.create_table(
        'logistics_vehicle_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('make_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_vehicle_makes.id'), nullable=False),
        sa.Column('code', sa.String(32), nullable=False),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('vehicle_type', sa.String(32), nullable=False),
        sa.Column('origin', sa.String(16), nullable=False, server_default='ORGANIZATION'),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # 3. Vehículos Principal
    op.create_table(
        'logistics_vehicles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vehicle_code', sa.String(32), nullable=False),
        sa.Column('normalized_vehicle_code', sa.String(32), nullable=False),
        sa.Column('display_plate', sa.String(16), nullable=False),
        sa.Column('normalized_plate', sa.String(16), nullable=False),
        sa.Column('vin', sa.String(32), nullable=True),
        sa.Column('normalized_vin', sa.String(32), nullable=True),
        sa.Column('chassis_number', sa.String(64), nullable=True),
        sa.Column('engine_number', sa.String(64), nullable=True),
        sa.Column('make_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_vehicle_makes.id'), nullable=False),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logistics_vehicle_models.id'), nullable=False),
        sa.Column('vehicle_type', sa.String(32), nullable=False),
        sa.Column('body_type', sa.String(32), nullable=False),
        sa.Column('lifecycle_status', sa.String(32), nullable=False, server_default='DRAFT'),
        sa.Column('operational_status', sa.String(32), nullable=False, server_default='UNAVAILABLE'),
        sa.Column('compliance_status', sa.String(32), nullable=False, server_default='PENDING_REVIEW'),
        sa.Column('row_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # Crear Índices B-Tree
    op.create_index('ix_logistics_vehicles_org_plate', 'logistics_vehicles', ['organization_id', 'normalized_plate'], unique=True)
    op.create_index('ix_logistics_vehicles_normalized_vin', 'logistics_vehicles', ['normalized_vin'])
    op.create_index('ix_logistics_vehicles_normalized_code', 'logistics_vehicles', ['organization_id', 'normalized_vehicle_code'])
    op.create_index('ix_logistics_vehicles_status', 'logistics_vehicles', ['organization_id', 'operational_status', 'compliance_status'])

def downgrade() -> None:
    op.drop_table('logistics_vehicles')
    op.drop_table('logistics_vehicle_models')
    op.drop_table('logistics_vehicle_makes')
```
