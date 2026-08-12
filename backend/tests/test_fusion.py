from datetime import datetime, timezone

import pytest

from app.core.exceptions import ApplicationError
from app.ml.fusion_runtime import FusionConfig
from app.services.fusion_service import FusionService


def _config(
    *,
    strategy: str = "renormalize_available_weights",
    minimum: int = 2,
) -> FusionConfig:
    return FusionConfig.model_validate(
        {
            "fusion_version": "v1",
            "method": "weighted_late_fusion",
            "weights": {
                "facial": 0.5,
                "pad": 0.3,
                "behavioral": 0.2,
            },
            "missing_component_strategy": strategy,
            "minimum_available_components": minimum,
            "neutral_risk": 0.5 if strategy == "use_neutral_risk" else None,
            "risk_thresholds": {
                "low_max": 0.3,
                "medium_max": 0.6,
                "high_max": 0.8,
            },
            "validation_metrics": {},
            "dataset_version": "pilot-v0.1.0",
            "generated_at": datetime.now(timezone.utc),
            "checksum": "0" * 64,
        }
    )


def test_fusion_calculates_weighted_risk() -> None:
    result = FusionService(_config()).fuse(
        {"facial": 0.2, "pad": 0.4, "behavioral": 0.8}
    )
    assert result.risk == pytest.approx(0.38)


def test_fusion_renormalizes_only_available_weights() -> None:
    result = FusionService(_config()).fuse(
        {"facial": 0.2, "pad": 0.4, "behavioral": None}
    )
    assert result.risk == pytest.approx((0.5 * 0.2 + 0.3 * 0.4) / 0.8)


def test_fusion_rejects_insufficient_components() -> None:
    with pytest.raises(ApplicationError) as error:
        FusionService(_config(minimum=2)).fuse(
            {"facial": 0.2, "pad": None, "behavioral": None}
        )
    assert error.value.code == "INSUFFICIENT_COMPONENTS"


def test_missing_component_is_never_treated_as_zero() -> None:
    result = FusionService(_config()).fuse(
        {"facial": 0.5, "pad": 0.5, "behavioral": None}
    )
    assert result.risk == pytest.approx(0.5)


@pytest.mark.parametrize("invalid_risk", [float("nan"), -0.1, 1.1])
def test_fusion_rejects_invalid_component_risk(
    invalid_risk: float,
) -> None:
    with pytest.raises(ApplicationError) as error:
        FusionService(_config()).fuse(
            {
                "facial": invalid_risk,
                "pad": 0.5,
                "behavioral": 0.5,
            }
        )
    assert error.value.code == "INTERNAL_INFERENCE_ERROR"


def test_fusion_weights_must_sum_to_one() -> None:
    payload = _config().model_dump()
    payload["weights"] = {
        "facial": 0.5,
        "pad": 0.5,
        "behavioral": 0.5,
    }
    with pytest.raises(ValueError):
        FusionConfig.model_validate(payload)
