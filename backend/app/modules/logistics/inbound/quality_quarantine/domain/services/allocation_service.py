"""Phase 042 — Allocation status transition service."""

from __future__ import annotations

from app.modules.logistics.inbound.quality_quarantine.domain.enums import (
    ALLOCATION_STATUS_TRANSITIONS,
    AllocationStatus,
)
from app.modules.logistics.inbound.quality_quarantine.domain.errors import (
    InboundInventoryAllocationStatusInvalid,
)


def require_allocation_transition(current: str, target: str) -> None:
    """Validate that a status transition is allowed."""
    allowed = ALLOCATION_STATUS_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InboundInventoryAllocationStatusInvalid(current=current, target=target)


def derive_availability_class(allocation_status: str) -> str:
    """Derive availability class from allocation status. Backend-only."""
    mapping = {
        AllocationStatus.PENDING_QUALITY_ASSESSMENT: "BLOCKED",
        AllocationStatus.QUARANTINE_REQUIRED: "QUARANTINE",
        AllocationStatus.QUARANTINED: "QUARANTINE",
        AllocationStatus.INSPECTION_PENDING: "QUARANTINE",
        AllocationStatus.INSPECTION_IN_PROGRESS: "QUARANTINE",
        AllocationStatus.DECISION_PENDING: "QUARANTINE",
        AllocationStatus.QUALITY_APPROVED: "QUARANTINE",
        AllocationStatus.RELEASE_PENDING_APPROVAL: "QUARANTINE",
        AllocationStatus.RELEASED_FOR_PUTAWAY: "AVAILABLE_FOR_PUTAWAY",
        AllocationStatus.REJECTION_PENDING_APPROVAL: "QUARANTINE",
        AllocationStatus.REJECTED_PENDING_DISPOSITION: "REJECTED_NOT_AVAILABLE",
        AllocationStatus.REINSPECTION_REQUIRED: "QUARANTINE",
        AllocationStatus.CANCELLED: "CANCELLED",
        AllocationStatus.SUPERSEDED_BY_SPLIT: "CANCELLED",
        AllocationStatus.SUPERSEDED: "CANCELLED",
    }
    return mapping.get(allocation_status, "UNKNOWN")


def derive_quality_status(inspection_result: str | None, allocation_status: str) -> str:
    """Derive quality status from inspection result. Backend-only."""
    if allocation_status in (AllocationStatus.CANCELLED, AllocationStatus.SUPERSEDED):
        return "NOT_APPLICABLE"
    if inspection_result is None:
        return "NOT_ASSESSED"
    result_map = {
        "PASS": "PASSED",
        "PASS_WITH_OBSERVATIONS": "PASSED_WITH_OBSERVATIONS",
        "FAIL": "FAILED",
        "INCONCLUSIVE": "INCONCLUSIVE",
        "REINSPECTION_REQUIRED": "REINSPECTION_REQUIRED",
        "NOT_CALCULATED": "UNDER_INSPECTION",
    }
    return result_map.get(inspection_result, "NOT_ASSESSED")
