from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.datasets.manifest_builder import write_manifest
from src.external_data.validation import (
    PROJECT_SPLITS,
    assert_group_isolation,
    duplicate_checksums,
    validate_pad_labels,
)

PAD_MANIFEST_COLUMNS = [
    "dataset_version",
    "source_dataset",
    "source_subject_id",
    "source_session_id",
    "source_video_id",
    "source_capture_id",
    "file_path",
    "checksum",
    "presentation_label",
    "attack_type",
    "capture_device",
    "presentation_device",
    "illumination",
    "environment",
    "split_original",
    "split_project",
    "quality_status",
    "rejection_reasons",
    "license_status",
]
PAD_NULLABLE_COLUMNS = {
    "source_subject_id",
    "source_session_id",
    "source_capture_id",
    "capture_device",
    "presentation_device",
    "illumination",
    "environment",
    "split_original",
    "split_project",
}
SPLIT_MAP = {
    "train": "train",
    "training": "train",
    "devel": "validation",
    "dev": "validation",
    "validation": "validation",
    "val": "validation",
    "test": "test",
}


def _normalize_split(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    return SPLIT_MAP.get(str(value).strip().casefold())


def build_external_pad_manifest(records: pd.DataFrame) -> pd.DataFrame:
    frame = records.copy()
    for column in PAD_MANIFEST_COLUMNS:
        if column not in frame:
            frame[column] = None
    frame["split_project"] = frame.apply(
        lambda row: (
            row["split_project"]
            if pd.notna(row["split_project"])
            else _normalize_split(row["split_original"])
        ),
        axis=1,
    )
    missing_core = frame[
        frame[["source_dataset", "source_video_id", "file_path", "checksum"]]
        .isna()
        .any(axis=1)
    ]
    if not missing_core.empty:
        raise ValueError("El manifiesto PAD contiene filas sin trazabilidad mínima.")
    for index, row in frame.iterrows():
        reasons = row["rejection_reasons"]
        reasons = list(reasons) if isinstance(reasons, (list, tuple)) else []
        if pd.isna(row["presentation_label"]):
            reasons.append("missing_presentation_label")
            frame.at[index, "quality_status"] = "rejected"
        if pd.isna(row["attack_type"]):
            reasons.append("missing_attack_type")
            frame.at[index, "quality_status"] = "rejected"
        frame.at[index, "rejection_reasons"] = sorted(set(reasons))
        if pd.isna(frame.at[index, "quality_status"]):
            frame.at[index, "quality_status"] = "accepted"
    labelled = frame.dropna(subset=["presentation_label", "attack_type"])
    validate_pad_labels(labelled)
    invalid_splits = set(frame["split_project"].dropna().astype(str)) - PROJECT_SPLITS
    if invalid_splits:
        raise ValueError(f"Splits de proyecto inválidos: {sorted(invalid_splits)}")
    assert_group_isolation(frame)
    duplicates = duplicate_checksums(frame)
    if not duplicates.empty:
        duplicate_indices = duplicates.index
        frame.loc[duplicate_indices, "quality_status"] = "rejected"
        for index in duplicate_indices:
            reasons = list(frame.at[index, "rejection_reasons"] or [])
            frame.at[index, "rejection_reasons"] = sorted(
                set([*reasons, "duplicate_checksum"])
            )
    if any(
        Path(str(value)).is_absolute() for value in frame["file_path"].dropna()
    ):
        raise ValueError("file_path debe ser relativo.")
    return frame.reindex(columns=PAD_MANIFEST_COLUMNS)


def write_external_pad_manifest(
    records: pd.DataFrame, output_path: str | Path, *, csv_copy: bool = False
) -> Path:
    return write_manifest(
        build_external_pad_manifest(records),
        output_path,
        csv_copy=csv_copy,
    )


def build_behavioral_manifest(
    frame: pd.DataFrame,
    *,
    source_dataset: str,
    modality: str,
    dataset_version: str,
    license_status: str,
) -> pd.DataFrame:
    required = {"subject_id", "session_id"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Faltan columnas conductuales: {sorted(missing)}")
    output = frame.copy()
    output.insert(0, "dataset_version", dataset_version)
    output.insert(1, "source_dataset", source_dataset)
    output.insert(2, "modality", modality)
    output["license_status"] = license_status
    return output
