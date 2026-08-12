from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from src.common.config import PreparationConfig, TrainingConfigBundle
from src.common.device import DeviceSelection
from src.common.hashing import sha256_file
from src.common.paths import PROJECT_ROOT
from src.experiments.experiment_registry import (
    ExperimentRegistry,
    create_experiment_id,
    finalize_experiment_record,
)
from src.experiments.model_registry import ModelRegistry
from src.pipelines.context import PipelineResult, training_paths
from src.pipelines.train_behavioral_pipeline import run_behavioral_pipeline
from src.pipelines.train_facial_pipeline import run_facial_pipeline
from src.pipelines.train_pad_pipeline import run_pad_pipeline

ModelSelection = Literal["facial", "pad", "behavioral", "all"]


def _config_for(
    bundle: TrainingConfigBundle, family: str
) -> tuple[Path, dict[str, object], int]:
    if family == "facial":
        return (
            bundle.source_path / "arcface.yaml",
            bundle.arcface.model_dump(mode="json"),
            bundle.arcface.random_seed,
        )
    if family == "pad":
        return (
            bundle.source_path / "pad_mobilenetv2.yaml",
            bundle.pad.model_dump(mode="json"),
            bundle.pad.random_seed,
        )
    return (
        bundle.source_path / "behavioral_autoencoder.yaml",
        bundle.behavioral.model_dump(mode="json"),
        bundle.behavioral.random_seed,
    )


def _register_model(
    registry: ModelRegistry,
    result: PipelineResult,
    *,
    bundle: TrainingConfigBundle,
    force: bool,
) -> None:
    base = {
        "model_family": result.model_family,
        "model_name": result.model_name,
        "model_version": result.model_version,
        "participant_id": result.participant_id,
        "dataset_version": bundle.experiment.dataset_version,
        "protocol_version": bundle.experiment.protocol_version,
        "status": result.status,
        "metrics": result.metrics,
        "artifacts": [
            {
                "path": path.resolve().relative_to(PROJECT_ROOT).as_posix(),
                "sha256": sha256_file(path),
            }
            for path in result.artifacts
            if path.is_file()
        ],
        "test_rows_used": 0,
        "notes": result.notes,
    }
    if result.model_family != "behavioral":
        registry.register(base, force=force)
        return
    metadata_paths = [
        path for path in result.artifacts if path.name == "metadata.json" and path.is_file()
    ]
    if not metadata_paths:
        registry.register(base, force=force)
        return
    for metadata_path in metadata_paths:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        participant_id = str(metadata["participant_id"])
        participant_artifacts = [
            path
            for path in result.artifacts
            if path.is_file()
            and participant_id in path.parts
            and path.parent == metadata_path.parent
        ]
        registry.register(
            {
                **base,
                "model_version": metadata["model_version"],
                "participant_id": participant_id,
                "metrics": json.loads(
                    (metadata_path.parent / "validation_metrics.json").read_text(
                        encoding="utf-8"
                    )
                ),
                "artifacts": [
                    {
                        "path": path.resolve().relative_to(PROJECT_ROOT).as_posix(),
                        "sha256": sha256_file(path),
                    }
                    for path in participant_artifacts
                ],
            },
            force=force,
        )


def run_training_pipelines(
    preparation: PreparationConfig,
    bundle: TrainingConfigBundle,
    *,
    models: ModelSelection,
    device: DeviceSelection,
    output_dir: Path | None = None,
    participant_id: str | None = None,
    experiment_name: str | None = None,
    dry_run: bool = False,
    resume: bool = False,
    force: bool = False,
) -> list[PipelineResult]:
    selected = (
        ["facial", "pad", "behavioral"]
        if models == "all"
        else [models]
    )
    paths = training_paths(bundle, output_dir)
    experiment_registry = ExperimentRegistry(paths.experiments_path)
    model_registry = ModelRegistry(paths.registry_path)
    results: list[PipelineResult] = []
    for family in selected:
        started_at = datetime.now(timezone.utc)
        experiment_id = create_experiment_id(family, experiment_name)
        config_path, config_payload, random_seed = _config_for(bundle, family)
        try:
            if family == "facial":
                result = run_facial_pipeline(
                    preparation,
                    bundle,
                    device=device,
                    output_dir=output_dir,
                    dry_run=dry_run,
                    force=force,
                )
            elif family == "pad":
                result = run_pad_pipeline(
                    preparation,
                    bundle,
                    device=device,
                    output_dir=output_dir,
                    dry_run=dry_run,
                    resume=resume,
                    force=force,
                )
            else:
                result = run_behavioral_pipeline(
                    preparation,
                    bundle,
                    device=device,
                    output_dir=output_dir,
                    participant_id=participant_id,
                    dry_run=dry_run,
                    resume=resume,
                    force=force,
                )
        except Exception as exc:
            if not dry_run:
                environment = {"device": device.as_dict()}
                record = finalize_experiment_record(
                    experiment_id=experiment_id,
                    experiment_name=experiment_name,
                    model_family=family,
                    model_name=family,
                    participant_id=participant_id if family == "behavioral" else None,
                    dataset_version=bundle.experiment.dataset_version,
                    protocol_version=bundle.experiment.protocol_version,
                    configuration_path=config_path,
                    configuration=config_payload,
                    started_at=started_at,
                    status="failed",
                    random_seed=random_seed,
                    metrics=None,
                    artifacts=[],
                    environment=environment,
                    code_commit=None,
                    notes=f"{type(exc).__name__}: {exc}",
                )
                experiment_registry.append(record)
            raise
        results.append(result)
        if dry_run:
            continue
        if any(not path.is_file() for path in result.artifacts):
            raise FileNotFoundError("El pipeline terminó con artefactos faltantes.")
        record = finalize_experiment_record(
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            model_family=family,
            model_name=result.model_name,
            participant_id=result.participant_id,
            dataset_version=bundle.experiment.dataset_version,
            protocol_version=bundle.experiment.protocol_version,
            configuration_path=config_path,
            configuration=config_payload,
            started_at=started_at,
            status="completed",
            random_seed=random_seed,
            metrics=result.metrics,
            artifacts=result.artifacts,
            environment={"device": device.as_dict()},
            code_commit=None,
            notes=result.notes,
        )
        experiment_registry.append(record)
        _register_model(model_registry, result, bundle=bundle, force=force)
    return results
