"""Logistics module — domain-specific exceptions.

All logistics exceptions inherit from :class:`LogisticsError` which in turn
wraps :class:`app.core.exceptions.ApplicationError` so the global error
handler formats them consistently.
"""

from app.core.exceptions import ApplicationError


class LogisticsError(ApplicationError):
    """Base exception for the logistics domain."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(code, message, status_code)


class LogisticsValidationError(LogisticsError):
    """Input data failed domain validation rules."""

    def __init__(self, message: str = "Los datos logísticos no son válidos.") -> None:
        super().__init__("LOGISTICS_VALIDATION_ERROR", message, 422)


class LogisticsConflictError(LogisticsError):
    """Request conflicts with current domain state."""

    def __init__(self, message: str = "La operación entra en conflicto con el estado actual.") -> None:
        super().__init__("LOGISTICS_CONFLICT", message, 409)


class LogisticsNotFoundError(LogisticsError):
    """Requested logistics resource was not found."""

    def __init__(self, message: str = "El recurso logístico no existe.") -> None:
        super().__init__("LOGISTICS_NOT_FOUND", message, 404)


class LogisticsPermissionError(LogisticsError):
    """User lacks the required logistics permission."""

    def __init__(self, message: str = "No tiene permiso para esta operación logística.") -> None:
        super().__init__("LOGISTICS_PERMISSION_DENIED", message, 403)


class LogisticsIntegrationError(LogisticsError):
    """External integration failed."""

    def __init__(self, message: str = "La integración externa no está disponible.") -> None:
        super().__init__("LOGISTICS_INTEGRATION_ERROR", message, 502)


class LogisticsDocumentError(LogisticsError):
    """Document operation failed (generation, emission, cancellation)."""

    def __init__(self, message: str = "No se pudo procesar el documento.") -> None:
        super().__init__("LOGISTICS_DOCUMENT_ERROR", message, 422)


class LogisticsRouteError(LogisticsError):
    """Route calculation or map-matching failed."""

    def __init__(self, message: str = "No se pudo calcular la ruta.") -> None:
        super().__init__("LOGISTICS_ROUTE_ERROR", message, 422)


class LogisticsFileError(LogisticsError):
    """File storage or validation failed."""

    def __init__(self, message: str = "No se pudo procesar el archivo.") -> None:
        super().__init__("LOGISTICS_FILE_ERROR", message, 422)