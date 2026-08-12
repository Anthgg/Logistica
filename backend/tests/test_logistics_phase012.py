"""Unit and integration tests for Phase 012 Document Coding Standard (TIPO-SEDE-AÑO-CORRELATIVO)."""

from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.database.session import SessionLocal, engine
from app.database.base import Base
import app.models.registry  # noqa: F401
import app.modules.logistics.documents.models  # noqa: F401
import app.modules.logistics.documents.codes.code_models  # noqa: F401
from app.modules.logistics.documents.codes.domain import (
    DocumentCodeFormatter,
    DocumentCodeNormalizer,
    DocumentCodeParser,
    DocumentCodeValidationError,
    DocumentCodeValidator,
    YearResolverService,
)
from app.modules.logistics.documents.codes.code_service import DocumentCodeStandardService


@pytest.fixture(scope="module")
def app():
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Creates database tables in the test environment."""
    Base.metadata.create_all(bind=engine)


# --- Unit Tests for Domain Objects & Pattern ---

def test_canonical_code_formatting():
    code = DocumentCodeFormatter.format(
        document_type_code="OC",
        site_code="LIM",
        year=2026,
        sequence=1,
    )
    assert code == "OC-LIM-2026-000001"


def test_canonical_code_parsing_and_parts():
    parts = DocumentCodeParser.parse("OC-LIM-2026-000001", strict=True)
    assert parts.document_type_code == "OC"
    assert parts.site_code == "LIM"
    assert parts.year == 2026
    assert parts.sequence == 1


def test_invalid_codes_rejected():
    with pytest.raises(DocumentCodeValidationError):
        DocumentCodeParser.parse("OC-LIM-2026-000000")  # Correlative zero is invalid

    with pytest.raises(DocumentCodeValidationError):
        DocumentCodeParser.parse("OC-LIM-26-000001")  # 2-digit year is invalid

    with pytest.raises(DocumentCodeValidationError):
        DocumentCodeParser.parse("oc-lim-2026-000001")  # Minúsculas rechazadas en parser estricto


def test_code_normalizer():
    normalized = DocumentCodeNormalizer.normalize("oc-lim-2026-1")
    assert normalized == "OC-LIM-2026-000001"


def test_structural_validator():
    res = DocumentCodeValidator.validate_structure("OC-LIM-2026-000001")
    assert res["valid"] is True
    assert res["normalized_code"] == "OC-LIM-2026-000001"

    inv = DocumentCodeValidator.validate_structure("INVALID_CODE")
    assert inv["valid"] is False
    assert len(inv["errors"]) > 0


def test_year_resolver_timezone():
    from datetime import datetime, timezone
    dt = datetime(2026, 12, 31, 23, 30, tzinfo=timezone.utc)
    # 23:30 UTC is 18:30 Lima (America/Lima = UTC-5)
    year = YearResolverService.resolve_year(dt, tz_name="America/Lima")
    assert year == 2026


# --- Service & API Endpoints Tests ---

def test_preview_does_not_reserve_or_modify_db():
    db = SessionLocal()
    try:
        srv = DocumentCodeStandardService(db)
        from app.modules.logistics.documents.codes.code_schemas import DocumentCodePreviewRequest
        preview = srv.preview_code(DocumentCodePreviewRequest(document_type_code="OC", site_code="LIM", example_sequence=1))
        assert preview.code_preview == "OC-LIM-2026-000001"
        assert preview.is_reserved is False
        assert "NO reserva" in preview.warning
    finally:
        db.close()


def test_api_openapi_registered(app):
    schema = app.openapi()
    paths = set(schema["paths"].keys())
    assert "/api/logistics/document-code-standard" in paths
    assert "/api/logistics/document-code-standard/examples" in paths
    assert "/api/logistics/document-code-standard/validate" in paths
    assert "/api/logistics/document-code-standard/parse" in paths
    assert "/api/logistics/document-code-standard/preview" in paths
    assert "/api/logistics/document-site-codes" in paths


def test_api_unauthenticated_returns_401(client: TestClient):
    assert client.get("/api/logistics/document-code-standard").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.get("/api/logistics/document-code-standard/examples").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.post("/api/logistics/document-code-standard/validate", json={"code": "OC-LIM-2026-000001"}).status_code == status.HTTP_401_UNAUTHORIZED
