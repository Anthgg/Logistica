"""Regresion HTTP del PDF de un documento ANULADO (Fase 020).

En UAT, un documento CANCELLED devolvia 500 en preview y en download:

    FileNotFoundError: Artifact not found under storage key:
    documents/<org>/2026/<doc>/cancelled/CANCELLED_PED_....pdf

La fila del artifact existia en base de datos; el binario no estaba en el
storage. El binario vive fuera de la transaccion, asi que ambas cosas pueden
divergir, y el servicio no lo traducia: el error escapaba como 500 crudo.

Estos casos recorren el camino que fallo en el navegador -- CANCELLED ->
CANCELLED_PDF -> storage.get() -- que los tests anteriores no tocaban porque
usaban un DRAFT.
"""

from __future__ import annotations

import hashlib
from collections.abc import Generator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.session import SessionLocal, engine, get_db
from app.main import app
from app.models.branch import Branch
from app.models.organization import Organization
from app.models.user import User
from app.modules.logistics.auth_dependencies import get_logistics_principal
from app.modules.logistics.documents.application.lifecycle_service import (
    DocumentLifecycleService,
)
from app.modules.logistics.documents.codes.code_models import DocumentSiteCodeModel
from app.modules.logistics.documents.models import (
    DocumentArtifactModel,
    DocumentFamilyModel,
    DocumentTypeModel,
    DocumentTypeVersionModel,
)
from app.modules.logistics.documents.series.series_schemas import (
    DocumentSeriesCreateRequest,
)
from app.modules.logistics.documents.series.series_service import DocumentSeriesService
from app.modules.logistics.principal import LogisticsPrincipal

pytestmark = [pytest.mark.http, pytest.mark.security]

@pytest.fixture(scope="module", autouse=True)
def _guard_isolated_database(isolated_database) -> None:
    """Estos casos hacen COMMIT: exigen una base de test aislada."""


@pytest.fixture(autouse=True)
def _guard_isolated_storage(isolated_document_storage) -> None:
    """Los PDF generados van a un temporal, no al storage del usuario."""


DOCUMENTS_BASE = "/api/logistics/documents"
PREVIEW = "logistics.documents.preview"
DOWNLOAD = "logistics.documents.download"
READ_SENSITIVE = "logistics.audit.read_sensitive"


@pytest.fixture(scope="module", autouse=True)
def setup_db() -> None:
    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _make_principal(org_id: UUID, permissions: list[str], user_id: UUID) -> LogisticsPrincipal:
    # El usuario debe existir: preview y download escriben un evento de
    # auditoria cuyo actor tiene FK contra `users`.
    return LogisticsPrincipal(
        user_id=user_id,
        email="documents_pdf@example.com",
        full_name="Operador PDF",
        platform_role="user",
        is_active=True,
        session_id=uuid4(),
        device_id=None,
        authentication_level="normal",
        session_expires_at=datetime.now(UTC),
        risk_score=0.1,
        logistics_enabled=True,
        role_codes=["DOCUMENT_OPERATOR"],
        permission_codes=permissions,
        organization_ids=[str(org_id)],
        default_organization_id=str(org_id),
    )


def _client(session: Session, principal: LogisticsPrincipal) -> TestClient:
    def override_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_logistics_principal] = lambda: principal
    return TestClient(app)


@pytest.fixture()
def cancelled_document(db_session: Session):
    """Documento emitido, reimpreso y anulado, con sus tres artifacts reales."""
    org = Organization(
        id=uuid4(),
        code=f"ORG-{uuid4().hex[:6]}",
        name="Org PDF Anulado",
        country_code="PE",
    )
    db_session.add(org)
    db_session.flush()

    branch = Branch(id=uuid4(), organization_id=org.id, code="PDF", name="Lima PDF")
    db_session.add(branch)
    db_session.flush()

    actor = User(
        id=uuid4(),
        email=f"pdf-{uuid4().hex[:8]}@example.com",
        full_name="Operador PDF",
        password_hash="x" * 60,
        role="user",
        is_active=True,
        is_verified=True,
    )
    db_session.add(actor)
    db_session.flush()

    family = db_session.scalars(
        select(DocumentFamilyModel).where(DocumentFamilyModel.code == "PURCHASING")
    ).first()
    if not family:
        family = DocumentFamilyModel(id=uuid4(), code="PURCHASING", name="Compras")
        db_session.add(family)
        db_session.flush()

    doc_type = db_session.scalars(
        select(DocumentTypeModel).where(DocumentTypeModel.code == "PDX")
    ).first()
    if not doc_type:
        doc_type = DocumentTypeModel(
            id=uuid4(),
            code="PDX",
            name="Documento PDF Anulado",
            short_name="PDX",
            family_id=family.id,
            origin_type="INTERNAL",
            owner_module="logistics",
            resource_type="OUTBOUND_ORDER",
            operation_type="OUTBOUND",
            catalog_status="ACTIVE",
        )
        db_session.add(doc_type)
        db_session.flush()

    version = db_session.scalars(
        select(DocumentTypeVersionModel).where(
            DocumentTypeVersionModel.document_type_id == doc_type.id
        )
    ).first()
    if not version:
        version = DocumentTypeVersionModel(
            id=uuid4(),
            document_type_id=doc_type.id,
            version="1.0.0",
            schema_version="1.0.0",
            status="ACTIVE",
            required_fields_schema={},
            allowed_statuses=["DRAFT", "ISSUED", "CANCELLED"],
            permission_policy={},
            template_key="purchasing.purchase_request",
            template_version="1.0.0",
        )
        db_session.add(version)
        db_session.flush()

    db_session.add(
        DocumentSiteCodeModel(
            id=uuid4(),
            organization_id=org.id,
            branch_id=branch.id,
            code="PDF",
            status="ACTIVE",
        )
    )
    db_session.flush()

    series_service = DocumentSeriesService(db_session)
    series = series_service.create_series(
        organization_id=org.id,
        req=DocumentSeriesCreateRequest(
            branch_id=branch.id,
            document_type_code="PDX",
            document_year=2026,
            sequence_start=1,
            sequence_max=9999,
        ),
        actor_id=None,
    )
    series_service.activate_series(series.id, "Activar para tests de PDF")

    lifecycle = DocumentLifecycleService(db_session)
    draft = lifecycle.create_draft(
        organization_id=org.id,
        branch_id=branch.id,
        warehouse_id=None,
        doc_type_code="PDX",
        source_resource_type="OUTBOUND_ORDER",
        source_resource_id=uuid4(),
        source_operation_id=uuid4(),
        title="Documento para anular",
        structured_data={"items": [{"sku": "SKU-1", "qty": 1}]},
        sensitivity="RESTRICTED",
        actor_id=None,
    )
    issued = lifecycle.issue_document(draft.id, f"idem-{uuid4().hex[:8]}", None)
    lifecycle.reprint_document(issued.id, "Copia extraviada", None)
    lifecycle.cancel_document(issued.id, "Error de digitacion", None)
    db_session.commit()

    yield {"org": org, "document": issued, "lifecycle": lifecycle, "actor": actor}

    app.dependency_overrides.clear()


def _artifact(db_session: Session, document_id: UUID, artifact_type: str) -> DocumentArtifactModel:
    artifact = db_session.scalars(
        select(DocumentArtifactModel).where(
            DocumentArtifactModel.document_id == document_id,
            DocumentArtifactModel.artifact_type == artifact_type,
        )
    ).first()
    assert artifact is not None, f"falta el artifact {artifact_type}"
    return artifact


def test_cancelled_document_preview_returns_pdf(
    db_session: Session, cancelled_document
) -> None:
    """El caso que fallaba en UAT: preview de un documento anulado."""
    document = cancelled_document["document"]
    assert document.status == "CANCELLED"
    client = _client(db_session, _make_principal(cancelled_document["org"].id, [PREVIEW], cancelled_document["actor"].id))

    response = client.get(f"{DOCUMENTS_BASE}/{document.id}/preview")

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF-")


def test_cancelled_document_download_serves_cancelled_artifact(
    db_session: Session, cancelled_document
) -> None:
    """La descarga normal de un anulado entrega el CANCELLED_PDF, no el original."""
    document = cancelled_document["document"]
    client = _client(db_session, _make_principal(cancelled_document["org"].id, [DOWNLOAD], cancelled_document["actor"].id))

    response = client.get(f"{DOCUMENTS_BASE}/{document.id}/pdf?original=false")

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF-")

    cancelled = _artifact(db_session, document.id, "CANCELLED_PDF")
    issued = _artifact(db_session, document.id, "ISSUED_PDF")
    served = hashlib.sha256(response.content).hexdigest()
    assert served == cancelled.file_hash
    assert served != issued.file_hash


def test_original_of_cancelled_requires_sensitive_permission(
    db_session: Session, cancelled_document
) -> None:
    """Sin el permiso de auditoria elevado, el original anulado no se entrega."""
    document = cancelled_document["document"]
    client = _client(db_session, _make_principal(cancelled_document["org"].id, [DOWNLOAD], cancelled_document["actor"].id))

    response = client.get(f"{DOCUMENTS_BASE}/{document.id}/pdf?original=true")

    assert response.status_code == 403, response.text


def test_original_of_cancelled_served_with_sensitive_permission(
    db_session: Session, cancelled_document
) -> None:
    """Con el permiso, se entrega el ISSUED_PDF original."""
    document = cancelled_document["document"]
    client = _client(
        db_session, _make_principal(
            cancelled_document["org"].id, [DOWNLOAD, READ_SENSITIVE], cancelled_document["actor"].id
        )
    )

    response = client.get(f"{DOCUMENTS_BASE}/{document.id}/pdf?original=true")

    assert response.status_code == 200, response.text
    issued = _artifact(db_session, document.id, "ISSUED_PDF")
    assert hashlib.sha256(response.content).hexdigest() == issued.file_hash


def test_reprint_artifact_survives(db_session: Session, cancelled_document) -> None:
    """La reimpresion sigue registrada con su propia copia y su propio hash."""
    document = cancelled_document["document"]
    reprint = _artifact(db_session, document.id, "REPRINT_PDF")
    issued = _artifact(db_session, document.id, "ISSUED_PDF")

    assert reprint.copy_number == 1
    assert reprint.is_authoritative is False
    assert reprint.file_hash != issued.file_hash


def test_missing_physical_file_returns_controlled_error_not_500(
    db_session: Session, cancelled_document
) -> None:
    """Fila en base de datos sin fichero: respuesta controlada, no 500 crudo."""
    document = cancelled_document["document"]
    cancelled = _artifact(db_session, document.id, "CANCELLED_PDF")
    cancelled.storage_key = f"documents/inexistente/{uuid4().hex}.pdf"
    db_session.flush()

    client = _client(
        db_session, _make_principal(
            cancelled_document["org"].id, [PREVIEW, DOWNLOAD], cancelled_document["actor"].id
        )
    )

    preview = client.get(f"{DOCUMENTS_BASE}/{document.id}/preview")
    download = client.get(f"{DOCUMENTS_BASE}/{document.id}/pdf?original=false")

    for response in (preview, download):
        # El manejador global normaliza el cuerpo a RESOURCE_NOT_FOUND; lo
        # esencial es que sea una respuesta controlada y no un 500 crudo, y que
        # no se entregue nada que parezca un PDF.
        assert response.status_code == 404, response.text
        assert response.json()["success"] is False
        assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert not response.content.startswith(b"%PDF-")
