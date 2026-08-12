import pandas as pd
import numpy as np


def facial_quality_table(quality: pd.DataFrame) -> pd.DataFrame:
    columns = ["quality_status", "reason", "count"]
    if quality.empty:
        return pd.DataFrame(columns=columns)
    rows: list[dict[str, object]] = []
    for status, count in quality.groupby("quality_status", dropna=False).size().items():
        rows.append(
            {
                "quality_status": str(status),
                "reason": "ALL",
                "count": int(count),
            }
        )
    for reasons in quality.get(
        "rejection_reasons", pd.Series(dtype=object)
    ).dropna():
        if not isinstance(reasons, list):
            continue
        for reason in reasons:
            rows.append(
                {
                    "quality_status": "rejected",
                    "reason": str(reason),
                    "count": 1,
                }
            )
    result = pd.DataFrame(rows, columns=columns)
    if result.empty:
        return result
    return (
        result.groupby(["quality_status", "reason"], as_index=False)["count"]
        .sum()
        .sort_values(["quality_status", "count", "reason"], ascending=[True, False, True])
        .reset_index(drop=True)
    )


def behavioral_quality_table(
    validated_batches: pd.DataFrame,
    windows: pd.DataFrame,
) -> pd.DataFrame:
    columns = ["stage", "quality_status", "reason", "count"]
    rows: list[dict[str, object]] = []
    sources = (
        ("batch", validated_batches, "valid", "rejection_reasons"),
        ("window", windows, "quality_status", "rejection_reasons"),
    )
    for stage, frame, status_column, reason_column in sources:
        if frame.empty:
            continue
        if stage == "batch":
            statuses = frame[status_column].map(
                lambda value: "accepted" if bool(value) else "rejected"
            )
        else:
            statuses = frame[status_column].astype(str)
        for status, count in statuses.value_counts().items():
            rows.append(
                {
                    "stage": stage,
                    "quality_status": str(status),
                    "reason": "ALL",
                    "count": int(count),
                }
            )
        for reasons in frame.get(reason_column, pd.Series(dtype=object)).dropna():
            if not isinstance(reasons, list):
                continue
            for reason in reasons:
                rows.append(
                    {
                        "stage": stage,
                        "quality_status": "rejected",
                        "reason": str(reason),
                        "count": 1,
                    }
                )
    result = pd.DataFrame(rows, columns=columns)
    if result.empty:
        return result
    return (
        result.groupby(
            ["stage", "quality_status", "reason"], as_index=False
        )["count"]
        .sum()
        .sort_values(
            ["stage", "quality_status", "count", "reason"],
            ascending=[True, True, False, True],
        )
        .reset_index(drop=True)
    )


def split_distribution_table(
    manifests: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for dataset, frame in manifests.items():
        if frame.empty or "split" not in frame:
            continue
        for split, count in frame.groupby("split", dropna=False).size().items():
            rows.append(
                {
                    "dataset": dataset,
                    "split": str(split),
                    "count": int(count),
                }
            )
    return pd.DataFrame(rows, columns=["dataset", "split", "count"])


def feature_statistics_table(features: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "feature",
        "count",
        "missing",
        "missing_ratio",
        "infinite",
        "mean",
        "std",
        "minimum",
        "maximum",
        "zero_variance",
    ]
    numeric = features.select_dtypes(include=[np.number])
    rows: list[dict[str, object]] = []
    for column in numeric.columns:
        values = numeric[column].astype(float)
        finite = values[np.isfinite(values)]
        variance = float(finite.var(ddof=0)) if len(finite) else np.nan
        rows.append(
            {
                "feature": str(column),
                "count": int(len(values)),
                "missing": int(values.isna().sum()),
                "missing_ratio": (
                    float(values.isna().sum() / len(values)) if len(values) else 0.0
                ),
                "infinite": int(np.isinf(values).sum()),
                "mean": float(finite.mean()) if len(finite) else np.nan,
                "std": float(finite.std(ddof=0)) if len(finite) else np.nan,
                "minimum": float(finite.min()) if len(finite) else np.nan,
                "maximum": float(finite.max()) if len(finite) else np.nan,
                "zero_variance": bool(len(finite) and variance == 0),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def write_quality_tables(
    tables: dict[str, pd.DataFrame],
    report_root: "Path",
    *,
    dry_run: bool = False,
) -> dict[str, "Path"]:
    from pathlib import Path

    paths: dict[str, Path] = {}
    for name, frame in tables.items():
        target = Path(report_root) / f"{name}.csv"
        paths[name] = target
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            frame.to_csv(target, index=False)
    return paths
