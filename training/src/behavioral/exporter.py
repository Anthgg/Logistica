from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sklearn.preprocessing import StandardScaler

from src.common.hashing import sha256_file
from src.common.serialization import configuration_checksum, write_json_atomic
from src.behavioral.scaler import save_scaler


def export_participant_artifacts(
    *,
    model: Any,
    scaler: StandardScaler,
    output_dir: Path,
    threshold_payload: dict[str, object],
    metrics: dict[str, object],
    feature_schema: dict[str, object],
    metadata: dict[str, object],
    config_payload: dict[str, object],
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "autoencoder.keras"
    scaler_path = output_dir / "scaler.joblib"
    threshold_path = output_dir / "threshold.json"
    schema_path = output_dir / "feature_schema.json"
    metrics_path = output_dir / "validation_metrics.json"
    metadata_path = output_dir / "metadata.json"
    if not model_path.is_file():
        model.save(model_path)
    scaler_checksum = save_scaler(scaler, scaler_path)
    write_json_atomic(threshold_path, threshold_payload)
    write_json_atomic(schema_path, feature_schema)
    write_json_atomic(metrics_path, metrics)
    payload = {
        **metadata,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "candidate",
        "model_checksum": sha256_file(model_path),
        "scaler_checksum": scaler_checksum,
        "threshold_checksum": sha256_file(threshold_path),
        "feature_schema_checksum": sha256_file(schema_path),
        "config_checksum": configuration_checksum(config_payload),
        "test_rows_used": 0,
    }
    write_json_atomic(metadata_path, payload)
    return payload
