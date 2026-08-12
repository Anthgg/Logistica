from __future__ import annotations

import _bootstrap

import pandas as pd

from evaluation.scripts._stage_support import prediction_parser
from evaluation.src.common.config import load_config
from evaluation.src.comparison.evaluator import compare_pretest_posttest


def main() -> None:
    arguments = prediction_parser(
        "Genera la comparación pareada pretest/postest por sesión."
    ).parse_args()
    compare_pretest_posttest(
        pd.read_parquet(arguments.predictions),
        load_config(arguments.config),
    )


if __name__ == "__main__":
    main()
