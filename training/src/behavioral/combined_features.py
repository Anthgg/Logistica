import math

import pandas as pd

from src.behavioral.keyboard_features import extract_keyboard_features
from src.behavioral.mouse_features import extract_mouse_features
from src.common.config import BehavioralConfig, PreparationConfig
from src.common.hashing import canonical_json_hash
from src.common.timestamps import deterministic_source_timestamp


def extract_combined_features(
    windows: pd.DataFrame,
    config: PreparationConfig,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    generated_at = deterministic_source_timestamp(windows, "ended_at")
    for window in windows.to_dict(orient="records"):
        events = window.get("events")
        safe_events = events if isinstance(events, list) else []
        duration = float(window["duration_seconds"])
        keyboard = extract_keyboard_features(
            safe_events, duration, config.behavioral
        )
        mouse = extract_mouse_features(safe_events, duration, config.behavioral)
        features: dict[str, object] = {
            "dataset_version": config.pipeline.dataset_version,
            "protocol_version": config.protocol.protocol_version,
            "generated_at": generated_at,
            "source_session_id": str(window["session_id"]),
            "participant_id": str(window["participant_id"]),
            "session_id": str(window["session_id"]),
            "window_id": str(window["window_id"]),
            "segment_id": str(window["segment_id"]),
            "scenario": str(window["scenario"]),
            "operator_label": str(window["operator_label"]),
            "window_started_at": window["started_at"],
            "window_ended_at": window["ended_at"],
            "quality_status": str(window["quality_status"]),
            "rejection_reasons": window["rejection_reasons"],
            **keyboard,
            **mouse,
            "split": None,
        }
        numeric = [
            float(value)
            for value in [*keyboard.values(), *mouse.values()]
            if isinstance(value, (int, float))
        ]
        if any(math.isinf(value) for value in numeric):
            features["quality_status"] = "rejected"
            features["rejection_reasons"] = sorted(
                set([*features["rejection_reasons"], "NON_FINITE_FEATURE"])
            )
        features["checksum"] = canonical_json_hash(
            {
                key: value
                for key, value in features.items()
                if key not in {"generated_at", "split", "checksum"}
            }
        )
        rows.append(features)
    return pd.DataFrame(rows)
