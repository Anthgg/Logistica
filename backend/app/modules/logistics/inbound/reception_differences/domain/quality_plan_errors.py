from app.core.exceptions import ApplicationError


class QualityInspectionPlanError(ApplicationError):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(code, message, status_code)


def quality_plan_error(name: str, message: str, status_code: int = 400) -> QualityInspectionPlanError:
    return QualityInspectionPlanError(name, message, status_code)


ERROR_CODES = (
    "QualityPlanNotFound",
    "QualityPlanVersionNotFound",
    "QualityPlanAlreadyExists",
    "QualityPlanStatusInvalid",
    "QualityPlanVersionStatusInvalid",
    "QualityPlanScopeConflict",
    "QualityPlanScopeNotFound",
    "QualityPlanControlNotFound",
    "QualityPlanToleranceNotFound",
    "QualityPlanSamplingNotFound",
    "QualityPlanCertificateNotFound",
    "QualityPlanActivationFailed",
    "QualityPlanDeactivationFailed",
    "QualityPlanArchiveFailed",
    "QualityPlanVersionConflict",
    "QualityPlanConflictDetected",
    "QualityPlanValidationFailed",
    "QualityPlanResolutionFailed",
    "QualityPlanSnapshotFailed",
    "QualityPlanIntegrityFailed",
    "QualityPlanControlTypeInvalid",
    "QualityPlanToleranceTypeInvalid",
    "QualityPlanToleranceValueInvalid",
    "QualityPlanSamplingTypeInvalid",
    "QualityPlanScopeDuplicate",
    "QualityPlanControlDuplicate",
    "QualityPlanConditionInvalid",
    "QualityPlanReferenceFileInvalid",
    "QualityPlanEditFailed",
    "QualityPlanFutureTemplateInvalid",
)


class QualityPlanNotFound(QualityInspectionPlanError): pass
class QualityPlanVersionNotFound(QualityInspectionPlanError): pass
class QualityPlanAlreadyExists(QualityInspectionPlanError): pass
class QualityPlanStatusInvalid(QualityInspectionPlanError): pass
class QualityPlanVersionStatusInvalid(QualityInspectionPlanError): pass
class QualityPlanScopeConflict(QualityInspectionPlanError): pass
class QualityPlanScopeNotFound(QualityInspectionPlanError): pass
class QualityPlanControlNotFound(QualityInspectionPlanError): pass
class QualityPlanToleranceNotFound(QualityInspectionPlanError): pass
class QualityPlanSamplingNotFound(QualityInspectionPlanError): pass
class QualityPlanCertificateNotFound(QualityInspectionPlanError): pass
class QualityPlanActivationFailed(QualityInspectionPlanError): pass
class QualityPlanDeactivationFailed(QualityInspectionPlanError): pass
class QualityPlanArchiveFailed(QualityInspectionPlanError): pass
class QualityPlanVersionConflict(QualityInspectionPlanError): pass
class QualityPlanConflictDetected(QualityInspectionPlanError): pass
class QualityPlanValidationFailed(QualityInspectionPlanError): pass
class QualityPlanResolutionFailed(QualityInspectionPlanError): pass
class QualityPlanSnapshotFailed(QualityInspectionPlanError): pass
class QualityPlanIntegrityFailed(QualityInspectionPlanError): pass
class QualityPlanControlTypeInvalid(QualityInspectionPlanError): pass
class QualityPlanToleranceTypeInvalid(QualityInspectionPlanError): pass
class QualityPlanToleranceValueInvalid(QualityInspectionPlanError): pass
class QualityPlanSamplingTypeInvalid(QualityInspectionPlanError): pass
class QualityPlanScopeDuplicate(QualityInspectionPlanError): pass
class QualityPlanControlDuplicate(QualityInspectionPlanError): pass
class QualityPlanConditionInvalid(QualityInspectionPlanError): pass
class QualityPlanReferenceFileInvalid(QualityInspectionPlanError): pass
class QualityPlanEditFailed(QualityInspectionPlanError): pass
class QualityPlanFutureTemplateInvalid(QualityInspectionPlanError): pass
