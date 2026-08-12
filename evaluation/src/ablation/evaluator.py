from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Mapping, cast

import matplotlib
import numpy as np
import pandas as pd

from evaluation.src.common.config import FinalEvaluationConfig
from evaluation.src.common.decisions import confirmed_predictions
from evaluation.src.common.io import JsonValue, json_value, read_json
from evaluation.src.common.metrics import (
    binary_classification_metrics,
    save_confusion_matrix,
)
from evaluation.src.common.privacy import participant_code

matplotlib.use("Agg")
from matplotlib import pyplot as plt


@dataclass(frozen=True)
class ApprovedAblation:
    name: str
    components: tuple[str, ...]
    weights: dict[str, float]
    decision_threshold: float
    confirmation_count: int
    hysteresis: bool


def _time_to_detection(
    frame: pd.DataFrame,
    labels: np.ndarray,
    decisions: np.ndarray,
    *,
    session_column: str,
    timestamp_column: str,
) -> tuple[float | None, int]:
    if timestamp_column not in frame or session_column not in frame:
        return None, 0
    working = frame[[session_column, timestamp_column]].copy()
    working["_label"] = labels
    working["_decision"] = decisions
    working["_timestamp"] = pd.to_datetime(
        working[timestamp_column], utc=True, errors="coerce"
    )
    latencies: list[float] = []
    missed = 0
    for _, group in working.groupby(session_column):
        ordered = group.dropna(subset=["_timestamp"]).sort_values("_timestamp")
        anomaly = ordered[ordered["_label"].astype(int) == 1]
        if anomaly.empty:
            continue
        started = anomaly["_timestamp"].iloc[0]
        detected = ordered[
            (ordered["_timestamp"] >= started)
            & (ordered["_decision"].astype(int) == 1)
        ]
        if detected.empty:
            missed += 1
            continue
        latencies.append(
            float(
                (
                    detected["_timestamp"].iloc[0] - started
                ).total_seconds()
            )
        )
    return (
        float(np.mean(latencies)) if latencies else None,
        missed,
    )


def _mapping(value: JsonValue, field: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} debe ser un objeto aprobado.")
    return cast(Mapping[str, JsonValue], value)


def _approved_variants(
    config: FinalEvaluationConfig,
) -> tuple[ApprovedAblation, ...]:
    approval = read_json(config.paths.integration_approval)
    raw_variants = _mapping(
        approval.get("ablation_configurations"),
        "ablation_configurations",
    )
    variants: list[ApprovedAblation] = []
    for name in config.ablation_configurations:
        payload = _mapping(raw_variants.get(name), name)
        raw_components = payload.get("components")
        if not isinstance(raw_components, list) or not all(
            isinstance(item, str)
            and item in {"facial", "pad", "behavioral"}
            for item in raw_components
        ):
            raise ValueError(f"{name}.components no es válido.")
        components = tuple(cast(list[str], raw_components))
        weight_values = _mapping(payload.get("weights"), f"{name}.weights")
        weights: dict[str, float] = {}
        for component in components:
            value = weight_values.get(component)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"Falta el peso aprobado {name}.{component}.")
            weights[component] = float(value)
        if (
            any(not math.isfinite(value) or value < 0 for value in weights.values())
            or abs(sum(weights.values()) - 1.0) > 1e-9
        ):
            raise ValueError(f"Los pesos aprobados de {name} deben sumar 1.")
        threshold_value = payload.get("decision_threshold")
        confirmation_value = payload.get("confirmation_count")
        hysteresis_value = payload.get("hysteresis")
        if (
            isinstance(threshold_value, bool)
            or not isinstance(threshold_value, (int, float))
            or not 0 <= float(threshold_value) <= 1
        ):
            raise ValueError(f"{name}.decision_threshold no es válido.")
        if (
            isinstance(confirmation_value, bool)
            or not isinstance(confirmation_value, int)
            or confirmation_value < 1
        ):
            raise ValueError(f"{name}.confirmation_count no es válido.")
        if not isinstance(hysteresis_value, bool):
            raise ValueError(f"{name}.hysteresis no es booleano.")
        variants.append(
            ApprovedAblation(
                name=name,
                components=components,
                weights=weights,
                decision_threshold=float(threshold_value),
                confirmation_count=confirmation_value,
                hysteresis=hysteresis_value,
            )
        )
    return tuple(variants)


def evaluate_ablation(
    predictions: pd.DataFrame,
    config: FinalEvaluationConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    schema = config.input_schema
    risk_columns = {
        "facial": "facial_risk",
        "pad": "pad_risk",
        "behavioral": "behavioral_risk",
    }
    complete = predictions[
        predictions[schema.fusion_label].notna()
        & predictions[list(risk_columns.values())].notna().all(axis=1)
    ].copy()
    if complete.empty:
        raise ValueError(
            "No existen casos completos compartidos para la ablación."
        )
    variants = _approved_variants(config)
    records: list[pd.DataFrame] = []
    summaries: list[dict[str, object]] = []
    labels = complete[schema.fusion_label].astype(int).to_numpy()
    figures = config.paths.output_directory / "figures"
    for variant in variants:
        scores = np.zeros(len(complete), dtype=float)
        for component, weight in variant.weights.items():
            scores += (
                complete[risk_columns[component]].astype(float).to_numpy()
                * weight
            )
        raw = (scores >= variant.decision_threshold).astype(np.int8)
        confirmed = confirmed_predictions(
            complete,
            raw,
            session_column=schema.session_id,
            timestamp_column=schema.timestamp,
            confirmation_count=(
                variant.confirmation_count if variant.hysteresis else 1
            ),
        )
        metrics = binary_classification_metrics(
            labels,
            scores,
            variant.decision_threshold,
        )
        decision_metrics = binary_classification_metrics(
            labels,
            confirmed.astype(float),
            0.5,
        )
        mean_detection_seconds, missed_anomaly_sessions = _time_to_detection(
            complete,
            labels,
            confirmed,
            session_column=schema.session_id,
            timestamp_column=schema.timestamp,
        )
        summaries.append(
            {
                "configuration": variant.name,
                "components": "+".join(variant.components),
                "hysteresis": variant.hysteresis,
                "confirmation_count": (
                    variant.confirmation_count if variant.hysteresis else 1
                ),
                "decision_threshold": variant.decision_threshold,
                "sample_count": len(complete),
                "accuracy": decision_metrics["accuracy"],
                "precision": decision_metrics["precision"],
                "recall": decision_metrics["recall"],
                "f1": decision_metrics["f1"],
                "roc_auc": metrics["roc_auc"],
                "far": decision_metrics["far"],
                "frr": decision_metrics["frr"],
                "eer": metrics["eer"],
                "mean_latency_ms": float(
                    complete[
                        [
                            f"{component}_latency_ms"
                            for component in variant.components
                        ]
                    ]
                    .fillna(0)
                    .sum(axis=1)
                    .mean()
                ),
                "mean_time_to_detection_seconds": mean_detection_seconds,
                "false_alert_count": int(
                    np.sum((labels == 0) & (confirmed == 1))
                ),
                "missed_anomaly_session_count": missed_anomaly_sessions,
                "availability": 1.0,
                "reverification_count": None,
                "restriction_count": None,
                "adaptive_action_note": (
                    "No medible en evaluación offline de ablación."
                ),
                "weights_recalibrated": False,
            }
        )
        slug = re.sub(r"[^a-z0-9]+", "-", variant.name.casefold()).strip("-")
        save_confusion_matrix(
            decision_metrics,
            figures / f"ablation_{slug}_confusion_matrix.png",
            title=f"Matriz de ablación: {variant.name}",
            negative_label="Normal",
            positive_label="Anomalía",
        )
        variant_frame = pd.DataFrame(
            {
                "row_id": complete[schema.row_id].astype(str),
                "session_id": complete[schema.session_id].astype(str),
                "participant_id": complete[schema.participant_id]
                .astype(str)
                .map(participant_code),
                "configuration": variant.name,
                "true_label": labels,
                "risk_score": scores,
                "raw_prediction": raw,
                "confirmed_prediction": confirmed,
                "correct": confirmed == labels,
            }
        )
        records.append(variant_frame)
    results = pd.concat(records, ignore_index=True)
    summary = pd.DataFrame(summaries)
    output = config.paths.output_directory / "ablation"
    output.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    results.to_parquet(output / "ablation_results.parquet", index=False)
    summary.to_csv(output / "ablation_summary.csv", index=False)
    figure = plt.figure()
    plt.bar(summary["configuration"], summary["f1"].astype(float))
    plt.xticks(rotation=35, ha="right")
    plt.ylabel("F1")
    plt.title("Comparación de configuraciones de ablación")
    figure.savefig(
        config.paths.output_directory / "figures" / "ablation_f1.png",
        bbox_inches="tight",
    )
    plt.close(figure)
    (output / "ablation_report.md").write_text(
        "\n".join(
            [
                "# Ablación multimodal",
                "",
                "Todas las variantes usan los mismos casos completos del test.",
                "Los pesos, límites e histéresis proceden de la aprobación previa.",
                "Las diferencias no prueban causalidad absoluta.",
                "",
                "```json",
                json.dumps(
                    json_value(summaries),
                    ensure_ascii=False,
                    indent=2,
                ),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return results, summary
