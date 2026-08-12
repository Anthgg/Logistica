"""Audit sanitizer — redacts sensitive fields before persistence."""

import re
from copy import deepcopy

REDACTED_FIELDS = frozenset({
    "password", "password_hash", "secret", "token", "csrf", "cookie",
    "authorization", "private_key", "access_key", "refresh_token", "otp",
    "biometric_embedding", "face_image", "signature_binary", "api_key",
    "session_token", "device_token", "csrf_token",
})

REDACTED_VALUE = "[REDACTED]"


def sanitize_for_audit(data: dict | None) -> dict | None:
    """Return a sanitized copy of data with sensitive fields redacted."""
    if data is None:
        return None
    cleaned = deepcopy(data)
    for key in list(cleaned.keys()):
        key_lower = key.lower()
        if key_lower in REDACTED_FIELDS or any(s in key_lower for s in REDACTED_FIELDS):
            cleaned[key] = REDACTED_VALUE
        elif isinstance(cleaned[key], dict):
            cleaned[key] = sanitize_for_audit(cleaned[key])
    return cleaned


def compute_changed_fields(previous: dict | None, new: dict | None) -> list[str]:
    """Compute the list of fields that changed between two snapshots."""
    if not previous and not new:
        return []
    if not previous:
        return list(new.keys()) if new else []
    if not new:
        return list(previous.keys()) if previous else []
    changed = []
    all_keys = set(previous.keys()) | set(new.keys())
    for key in all_keys:
        if previous.get(key) != new.get(key):
            changed.append(key)
    return changed