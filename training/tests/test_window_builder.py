from copy import deepcopy
from datetime import timedelta

import pandas as pd

from src.behavioral.window_builder import build_windows


def test_windows_are_thirty_seconds(event_frame, config):
    windows = build_windows(event_frame, config.behavioral, config.protocol)
    assert set(windows["duration_seconds"]) == {30}


def test_window_stride_is_ten_seconds(event_frame, config):
    windows = build_windows(event_frame, config.behavioral, config.protocol)
    starts = sorted(windows["started_at"])
    assert (starts[1] - starts[0]).total_seconds() == 10


def test_windows_never_mix_sessions(event_frame, config):
    second = event_frame.copy()
    second["session_id"] = "session-2"
    second["participant_id"] = "participant-2"
    windows = build_windows(
        pd.concat([event_frame, second], ignore_index=True),
        config.behavioral,
        config.protocol,
    )
    assert windows.groupby("window_id")["session_id"].nunique().max() == 1


def test_windows_do_not_cross_operator_change(event_frame, config):
    change = event_frame.iloc[0]["session_started_at"] + timedelta(seconds=35)
    protocol = deepcopy(config.protocol)
    protocol.session_annotations["session-1"] = {
        "operator_change_at": change.isoformat(),
        "sample_role": "change_operator",
    }
    windows = build_windows(event_frame, config.behavioral, protocol)
    crossing = windows[
        (windows["started_at"] < change) & (windows["ended_at"] > change)
    ]
    assert crossing.empty
