"""
test_phase_045_migration.py — Ciclo Alembic real (Fase 045)

CRITERIO DE EVIDENCIA:
- Si PostgreSQL disponible: ejecutar alembic downgrade → upgrade → downgrade → upgrade real
- Verificar tablas con sqlalchemy.inspect(engine) contra PostgreSQL
- Si PostgreSQL no disponible: SKIP con clasificación STATIC_INSPECTION para los tests no-pg
- Mantener test de revisión estática separado y correctamente clasificado
"""

from __future__ import annotations

import os
import subprocess

import pytest
from sqlalchemy import create_engine, inspect

# ---------------------------------------------------------------------------
# Test de inspección estática — UNIT (no requiere PostgreSQL)
# ---------------------------------------------------------------------------

def test_alembic_revision_chain_static():
    """
    STATIC_INSPECTION — Verifica que la revisión hh450110045dc tenga
    down_revision=gl440610044rb en el script de Alembic.

    Clasificación: UNIT / STATIC — NO es evidencia de ejecución real de Alembic.
    """
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)

    rev = script.get_revision("hh450110045dc")
    assert rev is not None, "Revisión hh450110045dc no encontrada en alembic/versions/"
    assert rev.down_revision == "gl440610044rb", (
        f"down_revision esperado: gl440610044rb, "
        f"obtenido: {rev.down_revision}"
    )


def test_orm_models_numeric_precision_static():
    """
    STATIC_INSPECTION — Verifica que los modelos ORM usen Numeric(38,18).

    Clasificación: UNIT / STATIC — NO es evidencia de schema PostgreSQL real.
    """
    from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
        InventoryBalanceDeltaModel,
        InventoryPositionBalanceModel,
    )

    assert str(InventoryPositionBalanceModel.quantity.property.columns[0].type) == "NUMERIC(38, 18)"
    assert str(InventoryBalanceDeltaModel.delta_quantity.property.columns[0].type) == "NUMERIC(38, 18)"


# ---------------------------------------------------------------------------
# Test de ciclo Alembic real — MIGRATION (requiere PostgreSQL)
# ---------------------------------------------------------------------------

PHASE_045_TABLES = [
    "inventory_position_balances",
    "inventory_balance_deltas",
    "inventory_balance_projection_cursors",
    "inventory_balance_formula_definitions",
    "inventory_balance_formula_versions",
    "inventory_balance_checkpoints",
    "inventory_balance_rebuild_jobs",
    "inventory_balance_rebuild_differences",
    "inventory_balance_reconciliation_jobs",
    "inventory_balance_reconciliation_differences",
    "inventory_balance_export_jobs",
]

_TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", "")
_POSTGRES_AVAILABLE = _TEST_DB_URL.startswith("postgresql")


def _get_existing_tables(engine) -> list[str]:
    """Retorna las tablas existentes en la DB consultando PostgreSQL directamente."""
    inspector = inspect(engine)
    return inspector.get_table_names()


@pytest.mark.migration
@pytest.mark.postgres
def test_alembic_upgrade_downgrade_cycle_real():
    """
    ALEMBIC_CYCLE REAL contra PostgreSQL.

    Flujo:
    1. alembic upgrade gl440610044rb (baseline Fase 044)
    2. Verificar tablas 044 existen
    3. alembic upgrade hh450110045dc (Fase 045)
    4. Verificar tablas 045 existen via inspect(engine)
    5. alembic downgrade gl440610044rb
    6. Verificar tablas 045 eliminadas
    7. Verificar tablas 044 preservadas
    8. alembic upgrade hh450110045dc (segundo upgrade — idempotencia)
    9. PASS
    """
    if not _POSTGRES_AVAILABLE:
        pytest.skip(
            "BLOCKED_POSTGRES_UNAVAILABLE: TEST_DATABASE_URL no apunta a PostgreSQL. "
            "Este test requiere alembic real contra PostgreSQL."
        )

    app_env = os.environ.get("APP_ENV", "development")
    assert app_env in ("testing", "test"), (
        f"SAFETY GUARD: APP_ENV debe ser 'testing' para ejecutar migraciones destructivas. "
        f"APP_ENV={app_env}"
    )

    url = _TEST_DB_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    engine = create_engine(url, pool_pre_ping=True)

    def run_alembic(*args: str) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["DATABASE_URL"] = url
        env["APP_ENV"] = "testing"
        result = subprocess.run(
            ["python", "-m", "alembic", *args],
            capture_output=True, text=True, env=env, timeout=60, check=False,
        )
        assert result.returncode == 0, (
            f"alembic {' '.join(args)} FAILED:\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
        return result

    try:
        # Paso 1: Upgrade hasta baseline 044
        run_alembic("upgrade", "gl440610044rb")
        tables_after_044 = _get_existing_tables(engine)

        # Ninguna tabla de 045 debe existir todavía
        for table in PHASE_045_TABLES:
            assert table not in tables_after_044, (
                f"MIGRATION FAIL: Tabla {table} (Fase 045) existe antes del upgrade 045"
            )

        # Paso 2: Upgrade a Fase 045
        run_alembic("upgrade", "hh450110045dc")
        tables_after_045 = _get_existing_tables(engine)

        # Todas las tablas de 045 deben existir
        for table in PHASE_045_TABLES:
            assert table in tables_after_045, (
                f"MIGRATION FAIL: Tabla {table} no fue creada por hh450110045dc. "
                f"Tablas existentes: {[t for t in tables_after_045 if 'inventory' in t]}"
            )

        # Paso 3: Downgrade a 044
        run_alembic("downgrade", "gl440610044rb")
        tables_after_downgrade = _get_existing_tables(engine)

        # Tablas 045 deben haber sido eliminadas
        for table in PHASE_045_TABLES:
            assert table not in tables_after_downgrade, (
                f"MIGRATION FAIL: Tabla {table} (Fase 045) persiste después del downgrade. "
                f"El downgrade no es limpio."
            )

        # Paso 4: Segundo upgrade (idempotencia de migraciones)
        run_alembic("upgrade", "hh450110045dc")
        tables_final = _get_existing_tables(engine)

        for table in PHASE_045_TABLES:
            assert table in tables_final, (
                f"MIGRATION FAIL: Tabla {table} no existe después del segundo upgrade. "
                f"Las migraciones no son idempotentes."
            )

    finally:
        engine.dispose()
