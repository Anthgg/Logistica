import numpy as np
import pandas as pd

from src.behavioral.feature_validator import validate_features
from src.behavioral.user_dataset import build_user_dataset


def _frame(training_config):
    rows = []
    for participant in ("P1", "P2"):
        for split, count in (("train", 25), ("validation", 8)):
            for index in range(count):
                row = {
                    "participant_id": participant,
                    "session_id": f"{participant}-{split}",
                    "window_id": f"{participant}-{split}-{index}",
                    "operator_label": "legitimate",
                    "split": split,
                }
                row.update(
                    {
                        name: float(index + position + (0 if participant == "P1" else 2))
                        for position, name in enumerate(
                            training_config.behavioral.feature_columns
                        )
                    }
                )
                rows.append(row)
    return pd.DataFrame(rows)


def test_validates_features_and_builds_user_impostors(training_config) -> None:
    frame = _frame(training_config)
    result = validate_features(frame, training_config.behavioral)
    assert result.valid
    dataset = build_user_dataset(frame, "P1", training_config.behavioral)
    assert dataset is not None
    assert set(dataset.train["participant_id"]) == {"P1"}
    assert set(dataset.validation_impostor["participant_id"]) == {"P2"}


def test_rejects_nan_and_infinite_features(training_config) -> None:
    frame = _frame(training_config)
    first = training_config.behavioral.feature_columns[0]
    second = training_config.behavioral.feature_columns[1]
    frame.loc[0, first] = np.nan
    frame.loc[1, second] = np.inf
    result = validate_features(frame, training_config.behavioral)
    assert not result.valid
    assert first in result.nan_columns
    assert second in result.infinite_columns
