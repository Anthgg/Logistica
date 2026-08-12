"""Domain exceptions for Supplier Evaluation (Phase 033)."""

from fastapi import HTTPException, status


class SupplierEvaluationError(HTTPException):
    def __init__(self, detail: str, code: str = "EVALUATION_ERROR", status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail={"code": code, "message": detail})


class TemplateNotFoundError(SupplierEvaluationError):
    def __init__(self, template_id: str):
        super().__init__(f"Plantilla de evaluación '{template_id}' no encontrada.", code="TEMPLATE_NOT_FOUND", status_code=404)


class TemplateVersionInvalidError(SupplierEvaluationError):
    def __init__(self, detail: str):
        super().__init__(detail, code="TEMPLATE_VERSION_INVALID")


class EvaluationWeightsInvalidError(SupplierEvaluationError):
    def __init__(self, sum_weights: str):
        super().__init__(f"La suma de los pesos de los criterios debe ser exactamente 100.0000. Suma actual: {sum_weights}.", code="WEIGHTS_SUM_INVALID")


class EvaluationNotFound(SupplierEvaluationError):
    def __init__(self, evaluation_id: str):
        super().__init__(f"Evaluación de cotización '{evaluation_id}' no encontrada.", code="EVALUATION_NOT_FOUND", status_code=404)


class EvaluationStatusInvalidError(SupplierEvaluationError):
    def __init__(self, current_status: str, expected_status: str):
        super().__init__(f"Estado de evaluación inválido: '{current_status}'. Se esperaba '{expected_status}'.", code="EVALUATION_STATUS_INVALID")


class EvaluationNoCandidatesError(SupplierEvaluationError):
    def __init__(self, detail: str = "No existen candidatos elegibles para evaluar en esta ronda."):
        super().__init__(detail, code="NO_EVALUATION_CANDIDATES")


class EvaluationDecisionAlreadyRecordedError(SupplierEvaluationError):
    def __init__(self, decision_id: str):
        super().__init__(f"La decisión '{decision_id}' ya está registrada (RECORDED) y es inmutable.", code="DECISION_ALREADY_RECORDED")


class ConflictOfInterestDetectedError(SupplierEvaluationError):
    def __init__(self, user_id: str):
        super().__init__(f"El evaluador '{user_id}' tiene un conflicto de interés confirmado y no puede calificar a este proveedor.", code="CONFLICT_OF_INTEREST_DETECTED", status_code=403)
