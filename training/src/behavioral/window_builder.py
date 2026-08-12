from datetime import datetime, timedelta

import pandas as pd

from src.common.config import BehavioralConfig, ProtocolConfig
from src.common.hashing import canonical_json_hash
from src.common.timestamps import ensure_utc
from src.pilot.protocol import annotation_from_record

WINDOW_COLUMNS = [
    "participant_id",
    "session_id",
    "window_id",
    "segment_id",
    "started_at",
    "ended_at",
    "duration_seconds",
    "scenario",
    "operator_label",
    "keyboard_event_count",
    "mouse_event_count",
    "activity_status",
    "quality_status",
    "rejection_reasons",
    "events",
]


def flatten_valid_batches(validated_batches: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for batch in validated_batches.to_dict(orient="records"):
        if not bool(batch.get("valid")):
            continue
        events = batch.get("events")
        if not isinstance(events, list):
            continue
        for event in events:
            if not isinstance(event, dict):
                continue
            rows.append(
                {
                    "participant_id": str(batch["participant_id"]),
                    "session_id": str(batch["session_id"]),
                    "scenario": str(batch["scenario"]),
                    "session_started_at": batch["session_started_at"],
                    "session_ended_at": batch["session_ended_at"],
                    "batch_id": str(batch["batch_id"]),
                    "identity_label": batch.get("identity_label"),
                    "sample_role": batch.get("sample_role"),
                    "operator_change_at": batch.get("operator_change_at"),
                    "presentation_label": batch.get("presentation_label"),
                    "attack_type": batch.get("attack_type"),
                    "source_device": batch.get("source_device"),
                    "pad_source_id": batch.get("pad_source_id"),
                    "annotation_status": batch.get("annotation_status"),
                    "event_id": canonical_json_hash(
                        {
                            "batch_id": batch["batch_id"],
                            "sequence_index": event.get("sequence_index"),
                            "timestamp": event.get("timestamp"),
                        }
                    ),
                    **event,
                }
            )
    return pd.DataFrame(rows)


def _idle_ratio(events: list[dict[str, object]], duration_seconds: float) -> float:
    if len(events) < 2 or duration_seconds <= 0:
        return 1.0
    timestamps = sorted(ensure_utc(str(event["timestamp"])) for event in events)
    active = sum(
        min((right - left).total_seconds(), 2.0)
        for left, right in zip(timestamps, timestamps[1:])
    )
    return max(0.0, min(1.0, 1.0 - active / duration_seconds))


def _segments(
    start: datetime,
    end: datetime,
    change: datetime | None,
) -> list[tuple[datetime, datetime, str, int]]:
    if change and start < change < end:
        return [
            (start, change, "legitimate", 0),
            (change, end, "impostor", 1),
        ]
    return [(start, end, "legitimate", 0)]


def build_windows(
    events: pd.DataFrame,
    behavioral: BehavioralConfig,
    protocol: ProtocolConfig,
) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(columns=WINDOW_COLUMNS)
    rows: list[dict[str, object]] = []
    size = timedelta(seconds=behavioral.window_size_seconds)
    stride = timedelta(seconds=behavioral.stride_seconds)
    for session_id, session_events in events.groupby("session_id", sort=True):
        session_events = session_events.copy()
        session_events["_timestamp"] = session_events["timestamp"].map(
            lambda value: ensure_utc(str(value))
        )
        session_events = session_events.sort_values(
            ["_timestamp", "sequence_index"], kind="stable"
        )
        session_start = ensure_utc(session_events.iloc[0]["session_started_at"])
        session_end_value = session_events.iloc[0]["session_ended_at"]
        session_end = (
            ensure_utc(session_end_value)
            if pd.notna(session_end_value)
            else max(session_events["_timestamp"]) + size
        )
        annotation = annotation_from_record(
            protocol,
            {
                "session_id": str(session_id),
                "identity_label": session_events.iloc[0].get("identity_label"),
                "sample_role": session_events.iloc[0].get("sample_role"),
                "operator_change_at": session_events.iloc[0].get(
                    "operator_change_at"
                ),
                "presentation_label": session_events.iloc[0].get(
                    "presentation_label"
                ),
                "attack_type": session_events.iloc[0].get("attack_type"),
                "source_device": session_events.iloc[0].get("source_device"),
                "pad_source_id": session_events.iloc[0].get("pad_source_id"),
                "annotation_status": session_events.iloc[0].get(
                    "annotation_status"
                ),
            },
        )
        for segment_start, segment_end, operator_label, segment_index in _segments(
            session_start, session_end, annotation.operator_change_at
        ):
            window_start = segment_start
            segment_id = canonical_json_hash(
                {
                    "session_id": str(session_id),
                    "segment": segment_index,
                    "start": segment_start,
                    "end": segment_end,
                }
            )
            while window_start + size <= segment_end:
                window_end = window_start + size
                selected = session_events[
                    (session_events["_timestamp"] >= window_start)
                    & (session_events["_timestamp"] < window_end)
                ]
                selected_events = selected.drop(columns=["_timestamp"]).to_dict(
                    orient="records"
                )
                keyboard_count = int((selected.get("type") == "keyboard").sum())
                mouse_count = int((selected.get("type") == "mouse").sum())
                idle_ratio = _idle_ratio(
                    selected_events, behavioral.window_size_seconds
                )
                reasons: list[str] = []
                if keyboard_count < behavioral.minimum_keyboard_events:
                    reasons.append("INSUFFICIENT_KEYBOARD_EVENTS")
                if mouse_count < behavioral.minimum_mouse_events:
                    reasons.append("INSUFFICIENT_MOUSE_EVENTS")
                if idle_ratio > behavioral.maximum_idle_ratio:
                    reasons.append("EXCESSIVE_IDLE_TIME")
                window_id = canonical_json_hash(
                    {
                        "session_id": str(session_id),
                        "segment_id": segment_id,
                        "started_at": window_start,
                        "ended_at": window_end,
                    }
                )
                rows.append(
                    {
                        "participant_id": str(
                            session_events.iloc[0]["participant_id"]
                        ),
                        "session_id": str(session_id),
                        "window_id": window_id,
                        "segment_id": segment_id,
                        "started_at": window_start,
                        "ended_at": window_end,
                        "duration_seconds": behavioral.window_size_seconds,
                        "scenario": str(session_events.iloc[0]["scenario"]),
                        "operator_label": operator_label,
                        "keyboard_event_count": keyboard_count,
                        "mouse_event_count": mouse_count,
                        "activity_status": "active" if not reasons else "insufficient",
                        "quality_status": "accepted" if not reasons else "rejected",
                        "rejection_reasons": reasons,
                        "events": selected_events,
                    }
                )
                window_start += stride
    return pd.DataFrame(rows, columns=WINDOW_COLUMNS)
