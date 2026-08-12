"""Unit, integration, and concurrency tests for Phase 013 Document Series & Talonarios."""

from __future__ import annotations

import os
import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.database.session import SessionLocal, engine
from app.database.base import Base
import app.models.registry  # noqa: F401
from app.models.organization import Organization
from app.models.branch import Branch
import app.modules.logistics.documents.models  # noqa: F401
from app.modules.logistics.documents.codes.code_models import DocumentSiteCodeModel
import app.modules.logistics.documents.series.series_models  # noqa: F401
from app.modules.logistics.documents.catalog.seeder import seed_document_catalog
from app.modules.logistics.documents.series.series_service import DocumentSeriesService
from app.modules.logistics.documents.series.series_schemas import (
    DocumentSeriesCreateRequest,
    DocumentTalonarioCreateRequest,
)


@pytest.fixture(scope="module")
def app():
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Creates database tables and seeds catalog for testing."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_document_catalog(db, dry_run=False)
    finally:
        db.close()


def _get_fresh_test_context(db):
    """Creates a fresh, isolated Organization, Branch, and DocumentSiteCode per test."""
    uid = uuid.uuid4().hex[:8]
    org = Organization(
        code=f"ORG_P13_{uid}",
        name=f"Organización Pruebas {uid}",
        country_code="PE",
        timezone="America/Lima",
    )
    db.add(org)
    db.flush()

    branch = Branch(
        organization_id=org.id,
        code=f"BRANCH_{uid}",
        name=f"Sede Pruebas {uid}",
    )
    db.add(branch)
    db.flush()

    site_code = DocumentSiteCodeModel(
        organization_id=org.id,
        branch_id=branch.id,
        code="LIM",
        is_primary=True,
        status="ACTIVE",
    )
    db.add(site_code)
    db.flush()
    db.commit()

    return org.id, branch.id


def test_create_and_activate_series():
    db = SessionLocal()
    try:
        org_id, branch_id = _get_fresh_test_context(db)
        srv = DocumentSeriesService(db)

        req = DocumentSeriesCreateRequest(
            branch_id=branch_id,
            document_type_code="OC",
            document_year=2026,
            sequence_start=1,
            sequence_max=999999,
        )
        series_resp = srv.create_series(org_id, req)
        assert series_resp.prefix == "OC-LIM-2026"
        assert series_resp.status == "DRAFT"
        assert series_resp.next_sequence == 1

        active_resp = srv.activate_series(series_resp.id, reason="Apertura operativa")
        assert active_resp.status == "ACTIVE"
    finally:
        db.close()


def test_individual_number_reservation_sequence():
    db = SessionLocal()
    try:
        org_id, branch_id = _get_fresh_test_context(db)
        srv = DocumentSeriesService(db)

        series = srv.create_series(
            org_id,
            DocumentSeriesCreateRequest(
                branch_id=branch_id,
                document_type_code="REQ",
                document_year=2026,
            ),
        )
        srv.activate_series(series.id, reason="Activar REQ")

        n1 = srv.reserve_next_number(series.id, purpose="Emisión 1")
        assert n1.sequence_number == 1
        assert n1.full_document_code == "REQ-LIM-2026-000001"

        n2 = srv.reserve_next_number(series.id, purpose="Emisión 2")
        assert n2.sequence_number == 2
        assert n2.full_document_code == "REQ-LIM-2026-000002"
    finally:
        db.close()


def test_talonario_range_reservation_and_cancellation():
    db = SessionLocal()
    try:
        org_id, branch_id = _get_fresh_test_context(db)
        srv = DocumentSeriesService(db)

        series = srv.create_series(
            org_id,
            DocumentSeriesCreateRequest(
                branch_id=branch_id,
                document_type_code="NI",
                document_year=2026,
            ),
        )
        srv.activate_series(series.id, reason="Activar NI")

        tal_req = DocumentTalonarioCreateRequest(quantity=10, purpose="Talonario recepción almacén")
        tal_resp = srv.reserve_number_range(series.id, tal_req)

        assert tal_resp.range_start == 1
        assert tal_resp.range_end == 10
        assert tal_resp.total_numbers == 10
        assert tal_resp.talonario_code == "TAL-NI-LIM-2026-000001-000010"

        # Cancel talonario -> Numbers must be VOIDED, available = 0
        cancelled_tal = srv.cancel_talonario(tal_resp.id, reason="Perdida de talonario físico")
        assert cancelled_tal.status == "CANCELLED"
        assert cancelled_tal.voided_numbers == 10
        assert cancelled_tal.available_numbers == 0

        # Next individual reservation must continue from sequence 11 (NO sequence recycling!)
        n11 = srv.reserve_next_number(series.id, purpose="Post-talonario cancelado")
        assert n11.sequence_number == 11
        assert n11.full_document_code == "NI-LIM-2026-000011"
    finally:
        db.close()


def test_talonario_manifest_generation():
    db = SessionLocal()
    try:
        org_id, branch_id = _get_fresh_test_context(db)
        srv = DocumentSeriesService(db)

        series = srv.create_series(
            org_id,
            DocumentSeriesCreateRequest(
                branch_id=branch_id,
                document_type_code="POD",
                document_year=2026,
            ),
        )
        srv.activate_series(series.id, reason="Activar POD")

        tal_resp = srv.reserve_number_range(
            series.id, DocumentTalonarioCreateRequest(quantity=5, purpose="Manifest Test")
        )
        manifest = srv.generate_manifest(tal_resp.id)

        assert manifest.manifest_version == "1.0.0"
        assert manifest.total_numbers == 5
        assert len(manifest.numbers) == 5
        assert manifest.rendering_status == "PENDING_RENDERER_PHASE_014"
    finally:
        db.close()


def test_api_openapi_registered(app):
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/document-series" in paths
    assert "/api/logistics/document-series/{series_id}" in paths
    assert "/api/logistics/document-series/{series_id}/activate" in paths
    assert "/api/logistics/document-series/{series_id}/talonarios" in paths
    assert "/api/logistics/document-talonarios/{talonario_id}" in paths
    assert "/api/logistics/document-talonarios/{talonario_id}/manifest" in paths


def test_api_unauthenticated_returns_401(client: TestClient):
    assert client.get("/api/logistics/document-series").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.get(f"/api/logistics/document-series/{uuid.uuid4()}").status_code == status.HTTP_401_UNAUTHORIZED
