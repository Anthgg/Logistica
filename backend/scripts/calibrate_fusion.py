import argparse
from datetime import datetime, timezone

from _phase9_common import (
    ensure_validation_only,
    project_path,
    read_table,
    write_json_atomic,
)

from app.ml.registry import canonical_checksum


def _combined_risk(frame, weights: dict[str, float], minimum: int):
    import numpy

    columns = [f"{name}_risk" for name in weights]
    values = frame[columns].to_numpy(dtype=float)
    output = numpy.full(len(frame), numpy.nan, dtype=float)
    for index, row in enumerate(values):
        available = numpy.isfinite(row)
        if int(available.sum()) < minimum:
            continue
        selected_weights = numpy.asarray(
            [weights[name] for name in weights], dtype=float
        )[available]
        total = float(selected_weights.sum())
        if total <= 0:
            continue
        output[index] = float(
            (row[available] * selected_weights).sum() / total
        )
    return output


def _metrics(labels, risks) -> tuple[dict[str, float], float]:
    import numpy
    from sklearn.metrics import (
        accuracy_score,
        average_precision_score,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )

    candidates = numpy.unique(
        numpy.append(
            risks,
            numpy.nextafter(float(numpy.max(risks)), numpy.inf),
        )
    )
    best: tuple[float, float, float] | None = None
    best_threshold = 0.0
    best_metrics: dict[str, float] = {}
    eer_candidates: list[tuple[float, float, float]] = []
    for threshold in candidates:
        predictions = (risks >= threshold).astype(int)
        matrix = confusion_matrix(labels, predictions, labels=[0, 1])
        true_negative, false_positive, false_negative, true_positive = (
            int(matrix[0, 0]),
            int(matrix[0, 1]),
            int(matrix[1, 0]),
            int(matrix[1, 1]),
        )
        far = false_positive / max(1, false_positive + true_negative)
        frr = false_negative / max(1, false_negative + true_positive)
        eer_candidates.append(
            (abs(far - frr), (far + frr) / 2, float(threshold))
        )
        f1 = float(f1_score(labels, predictions, zero_division=0))
        rank = (f1, -far, -abs(far - frr))
        if best is None or rank > best:
            best = rank
            best_threshold = float(threshold)
            best_metrics = {
                "accuracy": float(accuracy_score(labels, predictions)),
                "precision": float(
                    precision_score(labels, predictions, zero_division=0)
                ),
                "recall": float(
                    recall_score(labels, predictions, zero_division=0)
                ),
                "f1": f1,
                "far": float(far),
                "frr": float(frr),
                "roc_auc": float(roc_auc_score(labels, risks)),
                "pr_auc": float(
                    average_precision_score(labels, risks)
                ),
                "true_negative": float(true_negative),
                "false_positive": float(false_positive),
                "false_negative": float(false_negative),
                "true_positive": float(true_positive),
            }
    _, eer, eer_threshold = min(eer_candidates)
    best_metrics["eer"] = float(eer)
    best_metrics["eer_threshold"] = float(eer_threshold)
    return best_metrics, best_threshold


def _estimated_latency(frame, valid) -> float:
    import numpy

    columns = [
        "facial_latency_ms",
        "pad_latency_ms",
        "behavioral_latency_ms",
    ]
    values = frame[columns].to_numpy(dtype=float)
    selected = values[valid]
    finite = numpy.isfinite(selected)
    row_latency = numpy.where(finite, selected, -numpy.inf).max(axis=1)
    measurable = numpy.isfinite(row_latency)
    if not measurable.any():
        raise SystemExit(
            "Validation no contiene latencias medibles para la fusión."
        )
    return float(row_latency[measurable].mean())


def _weight_grid(step: float):
    units = round(1 / step)
    if units <= 0 or abs(units * step - 1) > 1e-9:
        raise SystemExit("--weight-step debe dividir exactamente 1.")
    for facial in range(units + 1):
        for pad in range(units - facial + 1):
            behavioral = units - facial - pad
            yield {
                "facial": facial / units,
                "pad": pad / units,
                "behavioral": behavioral / units,
            }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument(
        "--input",
        default=(
            "data/reports/integration/"
            "normalized_validation_predictions.parquet"
        ),
    )
    parser.add_argument(
        "--output", default="models/fusion/fusion_config.json"
    )
    parser.add_argument("--weight-step", type=float, default=0.05)
    parser.add_argument(
        "--f1-tolerance",
        type=float,
        default=0.02,
        help=(
            "Caída máxima de F1 frente al mejor candidato para priorizar FAR."
        ),
    )
    parser.add_argument(
        "--minimum-components", type=int, default=2, choices=(1, 2, 3)
    )
    arguments = parser.parse_args()
    frame = read_table(project_path(arguments.input))
    required = {
        "sample_id",
        "label",
        "split",
        "dataset_version",
        "facial_risk",
        "pad_risk",
        "behavioral_risk",
        "facial_latency_ms",
        "pad_latency_ms",
        "behavioral_latency_ms",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise SystemExit(f"Faltan columnas: {missing}")
    ensure_validation_only(frame)
    if set(frame["dataset_version"].astype(str)) != {
        arguments.dataset_version
    }:
        raise SystemExit("dataset_version no coincide con la solicitud.")
    labels = frame["label"].astype(int).to_numpy()
    if set(labels) != {0, 1}:
        raise SystemExit("La fusión requiere clases confiable y riesgosa.")
    if not 0 <= arguments.f1_tolerance <= 1:
        raise SystemExit("--f1-tolerance debe estar entre 0 y 1.")
    rows: list[dict[str, float]] = []
    for weights in _weight_grid(arguments.weight_step):
        combined = _combined_risk(
            frame, weights, arguments.minimum_components
        )
        valid = combined == combined
        if int(valid.sum()) < 2 or set(labels[valid]) != {0, 1}:
            continue
        metrics, threshold = _metrics(labels[valid], combined[valid])
        rows.append(
            {
                **{f"{name}_weight": value for name, value in weights.items()},
                **metrics,
                "threshold": threshold,
                "available_fraction": float(valid.mean()),
                "estimated_latency_ms": _estimated_latency(frame, valid),
            }
        )
    if not rows:
        raise SystemExit("No existen combinaciones de fusión evaluables.")
    import pandas

    search = pandas.DataFrame(rows).sort_values(
        ["f1", "far", "pr_auc", "facial_weight", "pad_weight"],
        ascending=[False, True, False, False, False],
        kind="mergesort",
    )
    best_f1 = float(search["f1"].max())
    eligible = search[
        search["f1"] >= best_f1 - arguments.f1_tolerance
    ].sort_values(
        [
            "far",
            "f1",
            "estimated_latency_ms",
            "pr_auc",
            "facial_weight",
            "pad_weight",
        ],
        ascending=[True, False, True, False, False, False],
        kind="mergesort",
    )
    selected = eligible.iloc[0]
    selected_weights = {
        "facial": float(selected["facial_weight"]),
        "pad": float(selected["pad_weight"]),
        "behavioral": float(selected["behavioral_weight"]),
    }
    combined = _combined_risk(
        frame, selected_weights, arguments.minimum_components
    )
    valid = combined == combined
    safe = combined[valid & (labels == 0)]
    risky = combined[valid & (labels == 1)]
    low_max = float(pandas.Series(safe).quantile(0.75))
    medium_max = float(selected["threshold"])
    high_max = float(pandas.Series(risky).quantile(0.25))
    if not 0 <= low_max < medium_max < high_max < 1:
        raise SystemExit(
            "Validation no separa límites low/medium/high; "
            "no se escribirá una política arbitraria."
        )
    validation_metrics = {
        name: float(selected[name])
        for name in (
            "accuracy",
            "precision",
            "recall",
            "f1",
            "roc_auc",
            "pr_auc",
            "far",
            "frr",
            "eer",
            "eer_threshold",
            "available_fraction",
            "estimated_latency_ms",
        )
    }
    validation_metrics["selection_f1_tolerance"] = float(
        arguments.f1_tolerance
    )
    payload: dict[str, object] = {
        "fusion_version": "fusion-v0.1.0",
        "method": "weighted_late_fusion",
        "weights": selected_weights,
        "missing_component_strategy": (
            "renormalize_available_weights"
        ),
        "minimum_available_components": arguments.minimum_components,
        "neutral_risk": None,
        "risk_thresholds": {
            "low_max": low_max,
            "medium_max": medium_max,
            "high_max": high_max,
        },
        "validation_metrics": validation_metrics,
        "dataset_version": arguments.dataset_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    payload["checksum"] = canonical_checksum(payload)
    report = project_path(
        "data/reports/integration/fusion_validation_search.parquet"
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    search["selected"] = search.index == selected.name
    search.to_parquet(report, index=False)
    write_json_atomic(project_path(arguments.output), payload)
    print(
        "Fusión calibrada con validation | "
        f"combinations={len(search)} checksum={payload['checksum']}"
    )


if __name__ == "__main__":
    main()
