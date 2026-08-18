"""Guardas estáticas del workflow de release de base de datos (Fase 005.2).

El workflow de migraciones no se puede probar ejecutándolo: apunta a producción. Lo
que sí se puede fijar es su forma, y en concreto las dos regresiones que lo dejaron
inservible durante meses:

1. el paso de ejecución solo imprimía el comando ``gcloud`` en vez de lanzarlo;
2. la autenticación llevaba ``continue-on-error: true``, de modo que un fallo de
   credenciales seguía adelante y el workflow terminaba en verde.

Estas pruebas fallan si cualquiera de las dos vuelve.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "database-migration.yml"


@pytest.fixture(scope="module")
def raw_workflow() -> str:
    assert WORKFLOW_PATH.is_file(), f"no existe {WORKFLOW_PATH}"
    return WORKFLOW_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def workflow(raw_workflow: str) -> dict:
    parsed = yaml.safe_load(raw_workflow)
    assert isinstance(parsed, dict), "el workflow no es un mapa YAML"
    return parsed


def _trigger(workflow: dict) -> dict:
    """`on:` es interpretado como booleano True por YAML 1.1; aceptamos ambas claves."""
    triggers = workflow.get("on", workflow.get(True))
    assert isinstance(triggers, dict), "no se encontró la sección de disparadores"
    return triggers


def _steps(workflow: dict) -> list[dict]:
    jobs = workflow["jobs"]
    assert len(jobs) == 1, "se espera un único job de migración"
    (job,) = jobs.values()
    return job["steps"]


def _step_by_uses(steps: list[dict], prefix: str) -> dict:
    for step in steps:
        if str(step.get("uses", "")).startswith(prefix):
            return step
    pytest.fail(f"no hay ningún paso que use {prefix}")


def test_workflow_is_valid_yaml(workflow: dict) -> None:
    assert workflow.get("name")
    assert workflow.get("jobs")


def test_only_manual_dispatch(workflow: dict) -> None:
    """Producción nunca debe migrarse por un push o un merge."""
    triggers = _trigger(workflow)
    assert set(triggers) == {"workflow_dispatch"}, f"disparadores inesperados: {sorted(triggers)}"


def test_target_environment_is_a_closed_choice(workflow: dict) -> None:
    inputs = _trigger(workflow)["workflow_dispatch"]["inputs"]
    target = inputs["target_environment"]
    assert target["type"] == "choice"
    assert target["options"] == ["staging", "production"]


def test_job_binds_to_github_environment(workflow: dict) -> None:
    """El environment es lo que permite exigir revisores para producción."""
    (job,) = workflow["jobs"].values()
    assert "${{ inputs.target_environment }}" in str(job.get("environment", ""))


def test_auth_step_is_fail_fast(workflow: dict) -> None:
    """Un fallo de autenticación GCP debe detener el release, no dejarlo pasar."""
    auth = _step_by_uses(_steps(workflow), "google-github-actions/auth")
    assert auth.get("continue-on-error") in (None, False), (
        "el paso de autenticación no puede llevar continue-on-error: "
        "un fallo de credenciales terminaría en verde"
    )


def test_no_step_silences_failures(workflow: dict) -> None:
    """Ningún paso del release puede continuar tras fallar."""
    offenders = [
        step.get("name", step.get("uses", "<sin nombre>"))
        for step in _steps(workflow)
        if step.get("continue-on-error") is True
    ]
    assert not offenders, f"pasos con continue-on-error: {offenders}"


def test_gcloud_execution_is_real_not_echoed(raw_workflow: str) -> None:
    """La regresión original: `echo "gcloud run jobs execute ..."`."""
    echoed = re.findall(r"""echo\s+["'][^"'\n]*gcloud\s+run\s+jobs\s+execute""", raw_workflow)
    assert not echoed, f"el comando de ejecución sigue siendo un echo: {echoed}"


def test_workflow_actually_executes_the_job(raw_workflow: str) -> None:
    invocations = [
        line.strip()
        for line in raw_workflow.splitlines()
        if "gcloud run jobs execute" in line and not line.strip().startswith("#")
    ]
    assert invocations, "el workflow no ejecuta el Cloud Run Job en ningún paso"
    for line in invocations:
        assert not line.lstrip().startswith("echo "), f"ejecución simulada: {line}"


def test_execution_waits_for_completion(raw_workflow: str) -> None:
    """Sin --wait, el workflow terminaría antes que la migración."""
    assert "--wait" in raw_workflow


def test_execution_result_is_verified(raw_workflow: str) -> None:
    """Lanzar el Job no es lo mismo que haberlo completado con éxito."""
    assert "jobs executions describe" in raw_workflow
    assert "succeededCount" in raw_workflow
    assert "failedCount" in raw_workflow


def test_job_existence_is_checked_before_executing(raw_workflow: str) -> None:
    assert "gcloud run jobs describe" in raw_workflow


def test_concurrency_prevents_parallel_releases(workflow: dict) -> None:
    """Dos migraciones simultáneas sobre la misma base es una carrera evitable."""
    concurrency = workflow.get("concurrency")
    assert concurrency, "el workflow no declara concurrency"
    assert "inputs.target_environment" in str(concurrency["group"])
    assert concurrency.get("cancel-in-progress") is False


def test_no_hardcoded_credentials(raw_workflow: str) -> None:
    """Las credenciales vienen de secrets; nunca literales en el YAML."""
    for needle in ("postgresql://", "postgres://", "SUPABASE_SERVICE_ROLE", "BEGIN PRIVATE KEY"):
        assert needle not in raw_workflow, f"posible credencial embebida: {needle}"


def test_database_url_is_never_handled_by_the_workflow(raw_workflow: str) -> None:
    """La cadena de conexión la inyecta Secret Manager en el Job, no el workflow.

    Se ignoran los comentarios: nombrar la variable al explicar de dónde sale no es lo
    mismo que manipularla.
    """
    effective = [
        line for line in raw_workflow.splitlines() if not line.lstrip().startswith("#")
    ]
    offenders = [line.strip() for line in effective if "DATABASE_URL" in line]
    assert not offenders, f"el workflow manipula DATABASE_URL: {offenders}"
