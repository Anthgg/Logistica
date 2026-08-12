from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from src.common.config import BehavioralTrainingConfig
from src.common.metrics import (
    binary_metrics,
    select_eer,
    select_target_far,
    threshold_candidates,
)
from src.common.serialization import configuration_checksum


def calibrate_behavioral_threshold(
    genuine_errors: np.ndarray,
    impostor_errors: np.ndarray,
    *,
    participant_id: str,
    model_version: str,
    config: BehavioralTrainingConfig,
    config_payload: dict[str, object],
) -> dict[str, object]:
    genuine = np.asarray(genuine_errors, dtype=float)
    impostor = np.asarray(impostor_errors, dtype=float)
    if not len(genuine) or not len(impostor):
        raise ValueError("Se requieren errores genuinos e impostores.")
    labels = np.concatenate([np.ones(len(genuine), dtype=int), np.zeros(len(impostor), dtype=int)])
    scores = np.concatenate([genuine, impostor])
    candidates = threshold_candidates(labels, scores, positive_direction="lower")
    eer = select_eer(candidates)
    target = select_target_far(candidates, config.target_far)
    percentile_threshold = float(np.percentile(genuine, config.threshold_percentile))
    percentile_candidate = min(
        candidates, key=lambda item: abs(item.threshold - percentile_threshold)
    )
    maximum_f1 = max(candidates, key=lambda item: (item.f1, item.recall))
    if config.threshold_method == "eer":
        selected = eer
    elif config.threshold_method == "target_far":
        if target is None:
            raise ValueError("No existe umbral conductual para el FAR objetivo.")
        selected = target
    elif config.threshold_method == "maximum_f1":
        selected = maximum_f1
    else:
        selected = percentile_candidate
    metrics = binary_metrics(
        labels, scores, selected.threshold, positive_direction="lower"
    )
    return {
        "participant_id": participant_id,
        "model_version": model_version,
        "dataset_version": config.dataset_version,
        "threshold": selected.threshold,
        "method": config.threshold_method,
        "validation_far": selected.far,
        "validation_frr": selected.frr,
        "validation_eer": eer.eer,
        "validation_auc": metrics["roc_auc"],
        "validation_f1": selected.f1,
        "legitimate_window_count": int(len(genuine)),
        "impostor_window_count": int(len(impostor)),
        "proposals": {
            "percentile": percentile_candidate.threshold,
            "eer": eer.threshold,
            "target_far": target.threshold if target else None,
            "maximum_f1": maximum_f1.threshold,
            "mean_plus_3std": float(np.mean(genuine) + 3 * np.std(genuine)),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_checksum": configuration_checksum(config_payload),
        "test_rows_used": 0,
    }
