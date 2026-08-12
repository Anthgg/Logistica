"""Unit, integration, and security tests for Phase 014 Document Rendering Engine & Templates."""

from __future__ import annotations

import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.database.session import SessionLocal, engine
from app.database.base import Base
import app.models.registry  # noqa: F401
import app.modules.logistics.documents.rendering.template_models  # noqa: F401
from app.modules.logistics.documents.rendering.rendering import (
    DocumentRenderCommand,
    DocumentRendererEngine,
    DocumentQRGenerator,
)
from app.modules.logistics.documents.rendering.rendering_service import DocumentRenderingService
from app.modules.logistics.documents.rendering.template_schemas import DocumentPreviewRenderRequest


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


def test_qr_generator():
    qr_b64 = DocumentQRGenerator.generate_qr_base64("TEST_QR_DATA", preview_mode=True)
    assert qr_b64.startswith("data:image/")


def test_renderer_engine_html():
    engine_inst = DocumentRendererEngine()
    cmd = DocumentRenderCommand(
        document_type_code="OC",
        template_key="base.document",
        template_version="1.0.0",
        document_code="OC-LIM-2026-000001",
        document_title="ORDEN DE COMPRA BASE",
        organization_name="EMPRESA PRUEBA S.A.C.",
        branch_name="SEDE LIMA",
        document_data={
            "items": [
                {"code": "ITEM01", "description": "Cajas de cartón", "quantity": 100, "unit_price": "5.50"}
            ]
        },
        preview_mode=True,
    )
    html_res = engine_inst.render_html(cmd)
    assert "ORDEN DE COMPRA BASE" in html_res.html
    assert "OC-LIM-2026-000001" in html_res.html
    assert "Cajas de cartón" in html_res.html
    assert html_res.content_hash != ""


def test_renderer_engine_pdf():
    engine_inst = DocumentRendererEngine()
    cmd = DocumentRenderCommand(
        document_type_code="REQ",
        document_title="REQUERIMIENTO DE PRUEBA",
        preview_mode=True,
    )
    pdf_res = engine_inst.render_pdf(cmd)
    assert pdf_res.pdf_bytes.startswith(b"%PDF-")
    assert pdf_res.mime_type == "application/pdf"
    assert pdf_res.size_bytes > 0
    assert "PREVIEW" in pdf_res.filename_suggestion


def test_rendering_service_catalog_and_preview():
    db = SessionLocal()
    try:
        srv = DocumentRenderingService(db)
        tpls = srv.list_templates()
        assert len(tpls) >= 1
        assert tpls[0].template_key == "base.document"

        status_info = srv.get_status()
        assert status_info.renderer_available is True
        assert status_info.active_template_key == "base.document"

        req = DocumentPreviewRenderRequest(
            document_type_code="NI",
            document_title="NOTA DE INGRESO PRUEBA",
            document_code="NI-LIM-2026-000005",
            watermark_text="VISTA PREVIA",
        )
        pdf_res = srv.render_preview_pdf("base.document", req, user_id=str(uuid.uuid4()))
        assert pdf_res.pdf_bytes.startswith(b"%PDF-")
    finally:
        db.close()


def test_api_openapi_registered(app):
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/document-templates" in paths
    assert "/api/logistics/document-templates/{template_key}" in paths
    assert "/api/logistics/document-templates/{template_key}/versions" in paths
    assert "/api/logistics/document-templates/{template_key}/preview" in paths
    assert "/api/logistics/document-renderer/status" in paths


def test_api_unauthenticated_returns_401(client: TestClient):
    assert client.get("/api/logistics/document-templates").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.get("/api/logistics/document-renderer/status").status_code == status.HTTP_401_UNAUTHORIZED
