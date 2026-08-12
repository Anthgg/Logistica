from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import PreparationConfig, TrainingConfigBundle
from src.common.device import DeviceSelection, insightface_providers
from src.common.serialization import write_json_atomic
from src.common.validation import validate_training_inputs
from src.facial.embedding_extractor import extract_embeddings, save_embeddings
from src.facial.facial_evaluator import evaluate_facial_validation
from src.facial.facial_exporter import export_facial_metadata
from src.facial.facial_threshold import calibrate_facial_threshold
from src.facial.insightface_loader import load_insightface
from src.facial.pair_builder import build_validation_pairs
from src.facial.template_builder import build_participant_templates, load_templates
from src.pipelines.context import PipelineResult, ensure_new_artifact, training_paths


def run_facial_pipeline(
    preparation: PreparationConfig,
    bundle: TrainingConfigBundle,
    *,
    device: DeviceSelection,
    output_dir: Path | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> PipelineResult:
    validation = validate_training_inputs(preparation, bundle, models={"facial"})
    validation.raise_if_invalid()
    config = bundle.arcface
    config_payload = config.model_dump(mode="json")
    paths = training_paths(bundle, output_dir)
    manifest_path = (
        preparation.pipeline.paths.root
        / preparation.pipeline.facial_identity_manifest
    )
    manifest = pd.read_parquet(manifest_path)
    development_count = int(
        (
            manifest["split"].isin(["train", "validation"])
            & manifest["quality_status"].isin(bundle.experiment.allowed_quality_statuses)
        ).sum()
    )
    if dry_run:
        return PipelineResult(
            model_family="facial",
            model_name=config.model_name,
            model_version=config.model_version,
            status="validated",
            metrics={
                "development_accepted_rows": development_count,
                "test_rows_used": 0,
                "device": device.as_dict(),
            },
        )
    metadata_dir = paths.models_root / "facial" / "metadata" / config.dataset_version
    metadata_path = metadata_dir / f"{config.model_version}.json"
    ensure_new_artifact(metadata_path, force=force)
    embedding_path = (
        paths.models_root
        / "facial"
        / "embeddings"
        / config.dataset_version
        / "embeddings.parquet"
    )
    template_dir = (
        paths.models_root / "facial" / "templates" / config.dataset_version
    )
    threshold_path = (
        paths.models_root
        / "facial"
        / "thresholds"
        / config.dataset_version
        / "facial_threshold.json"
    )
    report_dir = paths.reports_root / "facial"
    application = load_insightface(config, insightface_providers(device))
    embeddings = extract_embeddings(
        manifest,
        data_root=preparation.pipeline.paths.root,
        config=config,
        application=application,
    )
    save_embeddings(embeddings, embedding_path)
    templates, template_rejections = build_participant_templates(
        embeddings,
        output_dir=template_dir,
        config=config,
        config_payload=config_payload,
    )
    if not templates:
        raise ValueError("No se pudo construir ninguna plantilla facial.")
    loaded_templates = load_templates(template_dir)
    pairs = build_validation_pairs(
        loaded_templates,
        embeddings,
        maximum_impostor_pairs_per_identity=config.maximum_impostor_pairs_per_identity,
        random_seed=config.random_seed,
    )
    if pairs.empty or set(pairs["label"].astype(int)) != {0, 1}:
        raise ValueError("No existen pares genuinos e impostores suficientes.")
    report_dir.mkdir(parents=True, exist_ok=True)
    pairs_path = report_dir / "validation_pairs.parquet"
    pairs.to_parquet(pairs_path, index=False)
    threshold_payload = calibrate_facial_threshold(pairs, config, config_payload)
    write_json_atomic(threshold_path, threshold_payload)
    rejected_embeddings = embeddings.loc[
        embeddings["extraction_status"] != "accepted",
        ["participant_id", "session_id", "capture_id", "rejection_reason"],
    ].copy()
    rejected_templates = pd.DataFrame(template_rejections)
    rejections = pd.concat(
        [rejected_embeddings, rejected_templates], ignore_index=True, sort=False
    )
    rejections_path = report_dir / "facial_rejections.csv"
    rejections.to_csv(rejections_path, index=False)
    metrics = evaluate_facial_validation(
        pairs,
        threshold_payload=threshold_payload,
        report_dir=report_dir,
    )
    metrics_path = report_dir / "facial_validation_metrics.json"
    export_facial_metadata(
        metadata_path,
        model_version=config.model_version,
        dataset_version=config.dataset_version,
        template_paths=[artifact.template_path for artifact in templates],
        threshold_path=threshold_path,
        metrics_path=metrics_path,
    )
    artifacts = [
        embedding_path,
        *[artifact.template_path for artifact in templates],
        *[artifact.metadata_path for artifact in templates],
        pairs_path,
        threshold_path,
        metrics_path,
        rejections_path,
        metadata_path,
    ]
    return PipelineResult(
        model_family="facial",
        model_name=config.model_name,
        model_version=config.model_version,
        status="candidate",
        metrics=metrics,
        artifacts=artifacts,
    )
