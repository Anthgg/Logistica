"""Guardas de aislamiento para tests que escriben datos reales.

Algunas suites -- Fase 020 y las regresiones HTTP de Documents -- no usan las
fixtures de `conftest`: abren `SessionLocal()` de la aplicacion y hacen commit.
Si `DATABASE_URL` apunta a la base de desarrollo, esos commits quedan ahi.

Eso ya ocurrio: la suite de Fase 020 dejo documentos con filas de artifact cuyo
PDF se escribio en un contenedor efimero, y esos documentos aparecieron despues
en la UI durante una prueba de aceptacion. La contaminacion no se detecto sola;
la descubrio un usuario abriendo un documento roto.

Estas guardas fallan pronto y con un motivo legible en vez de confiar en que
quien ejecute los tests recuerde exportar la variable correcta.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

import pytest

from app.core.config import settings

#: Sufijos que identifican una base pensada para tests.
TEST_DATABASE_SUFFIXES = ("_test", "_testing")


def _database_name(url: str) -> str:
    return urlparse(url).path.lstrip("/")


def isolated_database_reason(database_url: str | None = None) -> str | None:
    """Devuelve el motivo por el que la base NO esta aislada, o None si lo esta.

    Se acepta una base cuando coincide con `TEST_DATABASE_URL`, cuando su nombre
    termina en un sufijo de test, o cuando es SQLite (en memoria o fichero
    temporal, que no es la base de nadie).
    """
    url = database_url or str(settings.DATABASE_URL)
    if url.startswith("sqlite"):
        return None

    configured = os.getenv("TEST_DATABASE_URL")
    if configured and url == configured:
        return None

    name = _database_name(url)
    if name.endswith(TEST_DATABASE_SUFFIXES):
        return None

    return (
        f"la base de datos '{name}' no es una base de test. "
        "Estos casos hacen COMMIT: contra una base de desarrollo dejarian "
        "documentos, series y eventos de auditoria reales. "
        "Exporta TEST_DATABASE_URL (y DATABASE_URL) apuntando a una base cuyo "
        "nombre termine en '_test'."
    )


def require_isolated_database() -> None:
    """Aborta la suite si los commits irian a una base que no es de test."""
    reason = isolated_database_reason()
    if reason:
        pytest.exit(f"AISLAMIENTO DE BASE DE TEST REQUERIDO: {reason}", returncode=2)


@pytest.fixture(scope="module")
def isolated_database() -> None:
    """Guarda de modulo para suites que escriben con `SessionLocal()`."""
    require_isolated_database()


@pytest.fixture()
def isolated_document_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Manda los artifacts del test a un temporal, no al storage del usuario."""
    root = tmp_path / "document-storage"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "DOCUMENT_STORAGE_PATH", str(root), raising=False)
    return root
