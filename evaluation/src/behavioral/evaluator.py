from __future__ import annotations

import json

import numpy as np
import pandas as pd

from evaluation.src.common.config import FinalEvaluationConfig
from evaluation.src.common.io import JsonValue, json_value, write_json_atomic
from evaluation.src.common.metrics import (
    binary_classification_metrics,
    save_bar_plot,
    save_confusion_matrix,
    save_precision_recall_plot,
    save_roc_plot,
)
from evaluation.src.common.privacy import (
    participant_code,
    public_prediction_columns,
)

METRIC_NAMES = (
    "accuracy",
    "precision",
    "recall",
    "f1",
    "roc_auc",
    "pr_auc",
    "far",
    "frr",
    "eer",
)


def _participant_metrics(
    participant_frame: pd.DataFrame,
    *,
    label_column: str,
) -> dict[str, object]:
    thresholds = (
        participant_frame["behavioral_threshold"]
        .dropna()
        .astype(float)
        .unique()
    )
    if len(thresholds) != 1:
        raise ValueError(
            "Cada participante conductual debe usar un umbral aprobado."
        )
    labels = participant_frame[label_column].astype(int).to_numpy()
    errors = (
        participant_frame["behavioral_reconstruction_error"]
        .astype(float)
        .to_numpy()
    )
    metrics = binary_classification_metrics(
        labels,
        errors,
        float(thresholds[0]),
        positive_direction="lower",
    )
    metrics.update(
        {
            "legitimate_windows": int(np.sum(labels == 1)),
            "impostor_windows": int(np.sum(labels == 0)),
            "legitimate_mse_mean": (
                float(np.mean(errors[labels == 1]))
                if np.any(labels == 1)
                else None
            ),
            "impostor_mse_mean": (
                float(np.mean(errors[labels == 0]))
                if np.any(labels == 0)
                else None
            ),
            "threshold_source": "approved_participant_artifact",
            "scaler_refitted": False,
            "recalibrated": False,
        }
    )
    return metrics


def evaluate_behavioral(
    predictions: pd.DataFrame,
    config: FinalEvaluationConfig,
) -> dict[str, JsonValue]:
    schema = config.input_schema
    requested = predictions[
        predictions[schema.behavioral_label].notna()
    ].copy()
    evaluated = requested[
        requested["behavioral_reconstruction_error"].notna()
    ].copy()
    if evaluated.empty:
        raise ValueError("No existen ventanas conductuales evaluables.")
    participants: list[dict[str, object]] = []
    for participant, group in evaluated.groupby(schema.participant_id):
        metrics = _participant_metrics(
            group,
            label_column=schema.behavioral_label,
        )
        metrics["participant_id"] = participant_code(str(participant))
        participants.append(metrics)
    macro: dict[str, dict[str, float] | None] = {}
    for metric in METRIC_NAMES:
        values = np.asarray(
            [
                float(item[metric])
                for item in participants
                if item.get(metric) is not None
            ],
            dtype=float,
        )
        macro[metric] = (
            {
                "mean": float(np.mean(values)),
                "median": float(np.median(values)),
                "std": (
                    float(np.std(values, ddof=1))
                    if len(values) > 1
                    else 0.0
                ),
                "minimum": float(np.min(values)),
                "maximum": float(np.max(values)),
            }
            if len(values)
            else None
        )
    all_labels = evaluated[schema.behavioral_label].astype(int).to_numpy()
    all_errors = (
        evaluated["behavioral_reconstruction_error"]
        .astype(float)
        .to_numpy()
    )
    approved_thresholds = (
        evaluated["behavioral_threshold"].astype(float).to_numpy()
    )
    approved_margins = approved_thresholds - all_errors
    summary: dict[str, object] = {
        "participant_count": len(participants),
        "requested_window_count": int(len(requested)),
        "evaluated_window_count": int(len(evaluated)),
        "rejection_rate": float(
            (len(requested) - len(evaluated)) / len(requested)
        ),
        "macro_statistics": macro,
        "participant_metrics": participants,
        "micro_official": binary_classification_metrics(
            all_labels,
            approved_margins,
            0.0,
        ),
        "micro_official_note": (
            "El puntaje agregado es el margen umbral_aprobado - error; "
            "cada decisión conserva el umbral individual."
        ),
        "recalibrated": False,
        "scalers_refitted": False,
    }
    output = config.paths.output_directory / "behavioral"
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(participants).to_parquet(
        output / "behavioral_test_metrics.parquet", index=False
    )
    public_prediction_columns(
        evaluated,
        participant_column=schema.participant_id,
    ).to_parquet(
        output / "behavioral_test_predictions.parquet", index=False
    )
    typed_summary = json_value(summary)
    if not isinstance(typed_summary, dict):
        raise TypeError("El resumen conductual debe ser un objeto.")
    write_json_atomic(
        output / "behavioral_test_summary.json", typed_summary
    )
    figures = config.paths.output_directory / "figures"
    save_roc_plot(
        summary["micro_official"],
        figures / "behavioral_aggregate_roc.png",
        title="ROC conductual agregada",
    )
    save_precision_recall_plot(
        summary["micro_official"],
        figures / "behavioral_aggregate_precision_recall.png",
        title="Precision-Recall conductual agregada",
    )
    save_confusion_matrix(
        summary["micro_official"],
        figures / "behavioral_confusion_matrix.png",
        title="Matriz conductual agregada",
        negative_label="Impostor",
        positive_label="Legítimo",
    )
    participant_labels = [
        str(item["participant_id"]) for item in participants
    ]
    participant_f1 = [float(item["f1"]) for item in participants]
    save_bar_plot(
        participant_labels,
        participant_f1,
        figures / "behavioral_metrics_by_participant.png",
        title="F1 conductual por participante",
        y_label="F1",
        rotate_labels=True,
    )
    (output / "behavioral_test_report.md").write_text(
        "\n".join(
            [
                "# Evaluación conductual final",
                "",
                "Cada participante conserva scaler, autoencoder, esquema y umbral aprobados.",
                "No se realizó ajuste ni recalibración sobre test.",
                "",
                "```json",
                json.dumps(typed_summary, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return typed_summary
