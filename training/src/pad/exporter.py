from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.common.hashing import sha256_file
from src.common.serialization import configuration_checksum, write_json_atomic


def export_pad_model(
    model: Any,
    *,
    export_path: Path,
    metadata_path: Path,
    threshold_path: Path,
    metrics_path: Path,
    model_version: str,
    dataset_version: str,
    config_payload: dict[str, object],
    best_epoch: int,
) -> dict[str, object]:
    export_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(export_path)
    for path in (export_path, threshold_path, metrics_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    metadata = {
        "model_type": "presentation_attack_detection",
        "model_name": "MobileNetV2",
        "model_version": model_version,
        "dataset_version": dataset_version,
        "status": "candidate",
        "best_epoch": best_epoch,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model_checksum": sha256_file(export_path),
        "threshold_checksum": sha256_file(threshold_path),
        "metrics_checksum": sha256_file(metrics_path),
        "config_checksum": configuration_checksum(config_payload),
        "test_rows_used": 0,
    }
    write_json_atomic(metadata_path, metadata)
    return metadata
