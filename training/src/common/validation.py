from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

import pandas as pd

from src.common.config import PreparationConfig, TrainingConfigBundle
from src.common.hashing import sha256_file
from src.common.paths import resolve_from_training

FACIAL_IDENTITY_COLUMNS = {
    "dataset_version",
    "protocol_version",
    "participant_id",
    "session_id",
    "capture_id",
    "file_path",
    "checksum",
    "identity_label",
    "sample_role",
    "quality_status",
    "split",
}
PAD_COLUMNS = {
    "dataset_version",
    "protocol_version",
    "participant_id",
    "session_id",
    "capture_id",
    "file_path",
    "checksum",
    "presentation_label",
    "attack_type",
    "quality_status",
    "split",
}
BEHAVIORAL_COLUMNS = {
    "dataset_version",
    "protocol_version",
    "participant_id",
    "session_id",
    "window_id",
    "checksum",
    "quality_status",
    "split",
}
FORBIDDEN_TEXT_COLUMNS = {
    "key",
    "key_value",
    "code",
    "text",
    "typed_text",
    "input_value",
    "password",
    "email",
    "clipboard",
    "payload",
    "events",
}


class TrainingInputError(ValueError):
    pass


@dataclass
class ValidationReport:
    dataset_version: str
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    datasets: dict[str, dict[str, object]] = field(default_factory=dict)
    frozen_test: dict[str, object] = field(default_factory=dict)

    def fail(self, message: str) -> None:
        self.valid = False
        self.errors.append(message)

    def as_dict(self) -> dict[str, object]:
        return asdict(self)

    def raise_if_invalid(self) -> None:
        if not self.valid:
            raise TrainingInputError("\n".join(self.errors))


def require_columns(frame: pd.DataFrame, required: Iterable[str], name: str) -> None:
    missing = set(required) - set(frame.columns)
    if missing:
        raise TrainingInputError(
            f"{name}: faltan columnas obligatorias: {', '.join(sorted(missing))}."
        )


def development_rows(
    frame: pd.DataFrame,
    *,
    dataset_version: str,
    allowed_quality_statuses: Iterable[str] = ("accepted",),
) -> pd.DataFrame:
    if "split" not in frame:
        raise TrainingInputError("El manifiesto no contiene la columna split.")
    unknown = set(frame["split"].dropna().astype(str)) - {"train", "validation", "test"}
    if unknown:
        raise TrainingInputError(f"Existen particiones desconocidas: {sorted(unknown)}.")
    selected = frame.loc[frame["split"].isin(["train", "validation"])].copy()
    if "dataset_version" in selected and not selected.empty:
        versions = set(selected["dataset_version"].astype(str))
        if versions != {dataset_version}:
            raise TrainingInputError(
                f"dataset_version inesperado: {sorted(versions)}; se esperaba {dataset_version}."
            )
    if "quality_status" in selected:
        selected = selected.loc[
            selected["quality_status"].isin(set(allowed_quality_statuses))
        ].copy()
    if (selected["split"] == "test").any():
        raise TrainingInputError("Se detectó uso accidental del conjunto test.")
    return selected.reset_index(drop=True)


def _validate_frozen_test(bundle: TrainingConfigBundle, report: ValidationReport) -> None:
    manifest = resolve_from_training(bundle.experiment.frozen_test_manifest)
    checksum_path = resolve_from_training(bundle.experiment.frozen_test_checksum)
    metadata_path = resolve_from_training(bundle.experiment.frozen_test_metadata)
    missing = [path for path in (manifest, checksum_path, metadata_path) if not path.is_file()]
    if missing:
        report.fail(
            "Faltan artefactos del test congelado: "
            + ", ".join(path.name for path in missing)
            + "."
        )
        return
    expected = checksum_path.read_text(encoding="utf-8").strip().split()[0]
    actual = sha256_file(manifest)
    if expected != actual:
        report.fail("El checksum del manifiesto test congelado no coincide.")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        report.fail(f"No se pudo leer frozen_test_metadata.json: {exc}.")
        return
    if str(metadata.get("dataset_version")) != bundle.experiment.dataset_version:
        report.fail("La versión del test congelado no coincide con la configuración.")
    if str(metadata.get("protocol_version")) != bundle.experiment.protocol_version:
        report.fail("La versión de protocolo del test congelado no coincide.")
    report.frozen_test = {
        "manifest": manifest.name,
        "sha256": actual,
        "integrity_verified": expected == actual,
        "rows_loaded_for_training": 0,
    }


def _check_cross_split(frame: pd.DataFrame, column: str, name: str) -> list[str]:
    if frame.empty or column not in frame:
        return []
    grouped = frame.dropna(subset=[column]).groupby(column)["split"].nunique()
    return [str(value) for value in grouped[grouped > 1].index.tolist()]


def _validate_frame(
    frame: pd.DataFrame,
    *,
    name: str,
    required: set[str],
    bundle: TrainingConfigBundle,
    preparation: PreparationConfig,
    report: ValidationReport,
    facial: bool,
) -> pd.DataFrame:
    try:
        require_columns(frame, required, name)
    except TrainingInputError as exc:
        report.fail(str(exc))
        return pd.DataFrame()
    version_values = set(frame["dataset_version"].dropna().astype(str))
    if version_values and version_values != {bundle.experiment.dataset_version}:
        report.fail(f"{name}: dataset_version no coincide: {sorted(version_values)}.")
    labels = set(frame["split"].dropna().astype(str))
    unknown = labels - {"train", "validation", "test"}
    if unknown:
        report.fail(f"{name}: particiones desconocidas: {sorted(unknown)}.")
    for column in ("checksum", "session_id"):
        duplicates = _check_cross_split(frame, column, name)
        if duplicates:
            report.fail(
                f"{name}: {column} aparece en varias particiones "
                f"({len(duplicates)} casos)."
            )
    try:
        selected = development_rows(
            frame,
            dataset_version=bundle.experiment.dataset_version,
            allowed_quality_statuses=bundle.experiment.allowed_quality_statuses,
        )
    except TrainingInputError as exc:
        report.fail(f"{name}: {exc}")
        return pd.DataFrame()
    counts = selected["split"].value_counts().to_dict() if not selected.empty else {}
    report.datasets[name] = {
        "total_manifest_rows": int(len(frame)),
        "development_accepted_rows": int(len(selected)),
        "split_counts": {str(key): int(value) for key, value in counts.items()},
        "test_rows_used": 0,
    }
    if selected.empty:
        report.fail(f"{name}: no existen filas aceptadas de train/validation.")
        return selected
    if set(selected["split"]) != {"train", "validation"}:
        report.fail(f"{name}: deben existir filas aceptadas tanto train como validation.")
    if name == "facial_identity":
        unknown_identity = set(selected["identity_label"].astype(str)) - {
            "genuine",
            "impostor",
        }
        unknown_roles = set(selected["sample_role"].astype(str)) - {
            "enrollment",
            "verification",
            "change_operator",
        }
        if unknown_identity:
            report.fail(f"{name}: identity_label inválido: {sorted(unknown_identity)}.")
        if unknown_roles:
            report.fail(f"{name}: sample_role inválido: {sorted(unknown_roles)}.")
    elif name == "facial_pad":
        unknown_labels = set(selected["presentation_label"].astype(str)) - {
            "bona_fide",
            "attack",
        }
        unknown_attacks = set(selected["attack_type"].astype(str)) - {
            "none",
            "printed_photo",
            "screen_photo",
            "replayed_video",
        }
        if unknown_labels:
            report.fail(
                f"{name}: presentation_label inválido: {sorted(unknown_labels)}."
            )
        if unknown_attacks:
            report.fail(f"{name}: attack_type inválido: {sorted(unknown_attacks)}.")
        if "pad_source_id" in selected:
            duplicates = _check_cross_split(selected, "pad_source_id", name)
            if duplicates:
                report.fail(
                    f"{name}: pad_source_id aparece en varias particiones "
                    f"({len(duplicates)} casos)."
                )
    if facial:
        for row in selected.to_dict(orient="records"):
            relative = Path(str(row["file_path"]))
            if relative.is_absolute() or ".." in relative.parts:
                report.fail(f"{name}: ruta facial insegura para {row.get('capture_id')}.")
                continue
            image_path = preparation.pipeline.paths.root / relative
            if not image_path.is_file():
                report.fail(f"{name}: falta el archivo {relative.as_posix()}.")
            elif sha256_file(image_path) != str(row["checksum"]):
                report.fail(f"{name}: checksum incorrecto en {relative.as_posix()}.")
    return selected


def _validate_behavioral_features(
    frame: pd.DataFrame,
    bundle: TrainingConfigBundle,
    report: ValidationReport,
) -> None:
    forbidden = FORBIDDEN_TEXT_COLUMNS & {str(column).casefold() for column in frame.columns}
    if forbidden:
        report.fail(
            "behavioral_features: contiene columnas textuales prohibidas: "
            + ", ".join(sorted(forbidden))
            + "."
        )
    missing = set(bundle.behavioral.feature_columns) - set(frame.columns)
    if missing:
        report.fail(
            "behavioral_features: faltan características configuradas: "
            + ", ".join(sorted(missing))
            + "."
        )
        return
    if frame.empty:
        report.fail("behavioral_features: no existen ventanas para entrenamiento.")
        return
    numeric = frame[bundle.behavioral.feature_columns].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        report.fail("behavioral_features: existen NaN o valores no numéricos.")
    if numeric.map(lambda value: math.isinf(float(value)) if pd.notna(value) else False).any().any():
        report.fail("behavioral_features: existen valores infinitos.")
    if {"window_started_at", "window_ended_at", "session_id", "split"} <= set(frame.columns):
        working = frame.copy()
        working["window_started_at"] = pd.to_datetime(
            working["window_started_at"], utc=True, errors="coerce"
        )
        working["window_ended_at"] = pd.to_datetime(
            working["window_ended_at"], utc=True, errors="coerce"
        )
        for _, group in working.groupby("session_id"):
            train = group[group["split"] == "train"]
            validation = group[group["split"] == "validation"]
            for left in train.itertuples():
                overlap = validation[
                    (validation["window_started_at"] < left.window_ended_at)
                    & (validation["window_ended_at"] > left.window_started_at)
                ]
                if not overlap.empty:
                    report.fail(
                        "behavioral_features: existen ventanas superpuestas entre "
                        "train y validation."
                    )
                    return


def validate_training_inputs(
    preparation: PreparationConfig,
    bundle: TrainingConfigBundle,
    *,
    models: set[str] | None = None,
) -> ValidationReport:
    report = ValidationReport(dataset_version=bundle.experiment.dataset_version)
    if preparation.pipeline.dataset_version != bundle.experiment.dataset_version:
        report.fail("data_pipeline.yaml y experiment.yaml usan versiones distintas.")
    _validate_frozen_test(bundle, report)
    selected_models = models or {"facial", "pad", "behavioral"}
    definitions = (
        (
            "facial",
            "facial_identity",
            preparation.pipeline.paths.root
            / preparation.pipeline.facial_identity_manifest,
            FACIAL_IDENTITY_COLUMNS,
            True,
        ),
        (
            "pad",
            "facial_pad",
            preparation.pipeline.paths.root / preparation.pipeline.facial_pad_manifest,
            PAD_COLUMNS,
            True,
        ),
        (
            "behavioral",
            "behavioral",
            preparation.pipeline.paths.root / preparation.pipeline.behavioral_manifest,
            BEHAVIORAL_COLUMNS,
            False,
        ),
    )
    for family, name, path, columns, facial in definitions:
        if family not in selected_models:
            continue
        if not path.is_file():
            report.fail(f"Falta el manifiesto {path.name}.")
            continue
        try:
            frame = pd.read_parquet(path)
        except Exception as exc:
            report.fail(f"No se pudo leer {path.name}: {exc}.")
            continue
        _validate_frame(
            frame,
            name=name,
            required=columns,
            bundle=bundle,
            preparation=preparation,
            report=report,
            facial=facial,
        )
    behavioral_path = (
        preparation.pipeline.paths.root
        / "processed"
        / "behavioral"
        / "behavioral_features.parquet"
    )
    if "behavioral" not in selected_models:
        return report
    if not behavioral_path.is_file():
        report.fail("Falta behavioral_features.parquet.")
    else:
        try:
            behavioral = pd.read_parquet(behavioral_path)
        except Exception as exc:
            report.fail(f"No se pudo leer behavioral_features.parquet: {exc}.")
        else:
            _validate_behavioral_features(behavioral, bundle, report)
    return report
