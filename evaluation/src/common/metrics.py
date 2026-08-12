from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

import matplotlib
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from statsmodels.stats.proportion import proportion_confint

matplotlib.use("Agg")
from matplotlib import pyplot as plt

PositiveDirection = Literal["higher", "lower"]


@dataclass(frozen=True)
class ConfidenceInterval:
    estimate: float
    lower: float
    upper: float
    confidence_level: float
    method: str
    iterations: int | None
    seed: int | None

    def as_dict(self) -> dict[str, float | int | str | None]:
        return {
            "estimate": self.estimate,
            "lower": self.lower,
            "upper": self.upper,
            "confidence_level": self.confidence_level,
            "method": self.method,
            "iterations": self.iterations,
            "seed": self.seed,
        }


def _arrays(
    labels: np.ndarray | list[int],
    scores: np.ndarray | list[float],
) -> tuple[np.ndarray, np.ndarray]:
    y_true = np.asarray(labels, dtype=np.int8).reshape(-1)
    y_score = np.asarray(scores, dtype=np.float64).reshape(-1)
    if y_true.size == 0 or y_true.size != y_score.size:
        raise ValueError("Las etiquetas y puntajes deben tener igual longitud no vacía.")
    if not set(np.unique(y_true)).issubset({0, 1}):
        raise ValueError("Las etiquetas binarias solo admiten 0 y 1.")
    if not np.isfinite(y_score).all():
        raise ValueError("Los puntajes contienen valores no finitos.")
    return y_true, y_score


def predictions_at_threshold(
    scores: np.ndarray,
    threshold: float,
    positive_direction: PositiveDirection,
) -> np.ndarray:
    if not math.isfinite(threshold):
        raise ValueError("El umbral debe ser finito.")
    if positive_direction == "higher":
        return (scores >= threshold).astype(np.int8)
    return (scores <= threshold).astype(np.int8)


def safe_rate(numerator: int, denominator: int) -> float | None:
    return float(numerator / denominator) if denominator else None


def _equal_error_rate(
    labels: np.ndarray,
    scores: np.ndarray,
    positive_direction: PositiveDirection,
) -> float | None:
    if len(np.unique(labels)) != 2:
        return None
    oriented = scores if positive_direction == "higher" else -scores
    false_positive, true_positive, _ = roc_curve(labels, oriented)
    false_reject = 1.0 - true_positive
    index = int(np.argmin(np.abs(false_positive - false_reject)))
    return float((false_positive[index] + false_reject[index]) / 2.0)


def _tar_at_far(
    labels: np.ndarray,
    scores: np.ndarray,
    positive_direction: PositiveDirection,
) -> dict[str, float | None]:
    targets = (0.001, 0.01, 0.05)
    if len(np.unique(labels)) != 2:
        return {f"{target:.3f}": None for target in targets}
    oriented = scores if positive_direction == "higher" else -scores
    false_positive, true_positive, _ = roc_curve(labels, oriented)
    values: dict[str, float | None] = {}
    for target in targets:
        eligible = true_positive[false_positive <= target]
        values[f"{target:.3f}"] = (
            float(np.max(eligible)) if eligible.size else None
        )
    return values


def binary_classification_metrics(
    labels: np.ndarray | list[int],
    scores: np.ndarray | list[float],
    threshold: float,
    *,
    positive_direction: PositiveDirection = "higher",
) -> dict[str, object]:
    y_true, y_score = _arrays(labels, scores)
    predicted = predictions_at_threshold(
        y_score, threshold, positive_direction
    )
    tn, fp, fn, tp = confusion_matrix(
        y_true, predicted, labels=[0, 1]
    ).ravel()
    far = safe_rate(int(fp), int(fp + tn))
    frr = safe_rate(int(fn), int(fn + tp))
    result: dict[str, object] = {
        "sample_count": int(y_true.size),
        "positive_count": int(np.sum(y_true == 1)),
        "negative_count": int(np.sum(y_true == 0)),
        "threshold": float(threshold),
        "positive_direction": positive_direction,
        "accuracy": float(accuracy_score(y_true, predicted)),
        "precision": float(
            precision_score(y_true, predicted, zero_division=0)
        ),
        "recall": float(recall_score(y_true, predicted, zero_division=0)),
        "f1": float(f1_score(y_true, predicted, zero_division=0)),
        "far": far,
        "frr": frr,
        "eer": _equal_error_rate(y_true, y_score, positive_direction),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
        "tar_at_far": _tar_at_far(
            y_true, y_score, positive_direction
        ),
    }
    if len(np.unique(y_true)) == 2:
        oriented = y_score if positive_direction == "higher" else -y_score
        result["roc_auc"] = float(roc_auc_score(y_true, oriented))
        result["pr_auc"] = float(
            average_precision_score(y_true, oriented)
        )
        false_positive, true_positive, thresholds = roc_curve(
            y_true, oriented
        )
        precision, recall, pr_thresholds = precision_recall_curve(
            y_true, oriented
        )
        result["roc_curve"] = {
            "false_positive_rate": false_positive.tolist(),
            "true_positive_rate": true_positive.tolist(),
            "thresholds": thresholds.tolist(),
        }
        result["precision_recall_curve"] = {
            "precision": precision.tolist(),
            "recall": recall.tolist(),
            "thresholds": pr_thresholds.tolist(),
        }
    else:
        result["roc_auc"] = None
        result["pr_auc"] = None
        result["roc_curve"] = None
        result["precision_recall_curve"] = None
    return result


def pad_error_rates(metrics: dict[str, object]) -> dict[str, float | None]:
    matrix = metrics.get("confusion_matrix")
    if not isinstance(matrix, list) or len(matrix) != 2:
        raise ValueError("La matriz PAD no es válida.")
    row_zero = matrix[0]
    row_one = matrix[1]
    if (
        not isinstance(row_zero, list)
        or not isinstance(row_one, list)
        or len(row_zero) != 2
        or len(row_one) != 2
    ):
        raise ValueError("La matriz PAD no es 2x2.")
    tn, fp = int(row_zero[0]), int(row_zero[1])
    fn, tp = int(row_one[0]), int(row_one[1])
    apcer = safe_rate(fn, fn + tp)
    bpcer = safe_rate(fp, fp + tn)
    acer = (
        float((apcer + bpcer) / 2.0)
        if apcer is not None and bpcer is not None
        else None
    )
    return {"apcer": apcer, "bpcer": bpcer, "acer": acer}


def grouped_binary_metrics(
    frame_columns: dict[str, np.ndarray],
    labels: np.ndarray,
    scores: np.ndarray,
    threshold: float,
    *,
    positive_direction: PositiveDirection = "higher",
) -> dict[str, dict[str, dict[str, object]]]:
    grouped: dict[str, dict[str, dict[str, object]]] = {}
    for column, values in frame_columns.items():
        if len(values) != len(labels):
            raise ValueError(f"Longitud incompatible para grupo {column}.")
        column_metrics: dict[str, dict[str, object]] = {}
        for value in sorted({str(item) for item in values if str(item)}):
            mask = np.asarray([str(item) == value for item in values])
            column_metrics[value] = binary_classification_metrics(
                labels[mask],
                scores[mask],
                threshold,
                positive_direction=positive_direction,
            )
        grouped[column] = column_metrics
    return grouped


def stratified_bootstrap_interval(
    labels: np.ndarray | list[int],
    scores: np.ndarray | list[float],
    statistic: Callable[[np.ndarray, np.ndarray], float],
    *,
    confidence_level: float,
    iterations: int,
    seed: int,
) -> ConfidenceInterval:
    y_true, y_score = _arrays(labels, scores)
    if iterations < 100:
        raise ValueError("Bootstrap requiere al menos 100 iteraciones.")
    rng = np.random.default_rng(seed)
    groups = [np.flatnonzero(y_true == value) for value in np.unique(y_true)]
    estimates = np.empty(iterations, dtype=float)
    for index in range(iterations):
        sampled_indices = np.concatenate(
            [rng.choice(group, size=len(group), replace=True) for group in groups]
        )
        estimates[index] = statistic(
            y_true[sampled_indices], y_score[sampled_indices]
        )
    estimates = estimates[np.isfinite(estimates)]
    if not len(estimates):
        raise ValueError("Bootstrap no produjo estimaciones finitas.")
    alpha = 1.0 - confidence_level
    estimate = statistic(y_true, y_score)
    return ConfidenceInterval(
        estimate=float(estimate),
        lower=float(np.quantile(estimates, alpha / 2.0)),
        upper=float(np.quantile(estimates, 1.0 - alpha / 2.0)),
        confidence_level=confidence_level,
        method="stratified_percentile_bootstrap",
        iterations=iterations,
        seed=seed,
    )


def wilson_interval(
    successes: int,
    total: int,
    *,
    confidence_level: float,
) -> ConfidenceInterval:
    if total <= 0 or not 0 <= successes <= total:
        raise ValueError("La proporción Wilson requiere conteos válidos.")
    lower, upper = proportion_confint(
        successes,
        total,
        alpha=1.0 - confidence_level,
        method="wilson",
    )
    return ConfidenceInterval(
        estimate=float(successes / total),
        lower=float(lower),
        upper=float(upper),
        confidence_level=confidence_level,
        method="wilson",
        iterations=None,
        seed=None,
    )


def bootstrap_mean_interval(
    values: np.ndarray | list[float],
    *,
    confidence_level: float,
    iterations: int,
    seed: int,
) -> ConfidenceInterval:
    array = np.asarray(values, dtype=float).reshape(-1)
    array = array[np.isfinite(array)]
    if not len(array):
        raise ValueError("Bootstrap de media requiere observaciones finitas.")
    if iterations < 100:
        raise ValueError("Bootstrap requiere al menos 100 iteraciones.")
    generator = np.random.default_rng(seed)
    estimates = np.empty(iterations, dtype=float)
    for index in range(iterations):
        sample = generator.choice(array, size=len(array), replace=True)
        estimates[index] = float(np.mean(sample))
    alpha = 1.0 - confidence_level
    return ConfidenceInterval(
        estimate=float(np.mean(array)),
        lower=float(np.quantile(estimates, alpha / 2.0)),
        upper=float(np.quantile(estimates, 1.0 - alpha / 2.0)),
        confidence_level=confidence_level,
        method="percentile_bootstrap_mean",
        iterations=iterations,
        seed=seed,
    )


def latency_statistics(
    values: np.ndarray | list[float],
) -> dict[str, float | int]:
    array = np.asarray(values, dtype=float).reshape(-1)
    array = array[np.isfinite(array)]
    if not len(array):
        raise ValueError("No hay latencias finitas para resumir.")
    return {
        "count": int(len(array)),
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "std": float(np.std(array, ddof=1)) if len(array) > 1 else 0.0,
        "p90": float(np.quantile(array, 0.90)),
        "p95": float(np.quantile(array, 0.95)),
        "p99": float(np.quantile(array, 0.99)),
        "minimum": float(np.min(array)),
        "maximum": float(np.max(array)),
    }


def save_bar_plot(
    labels: list[str],
    values: list[float],
    path: Path,
    *,
    title: str,
    y_label: str,
    x_label: str | None = None,
    rotate_labels: bool = False,
) -> None:
    if not labels or len(labels) != len(values):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    figure = plt.figure()
    plt.bar(labels, values)
    if rotate_labels:
        plt.xticks(rotation=35, ha="right")
    if x_label:
        plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    figure.savefig(path, bbox_inches="tight")
    plt.close(figure)


def save_histogram(
    values: np.ndarray | list[float],
    path: Path,
    *,
    title: str,
    x_label: str,
) -> None:
    array = np.asarray(values, dtype=float).reshape(-1)
    array = array[np.isfinite(array)]
    if not len(array):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    figure = plt.figure()
    plt.hist(array, bins=min(30, max(5, len(array))))
    plt.xlabel(x_label)
    plt.ylabel("Frecuencia")
    plt.title(title)
    figure.savefig(path, bbox_inches="tight")
    plt.close(figure)


def save_roc_plot(
    metrics: dict[str, object],
    path: Path,
    *,
    title: str,
) -> None:
    roc = metrics.get("roc_curve")
    if not isinstance(roc, dict):
        return
    false_positive = roc.get("false_positive_rate")
    true_positive = roc.get("true_positive_rate")
    if not isinstance(false_positive, list) or not isinstance(
        true_positive, list
    ):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    figure = plt.figure()
    plt.plot(false_positive, true_positive)
    plt.plot([0, 1], [0, 1], linestyle="--")
    plt.xlabel("Tasa de falsos positivos")
    plt.ylabel("Tasa de verdaderos positivos")
    plt.title(title)
    figure.savefig(path, bbox_inches="tight")
    plt.close(figure)


def save_precision_recall_plot(
    metrics: dict[str, object],
    path: Path,
    *,
    title: str,
) -> None:
    curve = metrics.get("precision_recall_curve")
    if not isinstance(curve, dict):
        return
    precision = curve.get("precision")
    recall = curve.get("recall")
    if not isinstance(precision, list) or not isinstance(recall, list):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    figure = plt.figure()
    plt.plot(recall, precision)
    plt.xlabel("Recall")
    plt.ylabel("Precisión")
    plt.title(title)
    figure.savefig(path, bbox_inches="tight")
    plt.close(figure)


def save_confusion_matrix(
    metrics: dict[str, object],
    path: Path,
    *,
    title: str,
    negative_label: str,
    positive_label: str,
) -> None:
    matrix = metrics.get("confusion_matrix")
    if not isinstance(matrix, list):
        return
    values = np.asarray(matrix, dtype=int)
    if values.shape != (2, 2):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    figure = plt.figure()
    plt.imshow(values, interpolation="nearest")
    plt.title(title)
    plt.xticks([0, 1], [negative_label, positive_label], rotation=20)
    plt.yticks([0, 1], [negative_label, positive_label])
    plt.xlabel("Predicción")
    plt.ylabel("Etiqueta real")
    for row in range(2):
        for column in range(2):
            plt.text(column, row, str(values[row, column]), ha="center", va="center")
    figure.colorbar(plt.gci())
    figure.savefig(path, bbox_inches="tight")
    plt.close(figure)
