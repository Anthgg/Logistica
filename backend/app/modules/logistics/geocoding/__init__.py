"""Logistics Geocoding module exports."""

from app.modules.logistics.geocoding.base import (
    GeocodeAddress,
    GeocodeLocationResult,
    GeocodingProvider,
    validate_coordinates,
)
from app.modules.logistics.geocoding.cache import GeocodingLRUCache
from app.modules.logistics.geocoding.exceptions import (
    GeocodingError,
    GeocodingInvalidCoordinatesError,
    GeocodingProviderUnavailableError,
    GeocodingRateLimitError,
    GeocodingValidationError,
)
from app.modules.logistics.geocoding.providers.nominatim import NominatimGeocodingProvider
from app.modules.logistics.geocoding.rate_limiter import AsyncRateLimiter
from app.modules.logistics.geocoding.router import (
    get_geocoding_service,
    router,
    set_geocoding_service,
)
from app.modules.logistics.geocoding.schemas import (
    GeocodeAddressDTO,
    GeocodeLocationResultDTO,
    GeocodeReverseRequest,
    GeocodeReverseResponse,
    GeocodeSearchData,
    GeocodeSearchRequest,
    GeocodeSearchResponse,
    GeocodeSearchResultsData,
)
from app.modules.logistics.geocoding.service import GeocodingService

__all__ = [
    "GeocodeAddress",
    "GeocodeLocationResult",
    "GeocodingProvider",
    "validate_coordinates",
    "GeocodingError",
    "GeocodingProviderUnavailableError",
    "GeocodingRateLimitError",
    "GeocodingInvalidCoordinatesError",
    "GeocodingValidationError",
    "AsyncRateLimiter",
    "GeocodingLRUCache",
    "NominatimGeocodingProvider",
    "GeocodingService",
    "GeocodeAddressDTO",
    "GeocodeLocationResultDTO",
    "GeocodeSearchRequest",
    "GeocodeSearchResponse",
    "GeocodeSearchData",
    "GeocodeSearchResultsData",
    "GeocodeReverseRequest",
    "GeocodeReverseResponse",
    "get_geocoding_service",
    "set_geocoding_service",
    "router",
]
