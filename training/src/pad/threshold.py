from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from src.common.config import PadTrainingConfig
from src.common.metrics import select_minimum_acer, threshold_candidates
from src.common.serialization import configuration_checksum


def calibrate_pad_threshold(
    labels: np.ndarray,
    attack_probabilities: np.ndarray,
    config: PadTrainingConfig,
    config_payload: dict[str, object],
) -> dict[str, object]:
    minimum, apcer, bpcer, acer = select_minimum_acer(labels, attack_probabilities)
    selected = minimum
    if config.threshold_objective == "target_apcer":
        candidates = threshold_candidates(labels, attack_probabilities)
        eligible = [candidate for candidate in candidates if candidate.frr <= config.target_apcer]
        if not eligible:
            raise ValueError("No existe umbral que cumpla el APCER objetivo.")
        selected = min(eligible, key=lambda item: (item.far, -item.f1))
        apcer = selected.frr
        bpcer = selected.far
        acer = (apcer + bpcer) / 2.0
    return {
        "model_type": "presentation_attack_detection",
        "model_name": config.backbone,
        "model_version": config.model_version,
        "dataset_version": config.dataset_version,
        "selected_threshold": selected.threshold,
        "selection_method": config.threshold_objective,
        "validation_apcer": apcer,
        "validation_bpcer": bpcer,
        "validation_acer": acer,
        "validation_f1": selected.f1,
        "target_apcer": config.target_apcer,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_checksum": configuration_checksum(config_payload),
        "test_rows_used": 0,
    }
