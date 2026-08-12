from pathlib import Path

import pandas as pd

from src.common.config import PreparationConfig
from src.common.paths import relative_to_root
from src.common.timestamps import deterministic_source_timestamp
from src.pilot.protocol import annotation_from_record

IDENTITY_COLUMNS = [
    "dataset_version",
    "protocol_version",
    "generated_at",
    "source_session_id",
    "participant_id",
    "session_id",
    "capture_id",
    "file_path",
    "checksum",
    "captured_at",
    "scenario",
    "identity_label",
    "sample_role",
    "quality_status",
    "rejection_reasons",
    "brightness_mean",
    "laplacian_variance",
    "face_count",
    "face_area_ratio",
    "split",
]


def build_facial_identity_manifest(
    captures: pd.DataFrame,
    quality: pd.DataFrame,
    config: PreparationConfig,
    capture_root: Path,
) -> pd.DataFrame:
    if captures.empty:
        return pd.DataFrame(columns=IDENTITY_COLUMNS)
    merged = captures.merge(
        quality,
        on=["capture_id", "session_id"],
        how="left",
        validate="one_to_one",
    )
    generated_at = deterministic_source_timestamp(captures, "captured_at")
    rows: list[dict[str, object]] = []
    for row in merged.to_dict(orient="records"):
        annotation = annotation_from_record(config.protocol, row)
        file_path = relative_to_root(
            capture_root / str(row["storage_path"]), config.pipeline.paths.root
        )
        rows.append(
            {
                "dataset_version": config.pipeline.dataset_version,
                "protocol_version": config.protocol.protocol_version,
                "generated_at": generated_at,
                "source_session_id": str(row["session_id"]),
                "participant_id": str(row["participant_id"]),
                "session_id": str(row["session_id"]),
                "capture_id": str(row["capture_id"]),
                "file_path": file_path,
                "checksum": str(row["checksum"]),
                "captured_at": row["captured_at"],
                "scenario": str(row["scenario"]),
                "identity_label": annotation.identity_label,
                "sample_role": annotation.sample_role,
                "quality_status": str(row.get("quality_status", "rejected")),
                "rejection_reasons": row.get("rejection_reasons", []),
                "brightness_mean": row.get("brightness_mean"),
                "laplacian_variance": row.get("laplacian_variance"),
                "face_count": int(row.get("face_count") or 0),
                "face_area_ratio": float(row.get("face_area_ratio") or 0),
                "split": None,
            }
        )
    return pd.DataFrame(rows, columns=IDENTITY_COLUMNS)
