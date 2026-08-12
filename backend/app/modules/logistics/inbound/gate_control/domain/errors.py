"""Domain errors for Phase 037 Gate Control."""

from app.core.exceptions import ApplicationError


# ── Gate ─────────────────────────────────────────────────────────────────────

class WarehouseGateNotFoundError(ApplicationError):
    def __init__(self, gate_id=None):
        super().__init__(
            "WAREHOUSE_GATE_NOT_FOUND",
            f"Gate '{gate_id}' no encontrado." if gate_id else "Gate no encontrado.",
            404,
        )


class WarehouseGateInactiveError(ApplicationError):
    def __init__(self, gate_id=None):
        super().__init__(
            "WAREHOUSE_GATE_INACTIVE",
            f"Gate '{gate_id}' está inactivo y no acepta nuevos check-ins.",
            409,
        )


class WarehouseGateDuplicateCodeError(ApplicationError):
    def __init__(self, code=None):
        super().__init__(
            "WAREHOUSE_GATE_DUPLICATE_CODE",
            f"Ya existe un gate con el código '{code}' en este almacén.",
            409,
        )


# ── Verification Policy ───────────────────────────────────────────────────────

class GateVerificationPolicyNotFoundError(ApplicationError):
    def __init__(self, policy_id=None):
        super().__init__(
            "GATE_VERIFICATION_POLICY_NOT_FOUND",
            f"Política de verificación '{policy_id}' no encontrada.",
            404,
        )


class GateVerificationPolicyVersionNotFoundError(ApplicationError):
    def __init__(self, version_id=None):
        super().__init__(
            "GATE_VERIFICATION_POLICY_VERSION_NOT_FOUND",
            f"Versión de política '{version_id}' no encontrada.",
            404,
        )


class GateVerificationPolicyVersionImmutableError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_VERIFICATION_POLICY_VERSION_IMMUTABLE",
            "Una versión ACTIVE es inmutable y no puede ser modificada.",
            409,
        )


# ── Check-In ─────────────────────────────────────────────────────────────────

class GateCheckInNotFoundError(ApplicationError):
    def __init__(self, check_in_id=None):
        super().__init__(
            "GATE_CHECK_IN_NOT_FOUND",
            f"Gate check-in '{check_in_id}' no encontrado.",
            404,
        )


class GateCheckInAlreadyExistsError(ApplicationError):
    def __init__(self, appointment_id=None):
        super().__init__(
            "GATE_CHECK_IN_ALREADY_EXISTS",
            f"Ya existe un check-in activo para la cita '{appointment_id}'.",
            409,
        )


class GateCheckInStatusInvalidError(ApplicationError):
    def __init__(self, current, expected):
        super().__init__(
            "GATE_CHECK_IN_STATUS_INVALID",
            f"Operación inválida: estado actual '{current}', se esperaba '{expected}'.",
            409,
        )


class GateCheckInNotEditableError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_NOT_EDITABLE",
            "El check-in no puede ser editado en su estado actual.",
            409,
        )


class GateCheckInAppointmentInvalidError(ApplicationError):
    def __init__(self, reason=""):
        super().__init__(
            "GATE_CHECK_IN_APPOINTMENT_INVALID",
            f"Cita inválida para el control de puerta: {reason}",
            422,
        )


class GateCheckInAppointmentCancelledError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_APPOINTMENT_CANCELLED",
            "La cita está cancelada y no permite el registro de llegada.",
            409,
        )


class GateCheckInAppointmentAlreadyUsedError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_APPOINTMENT_ALREADY_USED",
            "Esta cita ya tiene un check-in completado.",
            409,
        )


class GateCheckInWarehouseMismatchError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_WAREHOUSE_MISMATCH",
            "La cita pertenece a un almacén diferente a la garita seleccionada.",
            422,
        )


class GateCheckInGuardNotAuthorizedError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_GUARD_NOT_AUTHORIZED",
            "El usuario autenticado no tiene permisos de guardia para esta garita.",
            403,
        )


class GateCheckInArrivalAlreadyRecordedError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_ARRIVAL_ALREADY_RECORDED",
            "La llegada ya fue registrada para este check-in.",
            409,
        )


class GateCheckInVehicleMismatchError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_VEHICLE_MISMATCH",
            "El vehículo observado no coincide con el declarado en la cita.",
            422,
        )


class GateCheckInVehicleBlockedError(ApplicationError):
    def __init__(self, reason=""):
        super().__init__(
            "GATE_CHECK_IN_VEHICLE_BLOCKED",
            f"El vehículo está bloqueado y no puede ingresar: {reason}",
            422,
        )


class GateCheckInDriverMismatchError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_DRIVER_MISMATCH",
            "El conductor observado no coincide con el declarado en la cita.",
            422,
        )


class GateCheckInLicenseExpiredError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_LICENSE_EXPIRED",
            "La licencia del conductor está vencida. Se requiere excepción supervisada.",
            422,
        )


class GateCheckInDocumentMissingError(ApplicationError):
    def __init__(self, doc_kind=""):
        super().__init__(
            "GATE_CHECK_IN_DOCUMENT_MISSING",
            f"Documento requerido faltante: {doc_kind}",
            422,
        )


class GateCheckInGuideMismatchError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_GUIDE_MISMATCH",
            "La guía presentada no coincide con la referencia de la cita.",
            422,
        )


class GateCheckInSealMismatchError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_SEAL_MISMATCH",
            "El precinto observado no coincide con el precinto esperado.",
            422,
        )


class GateCheckInSealBrokenError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_SEAL_BROKEN",
            "El precinto presenta signos de ruptura o manipulación.",
            422,
        )


class GateCheckInRequiredPhotoMissingError(ApplicationError):
    def __init__(self, photo_type=""):
        super().__init__(
            "GATE_CHECK_IN_REQUIRED_PHOTO_MISSING",
            f"Fotografía requerida faltante: {photo_type}",
            422,
        )


class GateCheckInBlockingCheckFailedError(ApplicationError):
    def __init__(self, check_code=""):
        super().__init__(
            "GATE_CHECK_IN_BLOCKING_CHECK_FAILED",
            f"Verificación bloqueante fallida: {check_code}. Se requiere excepción aprobada.",
            422,
        )


class GateCheckInExceptionRequiredError(ApplicationError):
    def __init__(self, reason=""):
        super().__init__(
            "GATE_CHECK_IN_EXCEPTION_REQUIRED",
            f"Se requiere excepción supervisada: {reason}",
            422,
        )


class GateCheckInExceptionNotApprovedError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_EXCEPTION_NOT_APPROVED",
            "Existen excepciones pendientes de aprobación. No se puede tomar la decisión.",
            422,
        )


class GateCheckInDecisionConflictError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_DECISION_CONFLICT",
            "Ya existe una decisión final activa para este check-in.",
            409,
        )


class GateCheckInAlreadyCompletedError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_ALREADY_COMPLETED",
            "El check-in ya fue completado.",
            409,
        )


class GateCheckInDocumentAlreadyIssuedError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_DOCUMENT_ALREADY_ISSUED",
            "El CPV ya fue emitido para este check-in.",
            409,
        )


class GateCheckInCorrectionNotAllowedError(ApplicationError):
    def __init__(self, field=""):
        super().__init__(
            "GATE_CHECK_IN_CORRECTION_NOT_ALLOWED",
            f"El campo '{field}' no puede ser corregido mediante este flujo.",
            422,
        )


class GateCheckInIntegrityFailedError(ApplicationError):
    def __init__(self, detail=""):
        super().__init__(
            "GATE_CHECK_IN_INTEGRITY_FAILED",
            f"Fallo de integridad en el check-in: {detail}",
            500,
        )


class GateCheckInWalkInNotAllowedError(ApplicationError):
    def __init__(self):
        super().__init__(
            "GATE_CHECK_IN_WALK_IN_NOT_ALLOWED",
            "Los check-ins sin cita (walk-in) no están habilitados para este almacén.",
            403,
        )


__all__ = [
    "WarehouseGateNotFoundError",
    "WarehouseGateInactiveError",
    "WarehouseGateDuplicateCodeError",
    "GateVerificationPolicyNotFoundError",
    "GateVerificationPolicyVersionNotFoundError",
    "GateVerificationPolicyVersionImmutableError",
    "GateCheckInNotFoundError",
    "GateCheckInAlreadyExistsError",
    "GateCheckInStatusInvalidError",
    "GateCheckInNotEditableError",
    "GateCheckInAppointmentInvalidError",
    "GateCheckInAppointmentCancelledError",
    "GateCheckInAppointmentAlreadyUsedError",
    "GateCheckInWarehouseMismatchError",
    "GateCheckInGuardNotAuthorizedError",
    "GateCheckInArrivalAlreadyRecordedError",
    "GateCheckInVehicleMismatchError",
    "GateCheckInVehicleBlockedError",
    "GateCheckInDriverMismatchError",
    "GateCheckInLicenseExpiredError",
    "GateCheckInDocumentMissingError",
    "GateCheckInGuideMismatchError",
    "GateCheckInSealMismatchError",
    "GateCheckInSealBrokenError",
    "GateCheckInRequiredPhotoMissingError",
    "GateCheckInBlockingCheckFailedError",
    "GateCheckInExceptionRequiredError",
    "GateCheckInExceptionNotApprovedError",
    "GateCheckInDecisionConflictError",
    "GateCheckInAlreadyCompletedError",
    "GateCheckInDocumentAlreadyIssuedError",
    "GateCheckInCorrectionNotAllowedError",
    "GateCheckInIntegrityFailedError",
    "GateCheckInWalkInNotAllowedError",
]
