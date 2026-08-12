from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from src.common.config import ArcFaceTrainingConfig
from src.common.metrics import select_eer, select_target_far, threshold_candidates
from src.common.serialization import configuration_checksum


def calibrate_facial_threshold(
    pairs: pd.DataFrame,
    config: ArcFaceTrainingConfig,
    config_payload: dict[str, object],
) -> dict[str, object]:
    if pairs.empty or set(pairs["label"].astype(int)) != {0, 1}:
        raise ValueError("Se requieren pares genuinos e impostores de validation.")
    candidates = threshold_candidates(
        pairs["label"].astype(int).to_numpy(),
        pairs["similarity"].astype(float).to_numpy(),
        positive_direction="higher",
    )
    eer = select_eer(candidates)
    target = select_target_far(candidates, config.target_far)
    selected = target if config.threshold_objective == "target_far" else eer
    if selected is None:
        raise ValueError("No existe un umbral que cumpla el FAR objetivo.")
    from src.common.metrics import binary_metrics

    metrics = binary_metrics(
        pairs["label"].astype(int).to_numpy(),
        pairs["similarity"].astype(float).to_numpy(),
        selected.threshold,
    )
    return {
        "model_type": "arcface_verification",
        "model_name": config.model_name,
        "model_version": config.model_version,
        "dataset_version": config.dataset_version,
        "similarity_metric": config.similarity_metric,
        "selected_threshold": selected.threshold,
        "selection_method": config.threshold_objective,
        "validation_far": selected.far,
        "validation_frr": selected.frr,
        "validation_eer": eer.eer,
        "validation_auc": metrics["roc_auc"],
        "validation_precision": selected.precision,
        "validation_recall": selected.recall,
        "validation_f1": selected.f1,
        "eer_threshold": eer.threshold,
        "target_far": config.target_far,
        "target_far_threshold": target.threshold if target else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_checksum": configuration_checksum(config_payload),
        "test_rows_used": 0,
    }
