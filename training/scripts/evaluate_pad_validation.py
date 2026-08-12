import argparse
import json

import pandas as pd

from _training import load_bundles
from src.pad.evaluator import evaluate_pad_validation
from src.pipelines.context import training_paths


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenera métricas PAD desde predicciones de validation."
    )
    parser.add_argument("--dataset-version", default="pilot-v0.1.0")
    parser.add_argument("--config-dir")
    arguments = parser.parse_args()
    _, bundle = load_bundles(arguments.config_dir, arguments.dataset_version, None)
    paths = training_paths(bundle)
    report_dir = paths.reports_root / "pad"
    predictions = pd.read_parquet(report_dir / "pad_validation_predictions.parquet")
    threshold = json.loads(
        (
            paths.models_root
            / "pad"
            / "thresholds"
            / f"{bundle.pad.model_version}.json"
        ).read_text(encoding="utf-8")
    )
    metrics = evaluate_pad_validation(
        predictions.drop(columns=["attack_probability", "predicted_label"], errors="ignore"),
        predictions["attack_probability"].to_numpy(),
        threshold_payload=threshold,
        report_dir=report_dir,
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
