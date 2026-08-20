"""Comprehensive REST API Integration Test Suite for Geocoding Endpoints (Milestone M2 / F005.4).

Covers all 7 Categories:
- Category 1: HTTP 200 Success Cases (Search & Reverse with UBIGEO, Limits, Normalization)
- Category 2: HTTP 401 Unauthorized (Unauthenticated Requests, Invalid Session)
- Category 3: HTTP 403 Forbidden (RBAC Permissions Matrix & CSRF Token Verification)
- Category 4: HTTP 422 Unprocessable Entity (Schema Validation, WGS84 Boundaries)
- Category 5: HTTP 503 Service Unavailable (Downstream Timeouts & 502/503 Outages)
- Category 6: Tenant Isolation & Scope Enforcement
- Category 7: Cache Hit Verification (Search & Reverse Sub-meter Rounding)

Zero external internet dependency: Uses MockNominatimTransport for 100% offline isolation.
"""

from uuid import uuid4

import httpx
import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.logistics.geocoding.cache import GeocodingLRUCache
from app.modules.logistics.geocoding.providers.nominatim import NominatimGeocodingProvider
from app.modules.logistics.geocoding.rate_limiter import AsyncRateLimiter
from app.modules.logistics.geocoding.router import set_geocoding_service
from app.modules.logistics.geocoding.service import GeocodingService
from tests.fixtures.geocoding_fixtures import MockNominatimTransport
from tests.test_logistics_geocoding import (
    BRANCH_PERMISSIONS,
    _seed_geographic_hierarchy,
    _setup_scoped_environment,
)


def _setup_mock_geocoding_service(
    base_url: str = "https://nominatim.openstreetmap.org",
) -> tuple[GeocodingService, MockNominatimTransport, GeocodingLRUCache]:
    """Create a GeocodingService wired to MockNominatimTransport and register it as singleton."""
    transport = MockNominatimTransport()
    client = httpx.AsyncClient(transport=transport, base_url=base_url)
    provider = NominatimGeocodingProvider(
        base_url=base_url,
        user_agent="LogisticaT1-Test/1.0",
        client=client,
    )
    cache = GeocodingLRUCache(ttl_seconds=3600, max_entries=100)
    rate_limiter = AsyncRateLimiter(min_interval_seconds=0.0)
    service = GeocodingService(
        provider=provider,
        cache=cache,
        rate_limiter=rate_limiter,
    )
    set_geocoding_service(service)
    return service, transport, cache


@pytest.fixture(autouse=True)
def cleanup_geocoding_service():
    """Ensure mock geocoding service is cleaned up after each test."""
    yield
    set_geocoding_service(None)


# ============================================================================
# Category 1: HTTP 200 Success Cases (Search & Reverse)
# ============================================================================


def test_api_search_exact_address_200(client, database: Session):
    """TC-API-200-01: Exact address search returns HTTP 200 with normalized location data."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    payload = {"address": "Av. Larco 1234"}
    response = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json=payload,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert "data" in body
    assert body["data"]["count"] == 1
    assert len(body["data"]["results"]) == 1

    first = body["data"]["results"][0]
    assert first["latitude"] == pytest.approx(-12.1215)
    assert first["longitude"] == pytest.approx(-77.0298)
    assert "Miraflores" in first["display_name"]
    assert first["address"] is not None
    assert first["address"]["road"] == "Avenida José Larco"
    assert first["address"]["district"] == "Miraflores"
    assert first["address"]["country"] == "Perú"
    assert first["address"]["country_code"] == "pe"
    assert first["confidence"] == pytest.approx(0.75)


def test_api_search_with_ubigeo_enrichment_200(client, database: Session):
    """TC-API-200-02: Search enriched with valid UBIGEO code passes regional terms to provider."""
    _, transport, _ = _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    payload = {"address": "Av. Larco 1234", "ubigeo_code": "150122"}
    response = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json=payload,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["data"]["count"] == 1

    # Verify query string was enriched with Miraflores, Lima, Perú
    assert len(transport.recorded_requests) == 1
    req = transport.recorded_requests[0]
    q_param = req.url.params.get("q")
    assert "Av. Larco 1234" in q_param
    assert "Miraflores" in q_param
    assert "Lima" in q_param
    assert "Perú" in q_param


def test_api_search_multi_candidate_limit_200(client, database: Session):
    """TC-API-200-03: Search returning multiple candidates respects requested limit parameter."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    payload = {"address": "Av. Principal multi", "limit": 3}
    response = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json=payload,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["data"]["count"] == 3
    assert len(body["data"]["results"]) == 3
    assert body["data"]["results"][0]["latitude"] == pytest.approx(-12.1215)
    assert body["data"]["results"][1]["latitude"] == pytest.approx(-12.0950)
    assert body["data"]["results"][2]["latitude"] == pytest.approx(-12.0850)


def test_api_search_unmatched_query_returns_empty_list_200(client, database: Session):
    """TC-API-200-04: Unmatched query returns HTTP 200 with count=0 and results=[]."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    payload = {"address": "notfound non existent street 99999"}
    response = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json=payload,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["data"]["count"] == 0
    assert body["data"]["results"] == []


def test_api_reverse_valid_lima_coordinates_200(client, database: Session):
    """TC-API-200-05: Valid Lima coordinates reverse geocode into structured address."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    payload = {"latitude": -12.1215, "longitude": -77.0298}
    response = client.post(
        "/api/logistics/geocoding/reverse",
        headers=env["headers"],
        json=payload,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["data"] is not None
    assert body["data"]["latitude"] == pytest.approx(-12.1215)
    assert body["data"]["longitude"] == pytest.approx(-77.0298)
    assert body["data"]["address"]["road"] == "Avenida José Larco"
    assert body["data"]["address"]["district"] == "Miraflores"
    assert body["data"]["address"]["city"] == "Lima"
    assert body["data"]["address"]["country"] == "Perú"


def test_api_reverse_regional_arequipa_coordinates_200(client, database: Session):
    """TC-API-200-06: Regional coordinates (Arequipa) return correct province and department."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    payload = {"latitude": -16.4090, "longitude": -71.5375}
    response = client.post(
        "/api/logistics/geocoding/reverse",
        headers=env["headers"],
        json=payload,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["data"] is not None
    assert body["data"]["address"]["road"] == "Calle Mercaderes"
    assert body["data"]["address"]["province"] == "Arequipa"
    assert body["data"]["address"]["department"] == "Arequipa"


def test_api_reverse_unmapped_oceanic_coordinates_200(client, database: Session):
    """TC-API-200-07: Unmapped coordinates return HTTP 200 with data=null."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    payload = {"latitude": 0.0, "longitude": 0.0}
    response = client.post(
        "/api/logistics/geocoding/reverse",
        headers=env["headers"],
        json=payload,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["data"] is None


# ============================================================================
# Category 2: HTTP 401 Unauthorized (Unauthenticated Requests)
# ============================================================================


def test_api_search_unauthenticated_missing_cookie_401(client):
    """TC-API-401-01: Unauthenticated forward search request is rejected with 401."""
    response = client.post(
        "/api/logistics/geocoding/search",
        json={"address": "Av. Larco 1234"},
    )
    assert response.status_code in {401, 403}


def test_api_reverse_unauthenticated_missing_cookie_401(client):
    """TC-API-401-02: Unauthenticated reverse geocoding request is rejected with 401."""
    response = client.post(
        "/api/logistics/geocoding/reverse",
        json={"latitude": -12.1215, "longitude": -77.0298},
    )
    assert response.status_code in {401, 403}


def test_api_search_invalid_session_token_401(client):
    """TC-API-401-03: Request with invalid or expired session cookie is rejected with 401."""
    client.cookies.set(settings.SESSION_COOKIE_NAME, "invalid-token-header.payload.signature")
    response = client.post(
        "/api/logistics/geocoding/search",
        json={"address": "Av. Larco 1234"},
    )
    assert response.status_code in {401, 403}


# ============================================================================
# Category 3: HTTP 403 Forbidden (RBAC Permissions & CSRF Protection)
# ============================================================================


def test_api_search_authenticated_without_branch_permissions_403(client, database: Session):
    """TC-API-403-01: Authenticated user with no permissions assigned is rejected with 403."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database, permissions=[])

    response = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json={"address": "Av. Larco 1234"},
    )
    assert response.status_code == 403


def test_api_reverse_authenticated_without_branch_permissions_403(client, database: Session):
    """TC-API-403-02: Authenticated user with unrelated permission is rejected with 403."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database, permissions=["logistics.organizations.read"])

    response = client.post(
        "/api/logistics/geocoding/reverse",
        headers=env["headers"],
        json={"latitude": -12.1215, "longitude": -77.0298},
    )
    assert response.status_code == 403


def test_api_search_allowed_with_branch_read_permission_200(client, database: Session):
    """TC-API-403-03: User with only 'logistics.branches.read' can access geocoding search."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database, permissions=["logistics.branches.read"])

    response = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json={"address": "Av. Larco 1234"},
    )
    assert response.status_code == 200


def test_api_search_allowed_with_branch_create_permission_200(client, database: Session):
    """TC-API-403-04: User with only 'logistics.branches.create' can access geocoding search."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database, permissions=["logistics.branches.create"])

    response = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json={"address": "Av. Larco 1234"},
    )
    assert response.status_code == 200


def test_api_search_allowed_with_branch_update_permission_200(client, database: Session):
    """TC-API-403-05: User with only 'logistics.branches.update' can access geocoding search."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database, permissions=["logistics.branches.update"])

    response = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json={"address": "Av. Larco 1234"},
    )
    assert response.status_code == 200


def test_api_search_missing_csrf_token_403(client, database: Session):
    """TC-API-403-06: Authenticated request lacking X-CSRF-Token header is rejected with 403."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    # Omit CSRF header from request
    response = client.post(
        "/api/logistics/geocoding/search",
        headers={},  # Missing X-CSRF-Token
        json={"address": "Av. Larco 1234"},
    )
    assert response.status_code == 403


# ============================================================================
# Category 4: HTTP 422 Unprocessable Entity (Schema Validation)
# ============================================================================


def test_api_search_empty_address_string_422(client, database: Session):
    """TC-API-422-01: Empty or whitespace address string fails Pydantic validation with 422."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    resp_empty = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json={"address": ""},
    )
    assert resp_empty.status_code == 422

    resp_spaces = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json={"address": "    "},
    )
    assert resp_spaces.status_code == 422


def test_api_search_missing_address_payload_422(client, database: Session):
    """TC-API-422-02: Missing required address field fails with 422."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    response = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json={},
    )
    assert response.status_code == 422


def test_api_search_address_exceeds_max_length_422(client, database: Session):
    """TC-API-422-03: Address exceeding 500 characters fails with 422."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    response = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json={"address": "A" * 501},
    )
    assert response.status_code == 422


def test_api_search_invalid_limit_out_of_bounds_422(client, database: Session):
    """TC-API-422-04: Limit parameter outside range [1, 20] fails with 422."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    # limit=0
    resp_zero = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json={"address": "Av. Larco", "limit": 0},
    )
    assert resp_zero.status_code == 422

    # limit=25
    resp_high = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json={"address": "Av. Larco", "limit": 25},
    )
    assert resp_high.status_code == 422


def test_api_reverse_latitude_out_of_bounds_422(client, database: Session):
    """TC-API-422-05: Latitude > 90.0 fails with 422."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    response = client.post(
        "/api/logistics/geocoding/reverse",
        headers=env["headers"],
        json={"latitude": 90.0001, "longitude": -77.0},
    )
    assert response.status_code == 422


def test_api_reverse_latitude_negative_out_of_bounds_422(client, database: Session):
    """TC-API-422-06: Latitude < -90.0 fails with 422."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    response = client.post(
        "/api/logistics/geocoding/reverse",
        headers=env["headers"],
        json={"latitude": -90.0001, "longitude": -77.0},
    )
    assert response.status_code == 422


def test_api_reverse_longitude_out_of_bounds_422(client, database: Session):
    """TC-API-422-07: Longitude > 180.0 fails with 422."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    response = client.post(
        "/api/logistics/geocoding/reverse",
        headers=env["headers"],
        json={"latitude": -12.0, "longitude": 180.0001},
    )
    assert response.status_code == 422


def test_api_reverse_longitude_negative_out_of_bounds_422(client, database: Session):
    """TC-API-422-08: Longitude < -180.0 fails with 422."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    response = client.post(
        "/api/logistics/geocoding/reverse",
        headers=env["headers"],
        json={"latitude": -12.0, "longitude": -180.0001},
    )
    assert response.status_code == 422


def test_api_reverse_non_numeric_coordinates_422(client, database: Session):
    """TC-API-422-09: Non-numeric coordinate string fails with 422."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    response = client.post(
        "/api/logistics/geocoding/reverse",
        headers=env["headers"],
        json={"latitude": "invalido", "longitude": -77.0},
    )
    assert response.status_code == 422


def test_api_reverse_missing_coordinate_field_422(client, database: Session):
    """TC-API-422-10: Missing required longitude field fails with 422."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    response = client.post(
        "/api/logistics/geocoding/reverse",
        headers=env["headers"],
        json={"latitude": -12.0},
    )
    assert response.status_code == 422


# ============================================================================
# Category 5: HTTP 503 Service Unavailable (External Service Outages)
# ============================================================================


def test_api_search_upstream_timeout_returns_503(client, database: Session):
    """TC-API-503-01: Upstream Nominatim timeout returns HTTP 503 GEOCODING_PROVIDER_UNAVAILABLE."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    payload = {"address": "timeout address search"}
    response = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json=payload,
    )

    assert response.status_code == 503, response.text
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "GEOCODING_PROVIDER_UNAVAILABLE"


def test_api_search_upstream_502_503_returns_503(client, database: Session):
    """TC-API-503-02: Upstream Nominatim 502/503 returns HTTP 503 GEOCODING_PROVIDER_UNAVAILABLE."""
    _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    payload = {"address": "error503 address search"}
    response = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json=payload,
    )

    assert response.status_code == 503, response.text
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "GEOCODING_PROVIDER_UNAVAILABLE"


def test_api_reverse_upstream_timeout_returns_503(client, database: Session):
    """TC-API-503-03: Upstream reverse geocoding timeout/outage returns HTTP 503."""
    _setup_mock_geocoding_service(base_url="https://nominatim.openstreetmap.org/error503")
    env = _setup_scoped_environment(client, database)

    payload = {"latitude": -12.1215, "longitude": -77.0298}
    response = client.post(
        "/api/logistics/geocoding/reverse",
        headers=env["headers"],
        json=payload,
    )

    assert response.status_code == 503, response.text
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "GEOCODING_PROVIDER_UNAVAILABLE"


# ============================================================================
# Category 6: Tenant Isolation & Scope Enforcement
# ============================================================================


def test_api_geocoding_principal_organization_scoping(client, database: Session):
    """TC-API-ISO-01: Principal scoped to organization executes geocoding in tenant context."""
    _setup_mock_geocoding_service()
    env_a = _setup_scoped_environment(client, database, org_name="Org A Geocoding")

    response = client.post(
        "/api/logistics/geocoding/search",
        headers=env_a["headers"],
        json={"address": "Av. Larco 1234"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


# ============================================================================
# Category 7: Cache Hit Verification
# ============================================================================


def test_api_search_cache_hit_prevents_duplicate_http_transport_call(client, database: Session):
    """TC-API-CACHE-01: Repeated identical forward search hits cache with 0 additional transport calls."""
    _, transport, _ = _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    payload = {"address": "Av. Larco 1234"}

    # First request: cache miss, invokes transport
    resp1 = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json=payload,
    )
    assert resp1.status_code == 200
    assert transport.call_count == 1

    # Second request: cache hit, preserves call count
    resp2 = client.post(
        "/api/logistics/geocoding/search",
        headers=env["headers"],
        json=payload,
    )
    assert resp2.status_code == 200
    assert transport.call_count == 1
    assert resp1.json()["data"] == resp2.json()["data"]


def test_api_reverse_cache_hit_prevents_duplicate_http_transport_call(client, database: Session):
    """TC-API-CACHE-02: Sub-meter coordinate variations hit 5-decimal reverse cache."""
    _, transport, _ = _setup_mock_geocoding_service()
    env = _setup_scoped_environment(client, database)

    # First point: (-12.1215000, -77.0298000)
    resp1 = client.post(
        "/api/logistics/geocoding/reverse",
        headers=env["headers"],
        json={"latitude": -12.1215000, "longitude": -77.0298000},
    )
    assert resp1.status_code == 200
    assert transport.call_count == 1

    # Sub-meter variation (<10cm): (-12.1215002, -77.0298001)
    resp2 = client.post(
        "/api/logistics/geocoding/reverse",
        headers=env["headers"],
        json={"latitude": -12.1215002, "longitude": -77.0298001},
    )
    assert resp2.status_code == 200
    assert transport.call_count == 1  # Cache hit due to 5-decimal rounding
