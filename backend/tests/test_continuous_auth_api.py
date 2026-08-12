from datetime import datetime, timezone
from time import sleep

import pytest
from pydantic import ValidationError

from app.core.config import settings
from app.main import app
from app.ml.model_bundle import ComponentInference
from app.schemas.continuous_auth import ContinuousAuthEvaluateRequest
from app.services.continuous_auth_service import ContinuousAuthService
from app.services.model_loader_service import ModelLoaderService


def test_openapi_exposes_phase9a_routes() -> None:
    paths = app.openapi()["paths"]
    expected_methods = {
        "/api/models/status": "get",
        "/api/continuous-auth/evaluate": "post",
        "/api/continuous-auth/status": "get",
        "/api/continuous-auth/evaluations": "get",
        "/api/continuous-auth/evaluations/{evaluation_id}": "get",
        "/api/continuous-auth/reverify": "post",
    }
    for path, method in expected_methods.items():
        assert path in paths
        assert method in paths[path]


@pytest.mark.parametrize(
    "forbidden",
    [
        {"facial_score": 0.1},
        {"pad_score": 0.1},
        {"behavioral_score": 0.1},
        {"risk_score": 0.1},
        {"authentication_level": "continuously_verified"},
    ],
)
def test_evaluate_contract_rejects_client_scores(
    forbidden: dict[str, object],
) -> None:
    payload = {
        "experimental_session_id": (
            "00000000-0000-0000-0000-000000000001"
        ),
        "facial_capture_id": (
            "00000000-0000-0000-0000-000000000002"
        ),
        "evaluation_timestamp": datetime.now(timezone.utc),
        **forbidden,
    }
    with pytest.raises(ValidationError):
        ContinuousAuthEvaluateRequest.model_validate(payload)


def test_evaluate_requires_a_component_reference() -> None:
    with pytest.raises(ValidationError):
        ContinuousAuthEvaluateRequest(
            experimental_session_id=(
                "00000000-0000-0000-0000-000000000001"
            ),
            evaluation_timestamp=datetime.now(timezone.utc),
        )


def test_public_evaluation_schema_does_not_expose_sensitive_fields() -> None:
    response_schema = app.openapi()["components"]["schemas"][
        "ContinuousAuthPublicEvaluation"
    ]
    properties = set(response_schema["properties"])
    assert "embedding" not in properties
    assert "threshold" not in properties
    assert "weights" not in properties
    assert "model_path" not in properties


@pytest.mark.asyncio
async def test_component_timeout_returns_sanitized_degraded_result() -> None:
    configured = settings.model_copy(
        update={"INFERENCE_TIMEOUT_SECONDS": 1}
    )
    service = ContinuousAuthService(
        ModelLoaderService(configured),
        configured,
    )

    def slow_inference() -> ComponentInference:
        sleep(1.05)
        return ComponentInference(
            available=True,
            valid=True,
            score=0.5,
            risk=0.5,
            decision="completed_too_late",
            latency_ms=1050,
            model_version="fixture",
        )

    result = await service._safe_component("behavioral", slow_inference)

    assert result.available is False
    assert result.reason_code == "INFERENCE_TIMEOUT"
