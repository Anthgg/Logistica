from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from src.common.config import BehavioralTrainingConfig
from src.common.serialization import configuration_checksum


@dataclass(frozen=True)
class FeatureValidationResult:
    valid: bool
    missing_columns: list[str]
    non_numeric_columns: list[str]
    nan_columns: list[str]
    infinite_columns: list[str]
    zero_variance_columns: list[str]
    extreme_value_columns: list[str]
    statistics: dict[str, dict[str, float | None]]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_features(
    frame: pd.DataFrame, config: BehavioralTrainingConfig
) -> FeatureValidationResult:
    missing = sorted(set(config.feature_columns) - set(frame.columns))
    if missing:
        return FeatureValidationResult(
            valid=False,
            missing_columns=missing,
            non_numeric_columns=[],
            nan_columns=[],
            infinite_columns=[],
            zero_variance_columns=[],
            extreme_value_columns=[],
            statistics={},
        )
    numeric = frame[config.feature_columns].apply(pd.to_numeric, errors="coerce")
    non_numeric = [
        column
        for column in config.feature_columns
        if numeric[column].isna().sum() > frame[column].isna().sum()
    ]
    nan_columns = [column for column in config.feature_columns if numeric[column].isna().any()]
    infinite_columns = [
        column
        for column in config.feature_columns
        if numeric[column]
        .map(lambda value: math.isinf(float(value)) if pd.notna(value) else False)
        .any()
    ]
    zero_variance = [
        column
        for column in config.feature_columns
        if numeric[column].dropna().nunique() <= 1
    ]
    statistics: dict[str, dict[str, float | None]] = {}
    extreme: list[str] = []
    for column in config.feature_columns:
        series = numeric[column].replace([float("inf"), float("-inf")], pd.NA).dropna()
        if series.empty:
            statistics[column] = {
                "count": 0.0,
                "mean": None,
                "std": None,
                "minimum": None,
                "maximum": None,
            }
            continue
        first = float(series.quantile(0.25))
        third = float(series.quantile(0.75))
        spread = third - first
        lower = first - 10 * spread
        upper = third + 10 * spread
        if spread > 0 and ((series < lower) | (series > upper)).any():
            extreme.append(column)
        statistics[column] = {
            "count": float(series.count()),
            "mean": float(series.mean()),
            "std": float(series.std(ddof=0)),
            "minimum": float(series.min()),
            "maximum": float(series.max()),
        }
    return FeatureValidationResult(
        valid=not (missing or non_numeric or nan_columns or infinite_columns),
        missing_columns=missing,
        non_numeric_columns=non_numeric,
        nan_columns=nan_columns,
        infinite_columns=infinite_columns,
        zero_variance_columns=zero_variance,
        extreme_value_columns=sorted(extreme),
        statistics=statistics,
    )


def build_feature_schema(config: BehavioralTrainingConfig) -> dict[str, object]:
    features = []
    for name in config.feature_columns:
        if name.endswith("_ms") or name.startswith(("dwell_", "flight_", "interval_")):
            unit = "milliseconds"
        elif name.endswith("_ratio") or name.startswith("normalized_"):
            unit = "ratio"
        elif "count" in name:
            unit = "count"
        elif "rate" in name:
            unit = "events_per_second"
        else:
            unit = "derived_numeric"
        features.append(
            {
                "name": name,
                "position": len(features),
                "dtype": "float64",
                "unit": unit,
                "allowed": "finite",
                "missing_value_treatment": config.missing_value_strategy,
            }
        )
    payload: dict[str, object] = {
        "version": "behavioral-feature-schema-v0.1.0",
        "dataset_version": config.dataset_version,
        "feature_count": len(features),
        "features": features,
        "excluded_features": [],
    }
    payload["checksum"] = configuration_checksum(payload)
    return payload
