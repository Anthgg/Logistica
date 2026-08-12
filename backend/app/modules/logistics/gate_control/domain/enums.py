"""Domain enums for Phase 037 Gate Control Core Domain."""

from enum import StrEnum


class GateType(StrEnum):
    """Physical or logical gate classification."""

    MAIN_ENTRY = "MAIN_ENTRY"
    MAIN_EXIT = "MAIN_EXIT"
    BI_DIRECTIONAL = "BI_DIRECTIONAL"
    PEDESTRIAN = "PEDESTRIAN"
    EMERGENCY = "EMERGENCY"
    SERVICE = "SERVICE"


class GateStatus(StrEnum):
    """Operational status of a warehouse gate."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    BLOCKED = "BLOCKED"


class GateEventType(StrEnum):
    """Type of gate event recorded."""

    CHECK_IN = "CHECK_IN"
    CHECK_OUT = "CHECK_OUT"
    INSPECTION = "INSPECTION"
    DENIED_ENTRY = "DENIED_ENTRY"
    EMERGENCY_EXIT = "EMERGENCY_EXIT"


class AccessDecision(StrEnum):
    """Security/Gatekeeper access evaluation decision."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    CONDITIONAL_APPROVED = "CONDITIONAL_APPROVED"


class SealStatus(StrEnum):
    """Cargo seal condition observed at gate."""

    INTACT = "INTACT"
    BROKEN = "BROKEN"
    TAMPERED = "TAMPERED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    MISMATCH = "MISMATCH"


class GateRecordStatus(StrEnum):
    """Lifecycle status of a gate control record."""

    DRAFT = "DRAFT"
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
