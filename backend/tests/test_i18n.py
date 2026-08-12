from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import settings
from app.i18n import (
    negotiate_locale,
    reset_current_locale,
    set_current_locale,
    translate_error,
    translate_event,
)
from app.i18n.catalogs import CATALOGS, PUBLIC_PREFIXES
from app.main import app
from app.schemas.shipment import ShipmentEventRead, ShipmentRead

client = TestClient(app)


def _public_keys(locale: str) -> set[str]:
    return {
        key
        for key in CATALOGS[locale]
        if key.startswith(PUBLIC_PREFIXES)
    }


def test_accept_language_negotiation_honors_region_and_quality() -> None:
    assert negotiate_locale("en-US,en;q=0.8") == "en"
    assert negotiate_locale("fr-FR,pt-BR;q=0.9,en;q=0.5") == "pt"
    assert negotiate_locale("en;q=0.4,es-PE;q=0.9") == "es"
    assert negotiate_locale("fr-FR") == "es"
    assert negotiate_locale(None) == "es"


def test_public_catalogs_have_the_same_contract() -> None:
    assert _public_keys("es") == _public_keys("en") == _public_keys("pt")


def test_catalog_returns_frontend_labels_in_requested_language() -> None:
    response = client.get(
        "/api/i18n/catalog",
        headers={"Accept-Language": "en-US,en;q=0.8"},
    )

    assert response.status_code == 200
    assert response.headers["Content-Language"] == "en"
    assert "Accept-Language" in response.headers["Vary"]
    assert response.json()["locale"] == "en"
    assert response.json()["supported_locales"] == ["es", "en", "pt"]
    assert response.json()["translations"]["common"]["activity"] == "Activity"
    assert (
        response.json()["translations"]["status"]["in_transit"]
        == "In transit"
    )


def test_http_errors_keep_code_and_translate_message() -> None:
    response = client.get(
        "/api/route-that-does-not-exist",
        headers={"Accept-Language": "pt-BR"},
    )

    assert response.status_code == 404
    assert response.headers["Content-Language"] == "pt"
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert response.json()["error"]["message"] == "O recurso solicitado não existe."


def test_unknown_error_never_leaks_spanish_into_english_response() -> None:
    translated = translate_error(
        "CAPTURE_SIZE_EXCEEDED",
        "La captura supera el tamaño permitido.",
        "en",
    )
    assert translated == "The submitted data is invalid."


def test_shipment_and_timeline_include_localized_labels() -> None:
    token = set_current_locale("en")
    try:
        shipment = ShipmentRead(
            id=uuid4(),
            client_id=uuid4(),
            tracking_code="ALG-20260725-ABC123",
            origin_address="Lima",
            destination_address="Cusco",
            origin_district="Lima",
            destination_district="Cusco",
            package_description="Caja",
            package_count=1,
            total_weight=Decimal("2.5"),
            declared_value=Decimal("25.00"),
            priority="urgent",
            expected_delivery_at=None,
            status="in_transit",
            assigned_route_id=None,
            delivered_at=None,
            created_by=uuid4(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        event = ShipmentEventRead(
            id=uuid4(),
            previous_status="picked_up",
            new_status="in_transit",
            description=None,
            location=None,
            created_by=uuid4(),
            created_at=datetime.now(timezone.utc),
        )
    finally:
        reset_current_locale(token)

    assert shipment.status == "in_transit"
    assert shipment.status_label == "In transit"
    assert shipment.priority_label == "Urgent"
    assert event.previous_status_label == "Picked up"
    assert event.new_status_label == "In transit"


def test_activity_uses_localized_label_but_keeps_event_code() -> None:
    assert translate_event("LOGIN_SUCCESS", "es") == "Inicio de sesión correcto"
    assert translate_event("LOGIN_SUCCESS", "en") == "Login successful"
    assert translate_event("UNMAPPED_EVENT", "pt") == "Atividade registrada"


def test_shipments_supports_trailing_slash_without_redirect() -> None:
    response = client.get(
        "/api/shipments/",
        headers={"Accept-Language": "en"},
        follow_redirects=False,
    )

    assert response.status_code == 401
    assert response.headers["Content-Language"] == "en"
    assert response.json()["error"]["code"] == "SESSION_REQUIRED"


def test_cors_allows_language_header_and_exposes_response_language() -> None:
    response = client.options(
        "/api/i18n/catalog",
        headers={
            "Origin": settings.FRONTEND_URL,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Accept-Language",
        },
    )

    assert response.status_code == 200
    assert "accept-language" in response.headers["Access-Control-Allow-Headers"].lower()
    actual_response = client.get(
        "/api/i18n/catalog",
        headers={"Origin": settings.FRONTEND_URL},
    )
    assert (
        "content-language"
        in actual_response.headers["Access-Control-Expose-Headers"].lower()
    )
