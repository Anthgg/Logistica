"""Pruebas del detector de secretos (Fase 005.3).

Un detector sin pruebas es una falsa sensación de seguridad: si deja de detectar,
nadie se entera hasta el siguiente incidente. Se comprueban las dos mitades — que
encuentra lo que debe y que no denuncia a los ejemplos — y, sobre todo, que **nunca
imprime el valor** que encontró.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import scan_for_secrets as scanner

#: El valor sensible de cada caso se construye en la prueba; nunca se versiona uno real.
DETECTED_CASES = [
    ("cadena de conexión", "DATABASE_URL=postgresql://usuario:" + "S3cr3tPassw0rd" + "@db.prod-cluster.internal/x"),
    ("clave privada", "-----BEGIN PRIVATE KEY-----"),
    ("token JWT", "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abcdefghij"),
]


@pytest.mark.parametrize(("label", "line"), DETECTED_CASES, ids=[c[0] for c in DETECTED_CASES])
def test_detects_sensitive_lines(label: str, line: str) -> None:
    findings = scanner.scan_text(line, "prueba")
    assert findings, f"no detectó: {label}"


def test_findings_never_include_the_secret_value() -> None:
    """La regla que da sentido al detector: informar sin repetir."""
    secret = "Sup3rS3cretValue123"
    findings = scanner.scan_text(f"DATABASE_URL=postgresql://user:{secret}@db.prod-cluster.internal/db", "prueba")
    assert findings
    for finding in findings:
        assert secret not in finding
        assert "postgresql://" not in finding


def test_finding_reports_origin_and_line_number() -> None:
    text = "linea uno\nlinea dos\n-----BEGIN PRIVATE KEY-----\n"
    (finding,) = scanner.scan_text(text, "fichero.yml")
    assert finding.startswith("fichero.yml:3:")


@pytest.mark.parametrize(
    "line",
    [
        'SECRET_KEY: str = Field(default="development-only-change-me")',
        "DATABASE_URL=postgresql://user:<password>@host/db",
        "password=***",
        "SECRET_KEY=${{ secrets.SECRET_KEY }}",
        "--set-secrets=SECRET_KEY=SECRET_KEY_PRODUCTION:latest",
    ],
    ids=["default de desarrollo", "marcador", "enmascarado", "referencia de Actions", "referencia a Secret Manager"],
)
def test_placeholders_and_references_are_not_flagged(line: str) -> None:
    """Un detector que grita ante cada ejemplo se acaba desactivando."""
    assert scanner.scan_text(line, "prueba") == []


def test_clean_text_produces_no_findings() -> None:
    text = "APP_ENV=production\nLOG_LEVEL=INFO\nRUN_MIGRATIONS=false\n"
    assert scanner.scan_text(text, "prueba") == []


def test_deployment_workflows_are_clean() -> None:
    """Comprobación real sobre el repositorio, no sobre cadenas de laboratorio.

    Se auditan los workflows que tocan producción. `ci.yml` queda fuera a propósito:
    lleva credenciales de un contenedor PostgreSQL efímero contra `localhost` y una
    `SECRET_KEY` de test, que no son secretos productivos y desaparecen con el runner.
    """
    workflows = Path(__file__).resolve().parents[2] / ".github" / "workflows"
    findings: list[str] = []
    for name in ("production-deploy.yml", "staging-deploy.yml", "database-migration.yml"):
        path = workflows / name
        assert path.is_file(), f"no existe {name}"
        findings.extend(scanner.scan_text(path.read_text(encoding="utf-8"), str(path)))
    assert findings == [], f"posibles secretos en los workflows de despliegue: {findings}"
