from pathlib import Path

import pandas as pd
import pytest

from evaluation.src.ablation.evaluator import evaluate_ablation
from evaluation.src.common.privacy import (
    PrivacyViolationError,
    assert_report_privacy,
    public_prediction_columns,
)
from evaluation.src.comparison.evaluator import compare_pretest_posttest
from evaluation.src.performance.evaluator import evaluate_performance
from evaluation.src.statistics.analysis import run_statistical_analysis


def test_public_predictions_remove_paths_and_identity(
    synthetic_predictions,
) -> None:
    synthetic_predictions["email"] = "person@example.org"
    synthetic_predictions["image_path"] = "private.jpg"
    public = public_prediction_columns(
        synthetic_predictions,
        participant_column="participant_id",
    )
    assert "email" not in public
    assert "image_path" not in public
    assert public["participant_id"].str.startswith("P-").all()


def test_privacy_scanner_rejects_email(tmp_path: Path) -> None:
    (tmp_path / "report.md").write_text(
        "contacto: person@example.org", encoding="utf-8"
    )
    with pytest.raises(PrivacyViolationError, match="email"):
        assert_report_privacy(tmp_path)


def test_statistics_generate_paired_outputs(
    synthetic_config,
    synthetic_predictions,
) -> None:
    evaluate_performance(synthetic_predictions, synthetic_config)
    ablation_results, _ = evaluate_ablation(
        synthetic_predictions, synthetic_config
    )
    comparison, _ = compare_pretest_posttest(
        synthetic_predictions, synthetic_config
    )
    latency = pd.read_parquet(
        synthetic_config.paths.output_directory
        / "performance/latency_measurements.parquet"
    )
    tests, intervals, effects = run_statistical_analysis(
        synthetic_predictions,
        comparison,
        ablation_results,
        latency,
        synthetic_config,
    )
    assert "mcnemar_exact" in set(tests["test"])
    assert not intervals.empty
    assert not effects.empty
    output = synthetic_config.paths.output_directory / "statistics"
    assert (output / "statistical_tests.csv").is_file()
    assert (output / "confidence_intervals.csv").is_file()
    assert (output / "effect_sizes.csv").is_file()
