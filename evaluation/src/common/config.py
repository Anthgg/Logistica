from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, cast

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class EvaluationConfigurationError(ValueError):
    """Raised when the controlled evaluation configuration is invalid."""


@dataclass(frozen=True)
class EvaluationPaths:
    frozen_test_manifest: Path
    frozen_test_checksum: Path
    frozen_test_metadata: Path
    integration_approval: Path
    model_registry: Path
    fusion_config: Path
    normalization_config: Path
    test_data_root: Path
    output_directory: Path
    development_manifests: tuple[Path, ...]


@dataclass(frozen=True)
class ApprovedVersions:
    facial: str
    pad: str
    behavioral: str
    fusion: str
    normalization: str


@dataclass(frozen=True)
class LatencyConfig:
    warmup_iterations: int
    measurement_iterations: int
    concurrency_levels: tuple[int, ...]


@dataclass(frozen=True)
class InputSchema:
    row_id: str
    split: str
    participant_id: str
    session_id: str
    timestamp: str
    image_path: str
    sample_checksum: str
    facial_label: str
    pad_label: str
    behavioral_label: str
    fusion_label: str
    scenario: str
    attack_type: str
    source_device: str
    illumination: str
    condition: str
    pretest_detected: str
    pretest_latency_ms: str
    pretest_false_alert: str


@dataclass(frozen=True)
class FinalEvaluationConfig:
    source_path: Path
    schema_version: str
    dataset_version: str
    protocol_version: str
    paths: EvaluationPaths
    approved_versions: ApprovedVersions
    random_seed: int
    confidence_level: float
    bootstrap_iterations: int
    latency: LatencyConfig
    input_schema: InputSchema
    ablation_configurations: tuple[str, ...]
    statistical_tests: tuple[str, ...]


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise EvaluationConfigurationError(f"{field} debe ser un objeto.")
    return cast(Mapping[str, object], value)


def _string(mapping: Mapping[str, object], field: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        raise EvaluationConfigurationError(f"{field} debe ser texto no vacío.")
    return value.strip()


def _integer(mapping: Mapping[str, object], field: str, minimum: int = 1) -> int:
    value = mapping.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise EvaluationConfigurationError(
            f"{field} debe ser entero mayor o igual a {minimum}."
        )
    return value


def _float(mapping: Mapping[str, object], field: str) -> float:
    value = mapping.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvaluationConfigurationError(f"{field} debe ser numérico.")
    return float(value)


def _string_tuple(mapping: Mapping[str, object], field: str) -> tuple[str, ...]:
    value = mapping.get(field)
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise EvaluationConfigurationError(f"{field} debe ser una lista de textos.")
    return tuple(cast(list[str], value))


def _int_tuple(mapping: Mapping[str, object], field: str) -> tuple[int, ...]:
    value = mapping.get(field)
    if not isinstance(value, list) or not value:
        raise EvaluationConfigurationError(f"{field} debe ser una lista no vacía.")
    if any(isinstance(item, bool) or not isinstance(item, int) or item < 1 for item in value):
        raise EvaluationConfigurationError(f"{field} solo admite enteros positivos.")
    return tuple(cast(list[int], value))


def _project_path(value: str, field: str) -> Path:
    candidate = Path(value)
    resolved = (candidate if candidate.is_absolute() else PROJECT_ROOT / candidate).resolve()
    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise EvaluationConfigurationError(
            f"{field} debe permanecer dentro del proyecto."
        ) from exc
    return resolved


def _path(paths: Mapping[str, object], field: str) -> Path:
    return _project_path(_string(paths, field), f"paths.{field}")


def load_config(
    path: Path,
    *,
    output_override: Path | None = None,
) -> FinalEvaluationConfig:
    source = path.resolve()
    try:
        source.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise EvaluationConfigurationError(
            "El archivo de configuración debe pertenecer al proyecto."
        ) from exc
    if not source.is_file():
        raise EvaluationConfigurationError(f"No existe la configuración: {source.name}.")
    try:
        payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise EvaluationConfigurationError(
            "No fue posible leer la configuración final."
        ) from exc
    root = _mapping(payload, "config")
    paths = _mapping(root.get("paths"), "paths")
    versions = _mapping(root.get("approved_versions"), "approved_versions")
    latency = _mapping(root.get("latency"), "latency")
    schema = _mapping(root.get("input_schema"), "input_schema")
    development_value = paths.get("development_manifests")
    if not isinstance(development_value, list) or not all(
        isinstance(item, str) and item.strip() for item in development_value
    ):
        raise EvaluationConfigurationError(
            "paths.development_manifests debe ser una lista de rutas."
        )
    development = tuple(
        _project_path(item, "paths.development_manifests")
        for item in cast(list[str], development_value)
    )
    configured_output = (
        _project_path(str(output_override), "output_override")
        if output_override is not None
        else _path(paths, "output_directory")
    )
    confidence = _float(root, "confidence_level")
    if not 0.5 < confidence < 1:
        raise EvaluationConfigurationError(
            "confidence_level debe estar entre 0.5 y 1."
        )
    return FinalEvaluationConfig(
        source_path=source,
        schema_version=_string(root, "schema_version"),
        dataset_version=_string(root, "dataset_version"),
        protocol_version=_string(root, "protocol_version"),
        paths=EvaluationPaths(
            frozen_test_manifest=_path(paths, "frozen_test_manifest"),
            frozen_test_checksum=_path(paths, "frozen_test_checksum"),
            frozen_test_metadata=_path(paths, "frozen_test_metadata"),
            integration_approval=_path(paths, "integration_approval"),
            model_registry=_path(paths, "model_registry"),
            fusion_config=_path(paths, "fusion_config"),
            normalization_config=_path(paths, "normalization_config"),
            test_data_root=_path(paths, "test_data_root"),
            output_directory=configured_output,
            development_manifests=development,
        ),
        approved_versions=ApprovedVersions(
            facial=_string(versions, "facial"),
            pad=_string(versions, "pad"),
            behavioral=_string(versions, "behavioral"),
            fusion=_string(versions, "fusion"),
            normalization=_string(versions, "normalization"),
        ),
        random_seed=_integer(root, "random_seed", minimum=0),
        confidence_level=confidence,
        bootstrap_iterations=_integer(root, "bootstrap_iterations", minimum=100),
        latency=LatencyConfig(
            warmup_iterations=_integer(latency, "warmup_iterations", minimum=0),
            measurement_iterations=_integer(
                latency, "measurement_iterations", minimum=1
            ),
            concurrency_levels=_int_tuple(latency, "concurrency_levels"),
        ),
        input_schema=InputSchema(
            **{
                field: _string(schema, field)
                for field in InputSchema.__dataclass_fields__
            }
        ),
        ablation_configurations=_string_tuple(
            root, "ablation_configurations"
        ),
        statistical_tests=_string_tuple(root, "statistical_tests"),
    )
