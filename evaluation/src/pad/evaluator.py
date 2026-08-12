from __future__ import annotations

import json

import pandas as pd

from evaluation.src.common.config import FinalEvaluationConfig
from evaluation.src.common.io import JsonValue, json_value, write_json_atomic
from evaluation.src.common.metrics import (
    binary_classification_metrics,
    grouped_binary_metrics,
    pad_error_rates,
    save_bar_plot,
    save_confusion_matrix,
    save_precision_recall_plot,
    save_roc_plot,
)
from evaluation.src.common.privacy import (
    participant_code,
    public_prediction_columns,
)


def evaluate_pad(
    predictions: pd.DataFrame,
    config: FinalEvaluationConfig,
) -> dict[str, JsonValue]:
    schema = config.input_schema
    requested = predictions[predictions[schema.pad_label].notna()].copy()
    evaluated = requested[
        requested["pad_attack_probability"].notna()
    ].copy()
    if evaluated.empty:
        raise ValueError("No existen muestras PAD evaluables.")
    thresholds = evaluated["pad_threshold"].dropna().astype(float).unique()
    if len(thresholds) != 1:
        raise ValueError("PAD debe usar un único umbral aprobado.")
    threshold = float(thresholds[0])
    labels = evaluated[schema.pad_label].astype(int).to_numpy()
    scores = evaluated["pad_attack_probability"].astype(float).to_numpy()
    metrics = binary_classification_metrics(labels, scores, threshold)
    metrics.update(pad_error_rates(metrics))
    metrics.update(
        {
            "requested_sample_count": int(len(requested)),
            "evaluated_sample_count": int(len(evaluated)),
            "rejection_rate": float(
                (len(requested) - len(evaluated)) / len(requested)
            ),
            "threshold_source": "approved_validation_artifact",
            "recalibrated": False,
        }
    )
    grouping_columns = [
        column
        for column in (
            schema.attack_type,
            schema.participant_id,
            schema.source_device,
            schema.condition,
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
    output = config.paths.output_directory / "pad"
    output.mkdir(parents=True, exist_ok=True)
    public_prediction_columns(
        evaluated,
        participant_column=schema.participant_id,
    ).to_parquet(output / "pad_test_predictions.parquet", index=False)
    typed_metrics = json_value(metrics)
    if not isinstance(typed_metrics, dict):
        raise TypeError("Las métricas PAD deben ser un objeto.")
    write_json_atomic(output / "pad_test_metrics.json", typed_metrics)
    figures = config.paths.output_directory / "figures"
    save_roc_plot(
        metrics,
        figures / "pad_roc.png",
        title="ROC PAD en test congelado",
    )
    save_precision_recall_plot(
        metrics,
        figures / "pad_precision_recall.png",
        title="Precision-Recall PAD en test congelado",
    )
    save_confusion_matrix(
        metrics,
        figures / "pad_confusion_matrix.png",
        title="Matriz de confusión PAD",
        negative_label="Bona fide",
        positive_label="Ataque",
    )
    save_bar_plot(
        ["APCER", "BPCER", "ACER"],
        [
            float(metrics[name])
            for name in ("apcer", "bpcer", "acer")
            if metrics[name] is not None
        ],
        figures / "pad_error_rates.png",
        title="Tasas de error PAD",
        y_label="Tasa",
    )
    attack_groups = metrics["grouped"].get(schema.attack_type, {})
    attack_labels: list[str] = []
    attack_apcer: list[float] = []
    for attack_name, attack_metrics in attack_groups.items():
        value = pad_error_rates(attack_metrics)["apcer"]
        if value is not None:
            attack_labels.append(attack_name)
            attack_apcer.append(float(value))
    save_bar_plot(
        attack_labels,
        attack_apcer,
        figures / "pad_apcer_by_attack.png",
        title="APCER por tipo de ataque",
        y_label="APCER",
        rotate_labels=True,
    )
    (output / "pad_test_report.md").write_text(
        "\n".join(
            [
                "# Evaluación PAD final",
                "",
                "El umbral procede del artefacto aprobado y no fue recalibrado.",
                "APCER, BPCER y ACER se calcularon sobre el test congelado.",
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
