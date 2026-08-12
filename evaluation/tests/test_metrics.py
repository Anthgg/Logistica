import numpy as np

from evaluation.src.common.metrics import (
    binary_classification_metrics,
    bootstrap_mean_interval,
    latency_statistics,
    pad_error_rates,
    stratified_bootstrap_interval,
    wilson_interval,
)


def test_binary_metrics_are_exact_for_perfect_scores() -> None:
    labels = np.asarray([0, 0, 1, 1])
    scores = np.asarray([0.1, 0.2, 0.8, 0.9])
    metrics = binary_classification_metrics(labels, scores, 0.5)
    assert metrics["accuracy"] == 1.0
    assert metrics["far"] == 0.0
    assert metrics["frr"] == 0.0
    assert metrics["roc_auc"] == 1.0
    assert metrics["confusion_matrix"] == [[2, 0], [0, 2]]


def test_lower_direction_supports_behavioral_legitimate_class() -> None:
    metrics = binary_classification_metrics(
        [1, 1, 0, 0],
        [0.1, 0.2, 0.8, 0.9],
        0.5,
        positive_direction="lower",
    )
    assert metrics["accuracy"] == 1.0
    assert metrics["roc_auc"] == 1.0


def test_pad_rates_use_iso_error_definitions() -> None:
    metrics = binary_classification_metrics(
        [0, 0, 1, 1],
        [0.1, 0.8, 0.2, 0.9],
        0.5,
    )
    rates = pad_error_rates(metrics)
    assert rates == {"apcer": 0.5, "bpcer": 0.5, "acer": 0.5}


def test_bootstrap_is_reproducible() -> None:
    statistic = lambda labels, scores: float(np.mean((scores >= 0.5) == labels))
    first = stratified_bootstrap_interval(
        [0, 0, 1, 1],
        [0.1, 0.2, 0.8, 0.9],
        statistic,
        confidence_level=0.95,
        iterations=200,
        seed=42,
    )
    second = stratified_bootstrap_interval(
        [0, 0, 1, 1],
        [0.1, 0.2, 0.8, 0.9],
        statistic,
        confidence_level=0.95,
        iterations=200,
        seed=42,
    )
    assert first == second


def test_wilson_and_latency_summaries_are_finite() -> None:
    interval = wilson_interval(8, 10, confidence_level=0.95)
    assert interval.lower < interval.estimate < interval.upper
    latency = latency_statistics([1, 2, 3, 4, 5])
    assert latency["median"] == 3.0
    assert latency["p95"] > latency["p90"]
    first = bootstrap_mean_interval(
        [1, 2, 3, 4, 5],
        confidence_level=0.95,
        iterations=200,
        seed=42,
    )
    second = bootstrap_mean_interval(
        [1, 2, 3, 4, 5],
        confidence_level=0.95,
        iterations=200,
        seed=42,
    )
    assert first == second
