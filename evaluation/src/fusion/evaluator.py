from __future__ import annotations

import json

import numpy as np
import pandas as pd

from evaluation.src.common.config import FinalEvaluationConfig
from evaluation.src.common.decisions import (
    approved_confirmation_count,
    confirmed_predictions,
)
from evaluation.src.common.io import JsonValue, json_value, write_json_atomic
from evaluation.src.common.metrics import (
    binary_classification_metrics,
    grouped_binary_metrics,
    save_bar_plot,
    save_confusion_matrix,
    save_histogram,
    save_precision_recall_plot,
    save_roc_plot,
)
from evaluation.src.common.privacy import (
    participant_code,
    public_prediction_columns,
)


def _time_to_detection(
    frame: pd.DataFrame,
    *,
    session_column: str,
    timestamp_column: str,
    label_column: str,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    if timestamp_column not in frame or session_column not in frame:
        return pd.DataFrame(records)
    working = frame.copy()
    working["_timestamp"] = pd.to_datetime(
        working[timestamp_column], utc=True, errors="coerce"
    )
    for session, group in working.groupby(session_column):
        ordered = group.dropna(subset=["_timestamp"]).sort_values("_timestamp")
        anomaly = ordered[ordered[label_column].astype(int) == 1]
        if anomaly.empty:
            continue
        start = anomaly["_timestamp"].iloc[0]
        detected = ordered[
            (ordered["_timestamp"] >= start)
            & (ordered["fusion_predicted"].astype(int) == 1)
        ]
        seconds = (
            float((detected["_timestamp"].iloc[0] - start).total_seconds())
            if not detected.empty
            else None
        )
        records.append(
            {
                "session_id": str(session),
                "detected": not detected.empty,
                "time_to_detection_seconds": seconds,
            }
        )
    return pd.DataFrame(records)


def evaluate_fusion(
    predictions: pd.DataFrame,
    config: FinalEvaluationConfig,
) -> dict[str, JsonValue]:
    schema = config.input_schema
    requested = predictions[
        predictions[schema.fusion_label].notna()
    ].copy()
    evaluated = requested[requested["fusion_risk"].notna()].copy()
    if evaluated.empty:
        raise ValueError("No existen decisiones multimodales evaluables.")
    thresholds = (
        evaluated["fusion_threshold"].dropna().astype(float).unique()
    )
    if len(thresholds) != 1:
        raise ValueError("La fusión debe usar un único límite aprobado.")
    threshold = float(thresholds[0])
    labels = evaluated[schema.fusion_label].astype(int).to_numpy()
    scores = evaluated["fusion_risk"].astype(float).to_numpy()
    raw_predictions = (scores >= threshold).astype(np.int8)
    confirmation_count = approved_confirmation_count(config)
    official_predictions = confirmed_predictions(
        evaluated,
        raw_predictions,
        session_column=schema.session_id,
        timestamp_column=schema.timestamp,
        confirmation_count=confirmation_count,
    )
    evaluated["fusion_raw_predicted"] = raw_predictions
    evaluated["fusion_predicted"] = official_predictions
    predictions.loc[
        evaluated.index, "fusion_raw_predicted"
    ] = raw_predictions
    predictions.loc[
        evaluated.index, "fusion_predicted"
    ] = official_predictions
    score_metrics = binary_classification_metrics(labels, scores, threshold)
    decision_metrics = binary_classification_metrics(
        labels, official_predictions.astype(float), 0.5
    )
    metrics = score_metrics
    for name in (
        "accuracy",
        "precision",
        "recall",
        "f1",
        "far",
        "frr",
        "confusion_matrix",
    ):
        metrics[name] = decision_metrics[name]
    metrics.update(
        {
            "requested_decision_count": int(len(requested)),
            "evaluated_decision_count": int(len(evaluated)),
            "unavailable_decision_rate": float(
                (len(requested) - len(evaluated)) / len(requested)
            ),
            "threshold_source": "approved_fusion_config",
            "weights_recalibrated": False,
            "hysteresis_confirmation_count": confirmation_count,
            "sensitivity_to_operator_change": decision_metrics["recall"],
            "false_alert_count": int(
                np.sum((labels == 0) & (official_predictions == 1))
            ),
        }
    )
    grouping_columns = [
        column
        for column in (
            schema.participant_id,
            schema.scenario,
            "fusion_available_components",
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
        official_predictions.astype(float),
        0.5,
    )
    session_metrics = _time_to_detection(
        evaluated,
        session_column=schema.session_id,
        timestamp_column=schema.timestamp,
        label_column=schema.fusion_label,
    )
    metrics["detected_session_count"] = (
        int(session_metrics["detected"].sum())
        if not session_metrics.empty
        else 0
    )
    metrics["time_to_detection_seconds"] = (
        {
            "mean": float(
                session_metrics["time_to_detection_seconds"].dropna().mean()
            ),
            "median": float(
                session_metrics["time_to_detection_seconds"].dropna().median()
            ),
        }
        if not session_metrics.empty
        and session_metrics["time_to_detection_seconds"].notna().any()
        else None
    )
    output = config.paths.output_directory / "fusion"
    output.mkdir(parents=True, exist_ok=True)
    public_prediction_columns(
        evaluated,
        participant_column=schema.participant_id,
    ).to_parquet(output / "fusion_test_predictions.parquet", index=False)
    if not session_metrics.empty:
        session_metrics.to_parquet(
            output / "fusion_session_metrics.parquet", index=False
        )
    typed_metrics = json_value(metrics)
    if not isinstance(typed_metrics, dict):
        raise TypeError("Las métricas de fusión deben ser un objeto.")
    write_json_atomic(output / "fusion_test_metrics.json", typed_metrics)
    figures = config.paths.output_directory / "figures"
    save_roc_plot(
        metrics,
        figures / "fusion_roc.png",
        title="ROC de fusión multimodal",
    )
    save_precision_recall_plot(
        metrics,
        figures / "fusion_precision_recall.png",
        title="Precision-Recall de fusión multimodal",
    )
    save_confusion_matrix(
        metrics,
        figures / "fusion_confusion_matrix.png",
        title="Matriz de confusión multimodal",
        negative_label="Normal",
        positive_label="Anomalía",
    )
    save_histogram(
        scores,
        figures / "fusion_risk_distribution.png",
        title="Distribución del riesgo multimodal",
        x_label="Riesgo fusionado",
    )
    availability = (
        evaluated["fusion_available_components"]
        .fillna("unavailable")
        .astype(str)
        .value_counts()
    )
    save_bar_plot(
        availability.index.tolist(),
        availability.astype(float).tolist(),
        figures / "component_availability.png",
        title="Disponibilidad de componentes",
        y_label="Decisiones",
        rotate_labels=True,
    )
    if (
        not session_metrics.empty
        and session_metrics["time_to_detection_seconds"].notna().any()
    ):
        detected_latency = session_metrics[
            "time_to_detection_seconds"
        ].dropna().astype(float)
        save_bar_plot(
            [f"S-{index + 1:04d}" for index in range(len(detected_latency))],
            detected_latency.tolist(),
            figures / "time_to_detection.png",
            title="Tiempo hasta detección por sesión",
            y_label="Segundos",
            rotate_labels=True,
        )
    (output / "fusion_test_report.md").write_text(
        "\n".join(
            [
                "# Evaluación final de fusión multimodal",
                "",
                "Se conservaron normalización, pesos, límites y estrategia aprobados.",
                "No se ajustó ninguna decisión después de observar test.",
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
