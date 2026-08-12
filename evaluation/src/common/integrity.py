from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, cast
from uuid import uuid4

import pandas as pd

from evaluation.src.common.config import FinalEvaluationConfig, PROJECT_ROOT
from evaluation.src.common.io import (
    JsonValue,
    canonical_sha256,
    json_value,
    read_json,
    sha256_file,
    write_json_atomic,
)

APPROVED_STATUS = "approved_for_final_evaluation"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
SENSITIVE_COLUMNS = {
    "address",
    "code",
    "cookie",
    "content",
    "dni",
    "email",
    "key",
    "name",
    "password",
    "payload",
    "phone",
    "raw_payload",
    "text",
    "token",
    "transcript",
}


class EvaluationGateError(RuntimeError):
    """Raised when a scientific or execution gate blocks final evaluation."""


@dataclass(frozen=True)
class GateFinding:
    code: str
    message: str

    def as_json(self) -> dict[str, JsonValue]:
        return cast(dict[str, JsonValue], json_value(asdict(self)))


@dataclass(frozen=True)
class PreflightResult:
    approved: bool
    findings: tuple[GateFinding, ...]
    plan: tuple[str, ...]

    def as_json(self) -> dict[str, JsonValue]:
        return {
            "approved": self.approved,
            "findings": [finding.as_json() for finding in self.findings],
            "plan": list(self.plan),
            "test_manifest_opened": False,
            "markers_created": False,
            "results_created": False,
        }


@dataclass(frozen=True)
class ExecutionMarkers:
    run_id: str
    started_path: Path
    completed_path: Path
    authorized_rerun: bool
    rerun_reason: str | None


def _text(payload: Mapping[str, JsonValue], key: str) -> str:
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def _mapping(
    payload: Mapping[str, JsonValue], key: str
) -> Mapping[str, JsonValue]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.name


def _approval_findings(config: FinalEvaluationConfig) -> list[GateFinding]:
    path = config.paths.integration_approval
    if not path.is_file():
        return [
            GateFinding(
                "APPROVAL_MISSING",
                "No existe integration_approval.json.",
            )
        ]
    try:
        approval = read_json(path)
    except ValueError as exc:
        return [GateFinding("APPROVAL_INVALID", str(exc))]
    findings: list[GateFinding] = []
    if _text(approval, "status") != APPROVED_STATUS:
        findings.append(
            GateFinding(
                "APPROVAL_STATUS_INVALID",
                f"La aprobación no tiene estado {APPROVED_STATUS}.",
            )
        )
    for key, expected in (
        ("dataset_version", config.dataset_version),
        ("protocol_version", config.protocol_version),
    ):
        if _text(approval, key) != expected:
            findings.append(
                GateFinding(
                    "APPROVAL_VERSION_MISMATCH",
                    f"{key} no coincide con la configuración final.",
                )
            )
    model_versions = _mapping(approval, "model_versions")
    expected_versions = {
        "facial": config.approved_versions.facial,
        "pad": config.approved_versions.pad,
        "behavioral": config.approved_versions.behavioral,
    }
    for component, expected in expected_versions.items():
        if _text(model_versions, component) != expected:
            findings.append(
                GateFinding(
                    "MODEL_VERSION_NOT_APPROVED",
                    f"La versión {component} no coincide con la aprobación.",
                )
            )
    for key, expected in (
        ("fusion_version", config.approved_versions.fusion),
        ("normalization_version", config.approved_versions.normalization),
    ):
        if _text(approval, key) != expected:
            findings.append(
                GateFinding(
                    "CONFIG_VERSION_NOT_APPROVED",
                    f"{key} no coincide con la aprobación.",
                )
            )
    checksums = _mapping(approval, "checksums")
    required_paths = {
        config.source_path,
        config.paths.model_registry,
        config.paths.fusion_config,
        config.paths.normalization_config,
    }
    for required in sorted(required_paths):
        relative = _relative(required)
        expected = checksums.get(relative)
        if not isinstance(expected, str) or SHA256_PATTERN.fullmatch(expected) is None:
            findings.append(
                GateFinding(
                    "APPROVED_CHECKSUM_MISSING",
                    f"Falta SHA-256 aprobado para {relative}.",
                )
            )
    approved_at_text = _text(approval, "approved_at")
    if not approved_at_text:
        findings.append(
            GateFinding(
                "APPROVAL_DATE_MISSING",
                "La aprobación no declara approved_at.",
            )
        )
    if not _text(approval, "technical_owner"):
        findings.append(
            GateFinding(
                "APPROVAL_OWNER_MISSING",
                "La aprobación no declara responsable técnico.",
            )
        )
    if not _text(approval, "git_commit"):
        findings.append(
            GateFinding(
                "APPROVAL_COMMIT_MISSING",
                "La aprobación no declara el commit revisado.",
            )
        )
    if not _text(approval, "reason"):
        findings.append(
            GateFinding(
                "APPROVAL_REASON_MISSING",
                "La aprobación no declara su motivo.",
            )
        )
    hysteresis = _mapping(approval, "hysteresis")
    confirmation = hysteresis.get("positive_confirmation_count")
    if (
        isinstance(confirmation, bool)
        or not isinstance(confirmation, int)
        or confirmation < 1
    ):
        findings.append(
            GateFinding(
                "HYSTERESIS_NOT_APPROVED",
                "La aprobación no declara positive_confirmation_count.",
            )
        )
    approved_ablations = _mapping(approval, "ablation_configurations")
    for name in config.ablation_configurations:
        if name not in approved_ablations:
            findings.append(
                GateFinding(
                    "ABLATION_NOT_APPROVED",
                    f"La variante {name} no está en la aprobación.",
                )
            )
    return findings


def _artifact_findings(config: FinalEvaluationConfig) -> list[GateFinding]:
    required = (
        config.paths.model_registry,
        config.paths.fusion_config,
        config.paths.normalization_config,
    )
    findings: list[GateFinding] = []
    for path in required:
        if not path.is_file():
            findings.append(
                GateFinding(
                    "MODEL_ARTIFACT_MISSING",
                    f"No existe {_relative(path)}.",
                )
            )
    if findings or not config.paths.integration_approval.is_file():
        return findings
    try:
        approval = read_json(config.paths.integration_approval)
    except ValueError:
        return findings
    checksums = _mapping(approval, "checksums")
    approved_at: datetime | None = None
    approved_at_text = _text(approval, "approved_at")
    if approved_at_text:
        try:
            approved_at = datetime.fromisoformat(
                approved_at_text.replace("Z", "+00:00")
            )
            if approved_at.tzinfo is None:
                approved_at = approved_at.replace(tzinfo=timezone.utc)
        except ValueError:
            findings.append(
                GateFinding(
                    "APPROVAL_DATE_INVALID",
                    "approved_at no usa una fecha ISO-8601 válida.",
                )
            )
    for relative, expected_value in checksums.items():
        if not isinstance(expected_value, str) or SHA256_PATTERN.fullmatch(
            expected_value
        ) is None:
            findings.append(
                GateFinding(
                    "APPROVED_CHECKSUM_INVALID",
                    f"El checksum aprobado para {relative} no es SHA-256.",
                )
            )
            continue
        artifact = (PROJECT_ROOT / relative).resolve()
        try:
            artifact.relative_to(PROJECT_ROOT)
        except ValueError:
            findings.append(
                GateFinding(
                    "APPROVED_PATH_INVALID",
                    "La aprobación contiene una ruta fuera del proyecto.",
                )
            )
            continue
        if not artifact.is_file():
            findings.append(
                GateFinding(
                    "APPROVED_ARTIFACT_MISSING",
                    f"No existe el artefacto aprobado {relative}.",
                )
            )
            continue
        if artifact == config.paths.frozen_test_manifest:
            findings.append(
                GateFinding(
                    "TEST_HASH_IN_MODEL_APPROVAL",
                    "El test congelado debe verificarse en su compuerta separada.",
                )
            )
            continue
        if sha256_file(artifact) != expected_value:
            findings.append(
                GateFinding(
                    "APPROVED_ARTIFACT_CHANGED",
                    f"El artefacto aprobado {relative} cambió.",
                )
            )
        if approved_at is not None:
            modified_at = datetime.fromtimestamp(
                artifact.stat().st_mtime, tz=timezone.utc
            )
            if modified_at > approved_at:
                findings.append(
                    GateFinding(
                        "APPROVED_ARTIFACT_MODIFIED_LATE",
                        f"{relative} fue modificado después de la aprobación.",
                    )
                )
    return findings


def _frozen_sidecar_findings(config: FinalEvaluationConfig) -> list[GateFinding]:
    paths = (
        config.paths.frozen_test_manifest,
        config.paths.frozen_test_checksum,
        config.paths.frozen_test_metadata,
    )
    findings = [
        GateFinding(
            "FROZEN_TEST_ARTIFACT_MISSING",
            f"No existe {_relative(path)}.",
        )
        for path in paths
        if not path.is_file()
    ]
    if findings:
        return findings
    try:
        expected = (
            config.paths.frozen_test_checksum.read_text(encoding="utf-8")
            .strip()
            .split()[0]
        )
    except (OSError, IndexError):
        expected = ""
    if SHA256_PATTERN.fullmatch(expected) is None:
        findings.append(
            GateFinding(
                "FROZEN_TEST_CHECKSUM_INVALID",
                "El sidecar del manifiesto no contiene un SHA-256 válido.",
            )
        )
    try:
        metadata = read_json(config.paths.frozen_test_metadata)
    except ValueError as exc:
        findings.append(GateFinding("FROZEN_TEST_METADATA_INVALID", str(exc)))
        return findings
    for key, expected_value in (
        ("dataset_version", config.dataset_version),
        ("protocol_version", config.protocol_version),
    ):
        if _text(metadata, key) != expected_value:
            findings.append(
                GateFinding(
                    "FROZEN_TEST_VERSION_MISMATCH",
                    f"{key} del test congelado no coincide.",
                )
            )
    return findings


def preflight(config: FinalEvaluationConfig) -> PreflightResult:
    findings = (
        _approval_findings(config)
        + _artifact_findings(config)
        + _frozen_sidecar_findings(config)
    )
    plan = (
        "Verificar lock y autorización de ejecución.",
        "Crear evaluation_lock.json de forma atómica.",
        "Crear marcador test_evaluation_started.json.",
        "Abrir una sola vez el manifiesto test y verificar su SHA-256.",
        "Verificar muestras, fugas, sesiones y ventanas.",
        "Ejecutar inferencia facial, PAD, conductual y fusión sin recalibrar.",
        "Ejecutar ablaciones con la misma población.",
        "Comparar pretest/postest y medir rendimiento.",
        "Calcular intervalos, pruebas y tamaños de efecto.",
        "Generar informes, hashes y marcador de finalización.",
    )
    return PreflightResult(
        approved=not findings,
        findings=tuple(findings),
        plan=plan,
    )


def require_preflight(result: PreflightResult) -> None:
    if result.approved:
        return
    codes = ", ".join(finding.code for finding in result.findings)
    raise EvaluationGateError(f"Evaluación bloqueada por compuertas: {codes}.")


def _read_development_manifests(config: FinalEvaluationConfig) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in config.paths.development_manifests:
        if not path.is_file():
            raise EvaluationGateError(
                f"No existe el manifiesto de desarrollo {_relative(path)}."
            )
        frames.append(pd.read_parquet(path))
    return pd.concat(frames, ignore_index=True, sort=False)


def _assert_no_cross_split_duplicates(
    test_frame: pd.DataFrame,
    development_frame: pd.DataFrame,
) -> None:
    columns = (
        "capture_id",
        "checksum",
        "session_id",
        "batch_id",
        "event_id",
        "window_id",
        "segment_id",
        "pad_source_id",
    )
    overlaps: list[str] = []
    for column in columns:
        if column not in test_frame or column not in development_frame:
            continue
        test_values = set(test_frame[column].dropna().astype(str))
        development_values = set(development_frame[column].dropna().astype(str))
        count = len(test_values & development_values)
        if count:
            overlaps.append(f"{column}={count}")
    if overlaps:
        raise EvaluationGateError(
            "Se detectó fuga entre desarrollo y test: " + ", ".join(overlaps)
        )


def _assert_no_internal_duplicates(frame: pd.DataFrame) -> None:
    columns = (
        "capture_id",
        "checksum",
        "event_id",
        "window_id",
        "segment_id",
    )
    duplicated: list[str] = []
    for column in columns:
        if column not in frame:
            continue
        count = int(frame[column].dropna().astype(str).duplicated().sum())
        if count:
            duplicated.append(f"{column}={count}")
    if duplicated:
        raise EvaluationGateError(
            "El test congelado contiene identificadores duplicados: "
            + ", ".join(duplicated)
        )


def _assert_no_window_overlap(frame: pd.DataFrame) -> None:
    required = {"participant_id", "session_id", "window_start", "window_end"}
    if not required <= set(frame.columns):
        return
    working = frame.copy()
    working["_window_start"] = pd.to_datetime(
        working["window_start"],
        utc=True,
        errors="coerce",
    )
    working["_window_end"] = pd.to_datetime(
        working["window_end"],
        utc=True,
        errors="coerce",
    )
    if (
        working["_window_start"].isna().any()
        or working["_window_end"].isna().any()
    ):
        raise EvaluationGateError(
            "El test contiene ventanas con marcas temporales inválidas."
        )
    if (working["_window_end"] < working["_window_start"]).any():
        raise EvaluationGateError(
            "El test contiene ventanas cuyo final precede al inicio."
        )
    ordered = working.sort_values(
        ["participant_id", "session_id", "_window_start"]
    )
    for (_, _), group in ordered.groupby(
        ["participant_id", "session_id"], dropna=False
    ):
        starts = group["_window_start"].reset_index(drop=True)
        previous_end = group["_window_end"].shift(1).reset_index(drop=True)
        if (starts.iloc[1:] < previous_end.iloc[1:]).any():
            raise EvaluationGateError(
                "El test contiene ventanas conductuales superpuestas."
            )


def _assert_no_sensitive_columns(frame: pd.DataFrame) -> None:
    unsafe = {
        column
        for column in frame.columns
        if any(
            token in SENSITIVE_COLUMNS
            for token in re.split(r"[^a-z0-9]+", column.casefold())
            if token
        )
    }
    if unsafe:
        raise EvaluationGateError(
            "El manifiesto test contiene propiedades textuales o sensibles: "
            + ", ".join(sorted(unsafe))
        )


def _verify_sample_checksums(
    config: FinalEvaluationConfig,
    frame: pd.DataFrame,
) -> None:
    schema = config.input_schema
    if schema.image_path not in frame or schema.sample_checksum not in frame:
        raise EvaluationGateError(
            "El test no declara rutas y checksums de muestras."
        )
    path_available = frame[schema.image_path].notna()
    checksum_available = frame[schema.sample_checksum].notna()
    if not path_available.equals(checksum_available):
        raise EvaluationGateError(
            "Cada muestra test con ruta debe declarar su SHA-256 y viceversa."
        )
    for relative_value, expected_value in frame[
        [schema.image_path, schema.sample_checksum]
    ].dropna().itertuples(index=False, name=None):
        relative = Path(str(relative_value))
        sample = (config.paths.test_data_root / relative).resolve()
        try:
            sample.relative_to(config.paths.test_data_root.resolve())
        except ValueError as exc:
            raise EvaluationGateError(
                "Una muestra test intenta salir de test_data_root."
            ) from exc
        expected = str(expected_value)
        if SHA256_PATTERN.fullmatch(expected) is None:
            raise EvaluationGateError(
                "Una muestra test declara un checksum que no es SHA-256."
            )
        if not sample.is_file() or sha256_file(sample) != expected:
            raise EvaluationGateError(
                "Una muestra test falta o no coincide con su SHA-256."
            )


def verify_and_open_frozen_test(config: FinalEvaluationConfig) -> pd.DataFrame:
    expected = (
        config.paths.frozen_test_checksum.read_text(encoding="utf-8")
        .strip()
        .split()[0]
    )
    actual = sha256_file(config.paths.frozen_test_manifest)
    if expected != actual:
        raise EvaluationGateError(
            "El SHA-256 del manifiesto test congelado no coincide."
        )
    frame = pd.read_parquet(config.paths.frozen_test_manifest)
    split_column = config.input_schema.split
    if split_column not in frame:
        raise EvaluationGateError("El test congelado no declara split.")
    if set(frame[split_column].dropna().astype(str).str.casefold()) != {"test"}:
        raise EvaluationGateError(
            "El manifiesto congelado contiene particiones distintas de test."
        )
    _assert_no_sensitive_columns(frame)
    _assert_no_internal_duplicates(frame)
    _verify_sample_checksums(config, frame)
    development = _read_development_manifests(config)
    _assert_no_cross_split_duplicates(frame, development)
    _assert_no_window_overlap(frame)
    return frame


def _library_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


def _lock_payload(
    config: FinalEvaluationConfig,
    *,
    device: str,
) -> dict[str, JsonValue]:
    approval = read_json(config.paths.integration_approval)
    checksums = _mapping(approval, "checksums")
    payload: dict[str, JsonValue] = {
        "schema_version": "1.0",
        "dataset_version": config.dataset_version,
        "protocol_version": config.protocol_version,
        "model_versions": json_value(asdict(config.approved_versions)),
        "configuration_sha256": sha256_file(config.source_path),
        "approval_sha256": sha256_file(config.paths.integration_approval),
        "approved_artifact_checksums": dict(checksums),
        "random_seed": config.random_seed,
        "device": device,
        "git_commit": _git_commit(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": _library_version("numpy"),
            "tensorflow": _library_version("tensorflow-cpu")
            or _library_version("tensorflow"),
            "insightface": _library_version("insightface"),
            "onnxruntime": _library_version("onnxruntime"),
            "scikit_learn": _library_version("scikit-learn"),
        },
    }
    payload["locked_state_checksum"] = canonical_sha256(payload)
    return payload


def create_or_verify_lock(
    config: FinalEvaluationConfig,
    *,
    device: str,
) -> Path:
    lock_path = config.paths.output_directory / "evaluation_lock.json"
    expected = _lock_payload(config, device=device)
    if lock_path.is_file():
        existing = read_json(lock_path)
        comparable = {
            key: value
            for key, value in existing.items()
            if key != "locked_at"
        }
        if comparable != expected:
            raise EvaluationGateError(
                "evaluation_lock.json existe y no coincide con el estado aprobado."
            )
        return lock_path
    created = dict(expected)
    created["locked_at"] = datetime.now(timezone.utc).isoformat()
    write_json_atomic(lock_path, created)
    return lock_path


def begin_execution(
    config: FinalEvaluationConfig,
    *,
    authorized_rerun: bool,
    rerun_reason: str | None,
    command: Iterable[str],
) -> ExecutionMarkers:
    output = config.paths.output_directory
    started = output / "test_evaluation_started.json"
    completed = output / "test_evaluation_completed.json"
    if completed.is_file() and not started.is_file():
        raise EvaluationGateError(
            "Existe un marcador de finalización sin marcador de inicio."
        )
    if started.is_file() and not authorized_rerun:
        raise EvaluationGateError(
            "Ya existe un marcador de inicio; una repetición requiere "
            "--authorized-rerun y --rerun-reason."
        )
    if authorized_rerun and not started.is_file():
        raise EvaluationGateError(
            "--authorized-rerun requiere una ejecución previa registrada."
        )
    normalized_reason = rerun_reason.strip() if rerun_reason else None
    if authorized_rerun and (normalized_reason is None or len(normalized_reason) < 10):
        raise EvaluationGateError(
            "Una repetición autorizada requiere un motivo de al menos 10 caracteres."
        )
    if not authorized_rerun and normalized_reason:
        raise EvaluationGateError(
            "--rerun-reason solo puede usarse con --authorized-rerun."
        )
    run_id = str(uuid4())
    payload: dict[str, JsonValue] = {
        "run_id": run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "authorized_rerun": authorized_rerun,
        "rerun_reason": normalized_reason,
        "command": [Path(part).name if os.sep in part else part for part in command],
    }
    if started.is_file():
        archive = output / f"test_evaluation_started.previous-{run_id}.json"
        write_json_atomic(archive, read_json(started))
    if completed.is_file():
        completed_archive = (
            output / f"test_evaluation_completed.previous-{run_id}.json"
        )
        completed.replace(completed_archive)
    write_json_atomic(started, payload)
    return ExecutionMarkers(
        run_id=run_id,
        started_path=started,
        completed_path=completed,
        authorized_rerun=authorized_rerun,
        rerun_reason=normalized_reason,
    )


def complete_execution(
    markers: ExecutionMarkers,
    *,
    duration_seconds: float,
    artifact_checksums: Mapping[str, str],
) -> None:
    write_json_atomic(
        markers.completed_path,
        {
            "run_id": markers.run_id,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": duration_seconds,
            "authorized_rerun": markers.authorized_rerun,
            "rerun_reason": markers.rerun_reason,
            "artifact_checksums": dict(artifact_checksums),
        },
    )


def record_failure(
    config: FinalEvaluationConfig,
    markers: ExecutionMarkers | None,
    error: BaseException,
) -> None:
    if markers is None:
        return
    write_json_atomic(
        config.paths.output_directory / "evaluation_failure.json",
        {
            "run_id": markers.run_id,
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "error_type": error.__class__.__name__,
            "message": str(error),
        },
    )
