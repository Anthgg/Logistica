from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.common.metrics import binary_metrics, threshold_candidates
from src.common.serialization import write_json_atomic


def _save_distribution(values: np.ndarray, title: str, path: Path) -> None:
    figure = plt.figure()
    plt.hist(values, bins=min(30, max(5, len(values))))
    plt.title(title)
    plt.xlabel("Similitud coseno")
    plt.ylabel("Frecuencia")
    figure.savefig(path, bbox_inches="tight")
    plt.close(figure)


def evaluate_facial_validation(
    pairs: pd.DataFrame,
    *,
    threshold_payload: dict[str, object],
    report_dir: Path,
) -> dict[str, object]:
    report_dir.mkdir(parents=True, exist_ok=True)
    figures = report_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    threshold = float(threshold_payload["selected_threshold"])
    labels = pairs["label"].astype(int).to_numpy()
    scores = pairs["similarity"].astype(float).to_numpy()
    metrics = binary_metrics(labels, scores, threshold)
    metrics.update(
        {
            "selected_threshold": threshold,
            "far": float(threshold_payload["validation_far"]),
            "frr": float(threshold_payload["validation_frr"]),
            "eer": float(threshold_payload["validation_eer"]),
            "pair_count": int(len(pairs)),
            "genuine_pair_count": int((labels == 1).sum()),
            "impostor_pair_count": int((labels == 0).sum()),
            "test_rows_used": 0,
        }
    )
    predictions = pairs.copy()
    predictions["predicted_genuine"] = scores >= threshold
    predictions.to_parquet(report_dir / "facial_validation_predictions.parquet", index=False)
    write_json_atomic(report_dir / "facial_validation_metrics.json", metrics)
    _save_distribution(
        scores[labels == 1],
        "Distribución de similitudes genuinas",
        figures / "genuine_similarity_distribution.png",
    )
    _save_distribution(
        scores[labels == 0],
        "Distribución de similitudes impostoras",
        figures / "impostor_similarity_distribution.png",
    )
    roc = metrics.get("roc")
    if isinstance(roc, dict):
        figure = plt.figure()
        plt.plot(roc["false_positive_rate"], roc["true_positive_rate"])
        plt.xlabel("FAR")
        plt.ylabel("Tasa de verdaderos positivos")
        plt.title("Curva ROC facial")
        figure.savefig(figures / "facial_roc.png", bbox_inches="tight")
        plt.close(figure)
    candidates = threshold_candidates(labels, scores)
    figure = plt.figure()
    plt.plot([item.threshold for item in candidates], [item.far for item in candidates], label="FAR")
    plt.plot([item.threshold for item in candidates], [item.frr for item in candidates], label="FRR")
    plt.xlabel("Umbral")
    plt.ylabel("Tasa")
    plt.title("FAR y FRR por umbral")
    plt.legend()
    figure.savefig(figures / "facial_far_frr.png", bbox_inches="tight")
    plt.close(figure)
    (report_dir / "facial_report.md").write_text(
        "\n".join(
            [
                "# Validación facial ArcFace",
                "",
                "Las métricas se calcularon exclusivamente con pares de validation.",
                "El conjunto test congelado no fue leído para entrenamiento ni calibración.",
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
