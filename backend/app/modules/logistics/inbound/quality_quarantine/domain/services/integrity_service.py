"""Phase 042 — Integrity service (SHA-256 canonical hashing)."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_hash(data: dict[str, Any]) -> str:
    """Compute SHA-256 hash of canonical JSON representation."""
    canonical = json.dumps(data, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_hash(data: dict[str, Any], expected_hash: str) -> bool:
    """Verify that data matches expected hash."""
    return canonical_hash(data) == expected_hash


def compute_event_hash(
    *,
    previous_event_hash: str | None,
    event_type: str,
    sequence_number: int,
    quarantine_case_id: Any,
    allocation_id: Any,
    actor_user_id: Any,
    quantity: Any,
    event_at: Any,
) -> str:
    """Compute event chain hash for append-only event log."""
    payload = {
        "previous_event_hash": previous_event_hash or "",
        "event_type": event_type,
        "sequence_number": sequence_number,
        "quarantine_case_id": str(quarantine_case_id),
        "allocation_id": str(allocation_id),
        "actor_user_id": str(actor_user_id),
        "quantity": str(quantity) if quantity else "",
        "event_at": str(event_at),
    }
    return canonical_hash(payload)
