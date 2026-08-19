"""Pytest Test Suite for Phase 029 — Driver Master Data."""

from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.database.session import get_db
from tests.support import authenticate
from app.modules.logistics.drivers.domain.services.services import (
    DriverIdentityDocumentNormalizer,
    DriverLicenseNormalizer,
)


def test_driver_normalizers():
    norm_dni = DriverIdentityDocumentNormalizer.normalize("DNI", " 87654321 ")
    assert norm_dni == "87654321"
    assert DriverIdentityDocumentNormalizer.mask(norm_dni) == "*****321"

    norm_lic = DriverLicenseNormalizer.normalize(" Q-98765432 ")
    assert norm_lic == "Q98765432"
    assert DriverLicenseNormalizer.mask(norm_lic) == "*****5432"


def test_driver_full_lifecycle(client: TestClient, database):
    """Ciclo de vida completo del conductor, ahora con sesión real.

    La versión anterior se identificaba con `X-Org-Id` y `X-Actor-Id` fijos. F006
    retiró esa vía: la identidad y la organización salen del principal autenticado,
    así que el caso se apoya en una sesión y en permisos concedidos por rol.
    """
    from tests.test_logistics_f006_endpoint_authorization import _grant, _organization

    user, headers = authenticate(client, database, role="operator")
    # Ámbito de organización, no global: al retirar el UUID fijo de respaldo, un
    # principal sin organización resoluble recibe 400 en vez de escribir en la
    # organización por defecto. Aquí el tenant es explícito.
    organization = _organization(database)
    _grant(
        database,
        user,
        ["logistics.drivers.read", "logistics.drivers.create", "logistics.drivers.update"],
        scope_type="organization",
        organization_id=organization.id,
    )

    # Seed Categories
    client.post("/api/logistics/driver-license-categories/seed", headers=headers)

    # 1. Create Driver
    resp = client.post(
        "/api/logistics/drivers",
        headers=headers,
        json={
            "first_name": "Mario",
            "paternal_last_name": "Vargas",
            "middle_name": "Alberto",
            "maternal_last_name": "Llosa",
            "date_of_birth": "1985-03-28",
        },
    )
    assert resp.status_code == 201
    driver_id = resp.json()["id"]

    # 2. Add Identity Document (DNI)
    resp = client.post(
        f"/api/logistics/drivers/{driver_id}/identity-documents",
        headers=headers,
        json={"document_type": "DNI", "value": "11223344", "is_primary": True},
    )
    assert resp.status_code == 201
    assert resp.json()["masked_value"] == "*****344"

    # 3. Add License (A-IIIb)
    resp = client.post(
        f"/api/logistics/drivers/{driver_id}/licenses",
        headers=headers,
        json={"license_number": "Q11223344", "expires_at": "2030-01-01", "primary_license": True},
    )
    assert resp.status_code == 201
    lic_id = resp.json()["id"]

    resp = client.post(
        f"/api/logistics/driver-licenses/{lic_id}/categories",
        headers=headers,
        json={"category_code": "A-IIIb", "expires_at": "2030-01-01"},
    )
    assert resp.status_code == 201

    # 4. Activate
    resp = client.post(f"/api/logistics/drivers/{driver_id}/activate", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["lifecycle_status"] == "ACTIVE"

    # 5. Duplicate Check
    resp = client.post(
        "/api/logistics/drivers/duplicate-check",
        headers=headers,
        json={"identity_document_value": "11223344"},
    )
    assert resp.status_code == 200
    assert resp.json()["duplicate_found"] is True

    # 6. Block
    resp = client.post(
        f"/api/logistics/drivers/{driver_id}/block",
        headers=headers,
        json={"reason": "Suspensión administrativa preventiva"},
    )
    assert resp.status_code == 200
    assert resp.json()["lifecycle_status"] == "BLOCKED"
