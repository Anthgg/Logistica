"""Domain exceptions for Phase 035 — Procurement Approvals Engine."""

from __future__ import annotations


class ProcurementApprovalDomainError(Exception):
    """Base exception for procurement approval domain errors."""

    code: str = "PROCUREMENT_APPROVAL_ERROR"
    http_status: int = 400

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.__doc__ or self.code
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Policy & Version Errors
# ---------------------------------------------------------------------------
class ApprovalPolicyNotFound(ProcurementApprovalDomainError):
    """The approval policy was not found or belongs to another organization."""
    code = "APPROVAL_POLICY_NOT_FOUND"
    http_status = 404


class ApprovalPolicyVersionNotFound(ProcurementApprovalDomainError):
    """The approval policy version was not found."""
    code = "APPROVAL_POLICY_VERSION_NOT_FOUND"
    http_status = 404


class ApprovalPolicyVersionImmutable(ProcurementApprovalDomainError):
    """Active or retired policy versions cannot be modified."""
    code = "APPROVAL_POLICY_VERSION_IMMUTABLE"
    http_status = 409


class ApprovalPolicyConditionInvalid(ProcurementApprovalDomainError):
    """The policy condition parameter or operator is invalid."""
    code = "APPROVAL_POLICY_CONDITION_INVALID"
    http_status = 422


class ApprovalPolicyAmountRangeInvalid(ProcurementApprovalDomainError):
    """The monetary range parameters are invalid or inverted."""
    code = "APPROVAL_POLICY_AMOUNT_RANGE_INVALID"
    http_status = 422


class ApprovalPolicyConflict(ProcurementApprovalDomainError):
    """Blocking conflict detected in policy configuration (overlapping ranges, cyclic steps, etc.)."""
    code = "APPROVAL_POLICY_CONFLICT"
    http_status = 409


class ApprovalPolicyNoMatch(ProcurementApprovalDomainError):
    """No active approval policy matched the subject resource context."""
    code = "APPROVAL_POLICY_NO_MATCH"
    http_status = 404


class ApprovalPolicyMultipleMatches(ProcurementApprovalDomainError):
    """Multiple non-combinable policies matched with equal priority."""
    code = "APPROVAL_POLICY_MULTIPLE_MATCHES"
    http_status = 409


class ApprovalPolicyFallbackMissing(ProcurementApprovalDomainError):
    """No active fallback policy exists for the subject type and organization."""
    code = "APPROVAL_POLICY_FALLBACK_MISSING"
    http_status = 404


class ApprovalPolicyApproverUnresolved(ProcurementApprovalDomainError):
    """An approver source could not be resolved to any active user."""
    code = "APPROVAL_POLICY_APPROVER_UNRESOLVED"
    http_status = 422


class ApprovalPolicyChainInvalid(ProcurementApprovalDomainError):
    """The compiled approval chain is invalid or empty."""
    code = "APPROVAL_POLICY_CHAIN_INVALID"
    http_status = 422


class ApprovalPolicyCurrencyConversionMissing(ProcurementApprovalDomainError):
    """Approved currency exchange rate snapshot missing for cross-currency comparison."""
    code = "APPROVAL_POLICY_CURRENCY_CONVERSION_MISSING"
    http_status = 422


# ---------------------------------------------------------------------------
# Request & Subject Errors
# ---------------------------------------------------------------------------
class ApprovalRequestNotFound(ProcurementApprovalDomainError):
    """The approval request was not found."""
    code = "APPROVAL_REQUEST_NOT_FOUND"
    http_status = 404


class ApprovalRequestAlreadyExists(ProcurementApprovalDomainError):
    """An active approval request already exists for this subject revision."""
    code = "APPROVAL_REQUEST_ALREADY_EXISTS"
    http_status = 409


class ApprovalRequestStatusInvalid(ProcurementApprovalDomainError):
    """The operation is invalid for the current approval request status."""
    code = "APPROVAL_REQUEST_STATUS_INVALID"
    http_status = 409


class ApprovalRequestSubjectChanged(ProcurementApprovalDomainError):
    """The subject resource was modified while approval was in progress."""
    code = "APPROVAL_REQUEST_SUBJECT_CHANGED"
    http_status = 409


class ApprovalRequestRevisionMismatch(ProcurementApprovalDomainError):
    """The request revision does not match the active subject revision."""
    code = "APPROVAL_REQUEST_REVISION_MISMATCH"
    http_status = 409


class ApprovalRequestAlreadyCompleted(ProcurementApprovalDomainError):
    """The approval request has already reached a final decision."""
    code = "APPROVAL_REQUEST_ALREADY_COMPLETED"
    http_status = 409


class ApprovalRequestIntegrityFailed(ProcurementApprovalDomainError):
    """Approval request integrity check or hash chain verification failed."""
    code = "APPROVAL_REQUEST_INTEGRITY_FAILED"
    http_status = 409


# ---------------------------------------------------------------------------
# Step, Assignment & Decision Errors
# ---------------------------------------------------------------------------
class ApprovalStepNotActive(ProcurementApprovalDomainError):
    """The approval step is not currently active."""
    code = "APPROVAL_STEP_NOT_ACTIVE"
    http_status = 409


class ApprovalStepAlreadyCompleted(ProcurementApprovalDomainError):
    """The approval step has already completed."""
    code = "APPROVAL_STEP_ALREADY_COMPLETED"
    http_status = 409


class ApprovalAssignmentNotFound(ProcurementApprovalDomainError):
    """The approval assignment was not found."""
    code = "APPROVAL_ASSIGNMENT_NOT_FOUND"
    http_status = 404


class ApprovalAssignmentNotAuthorized(ProcurementApprovalDomainError):
    """The acting user is not authorized for this assignment."""
    code = "APPROVAL_ASSIGNMENT_NOT_AUTHORIZED"
    http_status = 403


class ApprovalAssignmentExpired(ProcurementApprovalDomainError):
    """The approval assignment deadline has expired."""
    code = "APPROVAL_ASSIGNMENT_EXPIRED"
    http_status = 409


class ApprovalDecisionAlreadyRecorded(ProcurementApprovalDomainError):
    """A decision has already been recorded for this assignment."""
    code = "APPROVAL_DECISION_ALREADY_RECORDED"
    http_status = 409


class ApprovalDecisionNotAllowed(ProcurementApprovalDomainError):
    """The specified decision type is not allowed for this step."""
    code = "APPROVAL_DECISION_NOT_ALLOWED"
    http_status = 422


class ApprovalSelfApprovalDenied(ProcurementApprovalDomainError):
    """Self-approval is denied: creator or requester cannot approve their own resource."""
    code = "APPROVAL_SELF_APPROVAL_DENIED"
    http_status = 403


class ApprovalSeparationOfDutiesViolation(ProcurementApprovalDomainError):
    """Separation of duties violation: same user cannot approve multiple mandatory levels."""
    code = "APPROVAL_SEPARATION_OF_DUTIES_VIOLATION"
    http_status = 403


class ApprovalConflictOfInterest(ProcurementApprovalDomainError):
    """A conflict of interest declaration blocks this approval action."""
    code = "APPROVAL_CONFLICT_OF_INTEREST"
    http_status = 403


# ---------------------------------------------------------------------------
# Delegation & Escalation Errors
# ---------------------------------------------------------------------------
class ApprovalDelegationInvalid(ProcurementApprovalDomainError):
    """The approval delegation configuration or dates are invalid."""
    code = "APPROVAL_DELEGATION_INVALID"
    http_status = 422


class ApprovalDelegationCycle(ProcurementApprovalDomainError):
    """Cyclic delegation detected (A -> B -> A)."""
    code = "APPROVAL_DELEGATION_CYCLE"
    http_status = 409


class ApprovalDelegationNotAuthorized(ProcurementApprovalDomainError):
    """The user is not authorized to create or approve this delegation."""
    code = "APPROVAL_DELEGATION_NOT_AUTHORIZED"
    http_status = 403


class ApprovalDelegationExpired(ProcurementApprovalDomainError):
    """The approval delegation has expired."""
    code = "APPROVAL_DELEGATION_EXPIRED"
    http_status = 409


class ApprovalEscalationInvalid(ProcurementApprovalDomainError):
    """The escalation target or rule configuration is invalid."""
    code = "APPROVAL_ESCALATION_INVALID"
    http_status = 422


# ---------------------------------------------------------------------------
# Audit Seal Errors
# ---------------------------------------------------------------------------
class ApprovalAuditSealNotFound(ProcurementApprovalDomainError):
    """The approval audit seal was not found."""
    code = "APPROVAL_AUDIT_SEAL_NOT_FOUND"
    http_status = 404


class ApprovalAuditSealInvalid(ProcurementApprovalDomainError):
    """The audit seal is invalid or failed verification."""
    code = "APPROVAL_AUDIT_SEAL_INVALID"
    http_status = 409


class ApprovalAuditSealHashMismatch(ProcurementApprovalDomainError):
    """Audit seal SHA-256 hash mismatch detected — data tampering suspected."""
    code = "APPROVAL_AUDIT_SEAL_HASH_MISMATCH"
    http_status = 409


class ApprovalAuditSealSignatureInvalid(ProcurementApprovalDomainError):
    """Audit seal KMS digital signature is invalid."""
    code = "APPROVAL_AUDIT_SEAL_SIGNATURE_INVALID"
    http_status = 409


class ApprovalAuditSealKeyUnavailable(ProcurementApprovalDomainError):
    """KMS verification key is unavailable."""
    code = "APPROVAL_AUDIT_SEAL_KEY_UNAVAILABLE"
    http_status = 503
