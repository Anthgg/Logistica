"""Standalone SQLite Runner for Phase 029 Driver Master Data."""

import os
import sys
from datetime import date
from uuid import uuid4

# Ensure backend root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.session import get_db
from app.main import app
import app.models.registry  # register ORM models
from app.modules.logistics.drivers.application.services.identity_license_service import (
    DriverCategoryService,
)
from app.modules.logistics.drivers.domain.services.services import (
    DriverIdentityDocumentNormalizer,
    DriverLicenseNormalizer,
)

# Setup SQLite in-memory
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

allowed_prefixes = (
    "organizations", "logistics_", "vehicles", "vehicle_", "assisted_",
    "business_", "units_", "measurement_", "document_", "product",
    "purchase_", "audit_logs", "users", "drivers", "driver_",
)

for table in Base.metadata.sorted_tables:
    if any(table.name.startswith(p) for p in allowed_prefixes):
        try:
            table.create(engine, checkfirst=True)
        except Exception:
            pass

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def run_tests():
    print("=== STARTING PHASE 029 SQLITE TESTS ===")

    # 1. Test Normalizers & Masking
    norm_dni = DriverIdentityDocumentNormalizer.normalize("DNI", " 12345678 ")
    assert norm_dni == "12345678"
    mask_dni = DriverIdentityDocumentNormalizer.mask(norm_dni)
    assert mask_dni == "*****678"
    print("✅ 1. Identity Normalizer & Masking PASSED")

    norm_lic = DriverLicenseNormalizer.normalize(" Q-12345678 ")
    assert norm_lic == "Q12345678"
    mask_lic = DriverLicenseNormalizer.mask(norm_lic)
    assert mask_lic == "*****678"
    print("✅ 2. License Normalizer & Masking PASSED")

    # Seed Categories
    with TestingSessionLocal() as db:
        cat_service = DriverCategoryService(db)
        cat_service.seed_default_categories()

    # Seed Organization and Carrier Partner
    org_id = "f8545a6d-4183-478b-8be2-0df2867475a2"
    with TestingSessionLocal() as db:
        db.execute(text("INSERT OR IGNORE INTO logistics_organizations (id, name, RUC) VALUES (:id, 'LOGIX S.A.C.', '20123456789')"), {"id": org_id})
        # Add carrier partner & role
        partner_id = str(uuid4())
        role_id = str(uuid4())
        db.execute(
            text("INSERT INTO business_partners (id, organization_id, partner_code, normalized_partner_code, legal_name, person_type, status, lifecycle_status) VALUES (:id, :org_id, 'CAR-001', 'CAR001', 'TRANSPORTES PERU S.A.C.', 'LEGAL_ENTITY', 'ACTIVE', 'ACTIVE')"),
            {"id": partner_id, "org_id": org_id}
        )
        db.execute(
            text("INSERT INTO business_partner_roles (id, partner_id, role_code, status) VALUES (:id, :partner_id, 'CARRIER', 'ACTIVE')"),
            {"id": role_id, "partner_id": partner_id}
        )
        db.commit()

    headers = {"X-Org-Id": org_id, "X-Actor-Id": "37432a2c-8420-4393-acab-c590a02b1987"}

    # 2. Create Driver
    resp = client.post(
        "/api/logistics/drivers",
        headers=headers,
        json={
            "first_name": "Juan",
            "paternal_last_name": "Perez",
            "middle_name": "Carlos",
            "maternal_last_name": "Gomez",
            "date_of_birth": "1990-05-15",
            "nationality_country_code": "PE",
        },
    )
    assert resp.status_code == 201, f"Error: {resp.text}"
    driver_data = resp.json()
    driver_id = driver_data["id"]
    assert driver_data["driver_code"].startswith("DRV-")
    assert driver_data["display_name"] == "JUAN CARLOS PEREZ GOMEZ"
    assert driver_data["lifecycle_status"] == "DRAFT"
    print(f"✅ 3. Create Driver PASSED (Code: {driver_data['driver_code']})")

    # 3. Add Identity Document
    resp = client.post(
        f"/api/logistics/drivers/{driver_id}/identity-documents",
        headers=headers,
        json={
            "document_type": "DNI",
            "value": "78945612",
            "is_primary": True,
        },
    )
    assert resp.status_code == 201, f"Error: {resp.text}"
    id_doc_data = resp.json()
    assert id_doc_data["masked_value"] == "*****612"
    print("✅ 4. Add Identity Document PASSED")

    # 4. Add License & Assign Category A-IIIc
    resp = client.post(
        f"/api/logistics/drivers/{driver_id}/licenses",
        headers=headers,
        json={
            "license_number": "Q78945612",
            "expires_at": "2029-12-31",
            "issuing_authority": "MTC",
            "primary_license": True,
        },
    )
    assert resp.status_code == 201, f"Error: {resp.text}"
    license_data = resp.json()
    license_id = license_data["id"]

    resp = client.post(
        f"/api/logistics/driver-licenses/{license_id}/categories",
        headers=headers,
        json={
            "category_code": "A-IIIc",
            "expires_at": "2029-12-31",
        },
    )
    assert resp.status_code == 201, f"Error: {resp.text}"
    print("✅ 5. Add License & Category A-IIIc PASSED")

    # 5. Assign Carrier
    resp = client.post(
        f"/api/logistics/drivers/{driver_id}/carrier-assignments",
        headers=headers,
        json={
            "carrier_business_partner_id": partner_id,
            "assignment_type": "INTERNAL",
        },
    )
    assert resp.status_code == 201, f"Error: {resp.text}"
    print("✅ 6. Assign Carrier PASSED")

    # 6. Activate Driver
    resp = client.post(f"/api/logistics/drivers/{driver_id}/activate", headers=headers)
    assert resp.status_code == 200, f"Error: {resp.text}"
    act_data = resp.json()
    assert act_data["lifecycle_status"] == "ACTIVE"
    assert act_data["compliance_status"] == "COMPLIANT"
    assert act_data["eligibility_status"] == "ELIGIBLE"
    assert act_data["active_version_id"] is not None
    print("✅ 7. Activate Driver PASSED")

    # 7. Duplicate Check
    resp = client.post(
        "/api/logistics/drivers/duplicate-check",
        headers=headers,
        json={"identity_document_value": "78945612"},
    )
    assert resp.status_code == 200, f"Error: {resp.text}"
    dup_data = resp.json()
    assert dup_data["duplicate_found"] == True
    print("✅ 8. Duplicate Detection PASSED")

    # 8. Link Photo using file_reference_id
    photo_file_ref = str(uuid4())
    resp = client.post(
        f"/api/logistics/drivers/{driver_id}/photos",
        headers=headers,
        json={
            "file_reference_id": photo_file_ref,
            "photo_type": "PROFILE",
            "source_type": "INTERNAL_CAPTURE",
        },
    )
    assert resp.status_code == 201, f"Error: {resp.text}"
    photo_data = resp.json()
    assert photo_data["file_reference_id"] == photo_file_ref
    print("✅ 9. Photo Link (no Base64, no biometrics) PASSED")

    # 9. Block Driver
    resp = client.post(
        f"/api/logistics/drivers/{driver_id}/block",
        headers=headers,
        json={"reason": "Sanción disciplinaria administrativa por exceso de jornada"},
    )
    assert resp.status_code == 200, f"Error: {resp.text}"
    blk_data = resp.json()
    assert blk_data["lifecycle_status"] == "BLOCKED"
    assert blk_data["eligibility_status"] == "BLOCKED"
    print("✅ 10. Block Driver PASSED")

    print("\n🎉 ALL 10 PHASE 029 TESTS PASSED SUCCESSFULLY! 🎉")


if __name__ == "__main__":
    run_tests()
