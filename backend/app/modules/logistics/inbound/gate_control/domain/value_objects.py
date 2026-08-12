"""Domain value objects and enumerations for Phase 037 Gate Control."""

from enum import Enum


# ── Gate ─────────────────────────────────────────────────────────────────────

class GateType(str, Enum):
    VEHICLE_ENTRY = "VEHICLE_ENTRY"
    VEHICLE_EXIT = "VEHICLE_EXIT"
    MIXED_VEHICLE_GATE = "MIXED_VEHICLE_GATE"
    SECURITY_CHECKPOINT = "SECURITY_CHECKPOINT"


class GateDirectionPolicy(str, Enum):
    ENTRY_ONLY = "ENTRY_ONLY"
    EXIT_ONLY = "EXIT_ONLY"
    BIDIRECTIONAL = "BIDIRECTIONAL"


class GateStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


# ── Policy ────────────────────────────────────────────────────────────────────

class PolicyScopeType(str, Enum):
    ORGANIZATION = "ORGANIZATION"
    WAREHOUSE = "WAREHOUSE"
    GATE = "GATE"
    TRANSPORT_MODE = "TRANSPORT_MODE"
    SPECIAL_REQUIREMENT = "SPECIAL_REQUIREMENT"
    CUSTOM_APPROVED = "CUSTOM_APPROVED"


class PolicyStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class PolicyVersionStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"
    ARCHIVED = "ARCHIVED"


class CheckCategory(str, Enum):
    APPOINTMENT = "APPOINTMENT"
    TIMING = "TIMING"
    SUPPLIER = "SUPPLIER"
    CARRIER = "CARRIER"
    VEHICLE = "VEHICLE"
    PLATE = "PLATE"
    DRIVER = "DRIVER"
    LICENSE = "LICENSE"
    DOCUMENT = "DOCUMENT"
    GUIDE = "GUIDE"
    SEAL = "SEAL"
    LOAD_VISUAL = "LOAD_VISUAL"
    SAFETY = "SAFETY"
    PHOTO = "PHOTO"
    OTHER = "OTHER"


# ── Check-In ──────────────────────────────────────────────────────────────────

class GateCheckInStatus(str, Enum):
    CREATED = "CREATED"
    ARRIVAL_RECORDED = "ARRIVAL_RECORDED"
    VERIFICATION_IN_PROGRESS = "VERIFICATION_IN_PROGRESS"
    WAITING_SUPERVISOR = "WAITING_SUPERVISOR"
    WAITING_DOCUMENTS = "WAITING_DOCUMENTS"
    HELD_AT_GATE = "HELD_AT_GATE"
    VERIFIED = "VERIFIED"
    ENTRY_AUTHORIZED = "ENTRY_AUTHORIZED"
    ENTRY_AUTHORIZED_WITH_OBSERVATIONS = "ENTRY_AUTHORIZED_WITH_OBSERVATIONS"
    ENTRY_DENIED = "ENTRY_DENIED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    SUPERSEDED = "SUPERSEDED"


class GateSourceType(str, Enum):
    APPOINTMENT = "APPOINTMENT"
    QR_CIT = "QR_CIT"
    MANUAL_CIT_LOOKUP = "MANUAL_CIT_LOOKUP"
    AUTHORIZED_WALK_IN = "AUTHORIZED_WALK_IN"
    LEGACY_IMPORT = "LEGACY_IMPORT"


class ArrivalClassification(str, Enum):
    ON_TIME = "ON_TIME"
    EARLY = "EARLY"
    LATE = "LATE"
    OUTSIDE_WINDOW = "OUTSIDE_WINDOW"
    UNSCHEDULED = "UNSCHEDULED"
    TIME_NOT_CLASSIFIED = "TIME_NOT_CLASSIFIED"


# ── Revision ──────────────────────────────────────────────────────────────────

class RevisionStatus(str, Enum):
    EDITABLE = "EDITABLE"
    IN_VERIFICATION = "IN_VERIFICATION"
    FROZEN = "FROZEN"
    SUPERSEDED = "SUPERSEDED"
    CANCELLED = "CANCELLED"


# ── Vehicle Inspection ────────────────────────────────────────────────────────

class PlateMatchStatus(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    EXPECTED_MISSING = "EXPECTED_MISSING"
    OBSERVED_UNREADABLE = "OBSERVED_UNREADABLE"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class VehicleMatchStatus(str, Enum):
    MATCH = "MATCH"
    DIFFERENT_REGISTERED_VEHICLE = "DIFFERENT_REGISTERED_VEHICLE"
    UNREGISTERED_OBSERVED = "UNREGISTERED_OBSERVED"
    UNCONFIRMED = "UNCONFIRMED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class PlateCaputreMethod(str, Enum):
    MANUAL_ENTRY = "MANUAL_ENTRY"
    MASTER_SELECTION = "MASTER_SELECTION"
    APPROVED_SCANNER = "APPROVED_SCANNER"


# ── Driver Inspection ─────────────────────────────────────────────────────────

class DriverMatchStatus(str, Enum):
    MATCH = "MATCH"
    DIFFERENT_REGISTERED_DRIVER = "DIFFERENT_REGISTERED_DRIVER"
    UNREGISTERED_OBSERVED = "UNREGISTERED_OBSERVED"
    EXPECTED_MISSING = "EXPECTED_MISSING"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class LicenseStatus(str, Enum):
    VALID = "VALID"
    EXPIRED = "EXPIRED"
    MISSING = "MISSING"
    CATEGORY_INCOMPATIBLE = "CATEGORY_INCOMPATIBLE"
    NOT_VERIFIED = "NOT_VERIFIED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class CarrierMatchStatus(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    NOT_VERIFIED = "NOT_VERIFIED"


# ── Document Inspection ───────────────────────────────────────────────────────

class PresentationStatus(str, Enum):
    PRESENTED = "PRESENTED"
    NOT_PRESENTED = "NOT_PRESENTED"
    UNREADABLE = "UNREADABLE"
    DIGITAL_ONLY = "DIGITAL_ONLY"
    ORIGINAL_PRESENTED = "ORIGINAL_PRESENTED"
    COPY_PRESENTED = "COPY_PRESENTED"


class DocComparisonStatus(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    NO_EXPECTED_REFERENCE = "NO_EXPECTED_REFERENCE"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class DocVerificationStatus(str, Enum):
    NOT_VERIFIED = "NOT_VERIFIED"
    FORMAT_VALID = "FORMAT_VALID"
    VERIFIED_FROM_AUTHORIZED_SOURCE = "VERIFIED_FROM_AUTHORIZED_SOURCE"
    MISMATCH = "MISMATCH"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


# ── Seal Inspection ───────────────────────────────────────────────────────────

class SealMatchStatus(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    EXPECTED_MISSING = "EXPECTED_MISSING"
    OBSERVED_MISSING = "OBSERVED_MISSING"
    UNREADABLE = "UNREADABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class SealPhysicalStatus(str, Enum):
    INTACT = "INTACT"
    BROKEN = "BROKEN"
    TAMPERED = "TAMPERED"
    DAMAGED = "DAMAGED"
    NOT_PRESENT = "NOT_PRESENT"
    UNREADABLE = "UNREADABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class SealInspectionResult(str, Enum):
    PASS = "PASS"
    PASS_WITH_OBSERVATION = "PASS_WITH_OBSERVATION"
    FAIL = "FAIL"
    REQUIRES_SUPERVISOR = "REQUIRES_SUPERVISOR"


# ── Photo Evidence ────────────────────────────────────────────────────────────

class PhotoEvidenceType(str, Enum):
    VEHICLE_FRONT = "VEHICLE_FRONT"
    VEHICLE_REAR = "VEHICLE_REAR"
    PLATE = "PLATE"
    DRIVER_RESTRICTED = "DRIVER_RESTRICTED"
    DRIVER_DOCUMENT_RESTRICTED = "DRIVER_DOCUMENT_RESTRICTED"
    LICENSE_RESTRICTED = "LICENSE_RESTRICTED"
    GUIDE = "GUIDE"
    SEAL = "SEAL"
    LOAD_EXTERNAL_CONDITION = "LOAD_EXTERNAL_CONDITION"
    SAFETY_CONDITION = "SAFETY_CONDITION"
    OTHER = "OTHER"


class PhotoSourceType(str, Enum):
    LIVE_CAMERA = "LIVE_CAMERA"
    FILE_UPLOAD = "FILE_UPLOAD"
    APPROVED_DEVICE = "APPROVED_DEVICE"
    LEGACY_IMPORT = "LEGACY_IMPORT"


# ── Check Result ──────────────────────────────────────────────────────────────

class CheckResult(str, Enum):
    PASS = "PASS"
    PASS_WITH_OBSERVATION = "PASS_WITH_OBSERVATION"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_VERIFIED = "NOT_VERIFIED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class OverrideStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    NOT_ALLOWED = "NOT_ALLOWED"
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ── Exception ─────────────────────────────────────────────────────────────────

class ExceptionType(str, Enum):
    PLATE_MISMATCH = "PLATE_MISMATCH"
    VEHICLE_CHANGE = "VEHICLE_CHANGE"
    DRIVER_CHANGE = "DRIVER_CHANGE"
    LICENSE_EXCEPTION = "LICENSE_EXCEPTION"
    VERIFICATION_EXPIRED = "VERIFICATION_EXPIRED"
    MISSING_DOCUMENT = "MISSING_DOCUMENT"
    GUIDE_MISMATCH = "GUIDE_MISMATCH"
    SEAL_MISMATCH = "SEAL_MISMATCH"
    BROKEN_SEAL = "BROKEN_SEAL"
    OUTSIDE_APPOINTMENT_WINDOW = "OUTSIDE_APPOINTMENT_WINDOW"
    UNSCHEDULED_ARRIVAL = "UNSCHEDULED_ARRIVAL"
    OTHER = "OTHER"


class ExceptionRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExceptionStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


# ── Decision ──────────────────────────────────────────────────────────────────

class DecisionType(str, Enum):
    AUTHORIZE_ENTRY = "AUTHORIZE_ENTRY"
    AUTHORIZE_WITH_OBSERVATIONS = "AUTHORIZE_WITH_OBSERVATIONS"
    HOLD_AT_GATE = "HOLD_AT_GATE"
    DENY_ENTRY = "DENY_ENTRY"
    REQUIRE_SUPERVISOR = "REQUIRE_SUPERVISOR"


# ── Correction ────────────────────────────────────────────────────────────────

class CorrectionStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class TimeCorrectionStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


# State machine transitions
GATE_CHECK_IN_TRANSITIONS: dict[str, list[str]] = {
    "CREATED": ["ARRIVAL_RECORDED", "CANCELLED"],
    "ARRIVAL_RECORDED": ["VERIFICATION_IN_PROGRESS", "CANCELLED"],
    "VERIFICATION_IN_PROGRESS": [
        "WAITING_SUPERVISOR",
        "WAITING_DOCUMENTS",
        "HELD_AT_GATE",
        "VERIFIED",
        "ENTRY_DENIED",
        "CANCELLED",
    ],
    "WAITING_SUPERVISOR": [
        "VERIFICATION_IN_PROGRESS",
        "HELD_AT_GATE",
        "ENTRY_AUTHORIZED_WITH_OBSERVATIONS",
        "ENTRY_DENIED",
    ],
    "WAITING_DOCUMENTS": ["VERIFICATION_IN_PROGRESS", "HELD_AT_GATE", "ENTRY_DENIED"],
    "HELD_AT_GATE": [
        "VERIFICATION_IN_PROGRESS",
        "ENTRY_AUTHORIZED_WITH_OBSERVATIONS",
        "ENTRY_DENIED",
        "CANCELLED",
    ],
    "VERIFIED": ["ENTRY_AUTHORIZED", "ENTRY_AUTHORIZED_WITH_OBSERVATIONS", "ENTRY_DENIED"],
    "ENTRY_AUTHORIZED": ["COMPLETED"],
    "ENTRY_AUTHORIZED_WITH_OBSERVATIONS": ["COMPLETED"],
    "ENTRY_DENIED": ["COMPLETED"],
    "CANCELLED": [],
    "COMPLETED": [],
    "SUPERSEDED": [],
}


def validate_status_transition(current: str, target: str) -> None:
    """Raise ValueError if the transition is not allowed by the state machine."""
    allowed = GATE_CHECK_IN_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise ValueError(
            f"Transición de estado inválida: '{current}' → '{target}'. "
            f"Permitidas: {allowed}"
        )


__all__ = [
    "GateType",
    "GateDirectionPolicy",
    "GateStatus",
    "PolicyScopeType",
    "PolicyStatus",
    "PolicyVersionStatus",
    "CheckCategory",
    "GateCheckInStatus",
    "GateSourceType",
    "ArrivalClassification",
    "RevisionStatus",
    "PlateMatchStatus",
    "VehicleMatchStatus",
    "PlateCaputreMethod",
    "DriverMatchStatus",
    "LicenseStatus",
    "CarrierMatchStatus",
    "PresentationStatus",
    "DocComparisonStatus",
    "DocVerificationStatus",
    "SealMatchStatus",
    "SealPhysicalStatus",
    "SealInspectionResult",
    "PhotoEvidenceType",
    "PhotoSourceType",
    "CheckResult",
    "OverrideStatus",
    "ExceptionType",
    "ExceptionRiskLevel",
    "ExceptionStatus",
    "DecisionType",
    "CorrectionStatus",
    "TimeCorrectionStatus",
    "GATE_CHECK_IN_TRANSITIONS",
    "validate_status_transition",
]
