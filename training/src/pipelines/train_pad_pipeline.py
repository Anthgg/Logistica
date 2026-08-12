from __future__ import annotations

from pathlib import Path

import numpy as np

from src.common.config import PreparationConfig, TrainingConfigBundle
from src.common.device import DeviceSelection
from src.common.serialization import write_json_atomic
from src.common.validation import validate_training_inputs
from src.pad.dataset_loader import (
    build_tf_dataset,
    class_weights,
    load_pad_frame,
)
from src.pad.evaluator import evaluate_pad_validation
from src.pad.exporter import export_pad_model
from src.pad.mobilenet_model import build_mobilenetv2
from src.pad.threshold import calibrate_pad_threshold
from src.pad.trainer import train_pad
from src.pipelines.context import PipelineResult, ensure_new_artifact, training_paths


def run_pad_pipeline(
    preparation: PreparationConfig,
    bundle: TrainingConfigBundle,
    *,
    device: DeviceSelection,
    output_dir: Path | None = None,
    dry_run: bool = False,
    resume: bool = False,
    force: bool = False,
) -> PipelineResult:
    validation = validate_training_inputs(preparation, bundle, models={"pad"})
    validation.raise_if_invalid()
    config = bundle.pad
    config_payload = config.model_dump(mode="json")
    paths = training_paths(bundle, output_dir)
    frame = load_pad_frame(
        preparation.pipeline.paths.root / preparation.pipeline.facial_pad_manifest,
        data_root=preparation.pipeline.paths.root,
        config=config,
    )
    balance = (
        frame.groupby(["split", "presentation_label"]).size().rename("count").to_dict()
    )
    if dry_run:
        return PipelineResult(
            model_family="pad",
            model_name=config.backbone,
            model_version=config.model_version,
            status="validated",
            metrics={
                "rows": int(len(frame)),
                "balance": {"/".join(key): int(value) for key, value in balance.items()},
                "test_rows_used": 0,
                "device": device.as_dict(),
            },
        )
    checkpoint_dir = (
        paths.models_root / "pad" / "checkpoints" / config.model_version
    )
    export_path = (
        paths.models_root / "pad" / "exported" / config.model_version / "model.keras"
    )
    metadata_path = (
        paths.models_root / "pad" / "metadata" / f"{config.model_version}.json"
    )
    threshold_path = (
        paths.models_root / "pad" / "thresholds" / f"{config.model_version}.json"
    )
    ensure_new_artifact(metadata_path, force=force)
    train_dataset = build_tf_dataset(frame, config=config, training=True)
    validation_dataset = build_tf_dataset(frame, config=config, training=False)
    model, backbone = build_mobilenetv2(config)
    training = train_pad(
        model,
        backbone,
        train_dataset,
        validation_dataset,
        config=config,
        checkpoint_dir=checkpoint_dir,
        class_weight=class_weights(frame) if config.class_weighting else None,
        resume=resume,
    )
    import tensorflow as tf

    best_model = tf.keras.models.load_model(training.best_model_path)
    probabilities = np.asarray(
        best_model.predict(validation_dataset, verbose=0), dtype=float
    ).reshape(-1)
    validation_frame = frame.loc[frame["split"] == "validation"].reset_index(drop=True)
    labels = validation_frame["label"].astype(int).to_numpy()
    threshold_payload = calibrate_pad_threshold(
        labels, probabilities, config, config_payload
    )
    write_json_atomic(threshold_path, threshold_payload)
    report_dir = paths.reports_root / "pad"
    metrics = evaluate_pad_validation(
        validation_frame,
        probabilities,
        threshold_payload=threshold_payload,
        report_dir=report_dir,
    )
    metrics_path = report_dir / "pad_validation_metrics.json"
    export_pad_model(
        best_model,
        export_path=export_path,
        metadata_path=metadata_path,
        threshold_path=threshold_path,
        metrics_path=metrics_path,
        model_version=config.model_version,
        dataset_version=config.dataset_version,
        config_payload=config_payload,
        best_epoch=training.best_epoch,
    )
    return PipelineResult(
        model_family="pad",
        model_name=config.backbone,
        model_version=config.model_version,
        status="candidate",
        metrics=metrics,
        artifacts=[
            training.frozen_checkpoint,
            training.finetuned_checkpoint,
            training.history_path,
            export_path,
            threshold_path,
            metadata_path,
            metrics_path,
            report_dir / "pad_validation_predictions.parquet",
        ],
    )
