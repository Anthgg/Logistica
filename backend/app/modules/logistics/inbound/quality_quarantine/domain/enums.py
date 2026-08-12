"""Phase 042 — Quality Quarantine enums and constants."""

from __future__ import annotations

from enum import StrEnum


# ---------------------------------------------------------------------------
# Allocation
# ---------------------------------------------------------------------------

class AllocationStatus(StrEnum):
    PENDING_QUALITY_ASSESSMENT = "PENDING_QUALITY_ASSESSMENT"
    QUARANTINE_REQUIRED = "QUARANTINE_REQUIRED"
    QUARANTINED = "QUARANTINED"
    INSPECTION_PENDING = "INSPECTION_PENDING"
    INSPECTION_IN_PROGRESS = "INSPECTION_IN_PROGRESS"
    DECISION_PENDING = "DECISION_PENDING"
    QUALITY_APPROVED = "QUALITY_APPROVED"
    RELEASE_PENDING_APPROVAL = "RELEASE_PENDING_APPROVAL"
    RELEASED_FOR_PUTAWAY = "RELEASED_FOR_PUTAWAY"
    REJECTION_PENDING_APPROVAL = "REJECTION_PENDING_APPROVAL"
    REJECTED_PENDING_DISPOSITION = "REJECTED_PENDING_DISPOSITION"
    REINSPECTION_REQUIRED = "REINSPECTION_REQUIRED"
    CANCELLED = "CANCELLED"
    SUPERSEDED_BY_SPLIT = "SUPERSEDED_BY_SPLIT"
    SUPERSEDED = "SUPERSEDED"


ALLOCATION_STATUS_TRANSITIONS: dict[str, set[str]] = {
    AllocationStatus.PENDING_QUALITY_ASSESSMENT: {
        AllocationStatus.QUARANTINE_REQUIRED,
        AllocationStatus.INSPECTION_PENDING,
        AllocationStatus.CANCELLED,
    },
    AllocationStatus.QUARANTINE_REQUIRED: {
        AllocationStatus.QUARANTINED,
    },
    AllocationStatus.QUARANTINED: {
        AllocationStatus.INSPECTION_PENDING,
        AllocationStatus.DECISION_PENDING,
    },
    AllocationStatus.INSPECTION_PENDING: {
        AllocationStatus.INSPECTION_IN_PROGRESS,
    },
    AllocationStatus.INSPECTION_IN_PROGRESS: {
        AllocationStatus.DECISION_PENDING,
        AllocationStatus.INSPECTION_PENDING,
    },
    AllocationStatus.DECISION_PENDING: {
        AllocationStatus.QUALITY_APPROVED,
        AllocationStatus.REJECTION_PENDING_APPROVAL,
        AllocationStatus.REINSPECTION_REQUIRED,
    },
    AllocationStatus.QUALITY_APPROVED: {
        AllocationStatus.RELEASE_PENDING_APPROVAL,
    },
    AllocationStatus.RELEASE_PENDING_APPROVAL: {
        AllocationStatus.RELEASED_FOR_PUTAWAY,
    },
    AllocationStatus.REJECTION_PENDING_APPROVAL: {
        AllocationStatus.REJECTED_PENDING_DISPOSITION,
    },
    AllocationStatus.REINSPECTION_REQUIRED: {
        AllocationStatus.INSPECTION_PENDING,
    },
    AllocationStatus.CANCELLED: set(),
    AllocationStatus.SUPERSEDED_BY_SPLIT: set(),
    AllocationStatus.SUPERSEDED: set(),
    AllocationStatus.RELEASED_FOR_PUTAWAY: set(),
    AllocationStatus.REJECTED_PENDING_DISPOSITION: set(),
}


class AvailabilityClass(StrEnum):
    BLOCKED = "BLOCKED"
    QUARANTINE = "QUARANTINE"
    AVAILABLE_FOR_PUTAWAY = "AVAILABLE_FOR_PUTAWAY"
    REJECTED_NOT_AVAILABLE = "REJECTED_NOT_AVAILABLE"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


class QualityStatus(StrEnum):
    NOT_ASSESSED = "NOT_ASSESSED"
    INSPECTION_REQUIRED = "INSPECTION_REQUIRED"
    UNDER_INSPECTION = "UNDER_INSPECTION"
    PASSED = "PASSED"
    PASSED_WITH_OBSERVATIONS = "PASSED_WITH_OBSERVATIONS"
    FAILED = "FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"
    REINSPECTION_REQUIRED = "REINSPECTION_REQUIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


# ---------------------------------------------------------------------------
# Split
# ---------------------------------------------------------------------------

class SplitReason(StrEnum):
    PARTIAL_RELEASE = "PARTIAL_RELEASE"
    PARTIAL_REJECTION = "PARTIAL_REJECTION"
    DIFFERENT_INSPECTION_RESULT = "DIFFERENT_INSPECTION_RESULT"
    DIFFERENT_LOT_OBSERVATION = "DIFFERENT_LOT_OBSERVATION"
    DIFFERENT_EXPIRATION = "DIFFERENT_EXPIRATION"
    DIFFERENT_CONDITION = "DIFFERENT_CONDITION"
    CORRECTION_BY_REVISION = "CORRECTION_BY_REVISION"
    OTHER_APPROVED = "OTHER_APPROVED"


# ---------------------------------------------------------------------------
# Quarantine Case
# ---------------------------------------------------------------------------

class QuarantineSourceType(StrEnum):
    INBOUND_RECEIPT = "INBOUND_RECEIPT"
    RECEPTION_DIFFERENCE = "RECEPTION_DIFFERENCE"
    QUALITY_PLAN = "QUALITY_PLAN"
    MANUAL_AUTHORIZED_HOLD = "MANUAL_AUTHORIZED_HOLD"
    EXPIRATION_ALERT = "EXPIRATION_ALERT"
    DOCUMENT_REVIEW = "DOCUMENT_REVIEW"
    SEAL_ANOMALY = "SEAL_ANOMALY"
    LEGACY_IMPORT = "LEGACY_IMPORT"


class QuarantineStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PHYSICAL_PLACEMENT_PENDING = "PHYSICAL_PLACEMENT_PENDING"
    INSPECTION_PENDING = "INSPECTION_PENDING"
    INSPECTION_IN_PROGRESS = "INSPECTION_IN_PROGRESS"
    INSPECTION_PAUSED = "INSPECTION_PAUSED"
    DECISION_PENDING = "DECISION_PENDING"
    QUALITY_APPROVED = "QUALITY_APPROVED"
    RELEASE_PENDING_APPROVAL = "RELEASE_PENDING_APPROVAL"
    PARTIALLY_RELEASED = "PARTIALLY_RELEASED"
    RELEASED = "RELEASED"
    REJECTION_PENDING_APPROVAL = "REJECTION_PENDING_APPROVAL"
    PARTIALLY_REJECTED = "PARTIALLY_REJECTED"
    REJECTED = "REJECTED"
    REINSPECTION_REQUIRED = "REINSPECTION_REQUIRED"
    FOLLOW_UP_REQUIRED = "FOLLOW_UP_REQUIRED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"
    CLOSED = "CLOSED"


QUARANTINE_STATUS_TRANSITIONS: dict[str, set[str]] = {
    QuarantineStatus.DRAFT: {QuarantineStatus.ACTIVE, QuarantineStatus.CANCELLED},
    QuarantineStatus.ACTIVE: {
        QuarantineStatus.PHYSICAL_PLACEMENT_PENDING,
        QuarantineStatus.INSPECTION_PENDING,
        QuarantineStatus.CANCELLED,
    },
    QuarantineStatus.PHYSICAL_PLACEMENT_PENDING: {
        QuarantineStatus.INSPECTION_PENDING,
        QuarantineStatus.ACTIVE,
    },
    QuarantineStatus.INSPECTION_PENDING: {
        QuarantineStatus.INSPECTION_IN_PROGRESS,
    },
    QuarantineStatus.INSPECTION_IN_PROGRESS: {
        QuarantineStatus.INSPECTION_PAUSED,
        QuarantineStatus.DECISION_PENDING,
    },
    QuarantineStatus.INSPECTION_PAUSED: {
        QuarantineStatus.INSPECTION_IN_PROGRESS,
    },
    QuarantineStatus.DECISION_PENDING: {
        QuarantineStatus.QUALITY_APPROVED,
        QuarantineStatus.REJECTION_PENDING_APPROVAL,
        QuarantineStatus.REINSPECTION_REQUIRED,
        QuarantineStatus.FOLLOW_UP_REQUIRED,
    },
    QuarantineStatus.QUALITY_APPROVED: {
        QuarantineStatus.RELEASE_PENDING_APPROVAL,
    },
    QuarantineStatus.RELEASE_PENDING_APPROVAL: {
        QuarantineStatus.RELEASED,
        QuarantineStatus.PARTIALLY_RELEASED,
    },
    QuarantineStatus.REJECTION_PENDING_APPROVAL: {
        QuarantineStatus.REJECTED,
        QuarantineStatus.PARTIALLY_REJECTED,
    },
    QuarantineStatus.REINSPECTION_REQUIRED: {
        QuarantineStatus.INSPECTION_PENDING,
    },
    QuarantineStatus.CANCELLED: set(),
    QuarantineStatus.SUPERSEDED: set(),
    QuarantineStatus.CLOSED: set(),
    QuarantineStatus.RELEASED: {QuarantineStatus.CLOSED},
    QuarantineStatus.PARTIALLY_RELEASED: {
        QuarantineStatus.RELEASED,
        QuarantineStatus.REINSPECTION_REQUIRED,
        QuarantineStatus.CLOSED,
    },
    QuarantineStatus.REJECTED: {QuarantineStatus.CLOSED},
    QuarantineStatus.PARTIALLY_REJECTED: {
        QuarantineStatus.REJECTED,
        QuarantineStatus.REINSPECTION_REQUIRED,
        QuarantineStatus.CLOSED,
    },
    QuarantineStatus.FOLLOW_UP_REQUIRED: {
        QuarantineStatus.INSPECTION_PENDING,
        QuarantineStatus.CANCELLED,
    },
}


class QuarantineSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PhysicalSegregationStatus(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CONFIRMED_WITH_OBSERVATION = "CONFIRMED_WITH_OBSERVATION"
    FAILED = "FAILED"
    SUPERSEDED = "SUPERSEDED"


# ---------------------------------------------------------------------------
# Quarantine Zone
# ---------------------------------------------------------------------------

class QuarantineZoneStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"
    MAINTENANCE = "MAINTENANCE"
    ARCHIVED = "ARCHIVED"


# ---------------------------------------------------------------------------
# Placement
# ---------------------------------------------------------------------------

class PlacementStatus(StrEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CONFIRMED_WITH_OBSERVATION = "CONFIRMED_WITH_OBSERVATION"
    FAILED = "FAILED"
    SUPERSEDED = "SUPERSEDED"


# ---------------------------------------------------------------------------
# Inspection
# ---------------------------------------------------------------------------

class InspectionStatus(StrEnum):
    CREATED = "CREATED"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    VALIDATING = "VALIDATING"
    REQUIRES_CORRECTION = "REQUIRES_CORRECTION"
    COMPLETED = "COMPLETED"
    INCONCLUSIVE = "INCONCLUSIVE"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"


class InspectionOverallResult(StrEnum):
    NOT_CALCULATED = "NOT_CALCULATED"
    PASS = "PASS"
    PASS_WITH_OBSERVATIONS = "PASS_WITH_OBSERVATIONS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    REINSPECTION_REQUIRED = "REINSPECTION_REQUIRED"


# ---------------------------------------------------------------------------
# Inspection Control
# ---------------------------------------------------------------------------

class InspectionControlStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    BLOCKED = "BLOCKED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    SUPERSEDED = "SUPERSEDED"


class ControlResultStatus(StrEnum):
    PASS = "PASS"
    PASS_WITH_OBSERVATION = "PASS_WITH_OBSERVATION"
    FAIL = "FAIL"
    CONDITIONAL = "CONDITIONAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    INVALID_MEASUREMENT = "INVALID_MEASUREMENT"


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------

class MeasurementType(StrEnum):
    WEIGHT = "WEIGHT"
    TEMPERATURE = "TEMPERATURE"
    LENGTH = "LENGTH"
    VOLUME = "VOLUME"
    COUNT = "COUNT"
    PERCENTAGE = "PERCENTAGE"
    OTHER_APPROVED = "OTHER_APPROVED"


class ToleranceResult(StrEnum):
    WITHIN_TOLERANCE = "WITHIN_TOLERANCE"
    BELOW_MINIMUM = "BELOW_MINIMUM"
    ABOVE_MAXIMUM = "ABOVE_MAXIMUM"
    EXACT_MATCH = "EXACT_MATCH"
    NOT_EVALUATED = "NOT_EVALUATED"
    INVALID_UNIT = "INVALID_UNIT"
    INCOMPLETE = "INCOMPLETE"


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

class SampleSetStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class SampleReferenceType(StrEnum):
    RECEIVED_LINE = "RECEIVED_LINE"
    LOT_OBSERVATION = "LOT_OBSERVATION"
    SERIAL_OBSERVATION = "SERIAL_OBSERVATION"
    PACKAGE_ORDINAL = "PACKAGE_ORDINAL"
    UNIT_ORDINAL = "UNIT_ORDINAL"
    OPERATOR_GUIDED_REFERENCE = "OPERATOR_GUIDED_REFERENCE"


# ---------------------------------------------------------------------------
# Certificate Review
# ---------------------------------------------------------------------------

class CertificateReviewStatus(StrEnum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    UNREADABLE = "UNREADABLE"
    EXPIRED = "EXPIRED"
    NOT_MATCHING = "NOT_MATCHING"
    METADATA_VALID = "METADATA_VALID"
    METADATA_INVALID = "METADATA_INVALID"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    NOT_APPLICABLE = "NOT_APPLICABLE"


# ---------------------------------------------------------------------------
# Disposition Decision
# ---------------------------------------------------------------------------

class DecisionType(StrEnum):
    APPROVE_QUALITY = "APPROVE_QUALITY"
    KEEP_IN_QUARANTINE = "KEEP_IN_QUARANTINE"
    REQUIRE_REINSPECTION = "REQUIRE_REINSPECTION"
    REJECT = "REJECT"
    REQUEST_ADDITIONAL_EVIDENCE = "REQUEST_ADDITIONAL_EVIDENCE"
    REQUEST_DOCUMENT_CORRECTION = "REQUEST_DOCUMENT_CORRECTION"
    REQUEST_SUPERVISOR_REVIEW = "REQUEST_SUPERVISOR_REVIEW"


class DecisionStatus(StrEnum):
    PROPOSED = "PROPOSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"
    CANCELLED = "CANCELLED"


# ---------------------------------------------------------------------------
# Approval
# ---------------------------------------------------------------------------

class ApprovalDecision(StrEnum):
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    REQUIRE_ADDITIONAL_REVIEW = "REQUIRE_ADDITIONAL_REVIEW"
    REJECT_PROPOSAL = "REJECT_PROPOSAL"


# ---------------------------------------------------------------------------
# Release
# ---------------------------------------------------------------------------

class ReleaseType(StrEnum):
    TOTAL = "TOTAL"
    PARTIAL = "PARTIAL"


class ReleaseStatus(StrEnum):
    REQUESTED = "REQUESTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"


# ---------------------------------------------------------------------------
# Rejection
# ---------------------------------------------------------------------------

class RejectionType(StrEnum):
    TOTAL = "TOTAL"
    PARTIAL = "PARTIAL"


class RejectionStatus(StrEnum):
    REQUESTED = "REQUESTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"


class FutureDispositionRecommendation(StrEnum):
    RETURN_TO_SUPPLIER_FUTURE = "RETURN_TO_SUPPLIER_FUTURE"
    DESTRUCTION_REVIEW_FUTURE = "DESTRUCTION_REVIEW_FUTURE"
    REWORK_REVIEW_FUTURE = "REWORK_REVIEW_FUTURE"
    CLAIM_REVIEW_FUTURE = "CLAIM_REVIEW_FUTURE"
    KEEP_BLOCKED = "KEEP_BLOCKED"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# Reinspection
# ---------------------------------------------------------------------------

class ReinspectionStatus(StrEnum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MATERIALIZED = "MATERIALIZED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# ---------------------------------------------------------------------------
# Disposition Event
# ---------------------------------------------------------------------------

class DispositionEventType(StrEnum):
    ALLOCATION_MATERIALIZED = "ALLOCATION_MATERIALIZED"
    QUARANTINE_REQUIRED = "QUARANTINE_REQUIRED"
    QUARANTINE_OPENED = "QUARANTINE_OPENED"
    PHYSICAL_PLACEMENT_CONFIRMED = "PHYSICAL_PLACEMENT_CONFIRMED"
    INSPECTION_MATERIALIZED = "INSPECTION_MATERIALIZED"
    INSPECTION_STARTED = "INSPECTION_STARTED"
    INSPECTION_PAUSED = "INSPECTION_PAUSED"
    CONTROL_COMPLETED = "CONTROL_COMPLETED"
    MEASUREMENT_RECORDED = "MEASUREMENT_RECORDED"
    CERTIFICATE_REVIEWED = "CERTIFICATE_REVIEWED"
    INSPECTION_COMPLETED = "INSPECTION_COMPLETED"
    QUALITY_DECISION_PROPOSED = "QUALITY_DECISION_PROPOSED"
    QUALITY_APPROVED = "QUALITY_APPROVED"
    QUARANTINE_MAINTAINED = "QUARANTINE_MAINTAINED"
    REINSPECTION_REQUESTED = "REINSPECTION_REQUESTED"
    RELEASE_REQUESTED = "RELEASE_REQUESTED"
    RELEASE_APPROVED = "RELEASE_APPROVED"
    RELEASE_EXECUTED = "RELEASE_EXECUTED"
    PARTIAL_RELEASE_EXECUTED = "PARTIAL_RELEASE_EXECUTED"
    REJECTION_REQUESTED = "REJECTION_REQUESTED"
    REJECTION_APPROVED = "REJECTION_APPROVED"
    REJECTION_EXECUTED = "REJECTION_EXECUTED"
    PARTIAL_REJECTION_EXECUTED = "PARTIAL_REJECTION_EXECUTED"
    ALLOCATION_SPLIT = "ALLOCATION_SPLIT"
    NC_ISSUED = "NC_ISSUED"
    INTEGRITY_FAILED = "INTEGRITY_FAILED"
    CASE_CLOSED = "CASE_CLOSED"


# ---------------------------------------------------------------------------
# Trigger evaluation
# ---------------------------------------------------------------------------

class TriggerEvaluationResult(StrEnum):
    QUARANTINE_REQUIRED = "QUARANTINE_REQUIRED"
    INSPECTION_REQUIRED = "INSPECTION_REQUIRED"
    DIRECT_RELEASE_ELIGIBLE = "DIRECT_RELEASE_ELIGIBLE"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    POLICY_CONFLICT = "POLICY_CONFLICT"
    INFORMATION_INCOMPLETE = "INFORMATION_INCOMPLETE"


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

class InspectionEvidenceType(StrEnum):
    PRODUCT_PHOTO = "PRODUCT_PHOTO"
    PACKAGING_PHOTO = "PACKAGING_PHOTO"
    LABEL_PHOTO = "LABEL_PHOTO"
    SCALE_DISPLAY_PHOTO = "SCALE_DISPLAY_PHOTO"
    TEMPERATURE_DISPLAY_PHOTO = "TEMPERATURE_DISPLAY_PHOTO"
    CERTIFICATE = "CERTIFICATE"
    MEASUREMENT_REPORT = "MEASUREMENT_REPORT"
    SAMPLE_PHOTO = "SAMPLE_PHOTO"
    QUARANTINE_LOCATION_PHOTO = "QUARANTINE_LOCATION_PHOTO"
    SUPERVISOR_NOTE = "SUPERVISOR_NOTE"
    OTHER = "OTHER"
