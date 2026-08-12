"""Unit, integration, and security tests for Phase 020 Document Lifecycle.

Covers: drafts, issuance, previews, prints, reprints, cancellations, ZIP exports, talonarios, security, and performance.
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select, text, and_, or_
from sqlalchemy.orm import Session

from app.database.session import SessionLocal, engine
from app.database.base import Base
from app.models.organization import Organization
from app.models.branch import Branch
from app.models.warehouse import Warehouse
from app.modules.logistics.documents.models import (
    DocumentFamilyModel,
    DocumentTypeModel,
    DocumentTypeVersionModel,
    DocumentInstanceModel,
    DocumentSnapshotModel,
    DocumentArtifactModel,
    DocumentReprintModel,
    DocumentCancellationModel,
    DocumentExportJobModel,
)
from app.modules.logistics.documents.series.series_models import (
    DocumentSeriesModel,
    DocumentNumberModel,
    IdempotencyRecordModel,
)
from app.modules.logistics.documents.series.series_service import DocumentSeriesService
from app.modules.logistics.documents.series.series_schemas import DocumentSeriesCreateRequest
from app.modules.logistics.documents.application.lifecycle_service import (
    DocumentLifecycleService,
    stable_json_hash,
)
from app.modules.logistics.documents.application.export_service import DocumentExportService
from app.modules.logistics.security.step_up_service import step_up_service
from app.modules.logistics.principal import LogisticsPrincipal
from tests.support import authenticate


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


@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def seed_test_data(db_session):
    """Seeds organizations, branches, document types and series for Phase 020 tests."""
    # 1. Create organization and branch
    org = Organization(
        id=uuid4(),
        code=f"ORG-{uuid4().hex[:6]}",
        name="Org Test Phase 020",
        country_code="PE",
    )
    db_session.add(org)
    db_session.flush()

    br = Branch(
        id=uuid4(),
        organization_id=org.id,
        code="LIM",
        name="Lima Principal",
    )
    db_session.add(br)
    db_session.flush()

    # 2. Add document family and type
    fam = db_session.scalars(
        select(DocumentFamilyModel).where(DocumentFamilyModel.code == "PURCHASING")
    ).first()
    if not fam:
        fam = DocumentFamilyModel(
            id=uuid4(),
            code="PURCHASING",
            name="Compras",
        )
        db_session.add(fam)
        db_session.flush()

    dt = db_session.scalars(
        select(DocumentTypeModel).where(DocumentTypeModel.code == "PED")
    ).first()
    if not dt:
        dt = DocumentTypeModel(
            id=uuid4(),
            code="PED",
            name="Pedido de Salida",
            short_name="PED",
            family_id=fam.id,
            origin_type="INTERNAL",
            owner_module="logistics",
            resource_type="OUTBOUND_ORDER",
            operation_type="OUTBOUND",
            catalog_status="ACTIVE",
        )
        db_session.add(dt)
        db_session.flush()

    # Create active version for type
    dt_ver = db_session.scalars(
        select(DocumentTypeVersionModel).where(DocumentTypeVersionModel.document_type_id == dt.id)
    ).first()
    if not dt_ver:
        dt_ver = DocumentTypeVersionModel(
            id=uuid4(),
            document_type_id=dt.id,
            version="1.0.0",
            schema_version="1.0.0",
            status="ACTIVE",
            required_fields_schema={},
            allowed_statuses=["DRAFT", "ISSUED", "CANCELLED"],
            permission_policy={},
            template_key="purchasing.purchase_request",
            template_version="1.0.0",
        )
        db_session.add(dt_ver)
        db_session.flush()

    # Define site codes
    from app.modules.logistics.documents.codes.code_models import DocumentSiteCodeModel
    site = db_session.scalars(
        select(DocumentSiteCodeModel)
        .where(
            and_(
                DocumentSiteCodeModel.organization_id == org.id,
                DocumentSiteCodeModel.branch_id == br.id,
                DocumentSiteCodeModel.code == "LIM"
            )
        )
    ).first()
    if not site:
        site = DocumentSiteCodeModel(
            id=uuid4(),
            organization_id=org.id,
            branch_id=br.id,
            code="LIM",
            status="ACTIVE",
        )
        db_session.add(site)
        db_session.flush()

    # Create document series
    ser_srv = DocumentSeriesService(db_session)
    series_resp = ser_srv.create_series(
        organization_id=org.id,
        req=DocumentSeriesCreateRequest(
            branch_id=br.id,
            document_type_code="PED",
            document_year=2026,
            sequence_start=1,
            sequence_max=9999,
        ),
        actor_id=None,
    )
    ser_srv.activate_series(series_resp.id, "Activar para tests")
    
    db_session.commit()

    return {
        "org_id": org.id,
        "branch_id": br.id,
        "dt_code": "PED",
        "series_id": series_resp.id,
    }


class TestDocumentSnapshot:
    def test_canonical_hash_stability(self):
        """Check stable_json_hash generates same hash regardless of dict key sorting order."""
        payload1 = {"b": 2, "a": 1, "c": {"z": 10, "y": 9}}
        payload2 = {"a": 1, "b": 2, "c": {"y": 9, "z": 10}}
        
        ser1, hash1 = stable_json_hash(payload1)
        ser2, hash2 = stable_json_hash(payload2)
        
        assert hash1 == hash2
        assert ser1 == ser2

    def test_stable_serialization_supports_types(self):
        """Check decimal, datetime and UUID are serialized safely without raising TypeError."""
        payload = {
            "dec": Decimal("10.50"),
            "dt": datetime(2026, 7, 26, 12, 0, 0, tzinfo=timezone.utc),
            "uid": uuid4(),
        }
        serialized, hash_val = stable_json_hash(payload)
        assert isinstance(serialized, str)
        assert len(hash_val) == 64


class TestDocumentLifecycle:
    def test_draft_emission_preview_reprint_cancel_flow(self, db_session, seed_test_data):
        """Covers draft creation, preview, emission, download, reprint, print intent, and cancel."""
        life_srv = DocumentLifecycleService(db_session)
        org_id = seed_test_data["org_id"]
        br_id = seed_test_data["branch_id"]

        # 1. Create draft
        draft = life_srv.create_draft(
            organization_id=org_id,
            branch_id=br_id,
            warehouse_id=None,
            doc_type_code="PED",
            source_resource_type="OUTBOUND_ORDER",
            source_resource_id=uuid4(),
            source_operation_id=uuid4(),
            title="Pedido de Salida de Pruebas",
            structured_data={"items": [{"sku": "SKU-1", "qty": 5}]},
            sensitivity="RESTRICTED",
            actor_id=None,
        )
        db_session.commit()
        assert draft.status == "DRAFT"
        assert draft.document_code is None

        # 2. Preview draft
        preview_pdf, preview_name = life_srv.preview_document(draft.id, None)
        assert len(preview_pdf) > 0
        assert "PREVIEW" in preview_name

        # 3. Emit document
        issued = life_srv.issue_document(draft.id, "idem-key-1", None)
        db_session.commit()
        assert issued.status == "ISSUED"
        assert issued.document_code == "PED-LIM-2026-000001"
        assert issued.authoritative_artifact_id is not None

        # Idempotency check: issuing same doc with same idem key should succeed
        re_issued = life_srv.issue_document(draft.id, "idem-key-1", None)
        assert re_issued.id == issued.id

        # 4. Print Intent
        life_srv.register_print_intent(issued.id, None, reason="Copia interna", client_context={"ip": "127.0.0.1"})
        db_session.commit()
        assert issued.print_request_count == 1

        # 5. Reprint Document
        rep = life_srv.reprint_document(issued.id, "Pérdida del original", None)
        db_session.commit()
        assert rep.copy_number == 1
        assert rep.reason == "Pérdida del original"

        # Check inmutability: snapshot version remains 1
        snap = db_session.get(DocumentSnapshotModel, issued.current_snapshot_id)
        assert snap.snapshot_version == 1

        # 6. Cancel/Annull Document
        cxl = life_srv.cancel_document(issued.id, "Error de digitación", None)
        db_session.commit()
        assert issued.status == "CANCELLED"
        assert cxl.reason == "Error de digitación"

        # Correlative number remains occupied
        num = db_session.get(DocumentNumberModel, issued.document_number_id)
        assert num.status == "CANCELLED"

        # Downgrade check
        history = life_srv.get_history(issued.id)
        assert len(history) > 0


class TestTalonariosAndZip:
    def test_talonario_rendering_and_zip_export(self, db_session, seed_test_data):
        """Tests generating a WeasyPrint talonario PDF and exporting it to ZIP."""
        ser_srv = DocumentSeriesService(db_session)
        series_id = seed_test_data["series_id"]
        org_id = seed_test_data["org_id"]

        # Reserve a range
        from app.modules.logistics.documents.series.series_schemas import DocumentTalonarioCreateRequest
        tal_resp = ser_srv.reserve_number_range(
            series_id=series_id,
            req=DocumentTalonarioCreateRequest(
                quantity=5,
                purpose="Talonario de contingencia",
                idempotency_key="idem-tal-1",
            ),
            actor_id=None,
        )

        exp_srv = DocumentExportService(db_session)
        pdf_bytes, filename = exp_srv.generate_talonario_pdf(tal_resp.id, None)
        assert len(pdf_bytes) > 0
        assert "TALONARIO" in filename

        # Numbers stay RESERVED, not ISSUED
        num = db_session.scalars(
            select(DocumentNumberModel).where(DocumentNumberModel.talonario_id == tal_resp.id)
        ).first()
        assert num.status == "RESERVED"

        # Export talonario ZIP
        zip_bytes, zip_filename = exp_srv.export_talonario_zip(tal_resp.id, None)
        assert len(zip_bytes) > 0
        assert zip_filename.endswith(".zip")


class TestSecurityGating:
    def test_api_unauthenticated_returns_401(self, client):
        response = client.get("/api/logistics/documents")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cross_org_access_denied(self, client, db_session, seed_test_data):
        """Verify user of organization A cannot access or cancel document of organization B."""
        # Create user for Organization B
        org_b = Organization(
            id=uuid4(),
            code=f"ORG-{uuid4().hex[:6]}",
            name="Org B",
            country_code="PE",
        )
        db_session.add(org_b)
        db_session.flush()
        db_session.commit()

        # Login as user from Org B
        identifier = uuid4().hex
        from app.models.user import User
        from app.models.device import Device
        from app.services.session_service import SessionService
        from app.modules.logistics.rbac.models_role import LogisticsRole
        from app.modules.logistics.rbac.models_permission import LogisticsPermission
        from app.modules.logistics.rbac.models_role_permission import LogisticsRolePermission
        from app.modules.logistics.rbac.models_assignment import LogisticsRoleAssignment

        user_b = User(
            email=f"user-b-{identifier}@example.test",
            password_hash="hash-ficticio-no-utilizable",
            full_name="User B",
            role="user",
            is_active=True,
        )
        db_session.add(user_b)
        db_session.flush()

        role = db_session.scalars(select(LogisticsRole).where(LogisticsRole.code == "operator")).first()
        if not role:
            role = LogisticsRole(id=uuid4(), code="operator", name="Operator", description="Operator role")
            db_session.add(role)
            db_session.flush()

        perm = db_session.scalars(select(LogisticsPermission).where(LogisticsPermission.code == "logistics.documents.read")).first()
        if not perm:
            perm = LogisticsPermission(
                id=uuid4(),
                code="logistics.documents.read",
                resource="documents",
                action="read",
                name="Read docs",
                description="Read documents",
                category="Logistics"
            )
            db_session.add(perm)
            db_session.flush()

        rp = db_session.scalars(
            select(LogisticsRolePermission)
            .where(
                and_(
                    LogisticsRolePermission.role_id == role.id,
                    LogisticsRolePermission.permission_id == perm.id
                )
            )
        ).first()
        if not rp:
            rp = LogisticsRolePermission(role_id=role.id, permission_id=perm.id)
            db_session.add(rp)
            db_session.flush()

        assign = LogisticsRoleAssignment(
            user_id=user_b.id,
            role_id=role.id,
            scope_type="ORGANIZATION",
            organization_id=org_b.id,
            status="active",
        )
        db_session.add(assign)
        db_session.flush()

        # Update user's default org/branch assignments or profile scope if necessary,
        # but User session binds org via user_session
        device = Device(user_id=user_b.id, device_identifier=f"device-{identifier}", browser="pytest")
        db_session.add(device)
        db_session.flush()

        from app.models.session import UserSession
        from app.core.config import settings
        from app.core.security import create_access_token, hash_session_token
        from datetime import timedelta
        
        session_id = uuid4()
        session_token = create_access_token(user_b.id, session_id)
        
        session = UserSession(
            id=session_id,
            user_id=user_b.id,
            device_id=device.id,
            token_hash=hash_session_token(session_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            ip_address="127.0.0.1",
            user_agent="pytest",
        )
        db_session.add(session)
        db_session.commit()

        client.cookies.set(settings.SESSION_COOKIE_NAME, session_token)
        csrf = "csrf-token-val"
        client.cookies.set(settings.CSRF_COOKIE_NAME, csrf)

        # Try to view a document draft of Org A
        life_srv = DocumentLifecycleService(db_session)
        org_a_id = seed_test_data["org_id"]
        draft_a = life_srv.create_draft(
            organization_id=org_a_id,
            branch_id=seed_test_data["branch_id"],
            warehouse_id=None,
            doc_type_code="PED",
            source_resource_type="OUTBOUND_ORDER",
            source_resource_id=uuid4(),
            source_operation_id=uuid4(),
            title="Draft Org A",
            structured_data={},
            sensitivity="RESTRICTED",
            actor_id=None,
        )
        db_session.commit()

        # Try GET from Client
        response = client.get(
            f"/api/logistics/documents/{draft_a.id}",
            headers={"X-CSRF-Token": csrf}
        )
        # Should raise 403 forbidden or 404
        assert response.status_code in (403, 404)
