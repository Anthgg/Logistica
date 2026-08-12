from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import pandas as pd

from evaluation.src.common.config import FinalEvaluationConfig, load_config
from evaluation.src.common.io import JsonValue

MetricEvaluator = Callable[
    [pd.DataFrame, FinalEvaluationConfig],
    dict[str, JsonValue],
]


def prediction_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("evaluation/configs/final_evaluation.yaml"),
    )
    parser.add_argument("--predictions", type=Path, required=True)
    return parser


def run_metric_stage(
    evaluator: MetricEvaluator,
    description: str,
) -> None:
    arguments = prediction_parser(description).parse_args()
    config = load_config(arguments.config)
    predictions = pd.read_parquet(arguments.predictions)
    evaluator(predictions, config)
