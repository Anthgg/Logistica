import math

import numpy as np

from src.common.config import BehavioralConfig
from src.common.timestamps import ensure_utc


def _statistics(values: list[float], prefix: str) -> dict[str, float]:
    finite = np.asarray([value for value in values if math.isfinite(value)], dtype=float)
    if finite.size == 0:
        return {
            f"{prefix}_mean": np.nan,
            f"{prefix}_std": np.nan,
            f"{prefix}_median": np.nan,
        }
    return {
        f"{prefix}_mean": float(np.mean(finite)),
        f"{prefix}_std": float(np.std(finite)),
        f"{prefix}_median": float(np.median(finite)),
    }


def extract_keyboard_features(
    events: list[dict[str, object]],
    duration_seconds: float,
    config: BehavioralConfig,
) -> dict[str, float]:
    keyboard = [event for event in events if event.get("type") == "keyboard"]
    dwell = [
        float(event["dwell_time_ms"])
        for event in keyboard
        if isinstance(event.get("dwell_time_ms"), (int, float))
    ]
    flight = [
        float(event["flight_time_ms"])
        for event in keyboard
        if isinstance(event.get("flight_time_ms"), (int, float))
    ]
    intervals = [
        float(event["interval_from_previous_ms"])
        for event in keyboard
        if isinstance(event.get("interval_from_previous_ms"), (int, float))
    ]
    dwell_array = np.asarray(dwell, dtype=float)
    pauses = [value for value in intervals if value >= config.burst_pause_threshold_ms]
    burst_lengths: list[int] = []
    if keyboard:
        length = 1
        for interval in intervals:
            if interval >= config.burst_pause_threshold_ms:
                burst_lengths.append(length)
                length = 1
            else:
                length += 1
        burst_lengths.append(length)
    count = len(keyboard)
    active_ms = sum(dwell) + sum(
        min(value, config.burst_pause_threshold_ms) for value in intervals
    )
    return {
        **_statistics(dwell, "dwell"),
        "dwell_min": float(np.min(dwell_array)) if dwell else np.nan,
        "dwell_max": float(np.max(dwell_array)) if dwell else np.nan,
        "dwell_p25": float(np.percentile(dwell_array, 25)) if dwell else np.nan,
        "dwell_p75": float(np.percentile(dwell_array, 75)) if dwell else np.nan,
        **_statistics(flight, "flight"),
        **{
            key: value
            for key, value in _statistics(intervals, "interval").items()
            if key != "interval_median"
        },
        "typing_event_rate": count / duration_seconds if duration_seconds else 0.0,
        "correction_ratio": (
            sum(
                bool(event.get("is_backspace"))
                or event.get("category") == "correction"
                for event in keyboard
            )
            / count
            if count
            else 0.0
        ),
        "modifier_ratio": (
            sum(
                bool(event.get("is_modifier"))
                or event.get("category") == "modifier"
                for event in keyboard
            )
            / count
            if count
            else 0.0
        ),
        "navigation_ratio": (
            sum(event.get("category") == "navigation" for event in keyboard) / count
            if count
            else 0.0
        ),
        "idle_ratio": (
            max(0.0, min(1.0, sum(pauses) / (duration_seconds * 1000)))
            if duration_seconds
            else 1.0
        ),
        "burst_count": float(len(burst_lengths)),
        "mean_burst_length": (
            float(np.mean(burst_lengths)) if burst_lengths else 0.0
        ),
        "maximum_pause_ms": max(intervals, default=0.0),
        "active_time_ratio": (
            max(0.0, min(1.0, active_ms / (duration_seconds * 1000)))
            if duration_seconds
            else 0.0
        ),
    }
