import argparse
import json

from _training import load_bundles
from src.behavioral.evaluator import aggregate_behavioral_metrics
from src.pipelines.context import training_paths


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenera el resumen conductual desde métricas por participante."
    )
    parser.add_argument("--dataset-version", default="pilot-v0.1.0")
    parser.add_argument("--config-dir")
    arguments = parser.parse_args()
    _, bundle = load_bundles(arguments.config_dir, arguments.dataset_version, None)
    paths = training_paths(bundle)
    metrics = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(
            (paths.models_root / "behavioral" / "participants").glob(
                "*/*/validation_metrics.json"
            )
        )
    ]
    summary = aggregate_behavioral_metrics(
        metrics,
        failed_participants=[],
        output_dir=paths.reports_root / "behavioral",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
