"""Domain exceptions for Phase 028 — Vehicle Verifications."""

from app.core.exceptions import ApplicationError


class VehicleVerificationNotFound(ApplicationError):
    def __init__(self, verification_id: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_NOT_FOUND",
            message=f"Verificación vehicular '{verification_id}' no encontrada.",
            status_code=404,
        )


class VehicleVerificationAlreadyRunning(ApplicationError):
    def __init__(self, verification_id: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_ALREADY_RUNNING",
            message=f"La verificación '{verification_id}' ya está en ejecución.",
            status_code=409,
        )


class VehicleVerificationAlreadyCompleted(ApplicationError):
    def __init__(self, verification_id: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_ALREADY_COMPLETED",
            message=f"La verificación '{verification_id}' ya fue completada y es inmutable.",
            status_code=409,
        )


class VehicleVerificationExpired(ApplicationError):
    def __init__(self, verification_id: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_EXPIRED",
            message=f"La verificación '{verification_id}' ha expirado.",
            status_code=410,
        )


class VehicleVerificationSourceDisabled(ApplicationError):
    def __init__(self, source_code: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_SOURCE_DISABLED",
            message=f"La fuente de verificación '{source_code}' está deshabilitada.",
            status_code=400,
        )


class VehicleVerificationSourceNotAuthorized(ApplicationError):
    def __init__(self, source_code: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_SOURCE_NOT_AUTHORIZED",
            message=f"La fuente '{source_code}' no tiene autorización legal o contractual activa para consultas automáticas.",
            status_code=403,
        )


class VehicleVerificationDomainUnsupported(ApplicationError):
    def __init__(self, domain: str, source_code: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_DOMAIN_UNSUPPORTED",
            message=f"El dominio '{domain}' no es soportado por la fuente '{source_code}'.",
            status_code=400,
        )


class VehicleVerificationProviderUnavailable(ApplicationError):
    def __init__(self, provider_code: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_PROVIDER_UNAVAILABLE",
            message=f"El proveedor externo '{provider_code}' no está disponible actualmente.",
            status_code=503,
        )


class VehicleVerificationProviderUnauthorized(ApplicationError):
    def __init__(self, provider_code: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_PROVIDER_UNAUTHORIZED",
            message=f"Credenciales o contrato inválido para el proveedor '{provider_code}'.",
            status_code=401,
        )


class VehicleVerificationProviderRateLimited(ApplicationError):
    def __init__(self, provider_code: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_PROVIDER_RATE_LIMITED",
            message=f"Límite de tasa excedido para el proveedor '{provider_code}'.",
            status_code=429,
        )


class VehicleVerificationProviderInvalidResponse(ApplicationError):
    def __init__(self, provider_code: str, details: str = ""):
        super().__init__(
            code="VEHICLE_VERIFICATION_PROVIDER_INVALID_RESPONSE",
            message=f"Respuesta inválida del proveedor '{provider_code}': {details}",
            status_code=502,
        )


class VehicleVerificationTimeout(ApplicationError):
    def __init__(self, provider_code: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_TIMEOUT",
            message=f"Tiempo de espera agotado al consultar la fuente '{provider_code}'.",
            status_code=504,
        )


class VehicleVerificationNotFoundExternally(ApplicationError):
    def __init__(self, plate: str, domain: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_NOT_FOUND_EXTERNALLY",
            message=f"No se encontraron registros externos para la placa '{plate}' en el dominio '{domain}'.",
            status_code=404,
        )


class VehicleVerificationEvidenceRequired(ApplicationError):
    def __init__(self, domain: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_EVIDENCE_REQUIRED",
            message=f"Se requiere referencia de evidencia documental para verificar el dominio '{domain}'.",
            status_code=400,
        )


class VehicleVerificationEvidenceInvalid(ApplicationError):
    def __init__(self, details: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_EVIDENCE_INVALID",
            message=f"La evidencia referenciada es inválida: {details}",
            status_code=400,
        )


class VehicleVerificationConflictDetected(ApplicationError):
    def __init__(self, conflict_type: str, details: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_CONFLICT_DETECTED",
            message=f"Conflicto de verificación detectado [{conflict_type}]: {details}",
            status_code=409,
        )


class VehicleVerificationConflictAlreadyResolved(ApplicationError):
    def __init__(self, conflict_id: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_CONFLICT_ALREADY_RESOLVED",
            message=f"El conflicto '{conflict_id}' ya se encuentra resuelto.",
            status_code=409,
        )


class VehicleVerificationApplicationConflict(ApplicationError):
    def __init__(self, details: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_APPLICATION_CONFLICT",
            message=f"No se pueden aplicar los datos verificados al vehículo: {details}",
            status_code=409,
        )


class VehicleVerificationRequirementNotMet(ApplicationError):
    def __init__(self, requirement_id: str, details: str):
        super().__init__(
            code="VEHICLE_VERIFICATION_REQUIREMENT_NOT_MET",
            message=f"Requisito de verificación '{requirement_id}' no cumplido: {details}",
            status_code=422,
        )


class AssistedVehicleVerificationInvalid(ApplicationError):
    def __init__(self, details: str):
        super().__init__(
            code="ASSISTED_VEHICLE_VERIFICATION_INVALID",
            message=f"Verificación asistida inválida: {details}",
            status_code=400,
        )


class AssistedVehicleVerificationAlreadyApproved(ApplicationError):
    def __init__(self, assisted_id: str):
        super().__init__(
            code="ASSISTED_VEHICLE_VERIFICATION_ALREADY_APPROVED",
            message=f"La verificación asistida '{assisted_id}' ya fue aprobada.",
            status_code=409,
        )


class AssistedVehicleVerificationSeparationOfDutiesError(ApplicationError):
    def __init__(self, user_id: str):
        super().__init__(
            code="ASSISTED_VEHICLE_VERIFICATION_SEPARATION_OF_DUTIES",
            message="El usuario creador de la verificación asistida no puede ser el mismo que la aprueba.",
            status_code=403,
        )


class VehicleVerificationBatchLimitExceeded(ApplicationError):
    def __init__(self, limit: int):
        super().__init__(
            code="VEHICLE_VERIFICATION_BATCH_LIMIT_EXCEEDED",
            message=f"El lote de verificación excede el límite máximo permitido de {limit} elementos.",
            status_code=400,
        )
