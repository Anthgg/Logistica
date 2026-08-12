import argparse
import math
from datetime import datetime, timezone
from pathlib import Path

from _phase9_common import (
    ensure_validation_only,
    project_path,
    read_table,
    write_json_atomic,
)

from app.ml.fusion_runtime import ScoreNormalizationConfig
from app.ml.registry import canonical_checksum
from app.services.score_normalization_service import (
    ScoreNormalizationService,
)

COMPONENT_DIRECTIONS = {
    "facial": "decreasing",
    "pad": "increasing",
    "behavioral": "increasing",
}


def _component_payload(
    group,
    *,
    component: str,
    dataset_version: str,
) -> dict[str, object]:
    scores = group["score"].astype(float)
    if not scores.map(math.isfinite).all():
        raise SystemExit(f"{component} contiene NaN o infinito.")
    thresholds = group["threshold"].dropna().astype(float).unique()
    if len(thresholds) != 1:
        raise SystemExit(
            f"{component} debe declarar un único threshold de validation."
        )
    threshold = float(thresholds[0])
    lower = float(scores.quantile(0.01))
    upper = float(scores.quantile(0.99))
    if not lower < threshold < upper:
        lower = float(scores.min())
        upper = float(scores.max())
    if not lower < threshold < upper:
        raise SystemExit(
            f"{component} no permite calibrar límites alrededor del umbral."
        )
    labels = group["label"].astype(int)
    if set(labels) != {0, 1}:
        raise SystemExit(
            f"{component} requiere ejemplos confiables y riesgosos."
        )
    return {
        "method": "piecewise_linear",
        "lower_bound": lower,
        "upper_bound": upper,
        "threshold": threshold,
        "clipping": True,
        "risk_direction": COMPONENT_DIRECTIONS[component],
        "dataset_version": dataset_version,
        "validation_statistics": {
            "minimum": float(scores.min()),
            "maximum": float(scores.max()),
            "median": float(scores.median()),
            "quantile_0.01": float(scores.quantile(0.01)),
            "quantile_0.99": float(scores.quantile(0.99)),
            "trusted_count": float((labels == 0).sum()),
            "risky_count": float((labels == 1).sum()),
        },
    }


def _write_plots(frame, output_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("Matplotlib es obligatorio para los gráficos.") from exc
    output_dir.mkdir(parents=True, exist_ok=True)
    for component, group in frame.groupby("component", sort=True):
        figure, axis = plt.subplots(figsize=(8, 5))
        for label, label_group in group.groupby("label", sort=True):
            axis.hist(
                label_group["score"].astype(float),
                bins=30,
                alpha=0.55,
                label=f"label={int(label)}",
            )
        axis.set_title(f"Validation raw scores — {component}")
        axis.set_xlabel("score")
        axis.set_ylabel("count")
        axis.legend()
        figure.tight_layout()
        figure.savefig(
            output_dir / f"{component}_normalization_validation.png",
            dpi=160,
        )
        plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument(
        "--input",
        default=(
            "data/reports/integration/"
            "component_validation_predictions.parquet"
        ),
    )
    parser.add_argument(
        "--output",
        default="models/fusion/score_normalization.json",
    )
    parser.add_argument(
        "--normalized-output",
        default=(
            "data/reports/integration/"
            "normalized_validation_predictions.parquet"
        ),
    )
    arguments = parser.parse_args()
    source = read_table(project_path(arguments.input))
    required = {
        "sample_id",
        "split",
        "dataset_version",
        "component",
        "score",
        "threshold",
        "label",
        "latency_ms",
    }
    missing = sorted(required - set(source.columns))
    if missing:
        raise SystemExit(f"Faltan columnas: {missing}")
    ensure_validation_only(source)
    versions = set(source["dataset_version"].astype(str))
    if versions != {arguments.dataset_version}:
        raise SystemExit("dataset_version no coincide con la solicitud.")
    components = set(source["component"].astype(str))
    if components != set(COMPONENT_DIRECTIONS):
        raise SystemExit(
            "Se requieren scores facial, pad y behavioral de validation."
        )
    component_payloads = {
        component: _component_payload(
            group,
            component=str(component),
            dataset_version=arguments.dataset_version,
        )
        for component, group in source.groupby("component", sort=True)
    }
    payload: dict[str, object] = {
        "normalization_version": "score-normalization-v0.1.0",
        "components": component_payloads,
        "dataset_version": arguments.dataset_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    payload["checksum"] = canonical_checksum(payload)
    output = project_path(arguments.output)
    config = ScoreNormalizationConfig.model_validate(payload)
    normalizer = ScoreNormalizationService(config)
    normalized = source.copy()
    normalized["risk"] = [
        normalizer.normalize(str(component), float(score))
        for component, score in zip(
            normalized["component"],
            normalized["score"],
            strict=True,
        )
    ]
    latencies = normalized["latency_ms"].astype(float)
    if (
        not latencies.map(math.isfinite).all()
        or (latencies < 0).any()
    ):
        raise SystemExit(
            "latency_ms debe contener valores finitos y no negativos."
        )
    duplicate = normalized.duplicated(
        subset=["sample_id", "component"], keep=False
    )
    if duplicate.any():
        raise SystemExit(
            "Existe más de un score por muestra y componente."
        )
    metadata_columns = ["label", "split", "dataset_version"]
    inconsistent = (
        normalized.groupby("sample_id")[metadata_columns]
        .nunique(dropna=False)
        .gt(1)
        .any(axis=1)
    )
    if inconsistent.any():
        raise SystemExit(
            "Una muestra tiene metadatos incompatibles entre componentes."
        )
    metadata = normalized[
        ["sample_id", *metadata_columns]
    ].drop_duplicates()
    risks = normalized.pivot(
        index="sample_id", columns="component", values="risk"
    ).rename(columns=lambda value: f"{value}_risk")
    latency = normalized.pivot(
        index="sample_id", columns="component", values="latency_ms"
    ).rename(columns=lambda value: f"{value}_latency_ms")
    wide = (
        metadata.merge(risks, on="sample_id", how="inner")
        .merge(latency, on="sample_id", how="inner")
    )
    normalized_output = project_path(arguments.normalized_output)
    normalized_output.parent.mkdir(parents=True, exist_ok=True)
    wide.to_parquet(normalized_output, index=False)
    _write_plots(
        source,
        project_path("data/reports/integration/normalization_plots"),
    )
    write_json_atomic(output, payload)
    print(
        "Normalización calibrada con validation | "
        f"rows={len(source)} checksum={payload['checksum']}"
    )


if __name__ == "__main__":
    main()
