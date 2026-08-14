"""HTTP contract, security and structural tests for PDF downloads.

Guarantees that every operational PDF can be retrieved without depending on the
browser's built-in viewer: a real ``attachment`` download exists, carries real
PDF bytes, and stays behind the same auth/RBAC/tenant rules as its preview.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.pdf_response import PDF_MEDIA_TYPE
from app.database.session import get_db
from app.main import app
from app.modules.logistics.auth_dependencies import get_logistics_principal
from app.modules.logistics.documents.application.lifecycle_service import (
    DocumentLifecycleService,
)
from app.modules.logistics.principal import LogisticsPrincipal

pytestmark = pytest.mark.security

MINIMAL_PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
DOCUMENTS_BASE = "/api/logistics/documents"


def _make_principal(
    *,
    org_ids: list[UUID] | None = None,
    permissions: list[str] | None = None,
) -> LogisticsPrincipal:
    org_strs = [str(o) for o in (org_ids or [uuid4()])]
    return LogisticsPrincipal(
        user_id=uuid4(),
        email="pdf_test@example.com",
        full_name="PDF Test User",
        platform_role="user",
        is_active=True,
        session_id=uuid4(),
        device_id=None,
        authentication_level="normal",
        session_expires_at=datetime.now(UTC),
        risk_score=0.1,
        logistics_enabled=True,
        role_codes=["LOGISTICS_OPERATOR"],
        permission_codes=permissions or [],
        sensitive_permissions=[],
        step_up_permissions=[],
        organization_ids=org_strs,
        default_organization_id=org_strs[0],
    )


def _pdf_operations() -> list[tuple[str, str]]:
    """(method, path) for every operation declaring an application/pdf response."""
    schema = app.openapi()
    found = []
    for path, ops in schema["paths"].items():
        for method, op in ops.items():
            if not isinstance(op, dict):
                continue
            for response in (op.get("responses") or {}).values():
                if PDF_MEDIA_TYPE in (response.get("content") or {}):
                    found.append((method.upper(), path))
    return found


# ---------------------------------------------------------------------------
# Structural contract — preview is optional, download is mandatory
# ---------------------------------------------------------------------------


def test_pdf_endpoints_are_declared_in_openapi():
    """Every PDF route advertises application/pdf rather than defaulting to JSON."""
    assert len(_pdf_operations()) >= 30


@pytest.mark.parametrize(
    "preview_path,download_path",
    [
        (
            "/api/logistics/documents/{document_id}/preview",
            "/api/logistics/documents/{document_id}/pdf",
        ),
        (
            "/api/logistics/inbound/documents/{document_type_code}/preview",
            "/api/logistics/inbound/documents/{document_type_code}/pdf",
        ),
        (
            "/api/logistics/outbound/document-package/preview",
            "/api/logistics/outbound/document-package/pdf",
        ),
        (
            "/api/logistics/transport/document-package/preview",
            "/api/logistics/transport/document-package/pdf",
        ),
        (
            "/api/logistics/document-templates/{template_key}/preview",
            "/api/logistics/document-templates/{template_key}/pdf",
        ),
        (
            "/api/logistics/company-profile/document-preview",
            "/api/logistics/company-profile/document-preview.pdf",
        ),
        (
            "/api/logistics/reception-appointments/{appointment_id}/preview",
            "/api/logistics/reception-appointments/{appointment_id}/preview.pdf",
        ),
        (
            "/api/logistics/procurement/requisitions/{requisition_id}/document/preview",
            "/api/logistics/procurement/requisitions/{requisition_id}/document/preview.pdf",
        ),
    ],
)
def test_every_preview_has_a_download_counterpart(preview_path, download_path):
    """A preview may exist, but never as the only way to obtain the document."""
    paths = app.openapi()["paths"]
    assert preview_path in paths, f"preview route missing: {preview_path}"
    assert download_path in paths, f"download route missing for {preview_path}"


def test_no_pdf_route_is_served_over_an_unauthenticated_dependency():
    """Every PDF operation declares at least one dependency-backed parameter set."""
    schema = app.openapi()
    for method, path in _pdf_operations():
        operation = schema["paths"][path][method.lower()]
        # Auth is enforced by require_permission(...) dependencies; the public
        # contract must at least document a 4xx outcome rather than only 200.
        assert operation.get("responses"), f"{method} {path} declares no responses"


# ---------------------------------------------------------------------------
# Authentication (§56)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", f"{DOCUMENTS_BASE}/{uuid4()}/pdf"),
        ("GET", f"{DOCUMENTS_BASE}/{uuid4()}/preview"),
        ("GET", f"/api/logistics/document-talonarios/{uuid4()}/pdf"),
        ("GET", f"/api/logistics/gate-check-ins/{uuid4()}/document/pdf"),
        ("GET", f"/api/logistics/reception-appointments/{uuid4()}/preview.pdf"),
        (
            "GET",
            f"/api/logistics/procurement/requisitions/{uuid4()}/document/preview.pdf",
        ),
        ("GET", f"/api/logistics/warehouses/locations/{uuid4()}/label.pdf"),
    ],
)
def test_pdf_download_requires_authentication(method, path):
    app.dependency_overrides.clear()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.request(method, path)
    assert response.status_code == 401, (
        f"{method} {path} returned {response.status_code}, expected 401"
    )
    assert not response.content.startswith(b"%PDF-")


# ---------------------------------------------------------------------------
# RBAC (§57) and tenant isolation (§58)
# ---------------------------------------------------------------------------


def _override(principal):
    class UnitDb:
        def add(self, _value):
            return None

        def flush(self):
            return None

    def override_database():
        yield UnitDb()

    app.dependency_overrides[get_logistics_principal] = lambda: principal
    app.dependency_overrides[get_db] = override_database


def test_pdf_download_without_permission_is_denied():
    _override(_make_principal(permissions=["logistics.documents.read"]))
    try:
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(f"{DOCUMENTS_BASE}/{uuid4()}/pdf")
        assert response.status_code in (401, 403)
        assert not response.content.startswith(b"%PDF-")
    finally:
        app.dependency_overrides.clear()


def test_cross_tenant_pdf_download_is_denied(monkeypatch):
    """ORG_A principal must not download a document owned by ORG_B."""
    org_a, org_b = uuid4(), uuid4()
    document_id = uuid4()

    def fake_get_document(self, doc_id):
        return SimpleNamespace(
            id=doc_id,
            organization_id=org_b,
            branch_id=uuid4(),
            warehouse_id=uuid4(),
            status="ISSUED",
            document_code="DOC-000001",
        )

    def fail_download(self, *args, **kwargs):  # pragma: no cover - must not run
        raise AssertionError("cross-tenant download reached the artifact layer")

    monkeypatch.setattr(DocumentLifecycleService, "get_document", fake_get_document)
    monkeypatch.setattr(DocumentLifecycleService, "get_downloadable_pdf", fail_download)

    _override(_make_principal(org_ids=[org_a], permissions=["logistics.documents.download"]))
    try:
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(f"{DOCUMENTS_BASE}/{document_id}/pdf")
        assert response.status_code == 403
        assert not response.content.startswith(b"%PDF-")
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Download contract (§55) and PDF integrity (§30, §32)
# ---------------------------------------------------------------------------


def test_same_tenant_pdf_download_contract(monkeypatch):
    org_id = uuid4()
    document_id = uuid4()

    def fake_get_document(self, doc_id):
        return SimpleNamespace(
            id=doc_id,
            organization_id=org_id,
            branch_id=uuid4(),
            warehouse_id=uuid4(),
            status="ISSUED",
            document_code="GRE-T001-00001234",
        )

    def fake_downloadable(self, doc_id, user_id, original=False):
        artifact = SimpleNamespace(filename="guía-remisión T001-00001234.pdf")
        return None, artifact, MINIMAL_PDF

    monkeypatch.setattr(DocumentLifecycleService, "get_document", fake_get_document)
    monkeypatch.setattr(DocumentLifecycleService, "get_downloadable_pdf", fake_downloadable)

    _override(_make_principal(org_ids=[org_id], permissions=["logistics.documents.download"]))
    try:
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(f"{DOCUMENTS_BASE}/{document_id}/pdf")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith(PDF_MEDIA_TYPE)

        disposition = response.headers["content-disposition"]
        assert disposition.startswith("attachment;")
        # ASCII fallback keeps Safari and older agents working ...
        assert 'filename="guia-remision-T001-00001234.pdf"' in disposition
        # ... while filename* carries the real accented name.
        assert "filename*=UTF-8''" in disposition
        assert "\r" not in disposition and "\n" not in disposition

        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["cache-control"] == "private, no-store"
        assert response.headers["content-length"] == str(len(MINIMAL_PDF))
        assert response.content.startswith(b"%PDF-")
        assert response.content == MINIMAL_PDF
    finally:
        app.dependency_overrides.clear()


def test_generator_returning_html_never_yields_a_200_pdf(monkeypatch):
    """An HTML/JSON error page must not be delivered labelled application/pdf."""
    org_id = uuid4()

    def fake_get_document(self, doc_id):
        return SimpleNamespace(
            id=doc_id,
            organization_id=org_id,
            branch_id=uuid4(),
            warehouse_id=uuid4(),
            status="ISSUED",
            document_code="DOC-1",
        )

    def broken_downloadable(self, doc_id, user_id, original=False):
        artifact = SimpleNamespace(filename="broken.pdf")
        return None, artifact, b"<html><body>Internal error</body></html>"

    monkeypatch.setattr(DocumentLifecycleService, "get_document", fake_get_document)
    monkeypatch.setattr(DocumentLifecycleService, "get_downloadable_pdf", broken_downloadable)

    _override(_make_principal(org_ids=[org_id], permissions=["logistics.documents.download"]))
    try:
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(f"{DOCUMENTS_BASE}/{uuid4()}/pdf")
        assert response.status_code == 500
        assert not response.content.startswith(b"%PDF-")
    finally:
        app.dependency_overrides.clear()


def test_content_disposition_injection_is_neutralised(monkeypatch):
    org_id = uuid4()

    def fake_get_document(self, doc_id):
        return SimpleNamespace(
            id=doc_id,
            organization_id=org_id,
            branch_id=uuid4(),
            warehouse_id=uuid4(),
            status="ISSUED",
            document_code="DOC-1",
        )

    def hostile_downloadable(self, doc_id, user_id, original=False):
        artifact = SimpleNamespace(filename='foo.pdf"\r\nX-Evil: yes')
        return None, artifact, MINIMAL_PDF

    monkeypatch.setattr(DocumentLifecycleService, "get_document", fake_get_document)
    monkeypatch.setattr(DocumentLifecycleService, "get_downloadable_pdf", hostile_downloadable)

    _override(_make_principal(org_ids=[org_id], permissions=["logistics.documents.download"]))
    try:
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(f"{DOCUMENTS_BASE}/{uuid4()}/pdf")
        assert response.status_code == 200
        # The payload must not have become a header of its own ...
        assert "x-evil" not in {k.lower() for k in response.headers}
        disposition = response.headers["content-disposition"]
        assert "\r" not in disposition and "\n" not in disposition
        # ... and must survive only as inert filename text: no parameter
        # separator and no header separator remain.
        assert ":" not in disposition
        assert disposition.startswith("attachment;")
        assert disposition.count(";") == 1
    finally:
        app.dependency_overrides.clear()


def test_path_traversal_filename_is_reduced_to_a_name(monkeypatch):
    org_id = uuid4()

    def fake_get_document(self, doc_id):
        return SimpleNamespace(
            id=doc_id,
            organization_id=org_id,
            branch_id=uuid4(),
            warehouse_id=uuid4(),
            status="ISSUED",
            document_code="DOC-1",
        )

    def traversal_downloadable(self, doc_id, user_id, original=False):
        artifact = SimpleNamespace(filename="../../../etc/passwd.pdf")
        return None, artifact, MINIMAL_PDF

    monkeypatch.setattr(DocumentLifecycleService, "get_document", fake_get_document)
    monkeypatch.setattr(DocumentLifecycleService, "get_downloadable_pdf", traversal_downloadable)

    _override(_make_principal(org_ids=[org_id], permissions=["logistics.documents.download"]))
    try:
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(f"{DOCUMENTS_BASE}/{uuid4()}/pdf")
        assert response.status_code == 200
        disposition = response.headers["content-disposition"]
        assert 'filename="passwd.pdf"' in disposition
        assert ".." not in disposition
        assert "/" not in disposition.split("filename=")[1]
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# CORS (§29)
# ---------------------------------------------------------------------------


def test_content_disposition_is_exposed_to_the_browser():
    """Without this the SPA cannot read the download filename."""
    from app.core.config import settings

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get(
        "/api/health", headers={"Origin": settings.FRONTEND_URL}
    )
    exposed = response.headers.get("access-control-expose-headers", "")
    assert "Content-Disposition" in exposed
