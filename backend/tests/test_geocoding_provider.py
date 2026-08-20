"""Unit and integration test suite for backend geocoding provider core, Nominatim client,
rate limiter, LRU cache, service orchestration, and UBIGEO enrichment.

All tests run 100% offline using mock HTTP transports.
"""

import asyncio
import time
from unittest.mock import MagicMock

import httpx
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.i18n.catalogs import CATALOGS
from app.modules.logistics.geocoding import (
    AsyncRateLimiter,
    GeocodeAddress,
    GeocodeLocationResult,
    GeocodingError,
    GeocodingInvalidCoordinatesError,
    GeocodingLRUCache,
    GeocodingProviderUnavailableError,
    GeocodingRateLimitError,
    GeocodingService,
    NominatimGeocodingProvider,
    validate_coordinates,
)
from app.modules.logistics.geography.schemas import UbigeoHierarchyResponse


# ============================================================================
# 1. Config Settings & Validation Tests
# ============================================================================


def test_geocoding_config_settings_defaults_and_validation():
    """Verify geocoding settings defaults and blank value validations."""
    settings = Settings()
    assert settings.GEOCODING_PROVIDER == "nominatim"
    assert settings.NOMINATIM_BASE_URL == "https://nominatim.openstreetmap.org"
    assert "LogisticaT1" in settings.NOMINATIM_USER_AGENT
    assert settings.NOMINATIM_TIMEOUT_SECONDS == 5.0
    assert settings.NOMINATIM_MIN_INTERVAL_SECONDS == 1.0
    assert settings.GEOCODING_CACHE_TTL_SECONDS == 3600
    assert settings.GEOCODING_CACHE_MAX_ENTRIES == 1000

    # Validate blank strings are rejected
    with pytest.raises(ValidationError):
        Settings(NOMINATIM_BASE_URL="   ")

    with pytest.raises(ValidationError):
        Settings(NOMINATIM_USER_AGENT="   ")


# ============================================================================
# 2. Coordinate Validation & DTO Serialization Tests
# ============================================================================


def test_coordinate_validation_wgs84():
    """Verify WGS84 bounding validations."""
    # Valid coordinates
    lat, lon = validate_coordinates(-12.046374, -77.042793)
    assert lat == pytest.approx(-12.046374)
    assert lon == pytest.approx(-77.042793)

    assert validate_coordinates(0, 0) == (0.0, 0.0)
    assert validate_coordinates(90, 180) == (90.0, 180.0)
    assert validate_coordinates(-90, -180) == (-90.0, -180.0)

    # Invalid latitude
    with pytest.raises(GeocodingInvalidCoordinatesError) as exc_info:
        validate_coordinates(90.0001, 0)
    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "GEOCODING_INVALID_COORDINATES"

    with pytest.raises(GeocodingInvalidCoordinatesError):
        validate_coordinates(-90.0001, 0)

    # Invalid longitude
    with pytest.raises(GeocodingInvalidCoordinatesError):
        validate_coordinates(0, 180.0001)

    with pytest.raises(GeocodingInvalidCoordinatesError):
        validate_coordinates(0, -180.0001)

    # Non-numeric
    with pytest.raises(GeocodingInvalidCoordinatesError):
        validate_coordinates("invalid", 0)  # type: ignore


def test_geocode_address_and_location_result_dto_serialization():
    """Verify DTO creation, validation, and dictionary conversion."""
    addr = GeocodeAddress(
        road="Av. Larco",
        house_number="1234",
        neighbourhood="Miraflores",
        district="Miraflores",
        city="Lima",
        province="Lima",
        department="Lima",
        postcode="15074",
        country="Perú",
        country_code="pe",
    )
    addr_dict = addr.to_dict()
    assert addr_dict["road"] == "Av. Larco"
    assert addr_dict["district"] == "Miraflores"
    assert addr_dict["country_code"] == "pe"

    loc = GeocodeLocationResult(
        latitude=-12.1215,
        longitude=-77.0298,
        display_name="Av. Larco 1234, Miraflores, Lima, Perú",
        place_id=123456,
        osm_type="way",
        osm_id=7890,
        bounding_box=[-12.1220, -12.1210, -77.0300, -77.0290],
        address=addr,
        confidence=0.85,
        raw_type="building",
    )
    loc_dict = loc.to_dict()
    assert loc_dict["latitude"] == -12.1215
    assert loc_dict["longitude"] == -77.0298
    assert loc_dict["place_id"] == "123456"
    assert loc_dict["osm_id"] == "7890"
    assert loc_dict["address"]["district"] == "Miraflores"


# ============================================================================
# 3. LRU Cache Tests
# ============================================================================


def test_geocoding_lru_cache_hit_miss_and_stats():
    """Verify cache hits, misses, and statistics tracking."""
    cache = GeocodingLRUCache(ttl_seconds=300, max_entries=10)
    assert cache.size() == 0
    assert cache.get("key1") is None

    stats = cache.stats()
    assert stats["hits"] == 0
    assert stats["misses"] == 1

    cache.set("key1", "value1")
    assert cache.size() == 1
    assert cache.get("key1") == "value1"

    stats = cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1

    cache.clear()
    assert cache.size() == 0
    assert cache.stats()["hits"] == 0


def test_geocoding_lru_cache_ttl_expiration(monkeypatch):
    """Verify TTL expiration invalidates entries."""
    cache = GeocodingLRUCache(ttl_seconds=10, max_entries=10)

    current_time = 1000.0
    monkeypatch.setattr(time, "monotonic", lambda: current_time)

    cache.set("item", "data")
    assert cache.get("item") == "data"

    # Fast-forward time past TTL
    current_time = 1015.0
    assert cache.get("item") is None
    assert cache.size() == 0


def test_geocoding_lru_cache_capacity_eviction_lru():
    """Verify oldest / least-recently-used item is evicted when capacity reached."""
    cache = GeocodingLRUCache(ttl_seconds=300, max_entries=2)

    cache.set("k1", "v1")
    cache.set("k2", "v2")

    # Access k1 to make k2 the least recently used
    assert cache.get("k1") == "v1"

    # Insert k3 -> should evict k2
    cache.set("k3", "v3")

    assert cache.get("k1") == "v1"
    assert cache.get("k2") is None
    assert cache.get("k3") == "v3"
    assert cache.size() == 2


def test_geocoding_lru_cache_key_canonicalization():
    """Verify search and reverse key generators."""
    k1 = GeocodingLRUCache.make_search_key("  Av.  Larco 1234  ", limit=5)
    k2 = GeocodingLRUCache.make_search_key("av. larco 1234", limit=5)
    assert k1 == k2 == "search:av. larco 1234:5"

    # Reverse key rounding to 5 decimal places
    r1 = GeocodingLRUCache.make_reverse_key(-12.12150001, -77.02980004)
    r2 = GeocodingLRUCache.make_reverse_key(-12.12150499, -77.02980499)
    assert r1 == r2 == "reverse:-12.12150:-77.02980"


# ============================================================================
# 4. Rate Limiter Tests
# ============================================================================


@pytest.mark.asyncio
async def test_rate_limiter_min_interval_enforcement():
    """Verify AsyncRateLimiter delays calls to satisfy min_interval."""
    limiter = AsyncRateLimiter(min_interval_seconds=0.05)

    start = time.monotonic()
    await limiter.acquire()
    await limiter.acquire()
    await limiter.acquire()
    elapsed = time.monotonic() - start

    # 3 acquires with 0.05 interval must take at least 0.09s
    assert elapsed >= 0.08
    limiter.reset()


# ============================================================================
# 5. Nominatim Provider HTTP & Parser Tests
# ============================================================================


@pytest.mark.asyncio
async def test_nominatim_search_success_parsing():
    """Verify Nominatim search parsing with full address components."""
    sample_response = [
        {
            "place_id": 1001,
            "osm_type": "way",
            "osm_id": 2002,
            "lat": "-12.1215000",
            "lon": "-77.0298000",
            "display_name": "Avenida José Larco, Miraflores, Lima, Perú",
            "importance": 0.75,
            "category": "highway",
            "type": "secondary",
            "boundingbox": ["-12.1250", "-12.1200", "-77.0310", "-77.0280"],
            "address": {
                "road": "Avenida José Larco",
                "house_number": "1234",
                "suburb": "Miraflores",
                "city_district": "Miraflores",
                "county": "Lima",
                "state": "Lima",
                "postcode": "15074",
                "country": "Perú",
                "country_code": "pe",
            },
        }
    ]

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/search"
        assert "q" in request.url.params
        assert request.url.params["format"] == "jsonv2"
        assert request.url.params["addressdetails"] == "1"
        assert request.url.params["countrycodes"] == "pe"
        assert "LogisticaT1" in request.headers["user-agent"]
        return httpx.Response(200, json=sample_response)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = NominatimGeocodingProvider(client=client)
        results = await provider.search("Av. Larco 1234, Miraflores", limit=5)

        assert len(results) == 1
        res = results[0]
        assert res.latitude == pytest.approx(-12.1215)
        assert res.longitude == pytest.approx(-77.0298)
        assert res.display_name == "Avenida José Larco, Miraflores, Lima, Perú"
        assert res.confidence == 0.75
        assert res.bounding_box == [-12.1250, -12.1200, -77.0310, -77.0280]
        assert res.address is not None
        assert res.address.road == "Avenida José Larco"
        assert res.address.house_number == "1234"
        assert res.address.district == "Miraflores"
        assert res.address.province == "Lima"
        assert res.address.department == "Lima"


@pytest.mark.asyncio
async def test_nominatim_search_empty_query_or_response():
    """Verify empty query returns empty list without network call."""
    provider = NominatimGeocodingProvider()
    assert await provider.search("") == []
    assert await provider.search("   ") == []

    # Empty array response from API
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        prov = NominatimGeocodingProvider(client=client)
        assert await prov.search("Nonexistent Place") == []


@pytest.mark.asyncio
async def test_nominatim_search_timeout_raises_unavailable():
    """Verify httpx Timeout translates to GeocodingProviderUnavailableError (503)."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Request timed out", request=request)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = NominatimGeocodingProvider(client=client)
        with pytest.raises(GeocodingProviderUnavailableError) as exc_info:
            await provider.search("Av. Larco 1234")

        assert exc_info.value.status_code == 503
        assert exc_info.value.code == "GEOCODING_PROVIDER_UNAVAILABLE"


@pytest.mark.asyncio
async def test_nominatim_search_rate_limit_429_raises_rate_limit_error():
    """Verify HTTP 429 translates to GeocodingRateLimitError (429)."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": "Too Many Requests"})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = NominatimGeocodingProvider(client=client)
        with pytest.raises(GeocodingRateLimitError) as exc_info:
            await provider.search("Av. Larco 1234")

        assert exc_info.value.status_code == 429
        assert exc_info.value.code == "GEOCODING_RATE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_nominatim_search_server_error_503_raises_unavailable():
    """Verify upstream HTTP 503 translates to GeocodingProviderUnavailableError (503)."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Service Unavailable")

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = NominatimGeocodingProvider(client=client)
        with pytest.raises(GeocodingProviderUnavailableError) as exc_info:
            await provider.search("Av. Larco 1234")

        assert exc_info.value.status_code == 503
        assert exc_info.value.code == "GEOCODING_PROVIDER_UNAVAILABLE"


@pytest.mark.asyncio
async def test_nominatim_reverse_success_parsing():
    """Verify reverse geocoding parses single location result."""
    sample_reverse = {
        "place_id": 555,
        "osm_type": "node",
        "osm_id": 999,
        "lat": "-12.046374",
        "lon": "-77.042793",
        "display_name": "Plaza Mayor de Lima, Centro Histórico, Lima, Perú",
        "category": "historic",
        "type": "memorial",
        "boundingbox": ["-12.0470", "-12.0460", "-77.0430", "-77.0420"],
        "address": {
            "historic": "Plaza Mayor de Lima",
            "road": "Jirón de la Unión",
            "suburb": "Centro Histórico",
            "city_district": "Lima",
            "county": "Lima",
            "state": "Lima",
            "country": "Perú",
            "country_code": "pe",
        },
    }

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/reverse"
        assert request.url.params["format"] == "jsonv2"
        return httpx.Response(200, json=sample_reverse)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = NominatimGeocodingProvider(client=client)
        result = await provider.reverse(-12.046374, -77.042793)

        assert result is not None
        assert result.latitude == pytest.approx(-12.046374)
        assert result.longitude == pytest.approx(-77.042793)
        assert "Plaza Mayor" in result.display_name
        assert result.address is not None
        assert result.address.road == "Jirón de la Unión"


@pytest.mark.asyncio
async def test_nominatim_reverse_unable_to_geocode_returns_none():
    """Verify Nominatim error payload returns None."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": "Unable to geocode"})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = NominatimGeocodingProvider(client=client)
        result = await provider.reverse(-12.0, -77.0)
        assert result is None


# ============================================================================
# 6. Geocoding Service & UBIGEO Enrichment Tests
# ============================================================================


def test_geocoding_service_enrich_query_with_ubigeo():
    """Verify query enrichment formatting and deduplication."""
    mock_provider = MagicMock(spec=NominatimGeocodingProvider)
    service = GeocodingService(provider=mock_provider)

    # All components distinct
    q1 = service.enrich_query_with_ubigeo(
        "Av. Real 123",
        district_name="El Tambo",
        province_name="Huancayo",
        department_name="Junín",
    )
    assert q1 == "Av. Real 123, El Tambo, Huancayo, Junín, Perú"

    # Redundant names (e.g. Lima province == Lima department)
    q2 = service.enrich_query_with_ubigeo(
        "Av. Larco 1234",
        district_name="Miraflores",
        province_name="Lima",
        department_name="Lima",
    )
    assert q2 == "Av. Larco 1234, Miraflores, Lima, Perú"

    # Blank / None components
    q3 = service.enrich_query_with_ubigeo("Av. Pardo 500")
    assert q3 == "Av. Pardo 500, Perú"


@pytest.mark.asyncio
async def test_geocoding_service_search_with_ubigeo_db_lookup(monkeypatch):
    """Verify GeocodingService resolves UBIGEO via GeographyService."""
    mock_provider = MagicMock()
    expected_result = [
        GeocodeLocationResult(
            latitude=-12.1215,
            longitude=-77.0298,
            display_name="Av. Larco 1234, Miraflores, Lima, Perú",
        )
    ]
    mock_provider.search = MagicMock(return_value=asyncio.Future())
    mock_provider.search.return_value.set_result(expected_result)

    mock_db = MagicMock()
    mock_hierarchy = UbigeoHierarchyResponse(
        code="150122",
        department_code="15",
        department_name="Lima",
        province_code="1501",
        province_name="Lima",
        district_name="Miraflores",
        formatted="Miraflores, Lima, Lima",
    )

    from app.modules.logistics.geography.service import GeographyService
    monkeypatch.setattr(GeographyService, "resolve_ubigeo", lambda db, code: mock_hierarchy)

    service = GeocodingService(provider=mock_provider)
    results = await service.search_address("Av. Larco 1234", ubigeo_code="150122", db=mock_db)

    assert results == expected_result
    mock_provider.search.assert_called_once_with(
        "Av. Larco 1234, Miraflores, Lima, Perú", limit=5
    )


@pytest.mark.asyncio
async def test_geocoding_service_caching_and_rate_limiting():
    """Verify service consults cache before provider and acquires rate limiter."""
    mock_provider = MagicMock()
    location = GeocodeLocationResult(
        latitude=-12.1215,
        longitude=-77.0298,
        display_name="Miraflores Result",
    )
    mock_provider.search = MagicMock(return_value=asyncio.Future())
    mock_provider.search.return_value.set_result([location])
    mock_provider.reverse = MagicMock(return_value=asyncio.Future())
    mock_provider.reverse.return_value.set_result(location)

    cache = GeocodingLRUCache(ttl_seconds=3600, max_entries=100)
    rate_limiter = AsyncRateLimiter(min_interval_seconds=0.01)

    service = GeocodingService(provider=mock_provider, cache=cache, rate_limiter=rate_limiter)

    # First search -> Miss, calls provider
    res1 = await service.search_address("Av. Larco 100")
    assert res1 == [location]
    assert mock_provider.search.call_count == 1
    assert cache.stats()["hits"] == 0
    assert cache.stats()["misses"] == 1

    # Second search -> Hit, returns from cache
    res2 = await service.search_address("Av. Larco 100")
    assert res2 == [location]
    assert mock_provider.search.call_count == 1
    assert cache.stats()["hits"] == 1

    # First reverse -> Miss, calls provider
    rev1 = await service.reverse_coords(-12.1215, -77.0298)
    assert rev1 == location
    assert mock_provider.reverse.call_count == 1

    # Second reverse with slightly different precision (~cm level) -> Hit
    rev2 = await service.reverse_coords(-12.12150002, -77.02980001)
    assert rev2 == location
    assert mock_provider.reverse.call_count == 1


# ============================================================================
# 7. i18n Localization Catalogs Tests
# ============================================================================


def test_i18n_geocoding_translations():
    """Verify geocoding error translation keys are present in es, en, and pt."""
    required_keys = [
        "error.GEOCODING_PROVIDER_UNAVAILABLE",
        "error.GEOCODING_RATE_LIMIT_EXCEEDED",
        "error.GEOCODING_INVALID_COORDINATES",
        "error.GEOCODING_VALIDATION_ERROR",
    ]

    for lang in ["es", "en", "pt"]:
        catalog = CATALOGS.get(lang, {})
        for key in required_keys:
            assert key in catalog, f"Missing key '{key}' in catalog '{lang}'"
            assert catalog[key], f"Empty translation for '{key}' in '{lang}'"
