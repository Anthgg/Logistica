import pandas as pd

from src.datasets.split_strategy import assign_group_splits


def _rows():
    return pd.DataFrame(
        [
            {
                "participant_id": "p1",
                "session_id": f"s{session}",
                "segment_id": f"g{session}",
                "window_id": f"w{session}-{window}",
            }
            for session in range(6)
            for window in range(3)
        ]
    )


def test_split_is_deterministic(config):
    first = assign_group_splits(
        _rows(),
        group_column="session_id",
        ratios=config.pipeline.split_ratios,
        random_seed=42,
    )
    second = assign_group_splits(
        _rows(),
        group_column="session_id",
        ratios=config.pipeline.split_ratios,
        random_seed=42,
    )
    assert first["split"].tolist() == second["split"].tolist()


def test_sessions_are_not_divided(config):
    result = assign_group_splits(
        _rows(),
        group_column="session_id",
        ratios=config.pipeline.split_ratios,
        random_seed=42,
    )
    assert result.groupby("session_id")["split"].nunique().max() == 1


def test_overlapping_windows_stay_with_segment(config):
    result = assign_group_splits(
        _rows(),
        group_column="segment_id",
        ratios=config.pipeline.split_ratios,
        random_seed=42,
    )
    assert result.groupby("segment_id")["split"].nunique().max() == 1
