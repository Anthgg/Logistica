from app.core.exceptions import ApplicationError


class ReceptionDifferenceError(ApplicationError):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(code, message, status_code)


def reception_difference_error(name: str, message: str, status_code: int = 400) -> ReceptionDifferenceError:
    return ReceptionDifferenceError(name, message, status_code)


ERROR_CODES = (
    "ReceptionDifferenceCaseNotFound",
    "ReceptionDifferenceCaseAlreadyExists",
    "ReceptionDifferenceCaseStatusInvalid",
    "ReceptionDifferenceCaseNotEditable",
    "ReceptionDifferenceRevisionConflict",
    "ReceptionDifferenceCandidateNotFound",
    "ReceptionDifferenceCandidateAlreadyFormalized",
    "ReceptionDifferenceCandidateInvalid",
    "ReceptionDifferenceItemNotFound",
    "ReceptionDifferenceTypeInvalid",
    "ReceptionDifferenceQuantityInvalid",
    "ReceptionDifferenceUnitInvalid",
    "ReceptionDifferenceProductInvalid",
    "ReceptionDifferenceEvidenceRequired",
    "ReceptionDifferenceEvidenceUnavailable",
    "ReceptionDifferenceResponsiblePartyRequired",
    "ReceptionDifferenceResponsibilityInvalid",
    "ReceptionDifferenceResponsibilityConflict",
    "ReceptionDifferenceReviewRequired",
    "ReceptionDifferenceApprovalRequired",
    "ReceptionDifferenceSeparationOfDutiesViolation",
    "ReceptionDifferenceValidationFailed",
    "ReceptionDifferenceAlreadyIssued",
    "ReceptionDifferenceDocumentIssueFailed",
    "ReceptionDifferenceAcknowledgementInvalid",
    "ReceptionDifferenceDisputeConflict",
    "ReceptionDifferenceIntegrityFailed",
)


class ReceptionDifferenceCaseNotFound(ReceptionDifferenceError): pass
class ReceptionDifferenceCaseAlreadyExists(ReceptionDifferenceError): pass
class ReceptionDifferenceCaseStatusInvalid(ReceptionDifferenceError): pass
class ReceptionDifferenceCaseNotEditable(ReceptionDifferenceError): pass
class ReceptionDifferenceRevisionConflict(ReceptionDifferenceError): pass
class ReceptionDifferenceCandidateNotFound(ReceptionDifferenceError): pass
class ReceptionDifferenceCandidateAlreadyFormalized(ReceptionDifferenceError): pass
class ReceptionDifferenceCandidateInvalid(ReceptionDifferenceError): pass
class ReceptionDifferenceItemNotFound(ReceptionDifferenceError): pass
class ReceptionDifferenceTypeInvalid(ReceptionDifferenceError): pass
class ReceptionDifferenceQuantityInvalid(ReceptionDifferenceError): pass
class ReceptionDifferenceUnitInvalid(ReceptionDifferenceError): pass
class ReceptionDifferenceProductInvalid(ReceptionDifferenceError): pass
class ReceptionDifferenceEvidenceRequired(ReceptionDifferenceError): pass
class ReceptionDifferenceEvidenceUnavailable(ReceptionDifferenceError): pass
class ReceptionDifferenceResponsiblePartyRequired(ReceptionDifferenceError): pass
class ReceptionDifferenceResponsibilityInvalid(ReceptionDifferenceError): pass
class ReceptionDifferenceResponsibilityConflict(ReceptionDifferenceError): pass
class ReceptionDifferenceReviewRequired(ReceptionDifferenceError): pass
class ReceptionDifferenceApprovalRequired(ReceptionDifferenceError): pass
class ReceptionDifferenceSeparationOfDutiesViolation(ReceptionDifferenceError): pass
class ReceptionDifferenceValidationFailed(ReceptionDifferenceError): pass
class ReceptionDifferenceAlreadyIssued(ReceptionDifferenceError): pass
class ReceptionDifferenceDocumentIssueFailed(ReceptionDifferenceError): pass
class ReceptionDifferenceAcknowledgementInvalid(ReceptionDifferenceError): pass
class ReceptionDifferenceDisputeConflict(ReceptionDifferenceError): pass
class ReceptionDifferenceIntegrityFailed(ReceptionDifferenceError): pass
