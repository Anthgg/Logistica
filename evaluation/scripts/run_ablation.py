from __future__ import annotations

import _bootstrap

import pandas as pd

from evaluation.scripts._stage_support import prediction_parser
from evaluation.src.ablation.evaluator import evaluate_ablation
from evaluation.src.common.config import load_config


def main() -> None:
    arguments = prediction_parser(
        "Ejecuta únicamente las variantes de ablación aprobadas."
    ).parse_args()
    evaluate_ablation(
        pd.read_parquet(arguments.predictions),
        load_config(arguments.config),
    )


if __name__ == "__main__":
    main()
