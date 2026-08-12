"""Domain Exceptions for Phase 037 (Gate Control Core Domain)."""

from fastapi import status
from app.core.exceptions import ApplicationError


class GateNotFoundError(ApplicationError):
    """Raised when a specified WarehouseGate is not found."""

    def __init__(self, gate_identifier: str):
        super().__init__(
            code="GATE_NOT_FOUND",
            message=f"Puerta de almacén '{gate_identifier}' no fue encontrada.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class GateRecordNotFoundError(ApplicationError):
    """Raised when a specified GateControlRecord is not found."""

    def __init__(self, record_identifier: str):
        super().__init__(
            code="GATE_RECORD_NOT_FOUND",
            message=f"Registro de control de puerta '{record_identifier}' no fue encontrado.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class InvalidGateStateError(ApplicationError):
    """Raised when an operation is invalid for the current gate or record state."""

    def __init__(self, message: str):
        super().__init__(
            code="INVALID_GATE_STATE",
            message=f"Operación no válida en el estado actual de la puerta/registro: {message}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class DriverLicenseExpiredError(ApplicationError):
    """Raised when a driver's license is expired during gate evaluation."""

    def __init__(self, driver_identifier: str, expiry_date: str):
        super().__init__(
            code="DRIVER_LICENSE_EXPIRED",
            message=f"La licencia del conductor '{driver_identifier}' venció el {expiry_date} y no está habilitada para ingreso.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class PlateMismatchWarning(ApplicationError):
    """Raised when observed license plate does not match expected appointment plate."""

    def __init__(self, expected_plate: str, observed_plate: str):
        super().__init__(
            code="PLATE_MISMATCH",
            message=f"Discrepancia de placa: se esperaba '{expected_plate}', pero se observó '{observed_plate}'.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class SealStatusInvalidError(ApplicationError):
    """Raised when cargo seal status is broken, tampered, or mismatched."""

    def __init__(self, seal_status: str):
        super().__init__(
            code="SEAL_STATUS_INVALID",
            message=f"Estado de precinto no válido para autorización de ingreso: '{seal_status}'.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
