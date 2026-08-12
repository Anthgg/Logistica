from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap

import pandas as pd

from evaluation.src.common.config import load_config
from evaluation.src.statistics.analysis import run_statistical_analysis


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ejecuta estadística sobre artefactos ya autorizados."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("evaluation/configs/final_evaluation.yaml"),
    )
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--ablation", type=Path, required=True)
    parser.add_argument("--latency", type=Path, required=True)
    arguments = parser.parse_args()
    run_statistical_analysis(
        pd.read_parquet(arguments.predictions),
        pd.read_parquet(arguments.comparison),
        pd.read_parquet(arguments.ablation),
        pd.read_parquet(arguments.latency),
        load_config(arguments.config),
    )


if __name__ == "__main__":
    main()
