from datetime import datetime, timezone

import pytest

from app.ml.fusion_runtime import ScoreNormalizationConfig
from app.services.score_normalization_service import (
    ScoreNormalizationService,
)


def _service() -> ScoreNormalizationService:
    component = {
        "method": "piecewise_linear",
        "lower_bound": 0.0,
        "upper_bound": 1.0,
        "threshold": 0.5,
        "clipping": True,
        "dataset_version": "pilot-v0.1.0",
        "validation_statistics": {},
    }
    config = ScoreNormalizationConfig.model_validate(
        {
            "normalization_version": "v1",
            "components": {
                "facial": {
                    **component,
                    "risk_direction": "decreasing",
                },
                "pad": {
                    **component,
                    "risk_direction": "increasing",
                },
                "behavioral": {
                    **component,
                    "risk_direction": "increasing",
                },
            },
            "dataset_version": "pilot-v0.1.0",
            "generated_at": datetime.now(timezone.utc),
            "checksum": "0" * 64,
        }
    )
    return ScoreNormalizationService(config)


@pytest.mark.parametrize("component", ["facial", "pad", "behavioral"])
def test_normalized_scores_remain_in_unit_interval(component: str) -> None:
    service = _service()
    assert 0 <= service.normalize(component, -10) <= 1
    assert 0 <= service.normalize(component, 10) <= 1


def test_facial_similarity_high_means_lower_risk() -> None:
    service = _service()
    assert service.normalize("facial", 0.9) < service.normalize(
        "facial", 0.2
    )


@pytest.mark.parametrize("component", ["pad", "behavioral"])
def test_increasing_component_score_means_higher_risk(
    component: str,
) -> None:
    service = _service()
    assert service.normalize(component, 0.9) > service.normalize(
        component, 0.2
    )


def test_empirical_cdf_interpolates_between_validation_quantiles() -> None:
    config = ScoreNormalizationConfig.model_validate(
        {
            "normalization_version": "v1",
            "components": {
                "pad": {
                    "method": "empirical_cdf",
                    "risk_direction": "increasing",
                    "lower_bound": 0.0,
                    "upper_bound": 1.0,
                    "threshold": 0.5,
                    "clipping": True,
                    "dataset_version": "pilot-v0.1.0",
                    "validation_statistics": {
                        "quantile_0.1": 0.1,
                        "quantile_0.5": 0.5,
                        "quantile_0.9": 0.9,
                    },
                }
            },
            "dataset_version": "pilot-v0.1.0",
            "generated_at": datetime.now(timezone.utc),
            "checksum": "0" * 64,
        }
    )

    service = ScoreNormalizationService(config)

    assert service.normalize("pad", 0.3) == pytest.approx(0.3)
