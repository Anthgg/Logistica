import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.common.config import BehavioralConfig
from src.common.hashing import canonical_json_hash
from src.common.timestamps import ensure_utc

FORBIDDEN_KEYS = {
    "key",
    "code",
    "key_value",
    "character",
    "text",
    "typed_text",
    "input_value",
    "target_value",
    "password",
    "email_value",
    "clipboard",
    "clipboard_text",
    "inner_html",
    "html",
}
COMMON_KEYS = {"type", "event", "timestamp", "sequence_index"}
KEYBOARD_KEYS = COMMON_KEYS | {
    "category",
    "dwell_time_ms",
    "flight_time_ms",
    "interval_from_previous_ms",
    "is_backspace",
    "is_modifier",
}
MOUSE_KEYS = COMMON_KEYS | {
    "normalized_x",
    "normalized_y",
    "delta_x",
    "delta_y",
    "distance",
    "velocity",
    "button_category",
    "scroll_delta",
}
KEYBOARD_CATEGORIES = {
    "alphanumeric",
    "navigation",
    "modifier",
    "correction",
    "function",
    "other",
}
MOUSE_EVENTS = {"move", "click", "scroll", "pointerdown", "pointerup"}


@dataclass(frozen=True)
class BatchValidation:
    valid: bool
    rejection_reasons: list[str]
    events: list[dict[str, object]]
    keyboard_event_count: int
    mouse_event_count: int


def contains_forbidden_data(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).casefold() in FORBIDDEN_KEYS
            or contains_forbidden_data(nested)
            for key, nested in value.items()
        )
    if isinstance(value, list):
        return any(contains_forbidden_data(item) for item in value)
    return False


def _finite_number(
    event: dict[str, object],
    field: str,
    reasons: list[str],
    minimum: float | None = None,
    maximum: float | None = None,
) -> None:
    value = event.get(field)
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        reasons.append("INVALID_NUMERIC_VALUE")
        return
    numeric = float(value)
    if not math.isfinite(numeric):
        reasons.append("NON_FINITE_VALUE")
    elif minimum is not None and numeric < minimum:
        reasons.append("VALUE_OUT_OF_RANGE")
    elif maximum is not None and numeric > maximum:
        reasons.append("VALUE_OUT_OF_RANGE")


def validate_batch(
    batch: dict[str, object],
    config: BehavioralConfig,
    *,
    seen_batch_ids: set[str] | None = None,
    seen_batch_sequences: set[tuple[str, int]] | None = None,
    seen_event_hashes: set[str] | None = None,
) -> BatchValidation:
    reasons: list[str] = []
    batch_id = str(batch.get("batch_id") or "")
    if not batch_id:
        reasons.append("MISSING_BATCH_ID")
    if seen_batch_ids is not None:
        if batch_id in seen_batch_ids:
            reasons.append("DUPLICATE_BATCH")
        seen_batch_ids.add(batch_id)
    sequence_number = batch.get("sequence_number")
    if (
        isinstance(sequence_number, bool)
        or not isinstance(sequence_number, int)
        or sequence_number <= 0
    ):
        reasons.append("INVALID_BATCH_SEQUENCE")
    elif seen_batch_sequences is not None:
        sequence_key = (str(batch.get("session_id") or ""), sequence_number)
        if sequence_key in seen_batch_sequences:
            reasons.append("DUPLICATE_BATCH_SEQUENCE")
        seen_batch_sequences.add(sequence_key)
    events_value = batch.get("payload", batch.get("events"))
    if not isinstance(events_value, list) or not events_value:
        return BatchValidation(
            valid=False,
            rejection_reasons=sorted(set(reasons + ["EMPTY_BATCH"])),
            events=[],
            keyboard_event_count=0,
            mouse_event_count=0,
        )
    if len(events_value) > config.maximum_batch_events:
        reasons.append("BATCH_TOO_LARGE")
    expected_checksum = str(batch.get("checksum") or "")
    if expected_checksum and canonical_json_hash(events_value) != expected_checksum:
        reasons.append("BATCH_CHECKSUM_MISMATCH")
    if contains_forbidden_data(events_value):
        return BatchValidation(
            valid=False,
            rejection_reasons=sorted(
                set(reasons + ["FORBIDDEN_TEXTUAL_DATA_DETECTED"])
            ),
            events=[],
            keyboard_event_count=0,
            mouse_event_count=0,
        )
    session_start = ensure_utc(batch["session_started_at"])
    session_end_value = batch.get("session_ended_at")
    session_end = ensure_utc(session_end_value) if session_end_value else None
    skew = timedelta(seconds=config.maximum_timestamp_skew_seconds)
    try:
        batch_start = ensure_utc(batch["started_at"])
        batch_end = ensure_utc(batch["ended_at"])
        if batch_end < batch_start:
            reasons.append("INVALID_BATCH_INTERVAL")
        if batch_start < session_start - skew or (
            session_end and batch_end > session_end + skew
        ):
            reasons.append("BATCH_OUTSIDE_SESSION")
    except (KeyError, ValueError, TypeError):
        batch_start = None
        batch_end = None
        reasons.append("INVALID_BATCH_TIMESTAMP")
    indexes: set[int] = set()
    timestamps: list[datetime] = []
    event_hashes: set[str] = set()
    validated_events: list[dict[str, object]] = []
    keyboard_count = 0
    mouse_count = 0
    for raw_event in events_value:
        if not isinstance(raw_event, dict):
            reasons.append("INVALID_EVENT_STRUCTURE")
            continue
        event = {str(key): value for key, value in raw_event.items()}
        index = event.get("sequence_index")
        if isinstance(index, bool) or not isinstance(index, int) or index <= 0:
            reasons.append("INVALID_EVENT_SEQUENCE")
        elif index in indexes:
            reasons.append("DUPLICATE_EVENT")
        else:
            indexes.add(index)
        try:
            timestamp = ensure_utc(str(event.get("timestamp") or ""))
            timestamps.append(timestamp)
            if timestamp < session_start - skew or (
                session_end and timestamp > session_end + skew
            ):
                reasons.append("EVENT_OUTSIDE_SESSION")
            if batch_start and batch_end and not (
                batch_start - skew <= timestamp <= batch_end + skew
            ):
                reasons.append("EVENT_OUTSIDE_BATCH")
        except ValueError:
            reasons.append("INVALID_EVENT_TIMESTAMP")
        event_type = event.get("type")
        event_name = event.get("event")
        if event_type == "keyboard":
            keyboard_count += 1
            if event_name != "timing" or set(event) - KEYBOARD_KEYS:
                reasons.append("INVALID_KEYBOARD_EVENT")
            if event.get("category") not in KEYBOARD_CATEGORIES:
                reasons.append("INVALID_KEYBOARD_CATEGORY")
            _finite_number(
                event,
                "dwell_time_ms",
                reasons,
                0,
                config.maximum_dwell_time_ms,
            )
            _finite_number(
                event,
                "flight_time_ms",
                reasons,
                config.minimum_flight_time_ms,
                config.maximum_flight_time_ms,
            )
            _finite_number(
                event,
                "interval_from_previous_ms",
                reasons,
                0,
                config.maximum_interval_ms,
            )
        elif event_type == "mouse":
            mouse_count += 1
            if event_name not in MOUSE_EVENTS or set(event) - MOUSE_KEYS:
                reasons.append("INVALID_MOUSE_EVENT")
            _finite_number(event, "normalized_x", reasons, 0, 1)
            _finite_number(event, "normalized_y", reasons, 0, 1)
            _finite_number(event, "velocity", reasons, 0, None)
            _finite_number(event, "distance", reasons, 0, None)
        else:
            reasons.append("INVALID_EVENT_TYPE")
        event_hash = canonical_json_hash(event)
        if event_hash in event_hashes or (
            seen_event_hashes is not None and event_hash in seen_event_hashes
        ):
            reasons.append("DUPLICATE_EVENT")
        event_hashes.add(event_hash)
        if seen_event_hashes is not None:
            seen_event_hashes.add(event_hash)
        validated_events.append(event)
    if timestamps != sorted(timestamps):
        reasons.append("EVENTS_OUT_OF_TEMPORAL_ORDER")
    unique_reasons = sorted(set(reasons))
    return BatchValidation(
        valid=not unique_reasons,
        rejection_reasons=unique_reasons,
        events=validated_events if not unique_reasons else [],
        keyboard_event_count=keyboard_count,
        mouse_event_count=mouse_count,
    )
