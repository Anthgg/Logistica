"""Phase 043 — Putaway domain errors."""

from __future__ import annotations


class PutawayError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class PutawayPolicyNotFound(PutawayError):
    def __init__(self, policy_id: str = ""):
        super().__init__("PUTAWAY_POLICY_NOT_FOUND", f"Política de putaway no encontrada: {policy_id}", 404)


class PutawayPolicyVersionNotEditable(PutawayError):
    def __init__(self, version_id: str = ""):
        super().__init__("PUTAWAY_POLICY_VERSION_NOT_EDITABLE", f"Versión de política no editable: {version_id}", 409)


class PutawayPolicyValidationFailed(PutawayError):
    def __init__(self, detail: str = ""):
        super().__init__("PUTAWAY_POLICY_VALIDATION_FAILED", f"Validación de política fallida: {detail}", 422)


class PutawayPolicyConflict(PutawayError):
    def __init__(self, detail: str = ""):
        super().__init__("PUTAWAY_POLICY_CONFFLICT", f"Conflicto de política: {detail}", 409)


class PutawaySourceNotEligible(PutawayError):
    def __init__(self, allocation_id: str = "", reasons: str = ""):
        super().__init__("PUTAWAY_SOURCE_NOT_ELIGIBLE", f"Asignación {allocation_id} no elegible: {reasons}", 422)


class PutawaySourceQuantityExhausted(PutawayError):
    def __init__(self, allocation_id: str = ""):
        super().__init__("PUTAWAY_SOURCE_QUANTITY_EXHAUSTED", f"Cantidad agotada en asignación: {allocation_id}", 409)


class PutawayRecommendationNotFound(PutawayError):
    def __init__(self, run_id: str = ""):
        super().__init__("PUTAWAY_RECOMMENDATION_NOT_FOUND", f"Recomendación no encontrada: {run_id}", 404)


class PutawayRecommendationNoCandidate(PutawayError):
    def __init__(self, run_id: str = ""):
        super().__init__("PUTAWAY_RECOMMENDATION_NO_CANDIDATE", f"Sin candidatos en recomendación: {run_id}", 404)


class PutawayRecommendationConflict(PutawayError):
    def __init__(self, detail: str = ""):
        super().__init__("PUTAWAY_RECOMMENDATION_CONFLICT", f"Conflicto de recomendación: {detail}", 409)


class PutawayLocationNotFound(PutawayError):
    def __init__(self, location_id: str = ""):
        super().__init__("PUTAWAY_LOCATION_NOT_FOUND", f"Ubicación no encontrada: {location_id}", 404)


class PutawayLocationBlocked(PutawayError):
    def __init__(self, location_id: str = ""):
        super().__init__("PUTAWAY_LOCATION_BLOCKED", f"Ubicación bloqueada: {location_id}", 409)


class PutawayLocationIncompatible(PutawayError):
    def __init__(self, location_id: str = "", detail: str = ""):
        super().__init__("PUTAWAY_LOCATION_INCOMPATIBLE", f"Ubicación incompatible {location_id}: {detail}", 409)


class PutawayLocationCapacityUnknown(PutawayError):
    def __init__(self, location_id: str = ""):
        super().__init__("PUTAWAY_LOCATION_CAPACITY_UNKNOWN", f"Capacidad desconocida: {location_id}", 422)


class PutawayLocationCapacityInsufficient(PutawayError):
    def __init__(self, location_id: str = "", detail: str = ""):
        super().__init__("PUTAWAY_LOCATION_CAPACITY_INSUFFICIENT", f"Capacidad insuficiente {location_id}: {detail}", 409)


class PutawayProximityDataUnavailable(PutawayError):
    def __init__(self, detail: str = ""):
        super().__init__("PUTAWAY_PROXIMITY_DATA_UNAVAILABLE", f"Datos de proximidad no disponibles: {detail}", 422)


class PutawayRotationDataUnavailable(PutawayError):
    def __init__(self, detail: str = ""):
        super().__init__("PUTAWAY_ROTATION_DATA_UNAVAILABLE", f"Datos de rotación no disponibles: {detail}", 422)


class PutawayReservationNotFound(PutawayError):
    def __init__(self, reservation_id: str = ""):
        super().__init__("PUTAWAY_RESERVATION_NOT_FOUND", f"Reserva no encontrada: {reservation_id}", 404)


class PutawayReservationExpired(PutawayError):
    def __init__(self, reservation_id: str = ""):
        super().__init__("PUTAWAY_RESERVATION_EXPIRED", f"Reserva expirada: {reservation_id}", 409)


class PutawayReservationConflict(PutawayError):
    def __init__(self, detail: str = ""):
        super().__init__("PUTAWAY_RESERVATION_CONFLICT", f"Conflicto de reserva: {detail}", 409)


class PutawayOrderNotFound(PutawayError):
    def __init__(self, order_id: str = ""):
        super().__init__("PUTAWAY_ORDER_NOT_FOUND", f"Orden PUT no encontrada: {order_id}", 404)


class PutawayOrderStatusInvalid(PutawayError):
    def __init__(self, current: str = "", target: str = ""):
        super().__init__("PUTAWAY_ORDER_STATUS_INVALID", f"Transición inválida: {current} -> {target}", 409)


class PutawayTaskNotFound(PutawayError):
    def __init__(self, task_id: str = ""):
        super().__init__("PUTAWAY_TASK_NOT_FOUND", f"Tarea no encontrada: {task_id}", 404)


class PutawayTaskStatusInvalid(PutawayError):
    def __init__(self, current: str = "", target: str = ""):
        super().__init__("PUTAWAY_TASK_STATUS_INVALID", f"Transición inválida: {current} -> {target}", 409)


class PutawayTaskAlreadyAssigned(PutawayError):
    def __init__(self, task_id: str = ""):
        super().__init__("PUTAWAY_TASK_ALREADY_ASSIGNED", f"Tarea ya asignada: {task_id}", 409)


class PutawayTaskScanRequired(PutawayError):
    def __init__(self, scan_type: str = ""):
        super().__init__("PUTAWAY_TASK_SCAN_REQUIRED", f"Escaneo requerido: {scan_type}", 422)


class PutawayProductMismatch(PutawayError):
    def __init__(self, expected: str = "", scanned: str = ""):
        super().__init__("PUTAWAY_PRODUCT_MISMATCH", f"Producto incorrecto: esperado {expected}, escaneado {scanned}", 409)


class PutawayProductCodeUnknown(PutawayError):
    def __init__(self, code: str = ""):
        super().__init__("PUTAWAY_PRODUCT_CODE_UNKNOWN", f"Código de producto desconocido: {code}", 404)


class PutawayLocationCodeUnknown(PutawayError):
    def __init__(self, code: str = ""):
        super().__init__("PUTAWAY_LOCATION_CODE_UNKNOWN", f"Código de ubicación desconocido: {code}", 404)


class PutawayQuantityInvalid(PutawayError):
    def __init__(self, detail: str = ""):
        super().__init__("PUTAWAY_QUANTITY_INVALID", f"Cantidad inválida: {detail}", 422)


class PutawayQuantityExceeded(PutawayError):
    def __init__(self, detail: str = ""):
        super().__init__("PUTAWAY_QUANTITY_EXCEEDED", f"Cantidad excedida: {detail}", 409)


class PutawayUnitInvalid(PutawayError):
    def __init__(self, detail: str = ""):
        super().__init__("PUTAWAY_UNIT_INVALID", f"Unidad inválida: {detail}", 422)


class PutawayConversionMissing(PutawayError):
    def __init__(self, detail: str = ""):
        super().__init__("PUTAWAY_CONVERSION_MISSING", f"Conversión no encontrada: {detail}", 422)


class PutawayPlacementConflict(PutawayError):
    def __init__(self, detail: str = ""):
        super().__init__("PUTAWAY_PLACEMENT_CONFLICT", f"Conflicto de colocación: {detail}", 409)


class PutawayReplanRequired(PutawayError):
    def __init__(self, detail: str = ""):
        super().__init__("PUTAWAY_REPLAN_REQUIRED", f"Replanificación requerida: {detail}", 409)


class PutawayExceptionBlocking(PutawayError):
    def __init__(self, detail: str = ""):
        super().__init__("PUTAWAY_EXCEPTION_BLOCKING", f"Excepción bloqueante: {detail}", 409)


class PutawayIntegrityFailed(PutawayError):
    def __init__(self, detail: str = ""):
        super().__init__("PUTAWAY_INTEGRITY_FAILED", f"Integridad fallida: {detail}", 409)


class PutawayDocumentAlreadyIssued(PutawayError):
    def __init__(self, order_id: str = ""):
        super().__init__("PUTAWAY_DOCUMENT_ALREADY_ISSUED", f"Documento PUT ya emitido: {order_id}", 409)
