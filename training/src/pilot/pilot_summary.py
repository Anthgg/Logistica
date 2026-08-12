import pandas as pd


def build_session_summary(audit: pd.DataFrame) -> pd.DataFrame:
    if audit.empty:
        return pd.DataFrame(
            columns=[
                "participant_id",
                "sessions",
                "valid_sessions",
                "duration_seconds",
                "facial_captures",
                "keyboard_events",
                "mouse_events",
            ]
        )
    grouped = audit.groupby("participant_id", dropna=False)
    return grouped.agg(
        sessions=("session_id", "nunique"),
        valid_sessions=("session_valid", "sum"),
        duration_seconds=("duration_seconds", "sum"),
        facial_captures=("facial_capture_count", "sum"),
        keyboard_events=("keyboard_event_count", "sum"),
        mouse_events=("mouse_event_count", "sum"),
    ).reset_index()
