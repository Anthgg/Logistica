"""Regresion HTTP del listado de documentos (Fase 020).

`GET /api/logistics/documents` devolvia 500 con:

    AttributeError: 'LogisticsPrincipal' object has no attribute 'role'

al calcular `can_cancel` / `can_reprint`. `LogisticsPrincipal` publica
`platform_role`, `role_codes` y `permission_codes`, y resuelve los permisos con
`has_permission()`, que ya concede el bypass de platform admin.

Los principals de estos tests se construyen con el contrato REAL. Fabricar un
doble con `role` y `permissions` volveria a esconder exactamente este fallo.
"""

from __future__ import annotations

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
from app.modules.logistics.auth_dependencies import get_logistics_principal
from app.modules.logistics.documents.application.lifecycle_service import (
    DocumentLifecycleService,
)
from app.modules.logistics.documents.codes.code_models import DocumentSiteCodeModel
from app.modules.logistics.documents.models import (
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
READ = "logistics.documents.read"
CANCEL = "logistics.documents.cancel"
REPRINT = "logistics.documents.reprint"


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


def _make_principal(
    org_id: UUID,
    permissions: list[str],
    *,
    is_admin: bool = False,
) -> LogisticsPrincipal:
    """Principal con el contrato real: nada de `role` ni `permissions`."""
    return LogisticsPrincipal(
        user_id=uuid4(),
        email="documents_list@example.com",
        full_name="Operador Documental",
        platform_role="admin" if is_admin else "user",
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
def issued_document(db_session: Session):
    """Organizacion, serie activa y un documento realmente EMITIDO."""
    org = Organization(
        id=uuid4(),
        code=f"ORG-{uuid4().hex[:6]}",
        name="Org Listado Documental",
        country_code="PE",
    )
    db_session.add(org)
    db_session.flush()

    branch = Branch(id=uuid4(), organization_id=org.id, code="LIS", name="Lima Listado")
    db_session.add(branch)
    db_session.flush()

    family = db_session.scalars(
        select(DocumentFamilyModel).where(DocumentFamilyModel.code == "PURCHASING")
    ).first()
    if not family:
        family = DocumentFamilyModel(id=uuid4(), code="PURCHASING", name="Compras")
        db_session.add(family)
        db_session.flush()

    doc_type = db_session.scalars(
        select(DocumentTypeModel).where(DocumentTypeModel.code == "LST")
    ).first()
    if not doc_type:
        doc_type = DocumentTypeModel(
            id=uuid4(),
            code="LST",
            name="Documento de Listado",
            short_name="LST",
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
            code="LIS",
            status="ACTIVE",
        )
    )
    db_session.flush()

    series_service = DocumentSeriesService(db_session)
    series = series_service.create_series(
        organization_id=org.id,
        req=DocumentSeriesCreateRequest(
            branch_id=branch.id,
            document_type_code="LST",
            document_year=2026,
            sequence_start=1,
            sequence_max=9999,
        ),
        actor_id=None,
    )
    series_service.activate_series(series.id, "Activar para tests de listado")

    lifecycle = DocumentLifecycleService(db_session)
    draft = lifecycle.create_draft(
        organization_id=org.id,
        branch_id=branch.id,
        warehouse_id=None,
        doc_type_code="LST",
        source_resource_type="OUTBOUND_ORDER",
        source_resource_id=uuid4(),
        source_operation_id=uuid4(),
        title="Documento listado",
        structured_data={"items": []},
        sensitivity="RESTRICTED",
        actor_id=None,
    )
    issued = lifecycle.issue_document(draft.id, f"idem-{uuid4().hex[:8]}", None)
    db_session.commit()

    yield {"org": org, "branch": branch, "document": issued, "lifecycle": lifecycle}

    app.dependency_overrides.clear()


def _fetch_row(client: TestClient, document_id: UUID) -> dict:
    response = client.get(f"{DOCUMENTS_BASE}?page=1&page_size=20")
    assert response.status_code == 200, response.text
    rows = [row for row in response.json()["items"] if row["id"] == str(document_id)]
    assert rows, "el documento emitido deberia aparecer en el listado"
    return rows[0]


def test_list_without_action_permissions_returns_200_and_denies_actions(
    db_session: Session, issued_document
) -> None:
    """El caso que reventaba en UAT: solo lectura, sin cancel ni reprint."""
    document = issued_document["document"]
    client = _client(db_session, _make_principal(issued_document["org"].id, [READ]))

    row = _fetch_row(client, document.id)

    assert row["status"] == "ISSUED"
    assert row["can_cancel"] is False
    assert row["can_reprint"] is False


def test_list_grants_cancel_with_permission(
    db_session: Session, issued_document
) -> None:
    document = issued_document["document"]
    client = _client(db_session, _make_principal(issued_document["org"].id, [READ, CANCEL]))

    row = _fetch_row(client, document.id)

    assert row["can_cancel"] is True
    assert row["can_reprint"] is False


def test_list_grants_reprint_with_permission(
    db_session: Session, issued_document
) -> None:
    document = issued_document["document"]
    client = _client(db_session, _make_principal(issued_document["org"].id, [READ, REPRINT]))

    row = _fetch_row(client, document.id)

    assert row["can_reprint"] is True
    assert row["can_cancel"] is False


def test_list_platform_admin_without_permissions_is_denied(
    db_session: Session, issued_document
) -> None:
    """El bypass de platform admin se retiró en F006.

    Este caso comprobaba lo contrario: que un administrador de plataforma sin
    permisos explícitos recibiera igualmente las acciones, porque `has_permission`
    devolvía True para él. Esa excepción concedía además alcance de tenant y
    saltaba el step-up, así que se retiró entera y el caso se invierte con ella.
    """
    client = _client(
        db_session, _make_principal(issued_document["org"].id, [], is_admin=True)
    )

    response = client.get("/api/logistics/documents/")

    assert response.status_code == 403


def test_list_cancelled_document_denies_cancel_but_allows_reprint(
    db_session: Session, issued_document
) -> None:
    """Un documento anulado ya no se puede anular; reimprimir sigue permitido."""
    document = issued_document["document"]
    issued_document["lifecycle"].cancel_document(
        document.id, "Anulado para prueba de listado", None
    )
    db_session.commit()

    client = _client(
        db_session, _make_principal(issued_document["org"].id, [READ, CANCEL, REPRINT])
    )

    row = _fetch_row(client, document.id)

    assert row["status"] == "CANCELLED"
    assert row["can_cancel"] is False
    assert row["can_reprint"] is True
