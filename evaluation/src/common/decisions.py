from __future__ import annotations

from typing import Mapping, cast

import numpy as np
import pandas as pd

from evaluation.src.common.config import FinalEvaluationConfig
from evaluation.src.common.io import JsonValue, read_json


def approved_confirmation_count(config: FinalEvaluationConfig) -> int:
    approval = read_json(config.paths.integration_approval)
    value = approval.get("hysteresis")
    if not isinstance(value, dict):
        raise ValueError("La aprobación no contiene histéresis.")
    hysteresis = cast(Mapping[str, JsonValue], value)
    count = hysteresis.get("positive_confirmation_count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("positive_confirmation_count no está aprobado.")
    return count


def confirmed_predictions(
    frame: pd.DataFrame,
    raw_predictions: np.ndarray,
    *,
    session_column: str,
    timestamp_column: str,
    confirmation_count: int,
) -> np.ndarray:
    raw = np.asarray(raw_predictions, dtype=np.int8).reshape(-1)
    if len(raw) != len(frame):
        raise ValueError("Las decisiones y filas no tienen igual longitud.")
    if confirmation_count == 1:
        return raw.copy()
    indexed = frame.reset_index(drop=True).copy()
    indexed["_position"] = np.arange(len(indexed))
    if session_column not in indexed:
        raise ValueError("La histéresis requiere session_id.")
    if timestamp_column in indexed:
        indexed["_time"] = pd.to_datetime(
            indexed[timestamp_column], utc=True, errors="coerce"
        )
        if indexed["_time"].isna().any():
            raise ValueError(
                "La histéresis requiere timestamps válidos."
            )
    else:
        indexed["_time"] = indexed["_position"]
    result = np.zeros(len(indexed), dtype=np.int8)
    for _, group in indexed.groupby(session_column, dropna=False):
        consecutive = 0
        for position in group.sort_values("_time")["_position"].astype(int):
            consecutive = consecutive + 1 if raw[position] == 1 else 0
            if consecutive >= confirmation_count:
                result[position] = 1
    return result
