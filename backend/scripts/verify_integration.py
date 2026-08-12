import argparse
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine, inspect, text

from _phase9_common import BACKEND_ROOT

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.main import app
from app.services.model_loader_service import ModelLoaderService

EXPECTED_COLUMNS = {
    "continuous_auth_evaluations": {
        "id",
        "user_id",
        "session_id",
        "combined_risk",
        "risk_level",
        "authentication_level",
        "model_versions",
        "latency_breakdown",
        "evaluated_at",
    },
    "risk_events": {
        "id",
        "continuous_auth_evaluation_id",
        "user_id",
        "session_id",
        "new_risk_level",
        "reason_code",
    },
    "sessions": {
        "risk_score",
        "authentication_level",
        "last_continuous_verification_at",
        "last_risk_action",
        "continuous_auth_status",
    },
}


def _verify_database(engine) -> None:
    inspector = inspect(engine)
    missing: dict[str, list[str]] = {}
    for table, expected in EXPECTED_COLUMNS.items():
        if not inspector.has_table(table):
            missing[table] = sorted(expected)
            continue
        actual = {
            str(column["name"]) for column in inspector.get_columns(table)
        }
        absent = sorted(expected - actual)
        if absent:
            missing[table] = absent
    if missing:
        raise SystemExit(f"Falta esquema de Fase 9A: {missing}")


def _transactional_write_test(engine) -> None:
    now = datetime.now(timezone.utc)
    user_id = uuid4()
    session_id = uuid4()
    evaluation_id = uuid4()
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(
                text(
                    """
                    INSERT INTO users (
                      id, email, password_hash, full_name, role, is_active,
                      is_verified, failed_login_attempts, created_at, updated_at
                    ) VALUES (
                      :id, :email, 'transactional-not-a-real-hash',
                      'Phase 9A Verification', 'admin', true, false, 0,
                      :now, :now
                    )
                    """
                ),
                {
                    "id": user_id,
                    "email": f"phase9-{user_id}@example.invalid",
                    "now": now,
                },
            )
            connection.execute(
                text(
                    """
                    INSERT INTO sessions (
                      id, user_id, token_hash, created_at, last_activity_at,
                      expires_at, risk_score, authentication_level,
                      created_by_login, continuous_auth_status
                    ) VALUES (
                      :id, :user_id, :token_hash, :now, :now,
                      :expires_at, 0, 'traditional', true, 'pending'
                    )
                    """
                ),
                {
                    "id": session_id,
                    "user_id": user_id,
                    "token_hash": uuid4().hex,
                    "now": now,
                    "expires_at": now.replace(year=now.year + 1),
                },
            )
            connection.execute(
                text(
                    """
                    INSERT INTO continuous_auth_evaluations (
                      id, user_id, session_id, facial_available,
                      pad_available, behavioral_available, combined_risk,
                      risk_level, authentication_level, recommended_action,
                      applied_action, model_versions, latency_ms,
                      latency_breakdown, evaluated_at, created_at
                    ) VALUES (
                      :id, :user_id, :session_id, true, true, false,
                      0.5, 'medium', 'traditional', 'increase_monitoring',
                      'observe_session', CAST('{}' AS jsonb), 1,
                      CAST('{"total_ms": 1}' AS jsonb), :now, :now
                    )
                    """
                ),
                {
                    "id": evaluation_id,
                    "user_id": user_id,
                    "session_id": session_id,
                    "now": now,
                },
            )
            connection.execute(
                text(
                    """
                    INSERT INTO risk_events (
                      id, continuous_auth_evaluation_id, user_id, session_id,
                      new_risk_level, recommended_action, applied_action,
                      reason_code, created_at
                    ) VALUES (
                      :id, :evaluation_id, :user_id, :session_id, 'medium',
                      'increase_monitoring', 'observe_session',
                      'TRANSACTIONAL_SCHEMA_TEST', :now
                    )
                    """
                ),
                {
                    "id": uuid4(),
                    "evaluation_id": evaluation_id,
                    "user_id": user_id,
                    "session_id": session_id,
                    "now": now,
                },
            )
        finally:
            transaction.rollback()
    print("Persistencia transaccional verificada y revertida.")


def _verify_openapi() -> None:
    paths = app.openapi()["paths"]
    expected = {
        "/api/models/status",
        "/api/continuous-auth/evaluate",
        "/api/continuous-auth/status",
        "/api/continuous-auth/evaluations",
        "/api/continuous-auth/evaluations/{evaluation_id}",
        "/api/continuous-auth/reverify",
    }
    missing = sorted(expected - set(paths))
    if missing:
        raise SystemExit(f"Faltan rutas OpenAPI: {missing}")


def _verify_http(api_url: str) -> None:
    import httpx

    base = api_url.rstrip("/")
    health = httpx.get(f"{base}/health", timeout=10)
    health.raise_for_status()
    for path in ("/models/status", "/continuous-auth/status"):
        response = httpx.get(f"{base}{path}", timeout=10)
        if response.status_code not in {401, 403}:
            raise SystemExit(
                f"{path} no aplicó autenticación: {response.status_code}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url")
    parser.add_argument(
        "--transactional-write-test", action="store_true"
    )
    arguments = parser.parse_args()
    strict = settings.model_copy(
        update={
            "REQUIRE_ALL_MODELS": True,
            "MODEL_LOAD_ON_STARTUP": True,
        }
    )
    loader = ModelLoaderService(strict)
    try:
        try:
            status = loader.startup()
        except ApplicationError as exc:
            raise SystemExit(
                f"Integración de modelos rechazada | code={exc.code}"
            ) from exc
    finally:
        loader.shutdown()
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    try:
        _verify_database(engine)
        if arguments.transactional_write_test:
            _transactional_write_test(engine)
    finally:
        engine.dispose()
    _verify_openapi()
    if arguments.api_url:
        _verify_http(arguments.api_url)
    print(
        "Integración Fase 9A verificada | "
        f"model_status={status.global_status} "
        f"backend={BACKEND_ROOT.name}"
    )


if __name__ == "__main__":
    main()
