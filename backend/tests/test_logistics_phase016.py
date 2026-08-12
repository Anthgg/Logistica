"""Unit, integration, and security tests for Phase 016 Inbound Document Templates (CIT, CPV, AREC, NI, DIF, NC)."""

from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.database.session import SessionLocal, engine
from app.database.base import Base
import app.models.registry  # noqa: F401
import app.modules.logistics.documents.rendering.template_models  # noqa: F401
from app.modules.logistics.documents.rendering.inbound_schemas import mask_sensitive_id
from app.modules.logistics.documents.rendering.inbound_service import InboundRenderingService


@pytest.fixture(scope="module")
def app():
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Creates database tables for testing."""
    Base.metadata.create_all(bind=engine)


def test_driver_privacy_masking_utility():
    assert mask_sensitive_id("12345642", visible_end=2) == "******42"
    assert mask_sensitive_id("Q49876521", visible_end=2) == "*******21"
    assert mask_sensitive_id(None) == "******"


def test_inbound_rendering_service_all_6_documents():
    db = SessionLocal()
    try:
        srv = InboundRenderingService(db)

        # 1. CIT
        cit_pdf = srv.render_inbound_preview("CIT", {"expected_items": [{"description": "Cajas de insumos", "quantity": 50}]})
        assert cit_pdf.pdf_bytes.startswith(b"%PDF-")
        assert "CIT" in cit_pdf.filename_suggestion

        # 2. CPV (Driver DNI and License masked)
        cpv_pdf = srv.render_inbound_preview("CPV", {"plate": "XYZ-987", "driver_dni_raw": "76543210", "driver_license_raw": "B21234567"})
        assert cpv_pdf.pdf_bytes.startswith(b"%PDF-")
        assert "CPV" in cpv_pdf.filename_suggestion

        # 3. AREC
        arec_pdf = srv.render_inbound_preview("AREC", {"received_items": [{"description": "Paletas de madera", "expected_quantity": 10, "received_quantity": 10, "accepted_quantity": 10}]})
        assert arec_pdf.pdf_bytes.startswith(b"%PDF-")
        assert "AREC" in arec_pdf.filename_suggestion

        # 4. NI
        ni_pdf = srv.render_inbound_preview("NI", {"accepted_items": [{"description": "Cajas de cartón", "accepted_quantity": 100}]})
        assert ni_pdf.pdf_bytes.startswith(b"%PDF-")
        assert "NI" in ni_pdf.filename_suggestion

        # 5. DIF
        dif_pdf = srv.render_inbound_preview("DIF", {"differences": [{"difference_type": "FALTANTE", "description": "Faltaron 2 cajas", "expected_quantity": 10, "received_quantity": 8}]})
        assert dif_pdf.pdf_bytes.startswith(b"%PDF-")
        assert "DIF" in dif_pdf.filename_suggestion

        # 6. NC (Family QUALITY)
        nc_pdf = srv.render_inbound_preview("NC", {"affected_items": [{"description": "Tiradores de plástico", "affected_quantity": 5}], "severity": "ALTA"})
        assert nc_pdf.pdf_bytes.startswith(b"%PDF-")
        assert "NC" in nc_pdf.filename_suggestion
    finally:
        db.close()


def test_reception_package_manifest_rules():
    db = SessionLocal()
    try:
        srv = InboundRenderingService(db)
        manifest = srv.build_reception_package_manifest({
            "has_appointment": True,
            "has_vehicle_entry": True,
            "accepted_quantity": 10,
            "has_differences": True,
            "has_non_conformity": True,
        })
        assert "CIT" in manifest.included_documents
        assert "CPV" in manifest.included_documents
        assert "AREC" in manifest.included_documents
        assert "NI" in manifest.included_documents
        assert "DIF" in manifest.included_documents
        assert "NC" in manifest.included_documents
        assert len(manifest.warnings) >= 1
    finally:
        db.close()


def test_api_openapi_inbound_registered(app):
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/inbound/documents/{document_type_code}/preview" in paths
    assert "/api/logistics/inbound/documents/{document_type_code}/pdf" in paths
    assert "/api/logistics/inbound/document-package/manifest" in paths


def test_api_unauthenticated_inbound_returns_401(client: TestClient):
    assert client.post("/api/logistics/inbound/documents/CIT/preview", json={}).status_code == status.HTTP_401_UNAUTHORIZED
    assert client.post("/api/logistics/inbound/document-package/manifest", json={}).status_code == status.HTTP_401_UNAUTHORIZED
