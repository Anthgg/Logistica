"""Domain value objects and enums for Purchase Requisitions (Phase 031)."""

from __future__ import annotations

from enum import StrEnum


class RequisitionStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    RETURNED_FOR_CHANGES = "RETURNED_FOR_CHANGES"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


class RequisitionPriority(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"


class RevisionStatus(StrEnum):
    EDITABLE = "EDITABLE"
    SUBMITTED = "SUBMITTED"
    FROZEN = "FROZEN"
    SUPERSEDED = "SUPERSEDED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DecisionType(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    RETURN_FOR_CHANGES = "RETURN_FOR_CHANGES"
    START_REVIEW = "START_REVIEW"
    WITHDRAW = "WITHDRAW"
    CANCEL = "CANCEL"


class CommentType(StrEnum):
    GENERAL = "GENERAL"
    REQUESTER_NOTE = "REQUESTER_NOTE"
    REVIEWER_NOTE = "REVIEWER_NOTE"
    APPROVAL_NOTE = "APPROVAL_NOTE"
    REJECTION_NOTE = "REJECTION_NOTE"
    RETURN_NOTE = "RETURN_NOTE"
    SYSTEM_NOTE = "SYSTEM_NOTE"


class CommentVisibility(StrEnum):
    INTERNAL = "INTERNAL"
    REQUESTER_AND_REVIEWERS = "REQUESTER_AND_REVIEWERS"
    AUDIT_ONLY = "AUDIT_ONLY"


class LineStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REMOVED = "REMOVED"
    CANCELLED = "CANCELLED"


class DuplicateResult(StrEnum):
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    HIGH_PROBABILITY_DUPLICATE = "HIGH_PROBABILITY_DUPLICATE"
    NOT_DUPLICATE = "NOT_DUPLICATE"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


# Allowed state machine transitions
ALLOWED_TRANSITIONS: dict[RequisitionStatus, set[RequisitionStatus]] = {
    RequisitionStatus.DRAFT: {
        RequisitionStatus.SUBMITTED,
        RequisitionStatus.CANCELLED,
    },
    RequisitionStatus.SUBMITTED: {
        RequisitionStatus.UNDER_REVIEW,
        RequisitionStatus.APPROVED,
        RequisitionStatus.REJECTED,
        RequisitionStatus.RETURNED_FOR_CHANGES,
        RequisitionStatus.WITHDRAWN,
    },
    RequisitionStatus.UNDER_REVIEW: {
        RequisitionStatus.APPROVED,
        RequisitionStatus.REJECTED,
        RequisitionStatus.RETURNED_FOR_CHANGES,
        RequisitionStatus.WITHDRAWN,
    },
    RequisitionStatus.RETURNED_FOR_CHANGES: {
        RequisitionStatus.SUBMITTED,
        RequisitionStatus.CANCELLED,
    },
    RequisitionStatus.APPROVED: {
        RequisitionStatus.ARCHIVED,
        RequisitionStatus.CANCELLED,
    },
    RequisitionStatus.REJECTED: {
        RequisitionStatus.ARCHIVED,
    },
    RequisitionStatus.WITHDRAWN: set(),
    RequisitionStatus.CANCELLED: set(),
    RequisitionStatus.ARCHIVED: set(),
}

# Priorities that require reinforced justification
REINFORCED_JUSTIFICATION_PRIORITIES = {
    RequisitionPriority.URGENT,
    RequisitionPriority.CRITICAL,
}

# Decision types that produce a final (immutable) decision
FINAL_DECISION_TYPES = {
    DecisionType.APPROVE,
    DecisionType.REJECT,
    DecisionType.WITHDRAW,
    DecisionType.CANCEL,
}

# Comment types that are immutable (decision-bound)
IMMUTABLE_COMMENT_TYPES = {
    CommentType.APPROVAL_NOTE,
    CommentType.REJECTION_NOTE,
}
