"""
Fixtures de PostgreSQL real para tests de integración de Fase 045.

REGLA: Si TEST_DATABASE_URL no apunta a PostgreSQL, los tests marcados
con @pytest.mark.postgres se saltarán con SKIP explicativo.
"""

from __future__ import annotations

import os
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

# Guard: si no hay URL postgres real → skip automático en cada test postgres
_TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", "")
_POSTGRES_AVAILABLE = _TEST_DB_URL.startswith("postgresql")

_SKIP_POSTGRES = pytest.mark.skipif(
    not _POSTGRES_AVAILABLE,
    reason=(
        "BLOCKED_POSTGRES_UNAVAILABLE: TEST_DATABASE_URL no apunta a PostgreSQL. "
        "Configura TEST_DATABASE_URL=postgresql+psycopg://user:pass@host:5432/dbname "
        "para ejecutar tests de integración real."
    ),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_postgres():
    """Saltar el test si no hay PostgreSQL disponible."""
    if not _POSTGRES_AVAILABLE:
        pytest.skip(
            "BLOCKED_POSTGRES_UNAVAILABLE: TEST_DATABASE_URL no apunta a PostgreSQL. "
            "Este test requiere engine y Session reales contra PostgreSQL."
        )


# ---------------------------------------------------------------------------
# Engine real de PostgreSQL
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def pg_engine():
    """
    Engine real contra PostgreSQL de testing.
    - Requiere TEST_DATABASE_URL=postgresql+psycopg://...
    - Crea el schema de tablas de Fase 045 via create_all.
    - Destruye las tablas al finalizar la sesión.
    """
    _require_postgres()

    url = _TEST_DB_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    # Verificar que la URL tiene driver psycopg
    assert "psycopg" in url, (
        f"TEST_DATABASE_URL debe usar driver psycopg (postgresql+psycopg://...). "
        f"URL detectada: {url[:40]}..."
    )

    # Guard: nunca ejecutar contra producción
    app_env = os.environ.get("APP_ENV", "development")
    assert app_env in ("testing", "test"), (
        f"SAFETY GUARD: APP_ENV debe ser 'testing' para ejecutar tests destructivos. "
        f"APP_ENV actual: {app_env}"
    )

    import app.models.registry  # noqa: F401 — registrar todos los ORM models

    from app.database.base import Base

    engine = create_engine(url, pool_pre_ping=True)

    # Verificar conectividad real
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        pg_version = result.scalar()
        assert "PostgreSQL" in pg_version, f"Engine no es PostgreSQL: {pg_version}"

    # Crear tablas de Fase 045 (y dependencias) via ORM
    # Nota: en CI se usa 'alembic upgrade head' antes de pytest.
    # Aquí se usa create_all para permitir ejecución local cuando hay PostgreSQL.
    Base.metadata.create_all(engine, checkfirst=True)

    yield engine

    # Limpiar tablas de Fase 045 al terminar la sesión de test
    _cleanup_phase045_tables(engine)
    engine.dispose()


def _cleanup_phase045_tables(engine) -> None:
    """Elimina (TRUNCATE o DROP) las tablas de Fase 045 después de los tests."""
    phase045_tables = [
        "inventory_balance_export_jobs",
        "inventory_balance_reconciliation_differences",
        "inventory_balance_reconciliation_jobs",
        "inventory_balance_rebuild_differences",
        "inventory_balance_rebuild_jobs",
        "inventory_balance_checkpoints",
        "inventory_balance_formula_versions",
        "inventory_balance_formula_definitions",
        "inventory_balance_projection_cursors",
        "inventory_balance_deltas",
        "inventory_position_balances",
    ]
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    with engine.begin() as conn:
        for table in phase045_tables:
            if table in existing_tables:
                conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))


# ---------------------------------------------------------------------------
# Session real de PostgreSQL (por test — con rollback al finalizar)
# ---------------------------------------------------------------------------

@pytest.fixture
def pg_session(pg_engine):
    """
    Session real contra PostgreSQL de testing.

    Cada test recibe una Session fresca. Al finalizar:
    - Se hace ROLLBACK de la transacción externa (aislamiento entre tests).

    Esto garantiza:
    - BEGIN real
    - INSERT/SELECT/UPDATE/DELETE reales
    - COMMIT real dentro de la transacción
    - Aislamiento: los cambios no contaminan otros tests
    """
    connection = pg_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Session independiente (para tests de concurrencia que necesitan 2 sesiones)
# ---------------------------------------------------------------------------

@pytest.fixture
def pg_engine_direct(pg_engine):
    """Retorna el engine directo para que los tests de concurrencia creen sus propias Sessions."""
    return pg_engine
