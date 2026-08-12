from pathlib import Path
import sys

import numpy
import pandas
import pytest

SCRIPTS_PATH = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_PATH) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_PATH))

from _phase9_common import PROJECT_ROOT, ensure_validation_only, project_path
from calibrate_fusion import (
    _combined_risk,
    _estimated_latency,
    _metrics,
    _weight_grid,
)


def test_fusion_weight_search_is_reproducible() -> None:
    first = list(_weight_grid(0.25))
    second = list(_weight_grid(0.25))

    assert first == second
    assert all(sum(weights.values()) == pytest.approx(1) for weights in first)


def test_validation_metrics_include_real_eer_and_latency() -> None:
    labels = numpy.asarray([0, 0, 1, 1], dtype=int)
    risks = numpy.asarray([0.1, 0.2, 0.8, 0.9], dtype=float)
    frame = pandas.DataFrame(
        {
            "facial_risk": risks,
            "pad_risk": risks,
            "behavioral_risk": risks,
            "facial_latency_ms": [4.0, 5.0, 4.0, 5.0],
            "pad_latency_ms": [3.0, 3.0, 3.0, 3.0],
            "behavioral_latency_ms": [2.0, 2.0, 2.0, 2.0],
        }
    )
    combined = _combined_risk(
        frame,
        {"facial": 0.5, "pad": 0.3, "behavioral": 0.2},
        2,
    )
    valid = numpy.isfinite(combined)
    metrics, threshold = _metrics(labels, combined)

    assert metrics["eer"] == pytest.approx(0)
    assert 0 <= threshold <= 1
    assert _estimated_latency(frame, valid) == pytest.approx(4.5)


def test_calibration_rejects_test_rows_and_external_paths(
) -> None:
    with pytest.raises(SystemExit):
        ensure_validation_only(
            pandas.DataFrame({"split": ["validation", "test"]})
        )
    with pytest.raises(SystemExit):
        project_path(str(PROJECT_ROOT.parent / "outside.parquet"))
