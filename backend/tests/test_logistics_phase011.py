"""Unit and integration tests for Phase 011 Document Catalog & Versioning Architecture."""

from __future__ import annotations

import os
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.database.session import SessionLocal, engine
from app.database.base import Base
import app.models.registry  # noqa: F401
import app.modules.logistics.documents.models  # noqa: F401
from app.modules.logistics.documents.catalog.loader import load_catalog_json
from app.modules.logistics.documents.catalog.seeder import seed_document_catalog
from app.modules.logistics.documents.catalog.validator import validate_catalog_data
from app.modules.logistics.documents.repository import DocumentTypeRepository


@pytest.fixture(scope="module")
def app():
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def seed_catalog_db():
    """Seeds the document catalog in the test database."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_document_catalog(db, dry_run=False)
    finally:
        db.close()


def test_catalog_json_structure_and_validation():
    data = load_catalog_json()
    report = validate_catalog_data(data)
    assert report["valid"] is True
    assert report["total_families"] == 13
    assert report["total_document_types"] >= 28
    assert report["total_proposed_types"] == 9


def test_seed_idempotency():
    db = SessionLocal()
    try:
        res1 = seed_document_catalog(db, dry_run=False)
        res2 = seed_document_catalog(db, dry_run=False)
        assert res1["status"] == "SEEDED_SUCCESSFULLY"
        assert res2["status"] == "SEEDED_SUCCESSFULLY"

        repo = DocumentTypeRepository(db)
        req_type = repo.get_by_code("REQ")
        assert req_type is not None
        assert req_type.family.code == "PURCHASING"
    finally:
        db.close()


def test_core_document_families_mapping():
    db = SessionLocal()
    try:
        repo = DocumentTypeRepository(db)

        req = repo.get_by_code("REQ")
        assert req is not None
        assert req.family.code == "PURCHASING"

        ods = repo.get_by_code("ODS")
        assert ods is not None
        assert ods.family.code == "OUTBOUND"

        pod = repo.get_by_code("POD")
        assert pod is not None
        assert pod.family.code == "DELIVERY"

        dev = repo.get_by_code("DEV")
        assert dev is not None
        assert dev.family.code == "REVERSE_LOGISTICS"
    finally:
        db.close()


def test_proposed_codes_not_active():
    data = load_catalog_json()
    active_codes = {dt["code"] for dt in data.get("document_types", [])}
    for pt in data.get("proposed_types", []):
        pcode = pt["code"]
        assert pcode not in active_codes
        assert pt["decision_status"] == "PROPOSED_PHASE_011"


def test_api_openapi_registered(app):
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/document-catalog" in paths
    assert "/api/logistics/document-catalog/families" in paths
    assert "/api/logistics/document-catalog/types" in paths
    assert "/api/logistics/document-catalog/types/{document_type_code}" in paths


def test_api_unauthenticated_returns_401(client: TestClient):
    assert client.get("/api/logistics/document-catalog").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.get("/api/logistics/document-catalog/families").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.get("/api/logistics/document-catalog/types").status_code == status.HTTP_401_UNAUTHORIZED
