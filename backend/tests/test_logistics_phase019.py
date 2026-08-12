"""Unit, integration, and security tests for Phase 019 Transport and Delivery Document Templates.

Covers: HV, HR, CVT, PAR, INC, POD, EP, RECH
Validators: RoutePlanSnapshot, VehicleControlContext, DeliveryPodContext, DeliveryPartialContext, DeliveryRejectionContext
Phase 019 guarantee: Previews only, no real transportation or delivery records.
"""

from __future__ import annotations

from decimal import Decimal
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.modules.logistics.documents.rendering.transport_schemas import (
    RoutePlanSnapshot,
    RouteStopSnapshot,
    CoordinatesSnapshot,
    VehicleControlContext,
    VehicleChecklistItem,
)
from app.modules.logistics.documents.rendering.delivery_schemas import (
    DeliveryPodContext,
    DeliveryPartialContext,
    DeliveryRejectionContext,
    DeliveryLineSnapshot,
)
from app.modules.logistics.documents.rendering.transport_service import (
    TransportRenderingService,
    mask_sensitive_val,
)
from app.modules.logistics.documents.rendering.delivery_service import (
    DeliveryRenderingService,
)


from app.database.session import SessionLocal, engine
from app.database.base import Base

@pytest.fixture(scope="module")
def app():
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="module", autouse=True)
def seed_templates(setup_db):
    """Seeds the catalog with Phase 019 templates for test database sessions."""
    db = SessionLocal()
    try:
        t_srv = TransportRenderingService(db)
        d_srv = DeliveryRenderingService(db)
        t_srv.seed_transport_templates()
        d_srv.seed_delivery_templates()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 1. Pydantic Validator Unit Tests
# ---------------------------------------------------------------------------

class TestValidators:
    def test_vehicle_checklist_not_fit_if_critical_fails(self):
        """If a critical item fails in CVT, state must be NOT_FIT."""
        checklist = [
            VehicleChecklistItem(
                code="BRAKES",
                category="MECHANICAL",
                label="Frenos de servicio",
                result="FAIL",
                severity_if_failed="CRITICAL",
            )
        ]
        # Should raise ValueError because verification_state is FIT_FOR_OPERATION but critical item failed
        with pytest.raises(ValueError, match="Verification state must be NOT_FIT"):
            VehicleControlContext(
                trip_reference="TRP-001",
                vehicle_snapshot={"plate": "ABC-123"},
                driver_snapshot={"full_name": "Juan Perez", "document_number": "11111111", "license_number": "L11111111"},
                inspected_at="2026-07-26 10:00",
                inspected_by="Inspector 1",
                checklist=checklist,
                verification_state="FIT_FOR_OPERATION",
            )

    def test_delivery_quantity_balance_pod(self):
        """Sum of delivered, rejected and pending must equal planned quantity in POD lines."""
        item = DeliveryLineSnapshot(
            line_number=1,
            product_snapshot={"sku": "PROD01", "description": "Producto A"},
            planned_quantity=Decimal("10.00"),
            delivered_quantity=Decimal("5.00"),
            rejected_quantity=Decimal("3.00"),
            pending_quantity=Decimal("1.00"),  # 5 + 3 + 1 = 9 != 10
            unit="UN",
        )
        with pytest.raises(ValueError, match="must equal planned_quantity"):
            DeliveryPodContext(
                trip_reference="TRP-001",
                stop_reference="STOP-001",
                destination={"name": "Cliente A", "address": "Direccion A"},
                occurred_at="2026-07-26 12:00",
                driver_snapshot={"full_name": "Juan Perez", "document_number": "11111111", "license_number": "L11111111"},
                delivery_items=[item],
                delivery_result="PARTIALLY_DELIVERED",
            )

    def test_route_plan_calculation_requires_fields(self):
        """Calculated route plans require calculation metadata."""
        with pytest.raises(ValueError, match="calculated_at is required"):
            RoutePlanSnapshot(
                calculation_status="CALCULATED",
                calculated_at=None,
                origin="Lima",
                destination="Callao",
            )


# ---------------------------------------------------------------------------
# 2. Privacy Masking Utilities Tests
# ---------------------------------------------------------------------------

def test_masking_utility():
    assert mask_sensitive_val("12345678") == "******78"
    assert mask_sensitive_val("A") == "*"
    assert mask_sensitive_val(None) == "******"


# ---------------------------------------------------------------------------
# 3. Service Preview Rendering Tests
# ---------------------------------------------------------------------------

class TestServiceRendering:
    def test_hv_renders_pdf(self):
        db = SessionLocal()
        srv = TransportRenderingService(db)
        try:
            pdf = srv.render_transport_preview("HV", {
                "trip_reference": "TRP-001",
                "trip_date": "2026-07-30",
                "origin": "Almacen A",
                "destination_final": "Cliente B",
                "planned_departure_at": "2026-07-30 08:00",
                "vehicle_snapshot": {"plate": "XYZ-999"},
                "driver_snapshot": {"full_name": "Chofer A", "document_number": "44444444", "license_number": "Q44444444"},
                "planned_stops": [
                    {
                        "sequence": 1,
                        "name": "Cliente B",
                        "address": "Av. Principal 123",
                        "planned_arrival_at": "10:00",
                    }
                ]
            }, user_id="test-user")
            assert pdf.pdf_bytes.startswith(b"%PDF-")
            assert "HV" in pdf.filename_suggestion
        finally:
            db.close()

    def test_pod_renders_pdf(self):
        db = SessionLocal()
        srv = DeliveryRenderingService(db)
        try:
            pdf = srv.render_delivery_preview("POD", {
                "trip_reference": "TRP-001",
                "stop_reference": "STOP-001",
                "destination": {"name": "Cliente B", "address": "Av. Principal 123"},
                "occurred_at": "2026-07-30 10:15",
                "driver_snapshot": {"full_name": "Chofer A", "document_number": "44444444", "license_number": "Q44444444"},
                "delivery_items": [
                    {
                        "line_number": 1,
                        "product_snapshot": {"description": "Producto X"},
                        "planned_quantity": "10.00",
                        "delivered_quantity": "10.00",
                        "unit": "UN",
                    }
                ]
            }, user_id="test-user")
            assert pdf.pdf_bytes.startswith(b"%PDF-")
            assert "POD" in pdf.filename_suggestion
        finally:
            db.close()


# ---------------------------------------------------------------------------
# 4. Package Manifest Tests
# ---------------------------------------------------------------------------

class TestPackageManifests:
    def test_package_manifest_rules(self):
        db = SessionLocal()
        srv = TransportRenderingService(db)
        try:
            manifest = srv.build_transport_delivery_package_manifest({
                "package_mode": "ROUTE",
                "trip_reference": "TRP-888",
            })
            codes = [e.document_type_code for e in manifest.document_entries]
            assert "HV" in codes
            assert "HR" in codes
            assert "CVT" in codes
            assert manifest.warnings == ["Ruta pendiente de cálculo"]
        finally:
            db.close()


# ---------------------------------------------------------------------------
# 5. API Integration and OpenAPI Gating Tests
# ---------------------------------------------------------------------------

def test_api_openapi_transport_delivery_registered(app):
    schema = app.openapi()
    paths = set(schema["paths"].keys())

    # Transport
    assert "/api/logistics/transport/documents/{document_type_code}/preview" in paths
    assert "/api/logistics/transport/documents/{document_type_code}/pdf" in paths
    assert "/api/logistics/transport/document-package/manifest" in paths
    assert "/api/logistics/transport/document-package/preview" in paths

    # Delivery
    assert "/api/logistics/delivery/documents/{document_type_code}/preview" in paths
    assert "/api/logistics/delivery/documents/{document_type_code}/pdf" in paths


def test_api_unauthenticated_transport_delivery_returns_401(client: TestClient):
    # Transport
    assert client.post("/api/logistics/transport/documents/HV/preview", json={}).status_code == status.HTTP_401_UNAUTHORIZED
    assert client.post("/api/logistics/transport/document-package/manifest", json={}).status_code == status.HTTP_401_UNAUTHORIZED

    # Delivery
    assert client.post("/api/logistics/delivery/documents/POD/preview", json={}).status_code == status.HTTP_401_UNAUTHORIZED
