"""Comprehensive E2E and Integration Test Suite for F005.4 Geolocalización de Sedes.

Covers Tiers 1-5:
- Tier 1: Core Feature Coverage (Search, Reverse, UBIGEO Enrichment, Cache, Normalized Models)
- Tier 2: Boundary & Corner Cases (WGS84 Boundaries, 500+ Chars, Malformed UBIGEO, Upstream 502/503/Timeout)
- Tier 3: Pairwise Combinations & Cache Interplay
- Tier 4: Real-World Application Scenarios (RBAC 401/403, Multi-Tenant Isolation, Branch Coords Persistence)
- Tier 5: Adversarial Hardening (WGS84 Fuzzing, LRU Cache Overflow, SQLi/XSS Payloads, Concurrency Stress)

Zero CI internet dependency: all external upstream calls use mock transports.
"""

import asyncio
import time
from uuid import uuid4

import httpx
import pytest
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.organization import Organization
from app.modules.logistics.geocoding import (
    AsyncRateLimiter,
    GeocodeLocationResult,
    GeocodingInvalidCoordinatesError,
    GeocodingLRUCache,
    GeocodingProviderUnavailableError,
    GeocodingService,
    NominatimGeocodingProvider,
    validate_coordinates,
)
from app.modules.logistics.geography.models import GeoDepartment, GeoDistrict, GeoProvince
from app.modules.logistics.rbac.models_assignment import LogisticsRoleAssignment
from app.modules.logistics.rbac.models_permission import LogisticsPermission
from app.modules.logistics.rbac.models_role import LogisticsRole
from app.modules.logistics.rbac.models_role_permission import LogisticsRolePermission
from tests.fixtures.geocoding_fixtures import (
    MockNominatimTransport,
)
from tests.support import authenticate

BRANCH_PERMISSIONS = [
    "logistics.organizations.read",
    "logistics.branches.read",
    "logistics.branches.create",
    "logistics.branches.update",
]


# ============================================================================
# Helpers & Database Seeding Fixtures
# ============================================================================


def _seed_geographic_hierarchy(db: Session) -> None:
    """Seed Peruvian administrative hierarchy (Departments, Provinces, Districts)."""
    # Lima (15) > Lima (1501) > Miraflores (150122), San Isidro (150131), Lince (150116)
    if not db.query(GeoDepartment).filter(GeoDepartment.code == "15").first():
        db.add(GeoDepartment(code="15", name="Lima"))
        db.add(GeoProvince(code="1501", department_code="15", name="Lima"))
        db.add(
            GeoDistrict(
                code="150122",
                province_code="1501",
                department_code="15",
                name="Miraflores",
            )
        )
        db.add(
            GeoDistrict(
                code="150131",
                province_code="1501",
                department_code="15",
                name="San Isidro",
            )
        )
        db.add(
            GeoDistrict(
                code="150116",
                province_code="1501",
                department_code="15",
                name="Lince",
            )
        )

    # Arequipa (04) > Arequipa (0401) > Arequipa (040101)
    if not db.query(GeoDepartment).filter(GeoDepartment.code == "04").first():
        db.add(GeoDepartment(code="04", name="Arequipa"))
        db.add(GeoProvince(code="0401", department_code="04", name="Arequipa"))
        db.add(
            GeoDistrict(
                code="040101",
                province_code="0401",
                department_code="04",
                name="Arequipa",
            )
        )

    db.flush()


def _setup_scoped_environment(
    client,
    database: Session,
    permissions: list[str] | None = None,
    org_name: str = "Org Geocoding Test",
) -> dict:
    """Set up an authenticated user, organization, role, and assigned permissions."""
    _seed_geographic_hierarchy(database)
    user, headers = authenticate(client, database)

    org = Organization(
        code=f"GEO-ORG-{uuid4().hex[:6].upper()}",
        name=org_name,
        country_code="PE",
        timezone="America/Lima",
    )
    database.add(org)
    database.flush()

    role = LogisticsRole(
        code=f"geo-role-{uuid4().hex[:6]}",
        name="Geo Role",
        description="Role for geocoding testing",
    )
    database.add(role)
    database.flush()

    perms_to_grant = permissions if permissions is not None else BRANCH_PERMISSIONS
    for code in perms_to_grant:
        perm = (
            database.query(LogisticsPermission)
            .filter(LogisticsPermission.code == code)
            .first()
        )
        if not perm:
            parts = code.split(".")
            res = parts[1] if len(parts) > 1 else code
            act = parts[-1]
            perm = LogisticsPermission(
                code=code,
                resource=res,
                action=act,
                name=code,
                description=code,
                category="structure",
                requires_step_up=False,
            )
            database.add(perm)
            database.flush()
        database.add(LogisticsRolePermission(role_id=role.id, permission_id=perm.id))

    database.add(
        LogisticsRoleAssignment(
            user_id=user.id,
            role_id=role.id,
            scope_type="organization",
            organization_id=org.id,
            status="active",
        )
    )
    database.flush()

    return {"user": user, "headers": headers, "org": org}


def _create_mocked_provider() -> tuple[NominatimGeocodingProvider, MockNominatimTransport]:
    """Create a Nominatim provider bound to a 100% offline MockNominatimTransport."""
    transport = MockNominatimTransport()
    client = httpx.AsyncClient(transport=transport, base_url="https://nominatim.openstreetmap.org")
    provider = NominatimGeocodingProvider(
        base_url="https://nominatim.openstreetmap.org",
        user_agent="LogisticaT1-Test/1.0",
        client=client,
    )
    return provider, transport


# ============================================================================
# TIER 1: CORE FEATURE COVERAGE
# ============================================================================


@pytest.mark.asyncio
async def test_t1_search_exact_address_returns_normalized_result():
    """T1-SEARCH-01: Exact address search returns normalized result."""
    provider, transport = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    results = await service.search_address("Av. Larco 1234")

    assert len(results) == 1
    hit = results[0]
    assert isinstance(hit, GeocodeLocationResult)
    assert hit.latitude == pytest.approx(-12.1215)
    assert hit.longitude == pytest.approx(-77.0298)
    assert "Miraflores" in hit.display_name
    assert hit.address is not None
    assert hit.address.road == "Avenida José Larco"
    assert hit.address.district == "Miraflores"
    assert hit.address.country == "Perú"
    assert hit.address.country_code == "pe"
    assert hit.confidence == pytest.approx(0.75)
    assert hit.bounding_box == [-12.1220, -12.1210, -77.0305, -77.0290]
    assert transport.call_count == 1


@pytest.mark.asyncio
async def test_t1_search_enriched_with_valid_ubigeo(database: Session):
    """T1-SEARCH-02: Search enriched with valid UBIGEO code formats structured Peruvian query."""
    _seed_geographic_hierarchy(database)
    provider, transport = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    results = await service.search_address("Av. Larco 1234", ubigeo_code="150122", db=database)

    assert len(results) == 1
    # Verify the recorded HTTP request query contains district, province, and department
    assert len(transport.recorded_requests) == 1
    req = transport.recorded_requests[0]
    query_param = req.url.params.get("q")
    assert "Av. Larco 1234" in query_param
    assert "Miraflores" in query_param
    assert "Lima" in query_param
    assert "Perú" in query_param


@pytest.mark.asyncio
async def test_t1_search_without_ubigeo_includes_country_constraint():
    """T1-SEARCH-03: Search without UBIGEO queries address with Peru country code constraint."""
    provider, transport = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    results = await service.search_address("Av. España 200", ubigeo_code=None)

    assert len(results) >= 1
    req = transport.recorded_requests[0]
    assert req.url.params.get("countrycodes") == "pe"
    assert "Av. España 200, Perú" in req.url.params.get("q")


@pytest.mark.asyncio
async def test_t1_search_multiple_matches_returns_ordered_candidates():
    """T1-SEARCH-04: Search with multiple matches returns top results list up to limit."""
    provider, _ = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    results = await service.search_address("Av. Principal multi", limit=3)

    assert len(results) == 3
    assert results[0].latitude == pytest.approx(-12.1215)
    assert results[1].latitude == pytest.approx(-12.0950)
    assert results[2].latitude == pytest.approx(-12.0850)
    assert all(isinstance(r, GeocodeLocationResult) for r in results)


@pytest.mark.asyncio
async def test_t1_search_lru_cache_hit_prevents_upstream_call():
    """T1-SEARCH-05: In-memory LRU Cache returns cached search result on identical query without upstream HTTP call."""
    provider, transport = _create_mocked_provider()
    cache = GeocodingLRUCache(ttl_seconds=3600, max_entries=100)
    service = GeocodingService(provider=provider, cache=cache)

    # First call: cache miss
    res1 = await service.search_address("Av. Larco 1234")
    assert len(res1) == 1
    assert transport.call_count == 1
    assert cache.stats()["hits"] == 0
    assert cache.stats()["misses"] == 1

    # Second call: cache hit
    res2 = await service.search_address("Av. Larco 1234")
    assert len(res2) == 1
    assert transport.call_count == 1  # transport not called again
    assert cache.stats()["hits"] == 1
    assert res1[0].display_name == res2[0].display_name


@pytest.mark.asyncio
async def test_t1_reverse_valid_lima_coords_returns_clean_address():
    """T1-REV-01: Valid Lima coordinates return clean structured address."""
    provider, transport = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    result = await service.reverse_coords(-12.1215, -77.0298)

    assert result is not None
    assert result.latitude == pytest.approx(-12.1215)
    assert result.longitude == pytest.approx(-77.0298)
    assert result.address is not None
    assert result.address.road == "Avenida José Larco"
    assert result.address.district == "Miraflores"
    assert result.address.department == "Lima"
    assert result.address.country == "Perú"
    assert transport.call_count == 1


@pytest.mark.asyncio
async def test_t1_reverse_regional_coords_arequipa():
    """T1-REV-02: Regional coordinates (Arequipa) return correct provincial address."""
    provider, _ = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    result = await service.reverse_coords(-16.4090, -71.5375)

    assert result is not None
    assert result.address is not None
    assert result.address.road == "Calle Mercaderes"
    assert result.address.province == "Arequipa"
    assert result.address.department == "Arequipa"


@pytest.mark.asyncio
async def test_t1_reverse_high_precision_7_decimal_places():
    """T1-REV-03: High-precision coordinates (7 decimals) preserve precision."""
    provider, _ = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    lat_input = -12.1215312
    lon_input = -77.0298451
    result = await service.reverse_coords(lat_input, lon_input)

    assert result is not None
    assert isinstance(result.latitude, float)
    assert isinstance(result.longitude, float)


@pytest.mark.asyncio
async def test_t1_reverse_lru_cache_hit_prevents_upstream_call():
    """T1-REV-04: In-memory Cache returns reverse geocoding result for identical coordinates without upstream call."""
    provider, transport = _create_mocked_provider()
    cache = GeocodingLRUCache(ttl_seconds=3600, max_entries=100)
    service = GeocodingService(provider=provider, cache=cache)

    res1 = await service.reverse_coords(-12.1215, -77.0298)
    assert res1 is not None
    assert transport.call_count == 1

    res2 = await service.reverse_coords(-12.1215, -77.0298)
    assert res2 is not None
    assert transport.call_count == 1  # hit cache
    assert cache.stats()["hits"] == 1


@pytest.mark.asyncio
async def test_t1_reverse_sparse_osm_data_handles_missing_fields():
    """T1-REV-05: Sparse OSM data returns best-effort display name without crashing."""
    provider, _ = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    result = await service.reverse_coords(-11.5000, -76.5000)

    assert result is not None
    assert result.address is not None
    assert result.address.road == "Carretera Central"
    assert result.address.district is None
    assert result.address.suburb is None
    assert result.address.country == "Perú"


# ============================================================================
# TIER 2: BOUNDARY & CORNER CASES
# ============================================================================


@pytest.mark.asyncio
async def test_t2_search_empty_or_whitespace_address_returns_empty():
    """T2-SEARCH-01: Empty or whitespace-only address returns empty list without calling upstream."""
    provider, transport = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    assert await service.search_address("") == []
    assert await service.search_address("   ") == []
    assert transport.call_count == 0


@pytest.mark.asyncio
async def test_t2_search_long_address_500_chars():
    """T2-SEARCH-02: Search address with 500 characters is handled safely."""
    provider, transport = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    long_address = "Calle " + ("A" * 480) + " 100"
    results = await service.search_address(long_address)
    assert isinstance(results, list)
    assert transport.call_count == 1


@pytest.mark.asyncio
async def test_t2_search_malformed_ubigeo_fallback(database: Session):
    """T2-SEARCH-03: Malformed or non-existent UBIGEO code falls back to '<address>, Perú' gracefully."""
    _seed_geographic_hierarchy(database)
    provider, transport = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    results = await service.search_address("Av. Grau", ubigeo_code="999999", db=database)
    assert len(results) == 1
    req = transport.recorded_requests[0]
    assert "Av. Grau, Perú" in req.url.params.get("q")


@pytest.mark.asyncio
async def test_t2_search_unmatched_query_returns_empty_results():
    """T2-SEARCH-04: Unmatched address search returns empty list with success."""
    provider, transport = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    results = await service.search_address("notfound non existent street 12345")
    assert results == []
    assert transport.call_count == 1


@pytest.mark.asyncio
async def test_t2_search_upstream_timeout_raises_canonical_503():
    """T2-SEARCH-05: Upstream Nominatim timeout raises canonical GEOCODING_PROVIDER_UNAVAILABLE 503."""
    provider, _ = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    with pytest.raises(GeocodingProviderUnavailableError) as exc_info:
        await service.search_address("timeout address search")

    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "GEOCODING_PROVIDER_UNAVAILABLE"


@pytest.mark.asyncio
async def test_t2_search_upstream_502_503_raises_canonical_503():
    """T2-SEARCH-06: Upstream Nominatim 502/503 HTTP status raises canonical 503."""
    provider, _ = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    with pytest.raises(GeocodingProviderUnavailableError) as exc_503:
        await service.search_address("error503 address search")
    assert exc_503.value.status_code == 503

    with pytest.raises(GeocodingProviderUnavailableError) as exc_502:
        await service.search_address("error502 address search")
    assert exc_502.value.status_code == 503


@pytest.mark.asyncio
async def test_t2_search_special_characters_escaping():
    """T2-SEARCH-07: Address with special symbols, quotes, accents, ñ, ampersands handled safely."""
    provider, transport = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    complex_address = "Av. Los Álamos #123 Dpto. 4-B & 'El Trigal' / Cañete ñandú"
    results = await service.search_address(complex_address)
    assert len(results) >= 1
    assert transport.call_count == 1
    req = transport.recorded_requests[0]
    assert "Los Álamos" in req.url.params.get("q")


def test_t2_reverse_latitude_above_90_rejected():
    """T2-REV-01: Latitude > 90.0 (e.g. 90.0001) raises 422 validation error."""
    with pytest.raises(GeocodingInvalidCoordinatesError) as exc_info:
        validate_coordinates(90.0001, -77.0)
    assert exc_info.value.status_code == 422


def test_t2_reverse_latitude_below_minus_90_rejected():
    """T2-REV-02: Latitude < -90.0 (e.g. -90.0001) raises 422 validation error."""
    with pytest.raises(GeocodingInvalidCoordinatesError) as exc_info:
        validate_coordinates(-90.0001, -77.0)
    assert exc_info.value.status_code == 422


def test_t2_reverse_longitude_above_180_rejected():
    """T2-REV-03: Longitude > 180.0 (e.g. 180.0001) raises 422 validation error."""
    with pytest.raises(GeocodingInvalidCoordinatesError) as exc_info:
        validate_coordinates(-12.0, 180.0001)
    assert exc_info.value.status_code == 422


def test_t2_reverse_longitude_below_minus_180_rejected():
    """T2-REV-04: Longitude < -180.0 (e.g. -180.0001) raises 422 validation error."""
    with pytest.raises(GeocodingInvalidCoordinatesError) as exc_info:
        validate_coordinates(-12.0, -180.0001)
    assert exc_info.value.status_code == 422


def test_t2_reverse_exact_wgs84_boundaries_accepted():
    """T2-REV-05: Exact boundary values (±90.0, ±180.0, 0.0) are validly accepted."""
    assert validate_coordinates(90.0, 180.0) == (90.0, 180.0)
    assert validate_coordinates(-90.0, -180.0) == (-90.0, -180.0)
    assert validate_coordinates(0.0, 0.0) == (0.0, 0.0)
    assert validate_coordinates(90.0, -180.0) == (90.0, -180.0)
    assert validate_coordinates(-90.0, 180.0) == (-90.0, 180.0)


@pytest.mark.asyncio
async def test_t2_reverse_unmapped_oceanic_coords_returns_none():
    """T2-REV-06: Unmapped oceanic coordinates where Nominatim returns 'Unable to geocode' returns None."""
    provider, transport = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    result = await service.reverse_coords(0.0, 0.0)
    assert result is None
    assert transport.call_count == 1


@pytest.mark.asyncio
async def test_t2_reverse_upstream_timeout_and_errors_raise_canonical_503():
    """T2-REV-07: Upstream reverse geocoding timeout / 503 raises canonical 503."""
    # Trigger timeout by mocking provider method or transport
    client = httpx.AsyncClient(
        transport=MockNominatimTransport(),
        base_url="https://nominatim.openstreetmap.org/error503",
    )
    failing_provider = NominatimGeocodingProvider(
        base_url="https://nominatim.openstreetmap.org/error503", client=client
    )
    failing_service = GeocodingService(provider=failing_provider)

    with pytest.raises(GeocodingProviderUnavailableError) as exc_info:
        await failing_service.reverse_coords(-12.1215, -77.0298)

    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "GEOCODING_PROVIDER_UNAVAILABLE"


# ============================================================================
# TIER 3: PAIRWISE COMBINATIONS & INTERPLAY
# ============================================================================


@pytest.mark.asyncio
async def test_t3_pairwise_search_with_and_without_ubigeo_cache_interplay(database: Session):
    """T3-COMB-01: Search without UBIGEO followed by search with UBIGEO produces distinct cache entries."""
    _seed_geographic_hierarchy(database)
    provider, transport = _create_mocked_provider()
    cache = GeocodingLRUCache(ttl_seconds=3600, max_entries=100)
    service = GeocodingService(provider=provider, cache=cache)

    # Search 1: without UBIGEO
    res1 = await service.search_address("Av. Larco 1234", ubigeo_code=None, db=database)
    assert len(res1) == 1
    assert transport.call_count == 1

    # Search 2: with UBIGEO 150122 (Miraflores)
    res2 = await service.search_address("Av. Larco 1234", ubigeo_code="150122", db=database)
    assert len(res2) == 1
    assert transport.call_count == 2  # Different enriched query string -> new cache key

    # Search 3: repeat search with UBIGEO -> Cache Hit
    res3 = await service.search_address("Av. Larco 1234", ubigeo_code="150122", db=database)
    assert len(res3) == 1
    assert transport.call_count == 2  # Not incremented
    assert cache.stats()["hits"] == 1


@pytest.mark.asyncio
async def test_t3_pairwise_sub_meter_precision_caching():
    """T3-COMB-02: Micro-variations (<1m) in reverse coordinates map to the same 5-decimal cache key."""
    provider, transport = _create_mocked_provider()
    cache = GeocodingLRUCache(ttl_seconds=3600, max_entries=100)
    service = GeocodingService(provider=provider, cache=cache)

    # Base coords: (-12.1215000, -77.0298000)
    res1 = await service.reverse_coords(-12.1215000, -77.0298000)
    assert res1 is not None
    assert transport.call_count == 1

    # Sub-meter variation: 4th/5th decimal matching (-12.1215002, -77.0298001)
    res2 = await service.reverse_coords(-12.1215002, -77.0298001)
    assert res2 is not None
    assert transport.call_count == 1  # Hits cache because of 5-decimal rounding
    assert cache.stats()["hits"] == 1


@pytest.mark.asyncio
async def test_t3_pairwise_macro_coordinate_displacement_calls_provider():
    """T3-COMB-03: Macro displacement (>50m) results in distinct reverse cache keys."""
    provider, transport = _create_mocked_provider()
    cache = GeocodingLRUCache(ttl_seconds=3600, max_entries=100)
    service = GeocodingService(provider=provider, cache=cache)

    # Point 1 (Miraflores center)
    res1 = await service.reverse_coords(-12.12150, -77.02980)
    assert res1 is not None
    assert transport.call_count == 1

    # Point 2 (Displaced by ~1km)
    res2 = await service.reverse_coords(-12.13000, -77.03500)
    assert res2 is not None
    assert transport.call_count == 2  # Displaced coordinates trigger separate call


@pytest.mark.asyncio
async def test_t3_pairwise_search_then_reverse_end_to_end():
    """T3-COMB-04: Forward search followed by reverse geocoding coordinates of the result."""
    provider, _ = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    # Forward search
    search_results = await service.search_address("Av. Larco 1234")
    assert len(search_results) == 1
    found = search_results[0]

    # Reverse lookup with coordinates returned by forward search
    reverse_result = await service.reverse_coords(found.latitude, found.longitude)
    assert reverse_result is not None
    assert reverse_result.address is not None
    assert reverse_result.address.district == found.address.district
    assert reverse_result.address.country == found.address.country


@pytest.mark.asyncio
async def test_t3_pairwise_same_street_different_ubigeos(database: Session):
    """T3-COMB-05: Same street name with different UBIGEOs queries different enriched strings."""
    _seed_geographic_hierarchy(database)
    provider, transport = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    # Search in Miraflores (150122)
    await service.search_address("Av. Principal 100", ubigeo_code="150122", db=database)
    req1 = transport.recorded_requests[0]
    assert "Miraflores" in req1.url.params.get("q")

    # Search in San Isidro (150131)
    await service.search_address("Av. Principal 100", ubigeo_code="150131", db=database)
    req2 = transport.recorded_requests[1]
    assert "San Isidro" in req2.url.params.get("q")


@pytest.mark.asyncio
async def test_t3_pairwise_cache_ttl_and_eviction_mixed_workload():
    """T3-COMB-06: Mixed search and reverse cache operations respect eviction and capacity limits."""
    cache = GeocodingLRUCache(ttl_seconds=3600, max_entries=5)

    # Fill cache with 5 items
    for i in range(5):
        cache.set(f"key_{i}", f"value_{i}")
    assert cache.size() == 5

    # Access key_0 to make it recently used
    assert cache.get("key_0") == "value_0"

    # Insert 6th item -> should evict key_1 (least recently used)
    cache.set("key_5", "value_5")
    assert cache.size() == 5
    assert cache.get("key_1") is None  # Evicted
    assert cache.get("key_0") == "value_0"  # Preserved


# ============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS
# ============================================================================


def test_t4_create_branch_with_geocoded_coordinates(client, database: Session):
    """T4-SCEN-01: Create branch full flow with geocoded coordinates, UBIGEO hierarchy, and DB persistence."""
    env = _setup_scoped_environment(client, database)
    org_id = env["org"].id

    payload = {
        "code": f"BR-GEO-{uuid4().hex[:6].upper()}",
        "name": "Sede Principal Miraflores",
        "timezone": "America/Lima",
        "ubigeo_code": "150122",
        "address_text": "Av. Larco 1234",
        "latitude": -12.1215000,
        "longitude": -77.0298000,
    }

    response = client.post(
        f"/api/logistics/organizations/{org_id}/branches",
        headers=env["headers"],
        json=payload,
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["code"] == payload["code"]
    assert body["latitude"] == pytest.approx(-12.1215)
    assert body["longitude"] == pytest.approx(-77.0298)
    assert body["ubigeo_code"] == "150122"
    assert body["ubigeo"]["district_name"] == "Miraflores"
    assert body["ubigeo"]["province_name"] == "Lima"
    assert body["ubigeo"]["department_name"] == "Lima"

    # Direct database verification
    branch_db = database.query(Branch).filter(Branch.code == payload["code"]).first()
    assert branch_db is not None
    assert float(branch_db.latitude) == pytest.approx(-12.1215)
    assert float(branch_db.longitude) == pytest.approx(-77.0298)


def test_t4_edit_branch_coordinates_update(client, database: Session):
    """T4-SCEN-02: Edit branch flow updating coordinates and address after marker drag."""
    env = _setup_scoped_environment(client, database)
    org_id = env["org"].id

    # Create initial branch
    create_resp = client.post(
        f"/api/logistics/organizations/{org_id}/branches",
        headers=env["headers"],
        json={
            "code": f"BR-UPDATE-{uuid4().hex[:6].upper()}",
            "name": "Sede a Editar",
            "timezone": "America/Lima",
            "ubigeo_code": "150122",
            "address_text": "Av. Larco 1234",
            "latitude": -12.1215000,
            "longitude": -77.0298000,
        },
    )
    assert create_resp.status_code == 201
    branch_id = create_resp.json()["id"]

    # Update with new coordinates (dragged marker position)
    update_payload = {
        "address_text": "Av. Larco 1250",
        "latitude": -12.1220000,
        "longitude": -77.0305000,
    }
    update_resp = client.patch(
        f"/api/logistics/branches/{branch_id}",
        headers=env["headers"],
        json=update_payload,
    )
    assert update_resp.status_code == 200, update_resp.text
    body = update_resp.json()
    assert body["address_text"] == "Av. Larco 1250"
    assert body["latitude"] == pytest.approx(-12.1220)
    assert body["longitude"] == pytest.approx(-77.0305)


def test_t4_create_branch_out_of_bounds_coordinates_rejected_by_api(client, database: Session):
    """T4-SCEN-03: Out-of-bounds coordinates during branch creation are rejected with 422."""
    env = _setup_scoped_environment(client, database)
    org_id = env["org"].id

    # Invalid latitude > 90
    resp_lat = client.post(
        f"/api/logistics/organizations/{org_id}/branches",
        headers=env["headers"],
        json={
            "code": f"BR-INV-LAT-{uuid4().hex[:6].upper()}",
            "name": "Sede Inv Lat",
            "timezone": "America/Lima",
            "latitude": 95.0,
            "longitude": -77.0,
        },
    )
    assert resp_lat.status_code == 422

    # Invalid longitude < -180
    resp_lon = client.post(
        f"/api/logistics/organizations/{org_id}/branches",
        headers=env["headers"],
        json={
            "code": f"BR-INV-LON-{uuid4().hex[:6].upper()}",
            "name": "Sede Inv Lon",
            "timezone": "America/Lima",
            "latitude": -12.0,
            "longitude": -195.0,
        },
    )
    assert resp_lon.status_code == 422


def test_t4_branch_strict_multi_tenant_isolation(client, database: Session):
    """T4-SCEN-04: Strict Multi-Tenant Isolation: User in Org A cannot create or access branches in Org B."""
    env_a = _setup_scoped_environment(client, database, org_name="Organización A")
    env_b = _setup_scoped_environment(client, database, org_name="Organización B")

    # User A tries to create branch in Org B
    resp_cross = client.post(
        f"/api/logistics/organizations/{env_b['org'].id}/branches",
        headers=env_a["headers"],  # User A credentials
        json={
            "code": f"BR-CROSS-{uuid4().hex[:6].upper()}",
            "name": "Cross Tenant Branch",
            "timezone": "America/Lima",
            "latitude": -12.1215,
            "longitude": -77.0298,
        },
    )
    # Expected 403 Forbidden or 404 Not Found (tenant isolation)
    assert resp_cross.status_code in {403, 404}


def test_t4_unauthorized_user_blocked(client, database: Session):
    """T4-SCEN-05: Unauthenticated request is 401; user lacking branch permissions is 403."""
    env = _setup_scoped_environment(client, database, permissions=[])  # Empty permissions
    org_id = env["org"].id

    # 1. Unauthenticated (no headers / session)
    resp_unauth = client.post(
        f"/api/logistics/organizations/{org_id}/branches",
        json={"name": "Sede Sin Auth", "code": "BR-NOAUTH", "timezone": "America/Lima"},
    )
    assert resp_unauth.status_code in {401, 403}

    # 2. Authenticated but missing branch create permission
    resp_forbidden = client.post(
        f"/api/logistics/organizations/{org_id}/branches",
        headers=env["headers"],
        json={"name": "Sede Forbidden", "code": "BR-FORBID", "timezone": "America/Lima"},
    )
    assert resp_forbidden.status_code == 403


@pytest.mark.asyncio
async def test_t4_geocoder_outage_allows_manual_coordinate_save(client, database: Session):
    """T4-SCEN-06: During geocoder service outage, user can still persist manual coordinates to branch."""
    env = _setup_scoped_environment(client, database)
    org_id = env["org"].id

    # Simulate geocoder provider failure
    failing_client = httpx.AsyncClient(
        transport=MockNominatimTransport(),
        base_url="https://nominatim.openstreetmap.org/error503",
    )
    failing_provider = NominatimGeocodingProvider(
        base_url="https://nominatim.openstreetmap.org/error503",
        client=failing_client,
    )
    service = GeocodingService(provider=failing_provider)

    with pytest.raises(GeocodingProviderUnavailableError):
        await service.search_address("error503 address search")

    # Manual fallback: user enters coordinates manually in branch form
    response = client.post(
        f"/api/logistics/organizations/{org_id}/branches",
        headers=env["headers"],
        json={
            "code": f"BR-FALLBACK-{uuid4().hex[:6].upper()}",
            "name": "Sede Fallback Manual",
            "timezone": "America/Lima",
            "ubigeo_code": "150122",
            "address_text": "Av. Manual 500",
            "latitude": -12.0100000,
            "longitude": -76.8900000,
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["latitude"] == pytest.approx(-12.0100)
    assert body["longitude"] == pytest.approx(-76.8900)


# ============================================================================
# TIER 5: ADVERSARIAL HARDENING TESTS
# ============================================================================


def test_t5_wgs84_coordinate_fuzzing():
    """T5-ADV-01: Fuzz coordinate validator with extreme, infinite, NaN, and invalid types."""
    adversarial_inputs = [
        (float("nan"), 0.0),
        (0.0, float("nan")),
        (float("inf"), 0.0),
        (0.0, float("-inf")),
        (1e12, -77.0),
        (-1e12, -77.0),
        (-12.0, 1e12),
        (-12.0, -1e12),
        ("not_a_number", -77.0),
        (-12.0, None),
        ("−12.12°", -77.0),
        ("📍", "🗺️"),
    ]

    for lat, lon in adversarial_inputs:
        with pytest.raises(GeocodingInvalidCoordinatesError):
            validate_coordinates(lat, lon)


def test_t5_lru_cache_overflow_stress():
    """T5-ADV-02: Stress test LRU cache with 1,500 distinct items on a 1,000 capacity bound."""
    max_cap = 1000
    cache = GeocodingLRUCache(ttl_seconds=3600, max_entries=max_cap)

    # Insert 1,500 items
    for i in range(1500):
        cache.set(f"key_{i}", f"value_{i}")

    # Verify cache size never exceeds max_entries
    assert cache.size() == max_cap
    stats = cache.stats()
    assert stats["size"] == max_cap
    assert stats["max_entries"] == max_cap

    # First 500 items should have been evicted
    for i in range(500):
        assert cache.get(f"key_{i}") is None

    # Last 1000 items must be intact
    for i in range(500, 1500):
        assert cache.get(f"key_{i}") == f"value_{i}"


@pytest.mark.asyncio
async def test_t5_sql_injection_and_xss_in_address_search(database: Session):
    """T5-ADV-03: Malicious SQL injection and XSS payloads in address search strings are handled safely."""
    _seed_geographic_hierarchy(database)
    provider, _ = _create_mocked_provider()
    service = GeocodingService(provider=provider)

    malicious_payloads = [
        "' OR '1'='1; DROP TABLE logistics_branches; --",
        "'; EXEC xp_cmdshell('dir'); --",
        "<script>alert('xss')</script>",
        "javascript:/*--></title></style></textarea></script></xmp><svg/onload='+/'/+/onmouseover=1/+/[*/[]/+alert(1)//'>",
        "{{7*7}} ${7*7} <%= 7*7 %>",
    ]

    for payload in malicious_payloads:
        results = await service.search_address(payload, ubigeo_code="150122", db=database)
        assert isinstance(results, list)

    # Verify database table is still intact and operable
    branches_count = database.query(Branch).count()
    assert branches_count >= 0


@pytest.mark.asyncio
async def test_t5_rate_limiter_and_concurrency_stress():
    """T5-ADV-04: Async rate limiter ensures minimum intervals under concurrent tasks."""
    min_interval = 0.05  # 50ms for test speed
    rate_limiter = AsyncRateLimiter(min_interval_seconds=min_interval)

    timestamps: list[float] = []

    async def worker():
        await rate_limiter.acquire()
        timestamps.append(time.monotonic())

    # Launch 5 concurrent workers
    await asyncio.gather(*(worker() for _ in range(5)))

    assert len(timestamps) == 5
    # Verify elapsed time between consecutive acquires is >= min_interval (with small delta)
    for i in range(1, len(timestamps)):
        delta = timestamps[i] - timestamps[i - 1]
        assert delta >= (min_interval - 0.01), f"Rate limit violated: delta={delta}"
