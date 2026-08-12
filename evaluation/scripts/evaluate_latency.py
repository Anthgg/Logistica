from __future__ import annotations

import _bootstrap

import pandas as pd

from evaluation.scripts._stage_support import prediction_parser
from evaluation.src.common.config import load_config
from evaluation.src.performance.evaluator import evaluate_performance


def main() -> None:
    arguments = prediction_parser(
        "Resume las latencias observadas en la pasada autorizada."
    ).parse_args()
    evaluate_performance(
        pd.read_parquet(arguments.predictions),
        load_config(arguments.config),
    )


if __name__ == "__main__":
    main()
