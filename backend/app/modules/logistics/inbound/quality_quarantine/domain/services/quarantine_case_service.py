"""Phase 042 — Quarantine case status transition service."""

from __future__ import annotations

from app.modules.logistics.inbound.quality_quarantine.domain.enums import (
    QUARANTINE_STATUS_TRANSITIONS,
    QuarantineStatus,
)
from app.modules.logistics.inbound.quality_quarantine.domain.errors import (
    QualityQuarantineStatusInvalid,
)


def require_quarantine_transition(current: str, target: str) -> None:
    """Validate that a quarantine status transition is allowed."""
    allowed = QUARANTINE_STATUS_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise QualityQuarantineStatusInvalid(current=current, target=target)


def derive_quarantine_quality_result(inspection_result: str | None) -> str | None:
    """Map inspection overall result to quarantine quality result."""
    if inspection_result is None:
        return None
    mapping = {
        "PASS": "PASSED",
        "PASS_WITH_OBSERVATIONS": "PASSED_WITH_OBSERVATIONS",
        "FAIL": "FAILED",
        "INCONCLUSIVE": "INCONCLUSIVE",
        "REINSPECTION_REQUIRED": "REINSPECTION_REQUIRED",
    }
    return mapping.get(inspection_result)
