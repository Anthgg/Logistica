"""Exceptions for the logistics geocoding subsystem."""

from app.modules.logistics.exceptions import LogisticsError


class GeocodingError(LogisticsError):
    """Base exception for geocoding operations."""

    def __init__(
        self,
        code: str = "GEOCODING_ERROR",
        message: str = "Error en el servicio de geolocalización.",
        status_code: int = 400,
    ) -> None:
        super().__init__(code, message, status_code)


class GeocodingProviderUnavailableError(GeocodingError):
    """Raised when upstream geocoding provider fails, times out, or is unreachable."""

    def __init__(
        self,
        message: str = "El servicio de geolocalización no está disponible temporalmente.",
    ) -> None:
        super().__init__("GEOCODING_PROVIDER_UNAVAILABLE", message, 503)


class GeocodingRateLimitError(GeocodingError):
    """Raised when local or upstream geocoding rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Se ha excedido el límite de solicitudes de geolocalización. Intente nuevamente en unos segundos.",
    ) -> None:
        super().__init__("GEOCODING_RATE_LIMIT_EXCEEDED", message, 429)


class GeocodingInvalidCoordinatesError(GeocodingError):
    """Raised when coordinates violate WGS84 bounding requirements (-90<=lat<=90, -180<=lon<=180)."""

    def __init__(
        self,
        message: str = "Las coordenadas geográficas proporcionadas no son válidas.",
    ) -> None:
        super().__init__("GEOCODING_INVALID_COORDINATES", message, 422)


class GeocodingValidationError(GeocodingError):
    """Raised when geocoding parameters or search queries fail validation."""

    def __init__(
        self,
        message: str = "Los datos de geolocalización no son válidos.",
    ) -> None:
        super().__init__("GEOCODING_VALIDATION_ERROR", message, 422)
