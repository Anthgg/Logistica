from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.common.metrics import binary_metrics, threshold_candidates
from src.common.serialization import write_json_atomic


def evaluate_participant(
    genuine_errors: np.ndarray,
    impostor_errors: np.ndarray,
    *,
    threshold_payload: dict[str, object],
    output_dir: Path,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = output_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    labels = np.concatenate(
        [np.ones(len(genuine_errors), dtype=int), np.zeros(len(impostor_errors), dtype=int)]
    )
    errors = np.concatenate([genuine_errors, impostor_errors]).astype(float)
    threshold = float(threshold_payload["threshold"])
    metrics = binary_metrics(labels, errors, threshold, positive_direction="lower")
    metrics.update(
        {
            "participant_id": threshold_payload["participant_id"],
            "threshold": threshold,
            "far": threshold_payload["validation_far"],
            "frr": threshold_payload["validation_frr"],
            "eer": threshold_payload["validation_eer"],
            "genuine_count": int(len(genuine_errors)),
            "impostor_count": int(len(impostor_errors)),
            "test_rows_used": 0,
        }
    )
    write_json_atomic(output_dir / "validation_metrics.json", metrics)
    for values, title, filename in (
        (genuine_errors, "MSE de ventanas legítimas", "genuine_mse.png"),
        (impostor_errors, "MSE de ventanas impostoras", "impostor_mse.png"),
    ):
        figure = plt.figure()
        plt.hist(values, bins=min(30, max(5, len(values))))
        plt.title(title)
        plt.xlabel("Error de reconstrucción MSE")
        plt.ylabel("Frecuencia")
        figure.savefig(figures / filename, bbox_inches="tight")
        plt.close(figure)
    candidates = threshold_candidates(labels, errors, positive_direction="lower")
    figure = plt.figure()
    plt.plot([item.threshold for item in candidates], [item.far for item in candidates], label="FAR")
    plt.plot([item.threshold for item in candidates], [item.frr for item in candidates], label="FRR")
    plt.xlabel("Umbral MSE")
    plt.ylabel("Tasa")
    plt.title("FAR y FRR conductual")
    plt.legend()
    figure.savefig(figures / "behavioral_far_frr.png", bbox_inches="tight")
    plt.close(figure)
    return metrics


def aggregate_behavioral_metrics(
    metrics: list[dict[str, object]],
    *,
    failed_participants: list[dict[str, object]],
    output_dir: Path,
) -> dict[str, object]:
    names = ("accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc", "far", "frr", "eer")
    aggregates: dict[str, object] = {}
    for name in names:
        values = np.asarray(
            [float(item[name]) for item in metrics if item.get(name) is not None],
            dtype=float,
        )
        aggregates[name] = (
            {
                "mean": float(np.mean(values)),
                "median": float(np.median(values)),
                "std": float(np.std(values)),
                "minimum": float(np.min(values)),
                "maximum": float(np.max(values)),
            }
            if len(values)
            else None
        )
    summary = {
        "trained_participant_count": len(metrics),
        "failed_participant_count": len(failed_participants),
        "failed_participants": failed_participants,
        "macro_statistics": aggregates,
        "test_rows_used": 0,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(output_dir / "behavioral_summary.json", summary)
    (output_dir / "behavioral_report.md").write_text(
        "\n".join(
            [
                "# Validación conductual por participante",
                "",
                "Los scalers y autoencoders se ajustaron únicamente con train legítimo.",
                "Los umbrales se calibraron únicamente con validation.",
                "El conjunto test congelado no fue utilizado.",
                "",
                "```json",
                json.dumps(summary, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return summary
