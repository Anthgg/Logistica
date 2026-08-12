"""Domain Exception definitions for Phase 027 (Vehicles Module)."""

from fastapi import HTTPException, status


class VehicleDomainError(HTTPException):
    def __init__(self, status_code: int, error_code: str, message: str):
        super().__init__(status_code=status_code, detail={"error_code": error_code, "message": message})
        self.error_code = error_code
        self.message = message


class VehicleNotFoundError(VehicleDomainError):
    def __init__(self, vehicle_id_or_code: str):
        super().__init__(status.HTTP_404_NOT_FOUND, "VEHICLE_NOT_FOUND", f"Vehículo '{vehicle_id_or_code}' no encontrado.")


class VehicleCodeConflictError(VehicleDomainError):
    def __init__(self, code: str):
        super().__init__(status.HTTP_409_CONFLICT, "VEHICLE_CODE_CONFLICT", f"El código de vehículo '{code}' ya está registrado en la organización.")


class VehiclePlateInvalidError(VehicleDomainError):
    def __init__(self, plate: str):
        super().__init__(status.HTTP_400_BAD_REQUEST, "VEHICLE_PLATE_INVALID", f"La placa '{plate}' no tiene un formato válido.")


class VehiclePlateConflictError(VehicleDomainError):
    def __init__(self, plate: str):
        super().__init__(status.HTTP_409_CONFLICT, "VEHICLE_PLATE_CONFLICT", f"La placa '{plate}' ya está asignada a otro vehículo activo en la organización.")


class VehicleVinInvalidError(VehicleDomainError):
    def __init__(self, vin: str):
        super().__init__(status.HTTP_400_BAD_REQUEST, "VEHICLE_VIN_INVALID", f"El VIN '{vin}' no es válido sintácticamente.")


class VehicleVinConflictError(VehicleDomainError):
    def __init__(self, vin: str):
        super().__init__(status.HTTP_409_CONFLICT, "VEHICLE_VIN_CONFLICT", f"El VIN '{vin}' ya está registrado en la organización.")


class VehicleMakeNotFoundError(VehicleDomainError):
    def __init__(self, make_id: str):
        super().__init__(status.HTTP_404_NOT_FOUND, "VEHICLE_MAKE_NOT_FOUND", f"Marca de vehículo '{make_id}' no encontrada.")


class VehicleModelNotFoundError(VehicleDomainError):
    def __init__(self, model_id: str):
        super().__init__(status.HTTP_404_NOT_FOUND, "VEHICLE_MODEL_NOT_FOUND", f"Modelo de vehículo '{model_id}' no encontrado.")


class VehicleModelMakeMismatchError(VehicleDomainError):
    def __init__(self, model_id: str, make_id: str):
        super().__init__(status.HTTP_400_BAD_REQUEST, "VEHICLE_MODEL_MAKE_MISMATCH", f"El modelo '{model_id}' no pertenece a la marca '{make_id}'.")


class VehicleCarrierRoleRequiredError(VehicleDomainError):
    def __init__(self, partner_id: str):
        super().__init__(status.HTTP_400_BAD_REQUEST, "VEHICLE_CARRIER_ROLE_REQUIRED", f"El socio '{partner_id}' no posee un rol CARRIER activo.")


class VehicleCarrierBlockedError(VehicleDomainError):
    def __init__(self, partner_id: str):
        super().__init__(status.HTTP_409_CONFLICT, "VEHICLE_CARRIER_BLOCKED", f"El transportista '{partner_id}' se encuentra bloqueado.")


class VehicleCapacityInvalidError(VehicleDomainError):
    def __init__(self, message: str):
        super().__init__(status.HTTP_400_BAD_REQUEST, "VEHICLE_CAPACITY_INVALID", message)


class VehicleCannotBeActivatedError(VehicleDomainError):
    def __init__(self, reason: str):
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, "VEHICLE_CANNOT_BE_ACTIVATED", f"No se puede activar el vehículo: {reason}")


class VehicleBlockedError(VehicleDomainError):
    def __init__(self, reason: str):
        super().__init__(status.HTTP_409_CONFLICT, "VEHICLE_BLOCKED", f"El vehículo se encuentra bloqueado: {reason}")


class VehicleDuplicateSuspectedError(VehicleDomainError):
    def __init__(self, details: str):
        super().__init__(status.HTTP_409_CONFLICT, "VEHICLE_DUPLICATE_SUSPECTED", details)
