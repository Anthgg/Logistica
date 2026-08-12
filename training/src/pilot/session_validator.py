from dataclasses import dataclass

from src.common.config import ProtocolConfig


@dataclass(frozen=True)
class SessionValidation:
    valid: bool
    reasons: list[str]


def validate_session(
    row: dict[str, object], protocol: ProtocolConfig
) -> SessionValidation:
    reasons: list[str] = []
    status = str(row.get("status") or "")
    if status != "completed":
        reasons.append("SESSION_NOT_COMPLETED")
    scenario = str(row.get("scenario") or "")
    if scenario not in protocol.scenarios:
        reasons.append("SCENARIO_NOT_ALLOWED")
    if not bool(row.get("consent_valid")):
        reasons.append("CONSENT_NOT_VALID")
    if str(row.get("annotation_status") or "") != "confirmed":
        reasons.append("SESSION_ANNOTATION_NOT_CONFIRMED")
    duration = float(row.get("duration_seconds") or 0)
    if duration < protocol.minimum_session_duration_seconds:
        reasons.append("SESSION_TOO_SHORT")
    expected_range = protocol.expected_session_duration.get(scenario)
    if expected_range and not expected_range[0] <= duration <= expected_range[1]:
        reasons.append("SESSION_DURATION_OUTSIDE_EXPECTED_RANGE")
    if int(row.get("facial_capture_count") or 0) < protocol.minimum_face_captures:
        reasons.append("INSUFFICIENT_FACE_CAPTURES")
    event_count = int(row.get("keyboard_event_count") or 0) + int(
        row.get("mouse_event_count") or 0
    )
    if event_count < protocol.minimum_behavioral_events:
        reasons.append("INSUFFICIENT_BEHAVIORAL_EVENTS")
    batches = max(1, int(row.get("batch_count") or 0))
    error_rate = int(row.get("error_count") or 0) / batches
    if error_rate > protocol.maximum_session_error_rate:
        reasons.append("SESSION_ERROR_RATE_EXCEEDED")
    if int(row.get("missing_files") or 0):
        reasons.append("MISSING_CAPTURE_FILES")
    if int(row.get("duplicate_files") or 0):
        reasons.append("DUPLICATE_CAPTURE_FILES")
    if int(row.get("duplicate_batches") or 0):
        reasons.append("DUPLICATE_BEHAVIOR_BATCHES")
    if bool(row.get("capture_count_mismatch")):
        reasons.append("FACIAL_COUNT_MISMATCH")
    if bool(row.get("batch_count_mismatch")):
        reasons.append("BATCH_COUNT_MISMATCH")
    if bool(row.get("keyboard_count_mismatch")):
        reasons.append("KEYBOARD_COUNT_MISMATCH")
    if bool(row.get("mouse_count_mismatch")):
        reasons.append("MOUSE_COUNT_MISMATCH")
    return SessionValidation(valid=not reasons, reasons=reasons)
