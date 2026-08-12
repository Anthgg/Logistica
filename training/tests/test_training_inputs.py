from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.common.validation import (
    TrainingInputError,
    development_rows,
    require_columns,
)


def test_rejects_manifest_without_required_columns() -> None:
    with pytest.raises(TrainingInputError, match="faltan columnas"):
        require_columns(pd.DataFrame({"split": ["train"]}), {"split", "checksum"}, "demo")


def test_development_rows_never_returns_test() -> None:
    frame = pd.DataFrame(
        {
            "dataset_version": ["pilot-v0.1.0"] * 3,
            "quality_status": ["accepted"] * 3,
            "split": ["train", "validation", "test"],
            "value": [1, 2, 3],
        }
    )
    selected = development_rows(frame, dataset_version="pilot-v0.1.0")
    assert selected["split"].tolist() == ["train", "validation"]
    assert 3 not in selected["value"].tolist()


def test_development_rows_rejects_unknown_split_and_version() -> None:
    unknown = pd.DataFrame(
        {
            "dataset_version": ["pilot-v0.1.0"],
            "quality_status": ["accepted"],
            "split": ["holdout"],
        }
    )
    with pytest.raises(TrainingInputError, match="desconocidas"):
        development_rows(unknown, dataset_version="pilot-v0.1.0")
    wrong_version = unknown.assign(split="train", dataset_version="other")
    with pytest.raises(TrainingInputError, match="dataset_version"):
        development_rows(wrong_version, dataset_version="pilot-v0.1.0")


def test_nonfinite_values_are_detectable() -> None:
    matrix = np.asarray([[1.0, np.inf]])
    assert not np.isfinite(matrix).all()
