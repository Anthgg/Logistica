"""Canonical JSON + SHA-256 hashing for the inventory ledger.

Implements the deterministic canonicalization used to compute
``movement_hash`` and ``line.content_hash`` for the append-only book.

Rules:
* Decimal values are serialized as their canonical string form
  (``str(value)``) — never float.
* UUID values are serialized in their canonical hyphenated form
  (``str(uuid)``) — never hex/bytes.
* datetimes are normalized to UTC ISO-8601 with microseconds.
* Field order is stable (alphabetical) and a top-level ``canonicalization_version``
  is included.
* No floating point. No silent rounding.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Iterable, Mapping
from uuid import UUID

from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
    CANONICALIZATION_VERSION,
    HASH_ALGORITHM,
)


# ---------------------------------------------------------------------------
# Canonicalization
# ---------------------------------------------------------------------------

def _normalize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat()
    if isinstance(value, (int,)):
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return {str(k): _normalize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_normalize_value(v) for v in value]
    return value


def canonicalize(payload: Mapping[str, Any]) -> str:
    """Return a deterministic JSON string for a payload."""

    normalized = {str(k): _normalize_value(v) for k, v in payload.items()}
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def hash_payload(payload: Mapping[str, Any]) -> str:
    """Compute the canonical hash for a payload."""

    envelope = {
        "canonicalization_version": CANONICALIZATION_VERSION,
        "algorithm": HASH_ALGORITHM,
        "payload": payload,
    }
    raw = canonicalize(envelope).encode("utf-8")
    return hashlib.new(HASH_ALGORITHM, raw).hexdigest()


# ---------------------------------------------------------------------------
# Movement hash
# ---------------------------------------------------------------------------

def compute_movement_hash(
    *,
    ledger_partition_key: str,
    ledger_sequence: int,
    movement_code: str,
    movement_type: str,
    movement_family: str,
    organization_id: UUID | str,
    branch_id: UUID | str,
    source_event_id: str,
    source_event_version: int,
    occurred_at: datetime,
    posted_at: datetime,
    reason_code: str | None,
    compensation_for_movement_id: UUID | str | None,
    previous_movement_hash: str | None,
    lines: Iterable[Mapping[str, Any]],
    sources: Iterable[Mapping[str, Any]],
) -> str:
    """Compute the chained movement hash for a posted movement.

    Inputs must already be in their final canonical representation
    (no mutable references).
    """

    payload = {
        "ledger_partition_key": str(ledger_partition_key),
        "ledger_sequence": int(ledger_sequence),
        "movement_code": str(movement_code),
        "movement_type": str(movement_type),
        "movement_family": str(movement_family),
        "organization_id": str(organization_id),
        "branch_id": str(branch_id),
        "source_event_id": str(source_event_id),
        "source_event_version": int(source_event_version),
        "occurred_at": occurred_at,
        "posted_at": posted_at,
        "reason_code": reason_code,
        "compensation_for_movement_id": (
            str(compensation_for_movement_id) if compensation_for_movement_id else None
        ),
        "previous_movement_hash": previous_movement_hash,
        "lines": [dict(line) for line in lines],
        "sources": [dict(source) for source in sources],
    }
    return hash_payload(payload)


def compute_line_content_hash(
    *,
    line_number: int,
    product_id: UUID | str,
    product_version_id: UUID | str | None,
    quantity: Decimal,
    unit_id: UUID | str,
    base_quantity: Decimal,
    base_unit_id: UUID | str,
    source_position_id: UUID | str | None,
    destination_position_id: UUID | str | None,
    source_external_boundary_kind: str | None,
    destination_external_boundary_kind: str | None,
    quantity_direction: str,
) -> str:
    payload = {
        "line_number": int(line_number),
        "product_id": str(product_id),
        "product_version_id": (
            str(product_version_id) if product_version_id else None
        ),
        "quantity": Decimal(quantity),
        "unit_id": str(unit_id),
        "base_quantity": Decimal(base_quantity),
        "base_unit_id": str(base_unit_id),
        "source_position_id": (
            str(source_position_id) if source_position_id else None
        ),
        "destination_position_id": (
            str(destination_position_id) if destination_position_id else None
        ),
        "source_external_boundary_kind": source_external_boundary_kind,
        "destination_external_boundary_kind": destination_external_boundary_kind,
        "quantity_direction": str(quantity_direction),
    }
    return hash_payload(payload)
