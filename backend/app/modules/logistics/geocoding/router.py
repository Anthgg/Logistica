"""FastAPI REST router for logistics geocoding operations (Phase 005.4 / F005.4)."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.dependencies.csrf import verify_csrf
from app.modules.logistics.auth_dependencies import require_permission
from app.modules.logistics.geocoding.cache import GeocodingLRUCache
from app.modules.logistics.geocoding.providers.nominatim import NominatimGeocodingProvider
from app.modules.logistics.geocoding.rate_limiter import AsyncRateLimiter
from app.modules.logistics.geocoding.schemas import (
    GeocodeLocationResultDTO,
    GeocodeReverseRequest,
    GeocodeReverseResponse,
    GeocodeSearchData,
    GeocodeSearchRequest,
    GeocodeSearchResponse,
)
from app.modules.logistics.geocoding.service import GeocodingService
from app.modules.logistics.principal import LogisticsPrincipal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/geocoding", tags=["Logistics - Geocoding (F005.4)"])

_geocoding_service: GeocodingService | None = None


def get_geocoding_service() -> GeocodingService:
    """Dependency factory returning the singleton GeocodingService instance."""
    global _geocoding_service
    if _geocoding_service is None:
        provider = NominatimGeocodingProvider(
            base_url=settings.NOMINATIM_BASE_URL,
            user_agent=settings.NOMINATIM_USER_AGENT,
            timeout_seconds=settings.NOMINATIM_TIMEOUT_SECONDS,
        )
        cache = GeocodingLRUCache(
            ttl_seconds=settings.GEOCODING_CACHE_TTL_SECONDS,
            max_entries=settings.GEOCODING_CACHE_MAX_ENTRIES,
        )
        rate_limiter = AsyncRateLimiter(
            min_interval_seconds=settings.NOMINATIM_MIN_INTERVAL_SECONDS,
        )
        _geocoding_service = GeocodingService(
            provider=provider,
            cache=cache,
            rate_limiter=rate_limiter,
        )
    return _geocoding_service


def set_geocoding_service(service: GeocodingService | None) -> None:
    """Setter for overriding the singleton service instance during testing."""
    global _geocoding_service
    _geocoding_service = service


@router.post(
    "/search",
    response_model=GeocodeSearchResponse,
    status_code=status.HTTP_200_OK,
    operation_id="logistics_geocoding_search",
    summary="Buscar coordenadas de dirección con enriquecimiento UBIGEO opcional",
    description=(
        "Busca coordenadas y componentes de dirección a partir de una consulta de texto. "
        "Si se provee `ubigeo_code`, enriquece la consulta con la jerarquía administrativa "
        "distrital, provincial y departamental de Perú."
    ),
)
async def search_address(
    payload: GeocodeSearchRequest,
    db: Session = Depends(get_db),
    _principal: LogisticsPrincipal = Depends(
        require_permission(
            "logistics.branches.read",
            "logistics.branches.create",
            "logistics.branches.update",
        )
    ),
    _csrf: None = Depends(verify_csrf),
    service: GeocodingService = Depends(get_geocoding_service),
) -> GeocodeSearchResponse:
    """Search forward geocoding candidates ordered by confidence."""
    domain_results = await service.search_address(
        address=payload.address,
        ubigeo_code=payload.ubigeo_code,
        db=db,
        limit=payload.limit,
    )
    dto_results = [
        dto
        for r in domain_results
        if (dto := GeocodeLocationResultDTO.from_domain(r)) is not None
    ]
    return GeocodeSearchResponse(
        success=True,
        data=GeocodeSearchData(results=dto_results, count=len(dto_results)),
    )


@router.post(
    "/reverse",
    response_model=GeocodeReverseResponse,
    status_code=status.HTTP_200_OK,
    operation_id="logistics_geocoding_reverse",
    summary="Geocodificación inversa de coordenadas WGS84 a dirección estructurada",
    description=(
        "Resuelve un par de coordenadas [latitude, longitude] WGS84 a una dirección "
        "estructurada normalizada y nombre de visualización."
    ),
)
async def reverse_coordinates(
    payload: GeocodeReverseRequest,
    _principal: LogisticsPrincipal = Depends(
        require_permission(
            "logistics.branches.read",
            "logistics.branches.create",
            "logistics.branches.update",
        )
    ),
    _csrf: None = Depends(verify_csrf),
    service: GeocodingService = Depends(get_geocoding_service),
) -> GeocodeReverseResponse:
    """Reverse geocode geographic coordinates to structured address."""
    domain_result = await service.reverse_coords(
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    dto_result = GeocodeLocationResultDTO.from_domain(domain_result)
    return GeocodeReverseResponse(
        success=True,
        data=dto_result,
    )
