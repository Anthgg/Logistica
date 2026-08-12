"""Unit, integration, and security tests for Phase 015 Purchasing Document Templates (REQ, SCOT, CCO, OC, APC, CEP)."""

from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.database.session import SessionLocal, engine
from app.database.base import Base
import app.models.registry  # noqa: F401
import app.modules.logistics.documents.rendering.template_models  # noqa: F401
from app.modules.logistics.documents.rendering.purchasing_service import PurchasingRenderingService


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


def test_purchasing_rendering_service_all_6_documents():
    db = SessionLocal()
    try:
        srv = PurchasingRenderingService(db)

        # 1. REQ
        req_pdf = srv.render_purchasing_preview("REQ", {"requesting_area": "Mantenimiento", "items": [{"description": "Filtros", "quantity": 10}]})
        assert req_pdf.pdf_bytes.startswith(b"%PDF-")
        assert "REQ" in req_pdf.filename_suggestion

        # 2. SCOT
        scot_pdf = srv.render_purchasing_preview("SCOT", {"supplier": {"business_name": "PROV TEST"}, "response_deadline": "2026-08-01", "items": [{"description": "Lubricantes", "quantity": 5}]})
        assert scot_pdf.pdf_bytes.startswith(b"%PDF-")
        assert "SCOT" in scot_pdf.filename_suggestion

        # 3. CCO
        cco_pdf = srv.render_purchasing_preview("CCO", {"suppliers": [{"business_name": "P1", "total_amount": "100.00"}, {"business_name": "P2", "total_amount": "90.00", "is_recommended": True}], "recommended_supplier_name": "P2", "recommendation_reason": "Menor costo"})
        assert cco_pdf.pdf_bytes.startswith(b"%PDF-")
        assert "CCO" in cco_pdf.filename_suggestion

        # 4. OC
        oc_pdf = srv.render_purchasing_preview("OC", {"supplier": {"business_name": "DISTRIBUIDORA X"}, "items": [{"description": "Repuestos", "quantity": 2, "unit_price": "150.00", "total": "300.00"}], "subtotal": "300.00", "tax": "54.00", "total": "354.00"})
        assert oc_pdf.pdf_bytes.startswith(b"%PDF-")
        assert "OC" in oc_pdf.filename_suggestion

        # 5. APC
        apc_pdf = srv.render_purchasing_preview("APC", {"decision": "APROBADO", "amount": "354.00", "approver": "Gerente Operaciones"})
        assert apc_pdf.pdf_bytes.startswith(b"%PDF-")
        assert "APC" in apc_pdf.filename_suggestion

        # 6. CEP
        cep_pdf = srv.render_purchasing_preview("CEP", {"related_document_code": "OC-LIM-2026-000001", "recipients": "proveedor@test.com"})
        assert cep_pdf.pdf_bytes.startswith(b"%PDF-")
        assert "CEP" in cep_pdf.filename_suggestion
    finally:
        db.close()


def test_api_openapi_purchasing_registered(app):
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/purchasing/documents/{document_type_code}/preview" in paths
    assert "/api/logistics/purchasing/documents/{document_type_code}/pdf" in paths


def test_api_unauthenticated_purchasing_returns_401(client: TestClient):
    assert client.post("/api/logistics/purchasing/documents/REQ/preview", json={}).status_code == status.HTTP_401_UNAUTHORIZED
    assert client.post("/api/logistics/purchasing/documents/OC/pdf", json={}).status_code == status.HTTP_401_UNAUTHORIZED
