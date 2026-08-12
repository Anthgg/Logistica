import numpy as np

from src.behavioral.feature_validator import build_feature_schema
from src.behavioral.threshold import calibrate_behavioral_threshold


def test_preserves_explicit_feature_order(training_config) -> None:
    schema = build_feature_schema(training_config.behavioral)
    names = [item["name"] for item in schema["features"]]
    assert names == training_config.behavioral.feature_columns
    assert schema["feature_count"] == len(names)
    assert len(schema["checksum"]) == 64


def test_calibrates_personal_threshold_without_test(training_config) -> None:
    payload = calibrate_behavioral_threshold(
        np.array([0.01, 0.02, 0.03]),
        np.array([0.5, 0.6, 0.7]),
        participant_id="P-0001",
        model_version="behavioral-ae-P-0001-v0.1.0",
        config=training_config.behavioral,
        config_payload=training_config.behavioral.model_dump(mode="json"),
    )
    assert payload["validation_far"] == 0.0
    assert payload["validation_frr"] <= 1 / 3
    assert payload["test_rows_used"] == 0
