from __future__ import annotations

import json

import matplotlib
import numpy as np
import pandas as pd

from evaluation.src.common.config import FinalEvaluationConfig
from evaluation.src.common.io import JsonValue, json_value, write_json_atomic
from evaluation.src.common.metrics import (
    binary_classification_metrics,
    save_bar_plot,
    save_confusion_matrix,
)
from evaluation.src.common.privacy import participant_code

matplotlib.use("Agg")
from matplotlib import pyplot as plt


def _first_detection_latency(
    group: pd.DataFrame,
    *,
    timestamp_column: str,
    label_column: str,
) -> float | None:
    if timestamp_column not in group:
        return None
    ordered = group.copy()
    ordered["_timestamp"] = pd.to_datetime(
        ordered[timestamp_column], utc=True, errors="coerce"
    )
    ordered = ordered.dropna(subset=["_timestamp"]).sort_values("_timestamp")
    changes = ordered[ordered[label_column].astype(int) == 1]
    if changes.empty:
        return None
    started = changes["_timestamp"].iloc[0]
    detections = ordered[
        (ordered["_timestamp"] >= started)
        & (ordered["fusion_predicted"].astype(int) == 1)
    ]
    if detections.empty:
        return None
    return float((detections["_timestamp"].iloc[0] - started).total_seconds() * 1000)


def compare_pretest_posttest(
    predictions: pd.DataFrame,
    config: FinalEvaluationConfig,
) -> tuple[pd.DataFrame, dict[str, JsonValue]]:
    schema = config.input_schema
    decision_column = (
        "fusion_predicted"
        if "fusion_predicted" in predictions
        else "fusion_raw_predicted"
    )
    required = {
        schema.session_id,
        schema.participant_id,
        schema.fusion_label,
        schema.pretest_detected,
        decision_column,
    }
    missing = required - set(predictions.columns)
    if missing:
        raise ValueError(
            "La comparación pretest/postest requiere: "
            + ", ".join(sorted(missing))
        )
    records: list[dict[str, object]] = []
    for session, group in predictions.groupby(schema.session_id):
        labels = group[schema.fusion_label].dropna().astype(int)
        if labels.empty:
            continue
        true_condition = int(labels.max())
        pretest_detected = int(
            group[schema.pretest_detected].fillna(False).astype(bool).any()
        )
        posttest_detected = int(
            group[decision_column].fillna(0).astype(int).any()
        )
        pretest_latency = (
            float(
                group[schema.pretest_latency_ms]
                .dropna()
                .astype(float)
                .min()
            )
            if schema.pretest_latency_ms in group
            and group[schema.pretest_latency_ms].notna().any()
            else None
        )
        posttest_latency = _first_detection_latency(
            group.rename(columns={decision_column: "fusion_predicted"}),
            timestamp_column=schema.timestamp,
            label_column=schema.fusion_label,
        )
        records.append(
            {
                "session_id": str(session),
                "participant_id": participant_code(
                    str(group[schema.participant_id].iloc[0])
                ),
                "unit_of_analysis": "experimental_session",
                "true_condition": true_condition,
                "pretest_decision": (
                    "detected" if pretest_detected else "not_detected"
                ),
                "posttest_decision": (
                    "detected" if posttest_detected else "not_detected"
                ),
                "pretest_detected": pretest_detected,
                "posttest_detected": posttest_detected,
                "pretest_latency_ms": pretest_latency,
                "posttest_latency_ms": posttest_latency,
                "pretest_false_alert": int(
                    true_condition == 0 and pretest_detected == 1
                ),
                "posttest_false_alert": int(
                    true_condition == 0 and posttest_detected == 1
                ),
            }
        )
    comparison = pd.DataFrame(records)
    if comparison.empty:
        raise ValueError("No existen sesiones comparables pretest/postest.")
    labels = comparison["true_condition"].astype(int).to_numpy()
    pre = comparison["pretest_detected"].astype(float).to_numpy()
    post = comparison["posttest_detected"].astype(float).to_numpy()
    summary: dict[str, object] = {
        "unit_of_analysis": "experimental_session",
        "session_count": len(comparison),
        "baseline_definition": (
            "Autenticación estática posterior al login, sin verificación continua."
        ),
        "pretest": binary_classification_metrics(labels, pre, 0.5),
        "posttest": binary_classification_metrics(labels, post, 0.5),
        "detected_change_difference": int(np.sum(post) - np.sum(pre)),
        "pretest_false_alerts": int(
            comparison["pretest_false_alert"].sum()
        ),
        "posttest_false_alerts": int(
            comparison["posttest_false_alert"].sum()
        ),
        "pretest_accuracy_interpretation": (
            "La exactitud refleja la regla estática declarada, no un clasificador "
            "adicional entrenado."
        ),
    }
    output = config.paths.output_directory / "comparison"
    output.mkdir(parents=True, exist_ok=True)
    comparison.to_parquet(output / "pretest_posttest.parquet", index=False)
    typed_summary = json_value(summary)
    if not isinstance(typed_summary, dict):
        raise TypeError("El resumen pretest/postest debe ser un objeto.")
    write_json_atomic(
        output / "pretest_posttest_summary.json", typed_summary
    )
    figure = plt.figure()
    plt.bar(
        ["Pretest", "Postest"],
        [
            float(summary["pretest"]["f1"]),
            float(summary["posttest"]["f1"]),
        ],
    )
    plt.ylabel("F1")
    plt.title("Comparación pretest y postest por sesión")
    figure.savefig(
        config.paths.output_directory
        / "figures"
        / "pretest_posttest_f1.png",
        bbox_inches="tight",
    )
    plt.close(figure)
    save_bar_plot(
        ["Pretest", "Postest"],
        [
            float(summary["pretest_false_alerts"]),
            float(summary["posttest_false_alerts"]),
        ],
        config.paths.output_directory / "figures" / "false_alerts.png",
        title="Falsas alertas por condición",
        y_label="Sesiones",
    )
    save_confusion_matrix(
        summary["pretest"],
        config.paths.output_directory
        / "figures"
        / "pretest_confusion_matrix.png",
        title="Matriz de confusión pretest",
        negative_label="Normal",
        positive_label="Cambio",
    )
    save_confusion_matrix(
        summary["posttest"],
        config.paths.output_directory
        / "figures"
        / "posttest_confusion_matrix.png",
        title="Matriz de confusión postest",
        negative_label="Normal",
        positive_label="Cambio",
    )
    (output / "pretest_posttest_report.md").write_text(
        "\n".join(
            [
                "# Comparación pretest/postest",
                "",
                "Unidad de análisis: sesión experimental.",
                "El pretest representa autenticación estática y no un clasificador inventado.",
                "",
                "```json",
                json.dumps(typed_summary, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return comparison, typed_summary
