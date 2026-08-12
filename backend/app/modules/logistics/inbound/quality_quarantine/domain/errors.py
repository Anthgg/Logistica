"""Phase 042 — Quality Quarantine error classes."""

from __future__ import annotations

from typing import Any


class QualityQuarantineError(Exception):
    """Base error for quality quarantine module."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def _error(name: str, message: str, status_code: int = 400) -> type[QualityQuarantineError]:
    """Factory for concrete error classes."""

    class _Err(QualityQuarantineError):
        def __init__(self, **kw: Any) -> None:
            super().__init__(code=name, message=message.format(**kw), status_code=status_code, details=kw)

    _Err.__name__ = name
    _Err.__qualname__ = name
    return _Err


# ---------------------------------------------------------------------------
# Allocation errors
# ---------------------------------------------------------------------------

InboundInventoryAllocationNotFound = _error(
    "InboundInventoryAllocationNotFound",
    "Asignación de disposición {allocation_id} no encontrada.",
    404,
)

InboundInventoryAllocationAlreadyMaterialized = _error(
    "InboundInventoryAllocationAlreadyMaterialized",
    "La línea recibida {received_line_id} ya fue materializada.",
    409,
)

InboundInventoryAllocationQuantityExceeded = _error(
    "InboundInventoryAllocationQuantityExceeded",
    "La cantidad {quantity} excede la recibida {received_quantity}.",
    422,
)

InboundInventoryAllocationSplitInvalid = _error(
    "InboundInventoryAllocationSplitInvalid",
    "La división no es válida: la suma de hijos {child_sum} no coincide con {original}.",
    422,
)

InboundInventoryAllocationStatusInvalid = _error(
    "InboundInventoryAllocationStatusInvalid",
    "Transición de estado no permitida: {current} -> {target}.",
    422,
)

# ---------------------------------------------------------------------------
# Quarantine errors
# ---------------------------------------------------------------------------

QualityQuarantineCaseNotFound = _error(
    "QualityQuarantineCaseNotFound",
    "Caso de cuarentena {case_id} no encontrado.",
    404,
)

QualityQuarantineAlreadyExists = _error(
    "QualityQuarantineAlreadyExists",
    "Ya existe un caso activo para la asignación {allocation_id}.",
    409,
)

QualityQuarantineStatusInvalid = _error(
    "QualityQuarantineStatusInvalid",
    "Transición de cuarentena no permitida: {current} -> {target}.",
    422,
)

QualityQuarantineZoneInvalid = _error(
    "QualityQuarantineZoneInvalid",
    "Zona de cuarentena {zone_id} no válida o inactiva.",
    422,
)

QualityQuarantinePhysicalPlacementRequired = _error(
    "QualityQuarantinePhysicalPlacementRequired",
    "Se requiere confirmación de colocación física antes de continuar.",
    422,
)

# ---------------------------------------------------------------------------
# Inspection errors
# ---------------------------------------------------------------------------

QualityInspectionNotFound = _error(
    "QualityInspectionNotFound",
    "Inspección {inspection_id} no encontrada.",
    404,
)

QualityInspectionAlreadyExists = _error(
    "QualityInspectionAlreadyExists",
    "Ya existe una inspección activa para el caso {case_id}.",
    409,
)

QualityInspectionPlanNotResolved = _error(
    "QualityInspectionPlanNotResolved",
    "No se pudo resolver un plan de calidad aplicable.",
    422,
)

QualityInspectionPlanConflict = _error(
    "QualityInspectionPlanConflict",
    "Conflicto al resolver plan de calidad: {reason}.",
    422,
)

QualityInspectionStatusInvalid = _error(
    "QualityInspectionStatusInvalid",
    "Transición de inspección no permitida: {current} -> {target}.",
    422,
)

QualityInspectionControlNotFound = _error(
    "QualityInspectionControlNotFound",
    "Control {control_id} no encontrado.",
    404,
)

QualityInspectionControlResultInvalid = _error(
    "QualityInspectionControlResultInvalid",
    "Resultado de control inválido: {reason}.",
    422,
)

QualityInspectionRequiredControlPending = _error(
    "QualityInspectionRequiredControlPending",
    "Existen {count} controles obligatorios pendientes.",
    422,
)

QualityInspectionEvidenceRequired = _error(
    "QualityInspectionEvidenceRequired",
    "Evidencia obligatoria faltante: {missing}.",
    422,
)

QualityInspectionMeasurementInvalid = _error(
    "QualityInspectionMeasurementInvalid",
    "Medición inválida: {reason}.",
    422,
)

QualityInspectionUnitMismatch = _error(
    "QualityInspectionUnitMismatch",
    "Unidad incompatible: se esperaba {expected}, se recibió {received}.",
    422,
)

QualityInspectionToleranceFailed = _error(
    "QualityInspectionToleranceFailed",
    "Tolerancia no cumplida para control {control_id}.",
    422,
)

QualityInspectionSampleIncomplete = _error(
    "QualityInspectionSampleIncomplete",
    "Muestreo incompleto: {reason}.",
    422,
)

QualityInspectionCertificateMissing = _error(
    "QualityInspectionCertificateMissing",
    "Certificado requerido no encontrado: {certificate_type}.",
    422,
)

QualityInspectionAlreadyCompleted = _error(
    "QualityInspectionAlreadyCompleted",
    "La inspección {inspection_id} ya fue completada.",
    409,
)

# ---------------------------------------------------------------------------
# Decision errors
# ---------------------------------------------------------------------------

QualityDispositionDecisionInvalid = _error(
    "QualityDispositionDecisionInvalid",
    "Decisión de disposición inválida: {reason}.",
    422,
)

QualityDecisionApprovalRequired = _error(
    "QualityDecisionApprovalRequired",
    "Se requiere aprobación antes de continuar.",
    422,
)

QualitySeparationOfDutiesViolation = _error(
    "QualitySeparationOfDutiesViolation",
    "Violación de separación de funciones: {reason}.",
    403,
)

# ---------------------------------------------------------------------------
# Release errors
# ---------------------------------------------------------------------------

QuarantineReleaseNotAllowed = _error(
    "QuarantineReleaseNotAllowed",
    "Liberación no permitida: {reason}.",
    422,
)

QuarantineReleaseApprovalRequired = _error(
    "QuarantineReleaseApprovalRequired",
    "Se requiere aprobación de liberación.",
    422,
)

QuarantineReleaseQuantityInvalid = _error(
    "QuarantineReleaseQuantityInvalid",
    "Cantidad de liberación inválida: {reason}.",
    422,
)

QuarantineAlreadyReleased = _error(
    "QuarantineAlreadyReleased",
    "El caso {case_id} ya fue liberado.",
    409,
)

# ---------------------------------------------------------------------------
# Rejection errors
# ---------------------------------------------------------------------------

QuarantineRejectionNotAllowed = _error(
    "QuarantineRejectionNotAllowed",
    "Rechazo no permitido: {reason}.",
    422,
)

QuarantineRejectionApprovalRequired = _error(
    "QuarantineRejectionApprovalRequired",
    "Se requiere aprobación de rechazo.",
    422,
)

QuarantineAlreadyRejected = _error(
    "QuarantineAlreadyRejected",
    "El caso {case_id} ya fue rechazado.",
    409,
)

# ---------------------------------------------------------------------------
# NC errors
# ---------------------------------------------------------------------------

QualityNonConformityAlreadyIssued = _error(
    "QualityNonConformityAlreadyIssued",
    "Ya existe una NC emitida para el caso {case_id}.",
    409,
)

# ---------------------------------------------------------------------------
# Integrity errors
# ---------------------------------------------------------------------------

QualityQuarantineIntegrityFailed = _error(
    "QualityQuarantineIntegrityFailed",
    "Verificación de integridad fallida: {reason}.",
    500,
)

# ---------------------------------------------------------------------------
# Zone errors
# ---------------------------------------------------------------------------

QuarantineZoneNotFound = _error(
    "QuarantineZoneNotFound",
    "Zona de cuarentena {zone_id} no encontrada.",
    404,
)

QuarantineZoneStatusInvalid = _error(
    "QuarantineZoneStatusInvalid",
    "Transición de zona no permitida: {current} -> {target}.",
    422,
)

# ---------------------------------------------------------------------------
# Placement errors
# ---------------------------------------------------------------------------

QuarantinePlacementNotFound = _error(
    "QuarantinePlacementNotFound",
    "Colocación {placement_id} no encontrada.",
    404,
)

# ---------------------------------------------------------------------------
# Measurement errors
# ---------------------------------------------------------------------------

QualityMeasurementNotFound = _error(
    "QualityMeasurementNotFound",
    "Medición {measurement_id} no encontrada.",
    404,
)

# ---------------------------------------------------------------------------
# Sample errors
# ---------------------------------------------------------------------------

QualitySampleSetNotFound = _error(
    "QualitySampleSetNotFound",
    "Conjunto de muestras {sample_set_id} no encontrado.",
    404,
)

# ---------------------------------------------------------------------------
# Certificate errors
# ---------------------------------------------------------------------------

QualityCertificateReviewNotFound = _error(
    "QualityCertificateReviewNotFound",
    "Revisión de certificado {review_id} no encontrada.",
    404,
)

# ---------------------------------------------------------------------------
# Evidence errors
# ---------------------------------------------------------------------------

QualityEvidenceLinkNotFound = _error(
    "QualityEvidenceLinkNotFound",
    "Enlace de evidencia {evidence_link_id} no encontrado.",
    404,
)

# ---------------------------------------------------------------------------
# Reinspection errors
# ---------------------------------------------------------------------------

QualityReinspectionRequestNotFound = _error(
    "QualityReinspectionRequestNotFound",
    "Solicitud de reinspección {request_id} no encontrada.",
    404,
)
