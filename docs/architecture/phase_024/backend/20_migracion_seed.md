# 20. Migración DDL Alembic y Script de Semilla (`seed.py`)

## 1. Migración Alembic `o260110024dc_phase_024_units_and_conversions.py`

La migración Alembic crea las 7 tablas relacionales, índices únicos, tipos enumerados de PostgreSQL y restricciones de clave foránea de la **Fase 024**.

```python
"""phase_024_units_and_conversions

Revision ID: o260110024dc
Revises: o230110023dc
Create Date: 2026-07-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'o260110024dc'
down_revision = 'o230110023dc'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Crear enumerados
    uom_scope = postgresql.ENUM('SYSTEM', 'ORGANIZATION', name='uom_scope_enum')
    uom_scope.create(op.get_bind(), checkfirst=True)

    uom_kind = postgresql.ENUM('BASE', 'DERIVED', 'PACKAGING', 'CUSTOM', name='uom_kind_enum')
    uom_kind.create(op.get_bind(), checkfirst=True)

    # 2. Crear measurement_dimensions
    op.create_table(
        'measurement_dimensions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('canonical_unit_code', sa.String(length=32), nullable=False),
        sa.Column('default_precision', sa.Integer(), server_default='6', nullable=False),
        sa.Column('is_system_defined', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('row_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_measurement_dimensions_code')
    )

    # 3. Crear units_of_measure
    op.create_table(
        'units_of_measure',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('dimension_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('symbol', sa.String(length=16), nullable=False),
        sa.Column('scope', sa.Enum('SYSTEM', 'ORGANIZATION', name='uom_scope_enum'), nullable=False),
        sa.Column('kind', sa.Enum('BASE', 'DERIVED', 'PACKAGING', 'CUSTOM', name='uom_kind_enum'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('row_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['dimension_id'], ['measurement_dimensions.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'code', name='uq_units_code_scope')
    )

    # 4. Crear unit_conversion_rules, product_unit_configurations, product_packaging_definitions, unit_of_measure_versions, unit_conversion_cache
    # ... (Resto de DDLs creados de forma análoga) ...

def downgrade() -> None:
    op.drop_table('unit_conversion_cache')
    op.drop_table('unit_of_measure_versions')
    op.drop_table('product_packaging_definitions')
    op.drop_table('product_unit_configurations')
    op.drop_table('unit_conversion_rules')
    op.drop_table('units_of_measure')
    op.drop_table('measurement_dimensions')
```

---

## 2. Script de Semilla Idempotente (`seed.py`)

El script de seeding inserta de forma segura e idempotente las 5 dimensiones del sistema, sus unidades canónicas y las reglas físicas primarias:

```python
import logging
from decimal import Decimal
from sqlalchemy.orm import Session
from src.apps.logistics.models import MeasurementDimensionModel, UnitOfMeasureModel, UnitConversionRuleModel

logger = logging.getLogger(__name__)

def seed_phase_024_units(db: Session):
    logger.info("Iniciando Seeding de la Fase 024: Unidades y Conversiones...")

    # 1. Definición de Dimensiones Primarias
    dimensions = [
        {"code": "COUNT", "name": "Conteo Discrete", "canonical_unit_code": "UND", "default_precision": 0},
        {"code": "MASS", "name": "Masa / Peso", "canonical_unit_code": "KG", "default_precision": 6},
        {"code": "LENGTH", "name": "Longitud / Distancia", "canonical_unit_code": "M", "default_precision": 6},
        {"code": "AREA", "name": "Área / Superficie", "canonical_unit_code": "M2", "default_precision": 6},
        {"code": "VOLUME", "name": "Volumen / Capacidad", "canonical_unit_code": "M3", "default_precision": 6},
    ]

    dim_map = {}
    for d in dimensions:
        dim = db.query(MeasurementDimensionModel).filter_by(code=d["code"]).first()
        if not dim:
            dim = MeasurementDimensionModel(**d, is_system_defined=True)
            db.add(dim)
            db.flush()
        dim_map[d["code"]] = dim

    # 2. Definición de Unidades Universales del Sistema
    units = [
        {"code": "UND", "name": "Unidad", "symbol": "ud", "dim": "COUNT", "kind": "BASE"},
        {"code": "DOCENA", "name": "Docena", "symbol": "doc", "dim": "COUNT", "kind": "DERIVED"},
        {"code": "KG", "name": "Kilogramo", "symbol": "kg", "dim": "MASS", "kind": "BASE"},
        {"code": "G", "name": "Gramo", "symbol": "g", "dim": "MASS", "kind": "DERIVED"},
        {"code": "TON", "name": "Tonelada", "symbol": "t", "dim": "MASS", "kind": "DERIVED"},
        {"code": "M", "name": "Metro", "symbol": "m", "dim": "LENGTH", "kind": "BASE"},
        {"code": "CM", "name": "Centímetro", "symbol": "cm", "dim": "LENGTH", "kind": "DERIVED"},
        {"code": "MM", "name": "Milímetro", "symbol": "mm", "dim": "LENGTH", "kind": "DERIVED"},
        {"code": "M2", "name": "Metro Cuadrado", "symbol": "m²", "dim": "AREA", "kind": "BASE"},
        {"code": "M3", "name": "Metro Cúbico", "symbol": "m³", "dim": "VOLUME", "kind": "BASE"},
        {"code": "L", "name": "Litro", "symbol": "L", "dim": "VOLUME", "kind": "DERIVED"},
    ]

    unit_map = {}
    for u in units:
        unit = db.query(UnitOfMeasureModel).filter_by(code=u["code"], scope="SYSTEM").first()
        if not unit:
            unit = UnitOfMeasureModel(
                code=u["code"],
                name=u["name"],
                symbol=u["symbol"],
                dimension_id=dim_map[u["dim"]].id,
                scope="SYSTEM",
                kind=u["kind"]
            )
            db.add(unit)
            db.flush()
        unit_map[u["code"]] = unit

    # 3. Insertar Reglas de Conversión Físicas Estándar
    rules = [
        ("KG", "G", Decimal("1000"), Decimal("0.001")),
        ("TON", "KG", Decimal("1000"), Decimal("0.001")),
        ("M", "CM", Decimal("100"), Decimal("0.01")),
        ("M", "MM", Decimal("1000"), Decimal("0.001")),
        ("M3", "L", Decimal("1000"), Decimal("0.001")),
        ("DOCENA", "UND", Decimal("12"), Decimal("0.083333333333333333")),
    ]

    for from_c, to_c, factor, inv_factor in rules:
        from_u = unit_map[from_c]
        to_u = unit_map[to_c]
        rule = db.query(UnitConversionRuleModel).filter_by(
            from_unit_id=from_u.id, to_unit_id=to_u.id, is_system_rule=True
        ).first()
        if not rule:
            rule = UnitConversionRuleModel(
                from_unit_id=from_u.id,
                to_unit_id=to_u.id,
                conversion_factor=factor,
                inverse_factor=inv_factor,
                is_system_rule=True
            )
            db.add(rule)

    db.commit()
    logger.info("Seeding de Fase 024 completado exitosamente.")
```
