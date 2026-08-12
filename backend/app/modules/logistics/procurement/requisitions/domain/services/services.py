"""Domain services for purchase requisitions — pure functions, no DB."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from app.modules.logistics.procurement.requisitions.domain.value_objects.enums import (
    ALLOWED_TRANSITIONS,
    RequisitionStatus,
)


def validate_required_date(
    required_date: date,
    branch_timezone: str = "America/Lima",
) -> None:
    """Raise ValueError if required_date is before today (business date)."""
    today = datetime.now(timezone.utc).date()
    if required_date < today:
        raise ValueError(
            f"required_date ({required_date}) must be on or after today ({today})."
        )


def validate_justification(
    text: str,
    min_length: int = 20,
    max_length: int = 2000,
) -> str:
    """Clean and validate justification text. Returns stripped text."""
    if not text or not text.strip():
        raise ValueError("Justification cannot be empty or whitespace-only.")
    stripped = text.strip()
    # No HTML tags
    if re.search(r"<[^>]+>", stripped):
        raise ValueError("Justification must not contain HTML tags.")
    # No control characters (except newlines/tabs)
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", stripped):
        raise ValueError("Justification contains invalid control characters.")
    if len(stripped) < min_length:
        raise ValueError(
            f"Justification is too short ({len(stripped)} chars). "
            f"Minimum is {min_length} characters."
        )
    if len(stripped) > max_length:
        raise ValueError(
            f"Justification is too long ({len(stripped)} chars). "
            f"Maximum is {max_length} characters."
        )
    return stripped


def compute_content_hash(revision_data: dict) -> str:
    """Compute SHA-256 hash over revision data with stable key ordering."""
    serialized = json.dumps(revision_data, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def normalize_quantity(value: str) -> Decimal:
    """Parse quantity from string decimal. Reject float, negative, zero."""
    if not isinstance(value, (str, int)):
        raise ValueError(f"Quantity must be a string decimal, not {type(value).__name__}.")
    try:
        qty = Decimal(str(value).strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal quantity: '{value}'.") from exc
    if qty <= Decimal("0"):
        raise ValueError(f"Quantity must be greater than zero. Got: {qty}.")
    return qty


def build_requester_snapshot(
    user_id: str,
    name: str,
    area: str | None = None,
) -> dict:
    """Build immutable requester snapshot for revision."""
    return {
        "user_id": str(user_id),
        "name": name,
        "area": area,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }


def build_cost_center_snapshot(
    cc_id: str,
    code: str,
    name: str,
    organization_id: str | None = None,
) -> dict:
    """Build immutable cost center snapshot for revision."""
    return {
        "id": str(cc_id),
        "code": code,
        "name": name,
        "organization_id": str(organization_id) if organization_id else None,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }


def build_branch_snapshot(branch_id: str, code: str, name: str) -> dict:
    return {
        "id": str(branch_id),
        "code": code,
        "name": name,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }


def build_destination_snapshot(
    warehouse_id: str | None,
    warehouse_name: str | None,
    description: str | None,
) -> dict | None:
    if not warehouse_id and not description:
        return None
    return {
        "warehouse_id": str(warehouse_id) if warehouse_id else None,
        "warehouse_name": warehouse_name,
        "description": description,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }


def is_valid_transition(
    current: RequisitionStatus | str,
    target: RequisitionStatus | str,
) -> bool:
    """Check if a state machine transition is allowed."""
    try:
        curr = RequisitionStatus(current)
        tgt = RequisitionStatus(target)
    except ValueError:
        return False
    return tgt in ALLOWED_TRANSITIONS.get(curr, set())


def normalize_code(raw: str) -> str:
    """Normalize a code to uppercase, trimmed, underscores for spaces."""
    return raw.strip().upper().replace(" ", "_").replace("-", "_")
