"""PostgreSQL integration gate for PDF audit ownership and transactions.

The renderer and artifact storage are the only substituted boundaries. HTTP
orchestration, audit repositories, SQLAlchemy persistence, and the request
dependency transaction all remain real.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.session import get_db
from app.main import app
from app.models.audit_log import AuditLog
from app.models.branch import Branch
from app.models.organization import Organization
from app.models.session import UserSession
from app.models.user import User
from app.models.warehouse import Warehouse
from app.modules.logistics.audit.models_event import LogisticsAuditEvent
from app.modules.logistics.auth_dependencies import get_logistics_principal
from app.modules.logistics.documents.infrastructure.storage import DocumentArtifactStorage
from app.modules.logistics.documents.models import (
    DocumentArtifactModel,
    DocumentFamilyModel,
    DocumentInstanceModel,
    DocumentSnapshotModel,
    DocumentTypeModel,
)
from app.modules.logistics.documents.rendering.rendering import (
    DocumentRendererEngine,
    PdfRenderResult,
)
from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
    ArrivalNoticeModel,
    ArrivalNoticeRevisionModel,
)
from app.modules.logistics.inbound.gate_control.infrastructure.persistence.models import (
    GateCheckInModel,
    WarehouseGateModel,
)
from app.modules.logistics.inbound.reception_calendar.infrastructure.persistence.models import (
    ReceptionAppointmentModel,
    WarehouseReceptionCalendarModel,
)
from app.modules.logistics.partners.models import BusinessPartnerModel
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.units.models import (
    MeasurementDimensionModel,
    UnitOfMeasureModel,
)
from app.modules.logistics.warehouses.models import WarehouseLocationModel

pytestmark = [pytest.mark.postgres, pytest.mark.pdf_postgres]

MINIMAL_PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
PREVIEW_SUCCESS = {"logistics.document.preview_rendered"}
DOWNLOAD_SUCCESS = {
    "logistics.inbound_document.preview_downloaded",
    "logistics.document.downloaded",
    "logistics.reception_appointment.document_downloaded",
    "logistics.purchase_requisition.document_downloaded",
    "logistics.warehouse_location.label_downloaded",
    "logistics.warehouse_location.batch_labels_downloaded",
}


@dataclass(frozen=True)
class PdfEventCounts:
    preview: int
    download: int

    def delta(self, before: PdfEventCounts) -> PdfEventCounts:
        return PdfEventCounts(
            preview=self.preview - before.preview,
            download=self.download - before.download,
        )


@dataclass(frozen=True)
class PdfPostgresScenario:
    organization_id: UUID
    other_organization_id: UUID
    branch_id: UUID
    warehouse_id: UUID
    user_id: UUID
    session_id: UUID
    draft_document_id: UUID
    issued_document_id: UUID
    cit_document_id: UUID
    gate_check_in_id: UUID
    appointment_id: UUID
    location_id: UUID
    document_type_code: str
    postgres_version: str


def _require_real_postgres(engine: Engine) -> None:
    if engine.dialect.name == "postgresql":
        return
    message = "PDF_POSTGRES_REQUIRED: TEST_DATABASE_URL must resolve to PostgreSQL"
    if os.getenv("CI", "").lower() in {"1", "true", "yes"}:
        pytest.fail(message)
    pytest.skip(message)


@pytest.fixture(scope="session")
def pdf_pg_engine(test_engine: Engine) -> Engine:
    """Reuse the isolated test schema, but reject the SQLite fallback."""
    _require_real_postgres(test_engine)
    with test_engine.connect() as connection:
        version = connection.execute(text("select version() ")).scalar_one()
    assert "PostgreSQL" in version
    return test_engine


def _snapshot(document_id: UUID, code: str, actor_id: UUID) -> DocumentSnapshotModel:
    return DocumentSnapshotModel(
        document_id=document_id,
        snapshot_version=1,
        canonical_payload={"source": "pdf-postgres-gate"},
        canonical_payload_hash="a" * 64,
        document_type_code=code,
        document_type_version="1.0.0",
        catalog_version="1.0.0",
        template_key="pdf.postgres.gate",
        template_version="1.0.0",
        organization_snapshot={},
        branch_snapshot={},
        created_by=actor_id,
    )


@pytest.fixture(scope="session")
def pdf_pg_scenario(pdf_pg_engine: Engine) -> PdfPostgresScenario:
    token = uuid4().hex[:8]
    now = datetime.now(UTC)
    with Session(pdf_pg_engine, expire_on_commit=False) as db:
        user = User(
            email=f"pdf-pg-{token}@example.test",
            password_hash="not-used-in-test",
            full_name="PDF PostgreSQL Gate",
            is_active=True,
        )
        organization = Organization(
            code=f"PG{token[:6]}", name="PDF PG Organization", country_code="PE"
        )
        other_organization = Organization(
            code=f"PX{token[:6]}", name="Other PDF PG Organization", country_code="PE"
        )
        db.add_all([user, organization, other_organization])
        db.flush()

        user_session = UserSession(
            user_id=user.id,
            token_hash=f"pdf-pg-token-{token}",
            expires_at=now + timedelta(hours=1),
            continuous_auth_status="active",
        )
        branch = Branch(
            organization_id=organization.id,
            code=f"B{token[:6]}",
            name="PDF PG Branch",
        )
        db.add_all([user_session, branch])
        db.flush()

        warehouse = Warehouse(
            organization_id=organization.id,
            branch_id=branch.id,
            code=f"W{token[:6]}",
            name="PDF PG Warehouse",
        )
        family = DocumentFamilyModel(
            code=f"PDF_PG_{token}", name="PDF PostgreSQL Gate"
        )
        db.add_all([warehouse, family])
        db.flush()

        document_type = DocumentTypeModel(
            code="CIT",
            name="CIT PDF PostgreSQL Gate",
            family_id=family.id,
            origin_type="INTERNAL",
            owner_module="logistics",
            resource_type="document",
            operation_type="PREVIEW",
        )
        db.add(document_type)
        db.flush()

        documents: list[DocumentInstanceModel] = []
        for source, status in (
            ("PG_PREVIEW", "DRAFT"),
            ("PG_DOWNLOAD", "ISSUED"),
            ("PG_CIT", "DRAFT"),
        ):
            document = DocumentInstanceModel(
                organization_id=organization.id,
                branch_id=branch.id,
                warehouse_id=warehouse.id,
                document_type_id=document_type.id,
                source_resource_type=source,
                title=source,
                status=status,
                lifecycle_status=status,
                created_by=user.id,
            )
            db.add(document)
            db.flush()
            snap = _snapshot(document.id, document_type.code, user.id)
            db.add(snap)
            db.flush()
            document.current_snapshot_id = snap.id
            documents.append(document)

        issued_artifact = DocumentArtifactModel(
            document_id=documents[1].id,
            snapshot_id=documents[1].current_snapshot_id,
            artifact_type="ISSUED_PDF",
            filename="postgres-evidence.pdf",
            storage_key=f"test://{documents[1].id}",
            size_bytes=len(MINIMAL_PDF),
            file_hash="b" * 64,
            content_hash="c" * 64,
            template_version="1.0.0",
            renderer_version="1.0.0",
            generated_by=user.id,
        )
        db.add(issued_artifact)
        db.flush()
        documents[1].authoritative_artifact_id = issued_artifact.id

        gate = WarehouseGateModel(
            organization_id=organization.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            code=f"G{token[:6]}",
            normalized_code=f"G{token[:6]}",
            name="PDF PG Gate",
            timezone="America/Lima",
            status="ACTIVE",
            created_by=user.id,
        )
        db.add(gate)
        db.flush()

        gate_check_in = GateCheckInModel(
            organization_id=organization.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            gate_id=gate.id,
            document_instance_id=documents[1].id,
            status="ENTRY_AUTHORIZED",
            source_type="APPOINTMENT",
            arrival_classification="ON_TIME",
            gate_timezone="America/Lima",
            guard_user_id=user.id,
            guard_snapshot={"user_id": str(user.id)},
        )
        db.add(gate_check_in)
        db.flush()
        documents[1].source_resource_type = "GATE_CHECK_IN"
        documents[1].source_resource_id = gate_check_in.id

        location = WarehouseLocationModel(
            organization_id=organization.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            location_type="BIN",
            code=f"L{token[:6]}",
            full_code=f"PG-{token}",
            name="PDF PG Location",
            hierarchy_path=f"/{token}/",
        )
        dimension = MeasurementDimensionModel(
            code=f"WEIGHT_{token}", name="PDF PG Weight"
        )
        partner = BusinessPartnerModel(
            organization_id=organization.id,
            partner_code=f"P{token[:6]}",
            normalized_partner_code=f"P{token[:6]}",
            legal_name="PDF PG Supplier",
        )
        db.add_all([location, dimension, partner])
        db.flush()

        unit = UnitOfMeasureModel(
            dimension_id=dimension.id,
            code=f"KG{token[:4]}",
            normalized_code=f"KG{token[:4]}",
            name="PDF PG Kilogram",
            symbol="kg",
            minimum_increment=Decimal("0.001"),
        )
        db.add(unit)
        db.flush()

        notice = ArrivalNoticeModel(
            organization_id=organization.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            supplier_business_partner_id=partner.id,
            supplier_snapshot={"name": partner.legal_name},
            expected_arrival_date=datetime.now(UTC).date(),
            expected_arrival_timezone="America/Lima",
            weight_unit_id=unit.id,
            created_by=user.id,
        )
        calendar = WarehouseReceptionCalendarModel(
            organization_id=organization.id,
            warehouse_id=warehouse.id,
            name="PDF PG Calendar",
            timezone="America/Lima",
            status="ACTIVE",
            created_by=user.id,
        )
        db.add_all([notice, calendar])
        db.flush()

        revision = ArrivalNoticeRevisionModel(
            arrival_notice_id=notice.id,
            revision_number=1,
            status="FROZEN",
            supplier_snapshot=notice.supplier_snapshot,
            warehouse_snapshot={"id": str(warehouse.id)},
            purchase_order_snapshots=[],
            transport_snapshot={},
            document_references_snapshot=[],
            expected_load_summary={},
            special_requirements=[],
            created_by=user.id,
        )
        db.add(revision)
        db.flush()
        notice.active_revision_id = revision.id
        notice.confirmed_revision_id = revision.id

        appointment = ReceptionAppointmentModel(
            organization_id=organization.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            calendar_id=calendar.id,
            arrival_notice_id=notice.id,
            arrival_notice_revision_id=revision.id,
            document_instance_id=documents[2].id,
            status="CONFIRMED",
            slot_start=now + timedelta(days=1),
            slot_end=now + timedelta(days=1, hours=1),
            timezone="America/Lima",
            weight_unit_id=unit.id,
            supplier_snapshot=notice.supplier_snapshot,
            special_requirements_snapshot=[],
        )
        db.add(appointment)
        db.commit()

        version = db.execute(text("select version() ")).scalar_one()
        return PdfPostgresScenario(
            organization_id=organization.id,
            other_organization_id=other_organization.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            user_id=user.id,
            session_id=user_session.id,
            draft_document_id=documents[0].id,
            issued_document_id=documents[1].id,
            cit_document_id=documents[2].id,
            gate_check_in_id=gate_check_in.id,
            appointment_id=appointment.id,
            location_id=location.id,
            document_type_code=document_type.code,
            postgres_version=version,
        )


@pytest.fixture
def pdf_pg_client(pdf_pg_engine: Engine):
    commits: list[str] = []

    class CountingSession(Session):
        def commit(self) -> None:
            commits.append("commit")
            super().commit()

    session_factory = sessionmaker(
        bind=pdf_pg_engine,
        class_=CountingSession,
        autoflush=False,
        expire_on_commit=False,
    )

    def override_database():
        database = session_factory()
        try:
            yield database
            database.commit()
        except Exception:
            database.rollback()
            raise
        finally:
            database.close()

    app.dependency_overrides[get_db] = override_database
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, commits
    app.dependency_overrides.clear()


def _principal(
    scenario: PdfPostgresScenario,
    *,
    organization_id: UUID | None = None,
    permissions: list[str] | None = None,
) -> LogisticsPrincipal:
    org_id = organization_id or scenario.organization_id
    return LogisticsPrincipal(
        user_id=scenario.user_id,
        email="pdf-pg@example.test",
        full_name="PDF PostgreSQL Gate",
        platform_role="user",
        is_active=True,
        session_id=scenario.session_id,
        device_id=None,
        authentication_level="normal",
        session_expires_at=datetime.now(UTC) + timedelta(hours=1),
        risk_score=0.0,
        logistics_enabled=True,
        role_codes=["LOGISTICS_OPERATOR"],
        permission_codes=permissions or [],
        sensitive_permissions=[],
        step_up_permissions=[],
        organization_ids=[str(org_id)],
        branch_ids=[str(scenario.branch_id)],
        warehouse_ids=[str(scenario.warehouse_id)],
        default_organization_id=str(org_id),
        default_branch_id=str(scenario.branch_id),
        default_warehouse_id=str(scenario.warehouse_id),
    )


def _authorize(principal: LogisticsPrincipal) -> None:
    app.dependency_overrides[get_logistics_principal] = lambda: principal


def _event_counts(engine: Engine, actor_id: UUID) -> PdfEventCounts:
    with Session(engine) as db:
        generic_preview = db.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.user_id == actor_id, AuditLog.event_type.in_(PREVIEW_SUCCESS))
        )
        generic_download = db.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.user_id == actor_id, AuditLog.event_type.in_(DOWNLOAD_SUCCESS))
        )
        logistics_preview = db.scalar(
            select(func.count())
            .select_from(LogisticsAuditEvent)
            .where(
                LogisticsAuditEvent.actor_user_id == actor_id,
                LogisticsAuditEvent.event_code.in_(PREVIEW_SUCCESS),
            )
        )
        logistics_download = db.scalar(
            select(func.count())
            .select_from(LogisticsAuditEvent)
            .where(
                LogisticsAuditEvent.actor_user_id == actor_id,
                LogisticsAuditEvent.event_code.in_(DOWNLOAD_SUCCESS),
            )
        )
    return PdfEventCounts(
        preview=int(generic_preview or 0) + int(logistics_preview or 0),
        download=int(generic_download or 0) + int(logistics_download or 0),
    )


def _assert_delta(
    engine: Engine,
    scenario: PdfPostgresScenario,
    before: PdfEventCounts,
    *,
    preview: int,
    download: int,
) -> None:
    delta = _event_counts(engine, scenario.user_id).delta(before)
    assert delta == PdfEventCounts(preview=preview, download=download)


def _render_bytes(pdf_bytes: bytes):
    def render(_renderer, _command):
        return PdfRenderResult(
            pdf_bytes=pdf_bytes,
            size_bytes=len(pdf_bytes),
            filename_suggestion="postgres-render.pdf",
        )

    return render


def test_document_preview_persists_exactly_one_preview_and_one_commit(
    monkeypatch, pdf_pg_engine, pdf_pg_scenario, pdf_pg_client
):
    client, commits = pdf_pg_client
    _authorize(
        _principal(pdf_pg_scenario, permissions=["logistics.documents.preview"])
    )
    monkeypatch.setattr(DocumentRendererEngine, "render_pdf", _render_bytes(MINIMAL_PDF))
    before = _event_counts(pdf_pg_engine, pdf_pg_scenario.user_id)
    commits.clear()

    response = client.get(
        f"/api/logistics/documents/{pdf_pg_scenario.draft_document_id}/preview"
    )

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")
    assert commits == ["commit"]
    _assert_delta(
        pdf_pg_engine, pdf_pg_scenario, before, preview=1, download=0
    )


def test_document_download_persists_exactly_one_download_and_one_commit(
    monkeypatch, pdf_pg_engine, pdf_pg_scenario, pdf_pg_client
):
    client, commits = pdf_pg_client
    _authorize(
        _principal(pdf_pg_scenario, permissions=["logistics.documents.download"])
    )
    monkeypatch.setattr(DocumentArtifactStorage, "get", lambda _storage, _key: MINIMAL_PDF)
    before = _event_counts(pdf_pg_engine, pdf_pg_scenario.user_id)
    commits.clear()

    response = client.get(
        f"/api/logistics/documents/{pdf_pg_scenario.issued_document_id}/pdf"
    )

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")
    assert commits == ["commit"]
    _assert_delta(
        pdf_pg_engine, pdf_pg_scenario, before, preview=0, download=1
    )


def test_cpv_download_records_one_download_without_preview(
    monkeypatch, pdf_pg_engine, pdf_pg_scenario, pdf_pg_client
):
    client, commits = pdf_pg_client
    _authorize(
        _principal(
            pdf_pg_scenario,
            permissions=["logistics.gate_documents.download"],
        )
    )
    monkeypatch.setattr(DocumentArtifactStorage, "get", lambda _storage, _key: MINIMAL_PDF)
    before = _event_counts(pdf_pg_engine, pdf_pg_scenario.user_id)
    commits.clear()

    response = client.get(
        f"/api/logistics/gate-check-ins/{pdf_pg_scenario.gate_check_in_id}/document/pdf"
    )

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")
    assert commits == ["commit"]
    _assert_delta(
        pdf_pg_engine, pdf_pg_scenario, before, preview=0, download=1
    )


def test_direct_render_download_seeding_flushes_and_request_commits_once(
    monkeypatch, pdf_pg_engine, pdf_pg_scenario, pdf_pg_client
):
    client, commits = pdf_pg_client
    _authorize(_principal(pdf_pg_scenario, permissions=["logistics.documents.read"]))
    monkeypatch.setattr(DocumentRendererEngine, "render_pdf", _render_bytes(MINIMAL_PDF))
    before = _event_counts(pdf_pg_engine, pdf_pg_scenario.user_id)
    commits.clear()

    response = client.post("/api/logistics/inbound/documents/CIT/pdf", json={})

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")
    assert commits == ["commit"]
    _assert_delta(
        pdf_pg_engine, pdf_pg_scenario, before, preview=0, download=1
    )


@pytest.mark.parametrize("invalid_bytes", [b"<html>error</html>", b""])
def test_invalid_document_bytes_roll_back_without_success_event(
    invalid_bytes, monkeypatch, pdf_pg_engine, pdf_pg_scenario, pdf_pg_client
):
    client, commits = pdf_pg_client
    _authorize(
        _principal(pdf_pg_scenario, permissions=["logistics.documents.download"])
    )
    monkeypatch.setattr(
        DocumentArtifactStorage, "get", lambda _storage, _key: invalid_bytes
    )
    before = _event_counts(pdf_pg_engine, pdf_pg_scenario.user_id)
    commits.clear()

    response = client.get(
        f"/api/logistics/documents/{pdf_pg_scenario.issued_document_id}/pdf"
    )

    assert response.status_code == 500
    assert commits == []
    _assert_delta(
        pdf_pg_engine, pdf_pg_scenario, before, preview=0, download=0
    )


def test_unauthenticated_forbidden_and_cross_tenant_persist_zero_success(
    pdf_pg_engine, pdf_pg_scenario, pdf_pg_client
):
    client, commits = pdf_pg_client
    path = f"/api/logistics/documents/{pdf_pg_scenario.issued_document_id}/pdf"
    before = _event_counts(pdf_pg_engine, pdf_pg_scenario.user_id)

    app.dependency_overrides.pop(get_logistics_principal, None)
    assert client.get(path).status_code == 401

    _authorize(_principal(pdf_pg_scenario, permissions=[]))
    assert client.get(path).status_code == 403

    _authorize(
        _principal(
            pdf_pg_scenario,
            organization_id=pdf_pg_scenario.other_organization_id,
            permissions=["logistics.documents.download"],
        )
    )
    assert client.get(path).status_code == 403
    _assert_delta(
        pdf_pg_engine, pdf_pg_scenario, before, preview=0, download=0
    )
    assert commits == []


def test_company_download_records_download_without_preview(
    monkeypatch, pdf_pg_engine, pdf_pg_scenario, pdf_pg_client
):
    client, commits = pdf_pg_client
    _authorize(
        _principal(pdf_pg_scenario, permissions=["logistics.company_profile.read"])
    )
    monkeypatch.setattr(DocumentRendererEngine, "render_pdf", _render_bytes(MINIMAL_PDF))
    before = _event_counts(pdf_pg_engine, pdf_pg_scenario.user_id)
    commits.clear()

    response = client.post(
        "/api/logistics/company-profile/document-preview.pdf",
        json={
            "doc_type_code": pdf_pg_scenario.document_type_code,
            "branch_id": str(pdf_pg_scenario.branch_id),
            "custom_data": {"gate": "postgres"},
        },
    )

    assert response.status_code == 200
    assert commits == ["commit"]
    _assert_delta(
        pdf_pg_engine, pdf_pg_scenario, before, preview=0, download=1
    )


def test_cit_download_records_download_without_preview(
    monkeypatch, pdf_pg_engine, pdf_pg_scenario, pdf_pg_client
):
    client, commits = pdf_pg_client
    _authorize(
        _principal(
            pdf_pg_scenario,
            permissions=["logistics.reception_appointments.download"],
        )
    )
    monkeypatch.setattr(DocumentRendererEngine, "render_pdf", _render_bytes(MINIMAL_PDF))
    before = _event_counts(pdf_pg_engine, pdf_pg_scenario.user_id)
    commits.clear()

    response = client.get(
        "/api/logistics/reception-appointments/"
        f"{pdf_pg_scenario.appointment_id}/preview.pdf"
    )

    assert response.status_code == 200
    assert commits == ["commit"]
    _assert_delta(
        pdf_pg_engine, pdf_pg_scenario, before, preview=0, download=1
    )


def test_single_label_valid_and_invalid_audit_semantics(
    monkeypatch, pdf_pg_engine, pdf_pg_scenario, pdf_pg_client
):
    client, commits = pdf_pg_client
    _authorize(
        _principal(pdf_pg_scenario, permissions=["logistics.warehouses.read"])
    )
    path = (
        "/api/logistics/warehouses/locations/"
        f"{pdf_pg_scenario.location_id}/label.pdf"
    )

    monkeypatch.setattr(DocumentRendererEngine, "render_pdf", _render_bytes(MINIMAL_PDF))
    before = _event_counts(pdf_pg_engine, pdf_pg_scenario.user_id)
    commits.clear()
    valid = client.get(path)
    assert valid.status_code == 200
    assert commits == ["commit"]
    _assert_delta(
        pdf_pg_engine, pdf_pg_scenario, before, preview=0, download=1
    )

    monkeypatch.setattr(
        DocumentRendererEngine,
        "render_pdf",
        _render_bytes(b"<html>not a pdf</html>"),
    )
    before = _event_counts(pdf_pg_engine, pdf_pg_scenario.user_id)
    commits.clear()
    invalid = client.get(path)
    assert invalid.status_code == 500
    assert commits == []
    _assert_delta(
        pdf_pg_engine, pdf_pg_scenario, before, preview=0, download=0
    )


def test_label_export_valid_and_invalid_audit_semantics(
    monkeypatch, pdf_pg_engine, pdf_pg_scenario, pdf_pg_client
):
    client, commits = pdf_pg_client
    _authorize(
        _principal(pdf_pg_scenario, permissions=["logistics.warehouses.read"])
    )
    path = "/api/logistics/warehouses/locations/labels/export"
    body = [str(pdf_pg_scenario.location_id)]

    monkeypatch.setattr(DocumentRendererEngine, "render_pdf", _render_bytes(MINIMAL_PDF))
    before = _event_counts(pdf_pg_engine, pdf_pg_scenario.user_id)
    commits.clear()
    valid = client.post(path, json=body)
    assert valid.status_code == 200
    assert commits == ["commit"]
    _assert_delta(
        pdf_pg_engine, pdf_pg_scenario, before, preview=0, download=1
    )

    monkeypatch.setattr(DocumentRendererEngine, "render_pdf", _render_bytes(b""))
    before = _event_counts(pdf_pg_engine, pdf_pg_scenario.user_id)
    commits.clear()
    invalid = client.post(path, json=body)
    assert invalid.status_code == 500
    assert commits == []
    _assert_delta(
        pdf_pg_engine, pdf_pg_scenario, before, preview=0, download=0
    )
