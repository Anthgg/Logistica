from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from src.common.hashing import directory_fingerprint
from src.external_data.registry import DatasetEntry, RegistryError

PAD_LABELS = {"bona_fide", "attack"}
ATTACK_TYPES = {
    "none",
    "printed_photo",
    "cut_photo",
    "screen_photo",
    "replayed_video",
    "mask",
    "makeup",
    "partial_attack",
    "other",
}
PROJECT_SPLITS = {"train", "validation", "test"}


@dataclass(frozen=True)
class ValidationResult:
    dataset_id: str
    valid: bool
    file_count: int
    total_bytes: int
    issues: list[str]
    fingerprint: dict[str, str]


def validate_raw_directory(entry: DatasetEntry, project_root: str | Path) -> ValidationResult:
    root = Path(project_root).resolve()
    raw_path = (root / entry.storage_path).resolve()
    expected_parent = (root / "external-data" / "raw").resolve()
    try:
        raw_path.relative_to(expected_parent)
    except ValueError as exc:
        raise RegistryError("storage_path debe permanecer dentro de external-data/raw.") from exc

    issues: list[str] = []
    if not raw_path.is_dir():
        issues.append("raw_directory_missing")
        fingerprint: dict[str, str] = {}
    else:
        fingerprint = {
            relative: checksum
            for relative, checksum in directory_fingerprint(raw_path).items()
            if Path(relative).name not in {".gitkeep", "README.md"}
        }
        if not fingerprint:
            issues.append("raw_directory_empty")
    files = (
        [
            item
            for item in raw_path.rglob("*")
            if item.is_file() and item.name not in {".gitkeep", "README.md"}
        ]
        if raw_path.exists()
        else []
    )
    if entry.status == "downloaded" and not entry.checksum:
        issues.append("download_checksum_missing")
    return ValidationResult(
        dataset_id=entry.dataset_id,
        valid=not issues,
        file_count=len(files),
        total_bytes=sum(item.stat().st_size for item in files),
        issues=issues,
        fingerprint=fingerprint,
    )


def validation_payload(result: ValidationResult) -> dict[str, object]:
    return asdict(result)


def validate_pad_labels(frame: pd.DataFrame) -> None:
    if "presentation_label" not in frame or "attack_type" not in frame:
        raise ValueError("Faltan presentation_label o attack_type.")
    labels = set(frame["presentation_label"].dropna().astype(str))
    attacks = set(frame["attack_type"].dropna().astype(str))
    invalid_labels = labels - PAD_LABELS
    invalid_attacks = attacks - ATTACK_TYPES
    if invalid_labels:
        raise ValueError(f"Etiquetas PAD inválidas: {sorted(invalid_labels)}")
    if invalid_attacks:
        raise ValueError(f"Tipos de ataque inválidos: {sorted(invalid_attacks)}")
    inconsistent = frame[
        ((frame["presentation_label"] == "bona_fide") & (frame["attack_type"] != "none"))
        | ((frame["presentation_label"] == "attack") & (frame["attack_type"] == "none"))
    ]
    if not inconsistent.empty:
        raise ValueError("presentation_label y attack_type son inconsistentes.")


def assert_group_isolation(
    frame: pd.DataFrame,
    *,
    group_columns: tuple[str, ...] = ("source_video_id",),
    split_column: str = "split_project",
) -> None:
    if split_column not in frame:
        raise ValueError(f"Falta la columna {split_column}.")
    for column in group_columns:
        if column not in frame:
            continue
        counts = (
            frame.dropna(subset=[column, split_column])
            .groupby(column, dropna=False)[split_column]
            .nunique()
        )
        leaked = counts[counts > 1]
        if not leaked.empty:
            raise ValueError(
                f"Fuga entre particiones por {column}: "
                + ", ".join(str(value) for value in leaked.index[:20])
            )


def assert_subject_isolation_when_required(
    frame: pd.DataFrame, *, protocol_requires_subject_disjoint: bool
) -> None:
    if not protocol_requires_subject_disjoint:
        return
    assert_group_isolation(frame, group_columns=("source_subject_id",))


def duplicate_checksums(frame: pd.DataFrame) -> pd.DataFrame:
    if "checksum" not in frame:
        raise ValueError("Falta la columna checksum.")
    return frame[
        frame["checksum"].notna() & frame["checksum"].duplicated(keep=False)
    ].sort_values("checksum")
