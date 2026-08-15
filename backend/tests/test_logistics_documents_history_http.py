"""Regresion HTTP del historial de documentos (Fase 020).

El endpoint `GET /api/logistics/documents/{id}/history` comparaba
`principal.organization_id`, atributo que `LogisticsPrincipal` no tiene: el
AttributeError salia como 500 fuera del middleware CORS y el navegador lo
reportaba como un fallo de CORS.

Los tests existentes no lo detectaron porque ejercitaban
`DocumentLifecycleService.get_history()` directamente, sin pasar por el router.
Estos van por HTTP a proposito y NO mockean el servicio: el fallo estaba en la
comprobacion de tenant del router, no en la consulta.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.session import SessionLocal, engine, get_db
from app.main import app
from app.models.branch import Branch
from app.models.organization import Organization
from app.models.user import User
from app.modules.logistics.audit.models_event import LogisticsAuditEvent
from app.modules.logistics.auth_dependencies import get_logistics_principal
from app.modules.logistics.documents.application.lifecycle_service import (
    DocumentLifecycleService,
)
from app.modules.logistics.documents.models import (
    DocumentFamilyModel,
    DocumentTypeModel,
    DocumentTypeVersionModel,
)
from app.modules.logistics.principal import LogisticsPrincipal

pytestmark = [pytest.mark.http, pytest.mark.security]

DOCUMENTS_BASE = "/api/logistics/documents"
FRONTEND_ORIGIN = "http://localhost:5173"


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


def _make_principal(org_ids: list[UUID], user_id: UUID) -> LogisticsPrincipal:
    return LogisticsPrincipal(
        user_id=user_id,
        email="documents_history@example.com",
        full_name="Auditor Documental",
        platform_role="user",
        is_active=True,
        session_id=uuid4(),
        device_id=None,
        authentication_level="normal",
        session_expires_at=datetime.now(UTC),
        risk_score=0.1,
        logistics_enabled=True,
        role_codes=["DOCUMENT_AUDITOR"],
        permission_codes=["logistics.documents.read"],
        organization_ids=[str(o) for o in org_ids],
        default_organization_id=str(org_ids[0]) if org_ids else None,
    )


def _client(session: Session, principal: LogisticsPrincipal) -> TestClient:
    def override_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_logistics_principal] = lambda: principal
    return TestClient(app)


@pytest.fixture()
def document_context(db_session: Session):
    """Organizacion, sede, tipo documental, usuario y borrador reales."""
    org = Organization(
        id=uuid4(),
        code=f"ORG-{uuid4().hex[:6]}",
        name="Org Historial Documental",
        country_code="PE",
    )
    db_session.add(org)
    db_session.flush()

    branch = Branch(id=uuid4(), organization_id=org.id, code="LIM", name="Lima")
    db_session.add(branch)
    db_session.flush()

    family = db_session.query(DocumentFamilyModel).filter_by(code="PURCHASING").first()
    if not family:
        family = DocumentFamilyModel(id=uuid4(), code="PURCHASING", name="Compras")
        db_session.add(family)
        db_session.flush()

    doc_type = db_session.query(DocumentTypeModel).filter_by(code="HIST").first()
    if not doc_type:
        doc_type = DocumentTypeModel(
            id=uuid4(),
            code="HIST",
            name="Documento de Historial",
            short_name="HIST",
            family_id=family.id,
            origin_type="INTERNAL",
            owner_module="logistics",
            resource_type="OUTBOUND_ORDER",
            operation_type="OUTBOUND",
            catalog_status="ACTIVE",
        )
        db_session.add(doc_type)
        db_session.flush()

    version = (
        db_session.query(DocumentTypeVersionModel)
        .filter_by(document_type_id=doc_type.id)
        .first()
    )
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

    actor = User(
        id=uuid4(),
        email=f"auditor-{uuid4().hex[:8]}@example.com",
        full_name="Auditor Documental",
        password_hash="x" * 60,
        role="user",
        is_active=True,
        is_verified=True,
    )
    db_session.add(actor)
    db_session.flush()

    draft = DocumentLifecycleService(db_session).create_draft(
        organization_id=org.id,
        branch_id=branch.id,
        warehouse_id=None,
        doc_type_code="HIST",
        source_resource_type="OUTBOUND_ORDER",
        source_resource_id=uuid4(),
        source_operation_id=uuid4(),
        title="Documento con historial",
        structured_data={"items": []},
        sensitivity="RESTRICTED",
        actor_id=actor.id,
    )
    db_session.commit()

    yield {"org": org, "branch": branch, "actor": actor, "document": draft}

    app.dependency_overrides.clear()


def _add_event(
    db_session: Session,
    document_id: UUID,
    *,
    actor_user_id: UUID | None,
    actor_snapshot: str | None,
    reason: str | None = None,
    metadata: dict | None = None,
) -> None:
    db_session.add(
        LogisticsAuditEvent(
            id=uuid4(),
            event_code="logistics.document.issued",
            event_category="logistics",
            actor_user_id=actor_user_id,
            actor_display_name_snapshot=actor_snapshot,
            occurred_at=datetime.now(UTC),
            resource_type="document_instance",
            resource_id=str(document_id),
            reason_text=reason,
            metadata_=metadata,
        )
    )
    db_session.commit()


def test_history_returns_events_for_authorized_organization(
    db_session: Session, document_context
) -> None:
    """El caso que reventaba en UAT: documento de la organizacion del principal."""
    document = document_context["document"]
    actor = document_context["actor"]
    _add_event(
        db_session,
        document.id,
        actor_user_id=actor.id,
        actor_snapshot=None,
        reason="Emision inicial",
        metadata={"copias": 1},
    )

    principal = _make_principal([document_context["org"].id], actor.id)
    client = _client(db_session, principal)

    response = client.get(f"{DOCUMENTS_BASE}/{document.id}/history")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["document_id"] == str(document.id)
    # `create_draft` ya deja su propio evento, asi que la emision es la segunda.
    assert [e["event_type"] for e in body["history"]] == [
        "logistics.document.draft_created",
        "logistics.document.issued",
    ]
    entry = body["history"][1]
    assert entry["event_type"] == "logistics.document.issued"
    assert entry["actor_user_id"] == str(actor.id)
    # Sin snapshot de nombre, se resuelve contra el usuario real.
    assert entry["actor_name"] == "Auditor Documental"
    assert entry["reason"] == "Emision inicial"
    assert entry["details"] == {"copias": 1}
    assert entry["timestamp"]


def test_history_without_events_returns_empty_list(
    db_session: Session, document_context
) -> None:
    """Un documento sin eventos responde 200 con lista vacia, no 500."""
    document = document_context["document"]
    db_session.query(LogisticsAuditEvent).filter_by(
        resource_type="document_instance", resource_id=str(document.id)
    ).delete()
    db_session.commit()

    principal = _make_principal(
        [document_context["org"].id], document_context["actor"].id
    )
    client = _client(db_session, principal)

    response = client.get(f"{DOCUMENTS_BASE}/{document.id}/history")

    assert response.status_code == 200, response.text
    assert response.json() == {"document_id": str(document.id), "history": []}


def test_history_tolerates_missing_actor(
    db_session: Session, document_context
) -> None:
    """Un actor nulo o borrado no debe convertir el historial en un 500."""
    document = document_context["document"]
    actor = document_context["actor"]
    org_id = document_context["org"].id
    _add_event(db_session, document.id, actor_user_id=None, actor_snapshot=None)
    _add_event(
        db_session, document.id, actor_user_id=actor.id, actor_snapshot="Nombre Congelado"
    )

    # Al borrar al usuario, la FK ON DELETE SET NULL deja el actor sin id: es el
    # escenario real de "usuario eliminado", no un id colgante.
    db_session.delete(actor)
    db_session.commit()

    principal = _make_principal([org_id], uuid4())
    client = _client(db_session, principal)

    response = client.get(f"{DOCUMENTS_BASE}/{document.id}/history")

    assert response.status_code == 200, response.text
    names = [entry["actor_name"] for entry in response.json()["history"]]
    # El evento con snapshot conserva el nombre; los demas quedan sin actor.
    assert "Nombre Congelado" in names
    assert all(name in (None, "Nombre Congelado") for name in names)


def test_history_rejects_other_organization_with_403(
    db_session: Session, document_context
) -> None:
    """El aislamiento por tenant sigue devolviendo 403, no 500 ni datos."""
    document = document_context["document"]
    principal = _make_principal([uuid4()], document_context["actor"].id)
    client = _client(db_session, principal)

    response = client.get(f"{DOCUMENTS_BASE}/{document.id}/history")

    assert response.status_code == 403, response.text
    assert "history" not in response.json()


def test_history_response_carries_cors_headers(
    db_session: Session, document_context
) -> None:
    """Sin cabecera CORS la respuesta no llega al navegador y parece fallo de CORS."""
    document = document_context["document"]
    principal = _make_principal(
        [document_context["org"].id], document_context["actor"].id
    )
    client = _client(db_session, principal)

    response = client.get(
        f"{DOCUMENTS_BASE}/{document.id}/history",
        headers={"Origin": FRONTEND_ORIGIN},
    )

    assert response.status_code == 200, response.text
    assert response.headers.get("access-control-allow-origin") == FRONTEND_ORIGIN
    assert response.headers.get("access-control-allow-credentials") == "true"
