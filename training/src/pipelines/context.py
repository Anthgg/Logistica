from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.common.config import TrainingConfigBundle
from src.common.paths import PROJECT_ROOT, resolve_from_training


@dataclass(frozen=True)
class PipelinePaths:
    models_root: Path
    reports_root: Path
    registry_path: Path
    experiments_path: Path


@dataclass
class PipelineResult:
    model_family: str
    model_name: str
    model_version: str
    status: str
    metrics: dict[str, Any] = field(default_factory=dict)
    artifacts: list[Path] = field(default_factory=list)
    participant_id: str | None = None
    notes: str | None = None


def training_paths(
    bundle: TrainingConfigBundle, output_dir: Path | None = None
) -> PipelinePaths:
    models_root = (
        output_dir.resolve()
        if output_dir
        else resolve_from_training(bundle.experiment.models_root)
    )
    reports_root = resolve_from_training(bundle.experiment.reports_root)
    return PipelinePaths(
        models_root=models_root,
        reports_root=reports_root,
        registry_path=(
            models_root / "registry" / "model_registry.json"
            if output_dir
            else resolve_from_training(bundle.experiment.registry_path)
        ),
        experiments_path=(
            models_root / "registry" / "experiments.parquet"
            if output_dir
            else resolve_from_training(bundle.experiment.experiments_path)
        ),
    )


def ensure_new_artifact(path: Path, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(
            f"El artefacto {path} ya existe; use --force para reemplazarlo."
        )


def relative_artifact(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()
