from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluation.src.common.config import FinalEvaluationConfig
from evaluation.src.common.io import JsonValue, json_value, write_json_atomic
from evaluation.src.common.metrics import (
    binary_classification_metrics,
    grouped_binary_metrics,
    save_confusion_matrix,
    save_precision_recall_plot,
    save_roc_plot,
)
from evaluation.src.common.privacy import (
    participant_code,
    public_prediction_columns,
)


def _single_threshold(frame: pd.DataFrame, column: str) -> float:
    values = frame[column].dropna().astype(float).unique()
    if len(values) != 1:
        raise ValueError(f"{column} debe contener un único umbral aprobado.")
    return float(values[0])


def evaluate_facial(
    predictions: pd.DataFrame,
    config: FinalEvaluationConfig,
) -> dict[str, JsonValue]:
    schema = config.input_schema
    requested = predictions[
        predictions[schema.facial_label].notna()
    ].copy()
    evaluated = requested[
        requested["facial_similarity"].notna()
    ].copy()
    if evaluated.empty:
        raise ValueError("No existen comparaciones faciales evaluables.")
    labels = evaluated[schema.facial_label].astype(int).to_numpy()
    scores = evaluated["facial_similarity"].astype(float).to_numpy()
    threshold = _single_threshold(evaluated, "facial_threshold")
    metrics = binary_classification_metrics(labels, scores, threshold)
    metrics.update(
        {
            "genuine_comparisons": int(np.sum(labels == 1)),
            "impostor_comparisons": int(np.sum(labels == 0)),
            "requested_capture_count": int(len(requested)),
            "evaluated_capture_count": int(len(evaluated)),
            "capture_rejection_rate": float(
                (len(requested) - len(evaluated)) / len(requested)
            ),
            "threshold_source": "approved_validation_artifact",
            "recalibrated": False,
        }
    )
    grouping_columns = [
        column
        for column in (
            schema.participant_id,
            schema.scenario,
            schema.illumination,
        )
        if column in evaluated
    ]
    metrics["grouped"] = grouped_binary_metrics(
        {
            column: (
                evaluated[column]
                .fillna("unknown")
                .astype(str)
                .map(participant_code)
                .to_numpy()
                if column == schema.participant_id
                else evaluated[column]
                .fillna("unknown")
                .astype(str)
                .to_numpy()
            )
            for column in grouping_columns
        },
        labels,
        scores,
        threshold,
    )
    output = config.paths.output_directory / "facial"
    output.mkdir(parents=True, exist_ok=True)
    public = public_prediction_columns(
        evaluated,
        participant_column=schema.participant_id,
    )
    public.to_parquet(
        output / "facial_test_predictions.parquet", index=False
    )
    typed_metrics = json_value(metrics)
    if not isinstance(typed_metrics, dict):
        raise TypeError("Las métricas faciales deben ser un objeto.")
    write_json_atomic(output / "facial_test_metrics.json", typed_metrics)
    figures = config.paths.output_directory / "figures"
    save_roc_plot(
        metrics,
        figures / "facial_roc.png",
        title="ROC facial en test congelado",
    )
    save_precision_recall_plot(
        metrics,
        figures / "facial_precision_recall.png",
        title="Precision-Recall facial en test congelado",
    )
    save_confusion_matrix(
        metrics,
        figures / "facial_confusion_matrix.png",
        title="Matriz de confusión facial",
        negative_label="Impostor",
        positive_label="Genuino",
    )
    (output / "facial_test_report.md").write_text(
        "\n".join(
            [
                "# Evaluación facial final",
                "",
                "El umbral procede del artefacto aprobado y no fue recalibrado.",
                "Los identificadores publicados están seudonimizados.",
                "",
                "```json",
                json.dumps(typed_metrics, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return typed_metrics
