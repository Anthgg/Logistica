"""Guardas estáticas del pipeline de despliegue productivo (Fase 005.3).

El workflow de despliegue no se puede ejercitar en CI: despliega producción. Lo que
sí se puede fijar es su forma, y en particular las regresiones que lo mantuvieron
inservible:

1. los pasos de despliegue solo imprimían el comando `gcloud` con `echo`;
2. la autenticación llevaba `continue-on-error: true`;
3. los secretos se pasaban como variables de entorno literales.

Se comprueba además que existen las dos verificaciones sin las cuales un despliegue
"correcto" no significa nada: que la revisión quede lista y que responda al health.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"
PRODUCTION = WORKFLOWS / "production-deploy.yml"
STAGING = WORKFLOWS / "staging-deploy.yml"

#: Patrones que nunca deben aparecer como literales en un workflow.
SECRET_PATTERNS: tuple[tuple[str, str], ...] = (
    ("cadena de conexión", r"postgres(?:ql)?://[^\s\"']*:[^\s\"']*@"),
    ("SECRET_KEY literal", r"SECRET_KEY=(?!\$\{\{)(?!SECRET_KEY_PRODUCTION)[^\s,\"']+"),
    ("password literal", r"(?i)password=(?!\$\{\{)[^\s,\"']+"),
    ("service role key", r"(?i)service[_-]role[_-]key\s*[:=]\s*[A-Za-z0-9]"),
    ("JWT secret literal", r"JWT_SECRET=(?!\$\{\{)[^\s,\"']+"),
    ("clave privada", r"BEGIN (?:RSA |EC )?PRIVATE KEY"),
)


@pytest.fixture(scope="module")
def raw() -> str:
    assert PRODUCTION.is_file(), f"no existe {PRODUCTION}"
    return PRODUCTION.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def workflow(raw: str) -> dict:
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    return parsed


def effective_lines(text: str) -> list[str]:
    """Líneas que ejecuta el workflow. Los comentarios explican las reglas y las nombran."""
    return [line for line in text.splitlines() if not line.lstrip().startswith("#")]


def steps(workflow: dict) -> list[dict]:
    (job,) = workflow["jobs"].values()
    return job["steps"]


def test_workflow_is_valid_yaml(workflow: dict) -> None:
    assert workflow.get("name")
    assert workflow.get("jobs")


def test_deploy_is_not_triggered_by_arbitrary_pushes(workflow: dict) -> None:
    """Producción se despliega a propósito, no por empujar a una rama."""
    triggers = workflow.get("on", workflow.get(True))
    assert set(triggers) == {"workflow_dispatch"}, f"disparadores inesperados: {sorted(triggers)}"


def test_deploy_uses_production_environment(workflow: dict) -> None:
    (job,) = workflow["jobs"].values()
    assert job.get("environment") == "production"


def test_auth_step_is_fail_fast(workflow: dict) -> None:
    auth = next(
        (s for s in steps(workflow) if str(s.get("uses", "")).startswith("google-github-actions/auth")),
        None,
    )
    assert auth is not None, "no hay paso de autenticación GCP"
    assert auth.get("continue-on-error") in (None, False)


def test_no_step_silences_failures(workflow: dict) -> None:
    offenders = [
        s.get("name", s.get("uses", "<sin nombre>"))
        for s in steps(workflow)
        if s.get("continue-on-error") is True
    ]
    assert not offenders, f"pasos con continue-on-error: {offenders}"


def test_deploy_is_real_not_echoed(raw: str) -> None:
    """La regresión original: `echo "Deploying Cloud Run service ..."`."""
    echoed = re.findall(r"""echo\s+["'][^"'\n]*gcloud\s+run\s+deploy""", raw)
    assert not echoed, f"el despliegue sigue siendo un echo: {echoed}"


def test_workflow_actually_deploys(raw: str) -> None:
    invocations = [line.strip() for line in effective_lines(raw) if "gcloud run deploy" in line]
    assert invocations, "el workflow no despliega Cloud Run en ningún paso"
    for line in invocations:
        assert not line.lstrip().startswith("echo "), f"despliegue simulado: {line}"


def test_image_is_pinned_by_digest(raw: str) -> None:
    """Una etiqueta se puede mover; un digest no."""
    assert "image_summary.digest" in raw, "el workflow no resuelve el digest de la imagen"
    assert "--image=\"${{ steps.digest.outputs.ref }}\"" in raw, (
        "el despliegue no usa la referencia por digest"
    )


def test_image_is_traceable_to_a_commit(raw: str) -> None:
    assert "steps.target.outputs.short" in raw, "la imagen no se etiqueta con el commit"


def test_secrets_are_injected_by_reference(raw: str) -> None:
    """`--set-secrets` referencia Secret Manager; `--set-env-vars` expondría el valor."""
    assert "--set-secrets=" in raw
    assert "DATABASE_URL=DATABASE_URL_PRODUCTION" in raw
    assert "SECRET_KEY=SECRET_KEY_PRODUCTION" in raw


def test_no_secret_is_passed_as_plain_env_var(raw: str) -> None:
    env_var_lines = [line for line in effective_lines(raw) if "--set-env-vars=" in line]
    assert env_var_lines, "se esperaba al menos una línea de configuración no sensible"
    for line in env_var_lines:
        for name in ("DATABASE_URL", "SECRET_KEY"):
            assert name not in line, f"{name} viaja como variable literal: {line.strip()}"


def test_revision_readiness_is_verified(raw: str) -> None:
    assert "gcloud run revisions describe" in raw
    assert "type:Ready" in raw


def test_health_is_checked_before_promoting_traffic(raw: str) -> None:
    """Una revisión que arranca no es una revisión que funciona."""
    body = effective_lines(raw)
    health = next((i for i, line in enumerate(body) if "/health" in line), None)
    promote = next((i for i, line in enumerate(body) if "update-traffic" in line), None)
    assert health is not None, "no hay comprobación de health"
    assert promote is not None, "no hay promoción de tráfico"
    assert health < promote, "el tráfico se promueve antes de comprobar el health"


def test_new_revision_receives_no_traffic_initially(raw: str) -> None:
    assert "--no-traffic" in raw


def test_rollback_exists_and_triggers_on_failure(raw: str) -> None:
    body = "\n".join(effective_lines(raw))
    assert "failure()" in body, "no hay paso condicionado al fallo"
    assert "steps.before.outputs.revision" in body, "no se registró la revisión previa"


def test_rollback_target_is_the_revision_actually_serving(raw: str) -> None:
    """El destino de rollback se toma del 100% del tráfico, no del primer elemento.

    Con `status.traffic[0]` el workflow devolvía una revisión etiquetada sin
    porcentaje, y el rollback mandaba el tráfico a una revisión que no estaba
    sirviendo. Ocurrió de verdad en el primer despliegue de F005.3.
    """
    body = "\n".join(effective_lines(raw))
    assert "status.traffic[0]" not in body, (
        "el destino de rollback sale del primer elemento del tráfico, "
        "que puede ser una revisión con tag y sin porcentaje"
    )
    assert 'status.traffic.filter("percent:100")' in body, (
        "el destino de rollback no se filtra por la revisión que sirve el 100%"
    )


def test_readiness_uses_exact_condition_match(raw: str) -> None:
    """`type:Ready` hace coincidencia laxa y devuelve varias condiciones a la vez."""
    body = "\n".join(effective_lines(raw))
    assert 'filter("type:Ready")' not in body, (
        "la comprobación de readiness usa coincidencia laxa y puede devolver "
        "el estado de varias condiciones"
    )
    assert 'filter("type=Ready")' in body


def test_concurrency_prevents_parallel_deploys(workflow: dict) -> None:
    concurrency = workflow.get("concurrency")
    assert concurrency, "el workflow no declara concurrency"
    assert concurrency.get("cancel-in-progress") is False


def test_no_secret_literals_in_workflow(raw: str) -> None:
    for label, pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, raw)
        assert not matches, f"posible {label} embebido en el workflow"


def test_secrets_are_not_written_to_workflow_outputs(raw: str) -> None:
    """`$GITHUB_OUTPUT` y `$GITHUB_ENV` sobreviven al paso y se ven en la interfaz."""
    for line in effective_lines(raw):
        if "GITHUB_OUTPUT" not in line and "GITHUB_ENV" not in line:
            continue
        for name in ("DATABASE_URL", "SECRET_KEY", "PASSWORD"):
            assert name not in line, f"se escribe {name} en una salida del workflow: {line.strip()}"


def test_no_shell_tracing_around_secrets(raw: str) -> None:
    """`set -x` imprimiría los comandos expandidos, secretos incluidos."""
    assert not re.search(r"set\s+-[a-z]*x", raw), "el workflow activa trazas de shell"


def test_staging_workflow_does_not_pretend_to_deploy() -> None:
    """Staging no existe: el workflow no puede simular que despliega."""
    text = STAGING.read_text(encoding="utf-8")
    body = "\n".join(effective_lines(text))
    assert "gcloud run deploy" not in body, "el workflow de staging aún intenta desplegar"
    assert "continue-on-error" not in body, "el workflow de staging silencia fallos"
    assert "STAGING_AVAILABLE=false" in body, "no declara que staging no existe"


def test_obsolete_cd_pipeline_is_gone() -> None:
    """Tres pipelines haciendo lo mismo garantizan que dos estén desactualizados."""
    assert not (WORKFLOWS / "cd.yml").exists(), "cd.yml sigue presente y duplica el despliegue"
