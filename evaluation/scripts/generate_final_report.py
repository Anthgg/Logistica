from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap

import pandas as pd

from evaluation.src.common.config import load_config
from evaluation.src.common.io import JsonValue, read_json
from evaluation.src.reports.generator import generate_final_outputs


def _json(path: Path) -> dict[str, JsonValue]:
    return read_json(path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenera el informe desde resultados finales existentes."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("evaluation/configs/final_evaluation.yaml"),
    )
    arguments = parser.parse_args()
    config = load_config(arguments.config)
    output = config.paths.output_directory
    generate_final_outputs(
        config,
        component_metrics={
            "facial": _json(output / "facial/facial_test_metrics.json"),
            "pad": _json(output / "pad/pad_test_metrics.json"),
            "behavioral": _json(
                output / "behavioral/behavioral_test_summary.json"
            ),
            "fusion": _json(output / "fusion/fusion_test_metrics.json"),
        },
        ablation_summary=pd.read_csv(
            output / "ablation/ablation_summary.csv"
        ),
        comparison=pd.read_parquet(
            output / "comparison/pretest_posttest.parquet"
        ),
        comparison_summary=_json(
            output / "comparison/pretest_posttest_summary.json"
        ),
        latency=pd.read_parquet(
            output / "performance/latency_measurements.parquet"
        ),
        performance_summary=_json(
            output / "performance/performance_summary.json"
        ),
        statistical_tests=pd.read_csv(
            output / "statistics/statistical_tests.csv"
        ),
        confidence_intervals=pd.read_csv(
            output / "statistics/confidence_intervals.csv"
        ),
        effect_sizes=pd.read_csv(
            output / "statistics/effect_sizes.csv"
        ),
    )


if __name__ == "__main__":
    main()
