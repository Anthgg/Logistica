from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


PositiveDirection = Literal["higher", "lower"]


@dataclass(frozen=True)
class ThresholdCandidate:
    threshold: float
    far: float
    frr: float
    eer: float
    accuracy: float
    precision: float
    recall: float
    f1: float


def _binary_predictions(
    scores: np.ndarray, threshold: float, positive_direction: PositiveDirection
) -> np.ndarray:
    return (scores >= threshold).astype(int) if positive_direction == "higher" else (
        scores <= threshold
    ).astype(int)


def threshold_candidates(
    labels: np.ndarray | list[int],
    scores: np.ndarray | list[float],
    *,
    positive_direction: PositiveDirection = "higher",
) -> list[ThresholdCandidate]:
    y_true = np.asarray(labels, dtype=int)
    y_score = np.asarray(scores, dtype=float)
    if y_true.size == 0 or y_true.size != y_score.size:
        raise ValueError("labels y scores deben tener la misma longitud no vacía.")
    if set(np.unique(y_true)) != {0, 1}:
        raise ValueError("La calibración requiere ejemplos de ambas clases.")
    unique = np.unique(y_score)
    epsilon = np.finfo(float).eps
    thresholds = np.concatenate(
        ([unique.min() - epsilon], unique, [unique.max() + epsilon])
    )
    candidates: list[ThresholdCandidate] = []
    negatives = y_true == 0
    positives = y_true == 1
    for threshold in thresholds:
        predicted = _binary_predictions(y_score, float(threshold), positive_direction)
        far = float(np.mean(predicted[negatives] == 1))
        frr = float(np.mean(predicted[positives] == 0))
        candidates.append(
            ThresholdCandidate(
                threshold=float(threshold),
                far=far,
                frr=frr,
                eer=(far + frr) / 2.0,
                accuracy=float(accuracy_score(y_true, predicted)),
                precision=float(precision_score(y_true, predicted, zero_division=0)),
                recall=float(recall_score(y_true, predicted, zero_division=0)),
                f1=float(f1_score(y_true, predicted, zero_division=0)),
            )
        )
    return candidates


def select_eer(candidates: list[ThresholdCandidate]) -> ThresholdCandidate:
    if not candidates:
        raise ValueError("No existen candidatos de umbral.")
    return min(candidates, key=lambda item: (abs(item.far - item.frr), item.eer))


def select_target_far(
    candidates: list[ThresholdCandidate], target_far: float
) -> ThresholdCandidate | None:
    eligible = [candidate for candidate in candidates if candidate.far <= target_far]
    return max(eligible, key=lambda item: (item.recall, item.f1)) if eligible else None


def select_minimum_acer(
    labels: np.ndarray | list[int], attack_probabilities: np.ndarray | list[float]
) -> tuple[ThresholdCandidate, float, float, float]:
    candidates = threshold_candidates(labels, attack_probabilities, positive_direction="higher")
    best = min(candidates, key=lambda item: ((item.far + item.frr) / 2.0, -item.f1))
    apcer = best.frr
    bpcer = best.far
    return best, apcer, bpcer, (apcer + bpcer) / 2.0


def binary_metrics(
    labels: np.ndarray | list[int],
    scores: np.ndarray | list[float],
    threshold: float,
    *,
    positive_direction: PositiveDirection = "higher",
) -> dict[str, object]:
    y_true = np.asarray(labels, dtype=int)
    y_score = np.asarray(scores, dtype=float)
    predicted = _binary_predictions(y_score, threshold, positive_direction)
    matrix = confusion_matrix(y_true, predicted, labels=[0, 1])
    metrics: dict[str, object] = {
        "accuracy": float(accuracy_score(y_true, predicted)),
        "precision": float(precision_score(y_true, predicted, zero_division=0)),
        "recall": float(recall_score(y_true, predicted, zero_division=0)),
        "f1": float(f1_score(y_true, predicted, zero_division=0)),
        "confusion_matrix": matrix.tolist(),
    }
    if len(np.unique(y_true)) == 2:
        oriented = y_score if positive_direction == "higher" else -y_score
        metrics["roc_auc"] = float(roc_auc_score(y_true, oriented))
        metrics["pr_auc"] = float(average_precision_score(y_true, oriented))
        false_positive, true_positive, roc_thresholds = roc_curve(y_true, oriented)
        metrics["roc"] = {
            "false_positive_rate": false_positive.tolist(),
            "true_positive_rate": true_positive.tolist(),
            "thresholds": roc_thresholds.tolist(),
        }
    else:
        metrics["roc_auc"] = None
        metrics["pr_auc"] = None
        metrics["roc"] = None
    return metrics
