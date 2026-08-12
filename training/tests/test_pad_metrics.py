import numpy as np

from src.common.metrics import select_minimum_acer
from src.pad.threshold import calibrate_pad_threshold


def test_calculates_apcer_bpcer_acer(training_config) -> None:
    labels = np.array([0, 0, 1, 1])
    probabilities = np.array([0.1, 0.2, 0.8, 0.9])
    candidate, apcer, bpcer, acer = select_minimum_acer(labels, probabilities)
    assert apcer == 0.0
    assert bpcer == 0.0
    assert acer == 0.0
    payload = calibrate_pad_threshold(
        labels,
        probabilities,
        training_config.pad,
        training_config.pad.model_dump(mode="json"),
    )
    assert payload["validation_acer"] == 0.0
    assert payload["test_rows_used"] == 0
