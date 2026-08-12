from pathlib import Path

import pandas as pd

from src.common.config import PreparationConfig
from src.common.paths import relative_to_root
from src.common.timestamps import deterministic_source_timestamp
from src.pilot.protocol import annotation_from_record

PAD_COLUMNS = [
    "dataset_version",
    "protocol_version",
    "generated_at",
    "source_session_id",
    "participant_id",
    "session_id",
    "capture_id",
    "file_path",
    "checksum",
    "presentation_label",
    "attack_type",
    "source_device",
    "pad_source_id",
    "quality_status",
    "rejection_reasons",
    "split",
]


def build_pad_manifest(
    captures: pd.DataFrame,
    quality: pd.DataFrame,
    config: PreparationConfig,
    capture_root: Path,
) -> pd.DataFrame:
    if captures.empty:
        return pd.DataFrame(columns=PAD_COLUMNS)
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
        if annotation.presentation_label is None:
            continue
        if annotation.attack_type is None:
            raise ValueError(
                f"La sesión PAD {row['session_id']} requiere attack_type controlado."
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
                "file_path": relative_to_root(
                    capture_root / str(row["storage_path"]),
                    config.pipeline.paths.root,
                ),
                "checksum": str(row["checksum"]),
                "presentation_label": annotation.presentation_label,
                "attack_type": annotation.attack_type,
                "source_device": annotation.source_device,
                "pad_source_id": annotation.pad_source_id,
                "quality_status": str(row.get("quality_status", "rejected")),
                "rejection_reasons": row.get("rejection_reasons", []),
                "split": None,
            }
        )
    return pd.DataFrame(rows, columns=PAD_COLUMNS)
