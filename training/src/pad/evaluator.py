from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.common.metrics import binary_metrics, select_minimum_acer
from src.common.serialization import write_json_atomic


def _group_metrics(
    frame: pd.DataFrame, column: str, threshold: float
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for value, group in frame.groupby(column, dropna=False, sort=True):
        labels = group["label"].astype(int).to_numpy()
        probabilities = group["attack_probability"].astype(float).to_numpy()
        metrics = binary_metrics(labels, probabilities, threshold)
        rows.append(
            {
                column: None if pd.isna(value) else str(value),
                "count": int(len(group)),
                **{key: result for key, result in metrics.items() if key != "roc"},
            }
        )
    return rows


def evaluate_pad_validation(
    validation_frame: pd.DataFrame,
    probabilities: np.ndarray,
    *,
    threshold_payload: dict[str, object],
    report_dir: Path,
) -> dict[str, object]:
    if len(validation_frame) != len(probabilities):
        raise ValueError("La cantidad de predicciones PAD no coincide con validation.")
    report_dir.mkdir(parents=True, exist_ok=True)
    figures = report_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    predictions = validation_frame.drop(columns=["_image_path"], errors="ignore").copy()
    predictions["attack_probability"] = probabilities.astype(float)
    threshold = float(threshold_payload["selected_threshold"])
    predictions["predicted_label"] = np.where(
        predictions["attack_probability"] >= threshold, "attack", "bona_fide"
    )
    predictions.to_parquet(report_dir / "pad_validation_predictions.parquet", index=False)
    labels = predictions["label"].astype(int).to_numpy()
    metrics = binary_metrics(labels, probabilities, threshold)
    _, apcer, bpcer, acer = select_minimum_acer(labels, probabilities)
    metrics.update(
        {
            "selected_threshold": threshold,
            "apcer": float(threshold_payload["validation_apcer"]),
            "bpcer": float(threshold_payload["validation_bpcer"]),
            "acer": float(threshold_payload["validation_acer"]),
            "minimum_acer_reference": acer,
            "by_attack_type": _group_metrics(predictions, "attack_type", threshold),
            "by_participant": _group_metrics(predictions, "participant_id", threshold),
            "by_session": _group_metrics(predictions, "session_id", threshold),
            "test_rows_used": 0,
        }
    )
    if "source_device" in predictions:
        metrics["by_source_device"] = _group_metrics(
            predictions, "source_device", threshold
        )
    write_json_atomic(report_dir / "pad_validation_metrics.json", metrics)
    for label, title, filename in (
        (0, "Probabilidades bona fide", "bona_fide_probabilities.png"),
        (1, "Probabilidades de ataque", "attack_probabilities.png"),
    ):
        figure = plt.figure()
        values = probabilities[labels == label]
        plt.hist(values, bins=min(30, max(5, len(values))))
        plt.title(title)
        plt.xlabel("Probabilidad de ataque")
        plt.ylabel("Frecuencia")
        figure.savefig(figures / filename, bbox_inches="tight")
        plt.close(figure)
    (report_dir / "pad_report.md").write_text(
        "\n".join(
            [
                "# Validación MobileNetV2 PAD",
                "",
                "Evaluación calculada exclusivamente sobre validation.",
                "",
                "```json",
                json.dumps(metrics, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return metrics
