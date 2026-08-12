from pathlib import Path

import numpy as np

from evaluation.src.ablation.evaluator import evaluate_ablation
from evaluation.src.behavioral.evaluator import evaluate_behavioral
from evaluation.src.common.decisions import confirmed_predictions
from evaluation.src.facial.evaluator import evaluate_facial
from evaluation.src.fusion.evaluator import evaluate_fusion
from evaluation.src.pad.evaluator import evaluate_pad


def test_hysteresis_requires_consecutive_positive_decisions() -> None:
    import pandas as pd

    frame = pd.DataFrame(
        {
            "session_id": ["s1"] * 5,
            "captured_at": pd.date_range(
                "2026-01-01", periods=5, freq="s", tz="UTC"
            ),
        }
    )
    result = confirmed_predictions(
        frame,
        np.asarray([1, 0, 1, 1, 1]),
        session_column="session_id",
        timestamp_column="captured_at",
        confirmation_count=2,
    )
    assert result.tolist() == [0, 0, 0, 1, 1]


def test_component_evaluators_write_expected_artifacts(
    synthetic_config,
    synthetic_predictions,
) -> None:
    facial = evaluate_facial(synthetic_predictions, synthetic_config)
    pad = evaluate_pad(synthetic_predictions, synthetic_config)
    behavioral = evaluate_behavioral(
        synthetic_predictions, synthetic_config
    )
    fusion = evaluate_fusion(synthetic_predictions, synthetic_config)
    assert facial["accuracy"] == 1.0
    assert pad["acer"] == 0.0
    assert behavioral["participant_count"] == 3
    assert fusion["weights_recalibrated"] is False
    output = synthetic_config.paths.output_directory
    assert (output / "facial/facial_test_metrics.json").is_file()
    assert (output / "pad/pad_test_metrics.json").is_file()
    assert (
        output / "behavioral/behavioral_test_summary.json"
    ).is_file()
    assert (output / "fusion/fusion_test_metrics.json").is_file()


def test_ablation_uses_approved_weights_and_same_population(
    synthetic_config,
    synthetic_predictions,
) -> None:
    results, summary = evaluate_ablation(
        synthetic_predictions, synthetic_config
    )
    expected = len(synthetic_predictions)
    assert set(summary["sample_count"]) == {expected}
    assert set(summary["weights_recalibrated"]) == {False}
    assert len(results) == expected * len(
        synthetic_config.ablation_configurations
    )
    assert (
        synthetic_config.paths.output_directory
        / "ablation/ablation_results.parquet"
    ).is_file()
