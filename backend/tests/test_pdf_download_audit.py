"""Audit-trail tests for PDF delivery.

Two invariants, both regressions from the first review pass:

1. A download is audited only once the bytes are known to be a real PDF, so a
   failed render can never leave a "downloaded" record behind an HTTP 500.
2. Viewing and downloading are recorded as different events, so the trail can
   tell "opened it" apart from "took a copy".
"""

from __future__ import annotations

import inspect
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import app
from app.modules.logistics.auth_dependencies import get_logistics_principal
from app.modules.logistics.principal import LogisticsPrincipal
from app.services.audit_service import AuditService

pytestmark = pytest.mark.security

MINIMAL_PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
HTML_ERROR = b"<html><body>Internal Server Error</body></html>"

DOWNLOAD_MARKERS = ("downloaded", ".download")
PREVIEW_MARKERS = ("preview_rendered", "previewed")


class AuditSpy:
    """Collects the audit events a request would persist."""

    def __init__(self):
        self.events: list[str] = []

    @property
    def downloads(self) -> list[str]:
        return [e for e in self.events if any(m in e for m in DOWNLOAD_MARKERS)]

    @property
    def previews(self) -> list[str]:
        return [e for e in self.events if any(m in e for m in PREVIEW_MARKERS)]


@pytest.fixture
def audit(monkeypatch) -> AuditSpy:
    spy = AuditSpy()

    def fake_record(self, *, db=None, event_type=None, **kwargs):
        spy.events.append(event_type)

    monkeypatch.setattr(AuditService, "record", fake_record)
    return spy


def _principal(org_id: UUID, permissions: list[str]) -> LogisticsPrincipal:
    return LogisticsPrincipal(
        user_id=uuid4(),
        email="pdf_audit@example.com",
        full_name="PDF Audit User",
        platform_role="user",
        is_active=True,
        session_id=uuid4(),
        device_id=None,
        authentication_level="normal",
        session_expires_at=datetime.now(UTC),
        risk_score=0.1,
        logistics_enabled=True,
        role_codes=["LOGISTICS_OPERATOR"],
        permission_codes=permissions,
        sensitive_permissions=[],
        step_up_permissions=[],
        organization_ids=[str(org_id)],
        default_organization_id=str(org_id),
    )


@pytest.fixture
def client_for():
    """Return a factory that wires an authenticated client, then cleans up."""

    def _factory(permissions: list[str], org_id: UUID | None = None) -> TestClient:
        principal = _principal(org_id or uuid4(), permissions)

        def _fake_db():
            yield SimpleNamespace(commit=lambda: None, flush=lambda: None)

        app.dependency_overrides[get_logistics_principal] = lambda: principal
        app.dependency_overrides[get_db] = _fake_db
        return TestClient(app, raise_server_exceptions=False)

    yield _factory
    app.dependency_overrides.clear()


def _render_result(pdf_bytes: bytes):
    return SimpleNamespace(
        pdf_bytes=pdf_bytes,
        filename_suggestion="cit-recepcion.pdf",
        size_bytes=len(pdf_bytes),
        renderer_name="reportlab",
        file_hash="f" * 64,
        content_hash="c" * 64,
    )


# ---------------------------------------------------------------------------
# 1. A failed render is never audited as a delivered download
# ---------------------------------------------------------------------------

INBOUND_DOWNLOAD = "/api/logistics/inbound/documents/CIT/pdf"
INBOUND_PREVIEW = "/api/logistics/inbound/documents/CIT/preview"


def _patch_inbound(monkeypatch, payload: bytes):
    from app.modules.logistics.documents.rendering.inbound_service import (
        InboundRenderingService,
    )

    monkeypatch.setattr(
        InboundRenderingService,
        "render_inbound_preview",
        lambda self, code, data, user_id: _render_result(payload),
    )


@pytest.mark.parametrize("payload", [HTML_ERROR, b"", b"not a pdf at all"])
def test_invalid_pdf_records_no_download_event(monkeypatch, audit, client_for, payload):
    _patch_inbound(monkeypatch, payload)
    client = client_for(["logistics.documents.read"])

    response = client.post(INBOUND_DOWNLOAD, json={})

    assert response.status_code == 500
    assert not response.content.startswith(b"%PDF-")
    assert audit.downloads == [], (
        f"a failed render was audited as a download: {audit.downloads}"
    )
    assert audit.events == [], f"unexpected audit on failure: {audit.events}"


def test_valid_pdf_records_exactly_one_download_event(monkeypatch, audit, client_for):
    _patch_inbound(monkeypatch, MINIMAL_PDF)
    client = client_for(["logistics.documents.read"])

    response = client.post(INBOUND_DOWNLOAD, json={})

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")
    assert len(audit.downloads) == 1, audit.events
    assert audit.downloads == ["logistics.inbound_document.preview_downloaded"]


def test_preview_records_a_preview_and_no_download(monkeypatch, audit, client_for):
    _patch_inbound(monkeypatch, MINIMAL_PDF)
    client = client_for(["logistics.documents.read"])

    response = client.post(INBOUND_PREVIEW, json={})

    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith("inline;")
    assert audit.downloads == [], f"a preview was audited as a download: {audit.events}"
    assert audit.events == ["logistics.inbound_document.preview_rendered"]


def test_invalid_preview_records_nothing(monkeypatch, audit, client_for):
    _patch_inbound(monkeypatch, HTML_ERROR)
    client = client_for(["logistics.documents.read"])

    response = client.post(INBOUND_PREVIEW, json={})

    assert response.status_code == 500
    assert audit.events == []


# ---------------------------------------------------------------------------
# 2. The stored-artifact path validates before auditing (service level)
# ---------------------------------------------------------------------------


def _lifecycle_service(monkeypatch, stored: bytes):
    from app.modules.logistics.documents.application import lifecycle_service as mod

    service = mod.DocumentLifecycleService.__new__(mod.DocumentLifecycleService)
    artifact = SimpleNamespace(filename="guia.pdf", storage_key="k/1.pdf")
    inst = SimpleNamespace(
        id=uuid4(),
        organization_id=uuid4(),
        branch_id=uuid4(),
        warehouse_id=uuid4(),
        status="ISSUED",
        document_code="GRE-000001",
        authoritative_artifact_id=None,
    )
    service.db = SimpleNamespace(
        scalars=lambda *a, **k: SimpleNamespace(first=lambda: artifact),
        get=lambda *a, **k: artifact,
    )
    service.storage = SimpleNamespace(get=lambda key: stored)
    monkeypatch.setattr(
        mod.DocumentLifecycleService, "get_document", lambda self, doc_id: inst
    )
    written: list[str] = []
    monkeypatch.setattr(
        mod.DocumentLifecycleService,
        "_write_audit",
        lambda self, event, *a, **k: written.append(event),
    )
    return service, written


def test_corrupt_stored_artifact_is_not_audited_as_downloaded(monkeypatch):
    service, written = _lifecycle_service(monkeypatch, HTML_ERROR)

    with pytest.raises(HTTPException) as exc:
        service.get_downloadable_pdf(uuid4(), uuid4())

    assert exc.value.status_code == 500
    assert written == [], f"corrupt artifact audited as downloaded: {written}"


def test_valid_stored_artifact_is_audited_once_after_response_boundary(monkeypatch):
    service, written = _lifecycle_service(monkeypatch, MINIMAL_PDF)

    actor_id = uuid4()
    inst, _, pdf_bytes = service.get_downloadable_pdf(uuid4(), actor_id)

    assert pdf_bytes.startswith(b"%PDF-")
    assert written == []

    service.record_download(inst, actor_id)
    assert written == ["logistics.document.downloaded"]


def test_lifecycle_render_methods_do_not_own_http_success_events():
    from app.modules.logistics.documents.application.lifecycle_service import (
        DocumentLifecycleService,
    )

    assert "_write_audit" not in inspect.getsource(
        DocumentLifecycleService.preview_document
    )
    assert "_write_audit" not in inspect.getsource(
        DocumentLifecycleService.get_downloadable_pdf
    )


# ---------------------------------------------------------------------------
# 3. Preview and download are distinct events on the endpoints added by the hotfix
# ---------------------------------------------------------------------------


def test_reception_appointment_preview_and_download_differ(monkeypatch, audit, client_for):
    from app.modules.logistics.inbound.reception_calendar.application.services import (
        ReceptionAppointmentDocumentService,
    )

    monkeypatch.setattr(
        ReceptionAppointmentDocumentService,
        "preview",
        lambda self, appointment_id, org_id, actor: (MINIMAL_PDF, "cit.pdf"),
    )
    monkeypatch.setattr(
        "app.modules.logistics.auth_dependencies.resolve_organization_id",
        lambda principal: uuid4(),
    )

    appointment_id = uuid4()
    client = client_for(
        [
            "logistics.reception_appointments.preview",
            "logistics.reception_appointments.download",
        ]
    )

    preview = client.get(f"/api/logistics/reception-appointments/{appointment_id}/preview")
    assert preview.status_code == 200
    assert preview.headers["content-disposition"].startswith("inline;")
    assert audit.events == ["logistics.document.preview_rendered"]
    assert audit.downloads == []

    audit.events.clear()

    download = client.get(
        f"/api/logistics/reception-appointments/{appointment_id}/preview.pdf"
    )
    assert download.status_code == 200
    assert download.headers["content-disposition"].startswith("attachment;")
    assert audit.events == ["logistics.reception_appointment.document_downloaded"]
    assert len(audit.downloads) == 1


def test_requisition_preview_and_download_differ(monkeypatch, audit, client_for):
    from app.modules.logistics.procurement.requisitions.application.services import (
        document_service as doc_mod,
    )

    monkeypatch.setattr(
        doc_mod.purchase_requisition_document_service,
        "preview",
        lambda **kwargs: MINIMAL_PDF,
    )
    monkeypatch.setattr(
        "app.modules.logistics.auth_dependencies.resolve_organization_id",
        lambda principal: uuid4(),
    )

    requisition_id = uuid4()
    client = client_for(["logistics.purchase_requisitions.read"])

    preview = client.get(
        f"/api/logistics/procurement/requisitions/{requisition_id}/document/preview"
    )
    assert preview.status_code == 200
    assert audit.events == ["logistics.document.preview_rendered"]

    audit.events.clear()

    download = client.get(
        f"/api/logistics/procurement/requisitions/{requisition_id}/document/preview.pdf"
    )
    assert download.status_code == 200
    assert download.headers["content-disposition"].startswith("attachment;")
    assert audit.events == ["logistics.purchase_requisition.document_downloaded"]


@pytest.mark.parametrize(
    ("payload", "expected_status", "expected_events"),
    [
        (MINIMAL_PDF, 200, ["logistics.document.downloaded"]),
        (HTML_ERROR, 500, []),
    ],
)
def test_talonario_download_audits_only_a_valid_response(
    payload, expected_status, expected_events, monkeypatch, audit, client_for
):
    from app.modules.logistics.documents.application.export_service import (
        DocumentExportService,
    )

    monkeypatch.setattr(
        DocumentExportService,
        "generate_talonario_pdf",
        lambda self, talonario_id, actor_id: (payload, "talonario.pdf"),
    )
    client = client_for(["logistics.documents.read"])

    response = client.get(f"/api/logistics/document-talonarios/{uuid4()}/pdf")

    assert response.status_code == expected_status
    assert audit.events == expected_events


def test_company_profile_preview_and_download_differ(monkeypatch, audit, client_for):
    monkeypatch.setattr(
        "app.modules.logistics.company_profile.router._render_institutional_document",
        lambda req, principal, db: (MINIMAL_PDF, "ficha-institucional.pdf"),
    )

    client = client_for(["logistics.company_profile.read"])
    body = {"doc_type_code": "AREC"}

    preview = client.post("/api/logistics/company-profile/document-preview", json=body)
    assert preview.status_code == 200
    assert preview.headers["content-disposition"].startswith("inline;")
    assert audit.events == ["logistics.document.preview_rendered"]
    assert audit.downloads == []

    audit.events.clear()

    download = client.post(
        "/api/logistics/company-profile/document-preview.pdf", json=body
    )
    assert download.status_code == 200
    assert download.headers["content-disposition"].startswith("attachment;")
    assert audit.events == ["logistics.document.downloaded"]
    assert len(audit.downloads) == 1


def test_company_profile_invalid_pdf_records_nothing(monkeypatch, audit, client_for):
    monkeypatch.setattr(
        "app.modules.logistics.company_profile.router._render_institutional_document",
        lambda req, principal, db: (HTML_ERROR, "ficha-institucional.pdf"),
    )

    client = client_for(["logistics.company_profile.read"])
    response = client.post(
        "/api/logistics/company-profile/document-preview.pdf", json={"doc_type_code": "AREC"}
    )

    assert response.status_code == 500
    assert audit.events == []
