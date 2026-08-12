from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.behavioral.autoencoder_model import build_autoencoder
from src.behavioral.evaluator import (
    aggregate_behavioral_metrics,
    evaluate_participant,
)
from src.behavioral.exporter import export_participant_artifacts
from src.behavioral.feature_loader import load_behavioral_features
from src.behavioral.feature_validator import build_feature_schema, validate_features
from src.behavioral.scaler import fit_participant_scaler
from src.behavioral.threshold import calibrate_behavioral_threshold
from src.behavioral.trainer import reconstruction_errors, train_autoencoder
from src.behavioral.user_dataset import build_user_dataset, feature_matrix
from src.common.config import PreparationConfig, TrainingConfigBundle
from src.common.device import DeviceSelection
from src.common.serialization import write_json_atomic
from src.common.validation import validate_training_inputs
from src.pipelines.context import PipelineResult, ensure_new_artifact, training_paths


def _model_version(prefix: str, participant_id: str) -> str:
    safe = "".join(
        character
        for character in participant_id
        if character.isalnum() or character in "-_"
    )
    return f"{prefix}-{safe}-v0.1.0"


def run_behavioral_pipeline(
    preparation: PreparationConfig,
    bundle: TrainingConfigBundle,
    *,
    device: DeviceSelection,
    output_dir: Path | None = None,
    participant_id: str | None = None,
    dry_run: bool = False,
    resume: bool = False,
    force: bool = False,
) -> PipelineResult:
    validation = validate_training_inputs(
        preparation, bundle, models={"behavioral"}
    )
    validation.raise_if_invalid()
    config = bundle.behavioral
    config_payload = config.model_dump(mode="json")
    paths = training_paths(bundle, output_dir)
    frame = load_behavioral_features(
        preparation.pipeline.paths.root
        / "processed"
        / "behavioral"
        / "behavioral_features.parquet",
        config,
    )
    feature_validation = validate_features(frame, config)
    if not feature_validation.valid:
        raise ValueError(f"Características conductuales inválidas: {feature_validation.as_dict()}")
    participants = sorted(
        frame.loc[
            (frame["split"] == "train")
            & (frame["operator_label"] == "legitimate"),
            "participant_id",
        ]
        .astype(str)
        .unique()
    )
    if participant_id:
        participants = [value for value in participants if value == participant_id]
        if not participants:
            raise ValueError(f"No existen ventanas train para {participant_id}.")
    trainable = [
        value
        for value in participants
        if build_user_dataset(frame, value, config) is not None
    ]
    if dry_run:
        return PipelineResult(
            model_family="behavioral",
            model_name="autoencoder",
            model_version=f"{config.model_version_prefix}-v0.1.0",
            status="validated",
            metrics={
                "participants_found": len(participants),
                "participants_trainable": len(trainable),
                "feature_count": len(config.feature_columns),
                "feature_validation": feature_validation.as_dict(),
                "test_rows_used": 0,
                "device": device.as_dict(),
            },
        )
    schema = build_feature_schema(config)
    global_schema_path = (
        paths.models_root / "behavioral" / "metadata" / "feature_schema.json"
    )
    write_json_atomic(global_schema_path, schema)
    participant_metrics: list[dict[str, object]] = []
    failed: list[dict[str, object]] = []
    artifacts: list[Path] = [global_schema_path]
    for current in participants:
        dataset = build_user_dataset(frame, current, config)
        if dataset is None:
            failed.append(
                {
                    "participant_id": current,
                    "status": "not_trainable",
                    "reason": "INSUFFICIENT_TRAIN_OR_VALIDATION_WINDOWS",
                }
            )
            continue
        version = _model_version(config.model_version_prefix, current)
        participant_dir = (
            paths.models_root / "behavioral" / "participants" / current / version
        )
        metadata_path = participant_dir / "metadata.json"
        try:
            ensure_new_artifact(metadata_path, force=force)
            train_matrix = feature_matrix(dataset.train, config.feature_columns)
            genuine_matrix = feature_matrix(
                dataset.validation_genuine, config.feature_columns
            )
            impostor_matrix = feature_matrix(
                dataset.validation_impostor, config.feature_columns
            )
            scaler = fit_participant_scaler(train_matrix)
            scaled_train = scaler.transform(train_matrix)
            scaled_genuine = scaler.transform(genuine_matrix)
            scaled_impostor = scaler.transform(impostor_matrix)
            model = build_autoencoder(len(config.feature_columns), config)
            training = train_autoencoder(
                model,
                scaled_train,
                config=config,
                output_dir=participant_dir,
                resume=resume,
            )
            import tensorflow as tf

            best_model = tf.keras.models.load_model(training.model_path)
            genuine_mse, _ = reconstruction_errors(best_model, scaled_genuine)
            impostor_mse, _ = reconstruction_errors(best_model, scaled_impostor)
            threshold_payload = calibrate_behavioral_threshold(
                genuine_mse,
                impostor_mse,
                participant_id=current,
                model_version=version,
                config=config,
                config_payload=config_payload,
            )
            write_json_atomic(participant_dir / "threshold.json", threshold_payload)
            metrics = evaluate_participant(
                genuine_mse,
                impostor_mse,
                threshold_payload=threshold_payload,
                output_dir=participant_dir,
            )
            metadata = {
                "participant_id": current,
                "model_type": "behavioral_autoencoder",
                "model_version": version,
                "dataset_version": config.dataset_version,
                "protocol_version": bundle.experiment.protocol_version,
                "training_session_ids": list(dataset.train_session_ids),
                "validation_session_ids": list(dataset.validation_session_ids),
                "feature_count": len(config.feature_columns),
                "train_window_count": len(dataset.train),
                "validation_genuine_count": len(dataset.validation_genuine),
                "validation_impostor_count": len(dataset.validation_impostor),
                "architecture": config.architecture.model_dump(mode="json"),
                "optimizer": "Adam",
                "learning_rate": config.learning_rate,
                "epochs_executed": training.epochs_executed,
                "best_epoch": training.best_epoch,
            }
            export_participant_artifacts(
                model=best_model,
                scaler=scaler,
                output_dir=participant_dir,
                threshold_payload=threshold_payload,
                metrics=metrics,
                feature_schema=schema,
                metadata=metadata,
                config_payload=config_payload,
            )
            participant_metrics.append(metrics)
            artifacts.extend(
                [
                    participant_dir / "autoencoder.keras",
                    participant_dir / "scaler.joblib",
                    participant_dir / "threshold.json",
                    participant_dir / "feature_schema.json",
                    participant_dir / "training_history.csv",
                    participant_dir / "validation_metrics.json",
                    participant_dir / "metadata.json",
                ]
            )
        except Exception as exc:
            failed.append(
                {
                    "participant_id": current,
                    "status": "failed",
                    "reason": type(exc).__name__,
                    "message": str(exc),
                }
            )
    report_dir = paths.reports_root / "behavioral"
    summary = aggregate_behavioral_metrics(
        participant_metrics, failed_participants=failed, output_dir=report_dir
    )
    metrics_path = report_dir / "behavioral_validation_metrics.parquet"
    metric_rows = [
        {
            key: value
            for key, value in item.items()
            if isinstance(value, (str, int, float, bool)) or value is None
        }
        for item in participant_metrics
    ]
    pd.DataFrame(metric_rows).to_parquet(metrics_path, index=False)
    artifacts.extend(
        [
            metrics_path,
            report_dir / "behavioral_summary.json",
            report_dir / "behavioral_report.md",
        ]
    )
    status = "candidate" if participant_metrics else "rejected"
    return PipelineResult(
        model_family="behavioral",
        model_name="autoencoder",
        model_version=f"{config.model_version_prefix}-v0.1.0",
        status=status,
        metrics=summary,
        artifacts=artifacts,
        participant_id=participant_id,
        notes=(
            None
            if status == "candidate"
            else "No existieron participantes entrenables."
        ),
    )
