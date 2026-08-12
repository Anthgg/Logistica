import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
    InventoryBalanceDeltaModel,
    InventoryPositionBalanceModel,
)


def test_alembic_migration_revision_chain():
    """Valida que la migración Alembic hh450110045dc tenga como down_revision gl440610044rb de la Fase 044."""
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)

    rev = script.get_revision("hh450110045dc")
    assert rev is not None
    assert rev.down_revision == "gl440610044rb"


def test_orm_models_numeric_precision_definitions():
    """Verifica que las columnas de cantidad en los modelos ORM usen Numeric(38,18)."""
    assert str(InventoryPositionBalanceModel.quantity.property.columns[0].type) == "NUMERIC(38, 18)"
    assert str(InventoryBalanceDeltaModel.delta_quantity.property.columns[0].type) == "NUMERIC(38, 18)"
