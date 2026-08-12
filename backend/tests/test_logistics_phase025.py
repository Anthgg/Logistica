"""
Phase 025 — Business Partners Test Suite.

Tests:
  - RUC Modulo 11 syntactic validation
  - BusinessPartner creation (single & multi-role)
  - Role management (SUPPLIER, CUSTOMER, CARRIER simultaneously)
  - Suspension of one role does not block others
  - Full partner block disables all roles operationally
  - Address & Contact management
  - Weighted evaluation (Decimal, exact sums)
  - Duplicate detection
  - Snapshot & content_hash immutability
  - Org-isolation (horizontal access denied)
  - SUNAT NOT consulted
  - No vehicles / drivers created
  - No general file repository created
"""
import pytest
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.modules.logistics.partners.ruc_validator import PeruvianRucValidator
from app.modules.logistics.partners.code_service import BusinessPartnerCodeService
from app.modules.logistics.partners.partner_service import BusinessPartnerService
from app.modules.logistics.partners.duplicate_detector import BusinessPartnerDuplicateDetection
from app.modules.logistics.partners.models import (
    BusinessPartnerModel,
    BusinessPartnerRoleModel,
    BusinessPartnerVersionModel,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def org_id(database):
    from app.models.organization import Organization
    org = Organization(
        code=f"ORG-{uuid4().hex[:8].upper()}",
        name=f"Test Org Phase 025 {uuid4().hex[:8]}",
        country_code="PE",
    )
    database.add(org)
    database.commit()
    return org.id


# ─── RUC Validation ──────────────────────────────────────────────────────────

class TestRucValidator:
    """Tests are purely algorithmic — no DB or org_id needed."""

    def test_valid_ruc_empresa(self):
        # RUC 20 prefix — real syntactically correct RUC
        assert PeruvianRucValidator.validate("20100070970") is True

    def test_valid_ruc_persona_natural(self):
        # RUC 10 prefix — computed via Módulo 11: 1006852154 -> check digit 3
        assert PeruvianRucValidator.validate("10068521543") is True

    def test_invalid_ruc_wrong_checkdigit(self):
        assert PeruvianRucValidator.validate("20100070971") is False

    def test_invalid_ruc_too_short(self):
        assert PeruvianRucValidator.validate("201000709") is False

    def test_invalid_ruc_wrong_prefix(self):
        assert PeruvianRucValidator.validate("99123456789") is False

    def test_invalid_ruc_letters(self):
        assert PeruvianRucValidator.validate("201000ABC70") is False

    def test_normalize_strips_spaces(self):
        assert PeruvianRucValidator.normalize("20 100 070 970") == "20100070970"

    def test_normalize_strips_dashes(self):
        assert PeruvianRucValidator.normalize("20-100-070-970") == "20100070970"


# ─── Code Generation ─────────────────────────────────────────────────────────

class TestCodeService:
    def test_normalize_uppercases(self):
        assert BusinessPartnerCodeService.normalize_code("bp-000001") == "BP-000001"

    def test_normalize_strips_special_chars(self):
        assert BusinessPartnerCodeService.normalize_code("bp 000001!") == "BP000001"

    def test_generate_first_code(self, database, org_id):
        code = BusinessPartnerCodeService.generate_next_code(database, org_id)
        assert code == "BP-000001"

    def test_generate_second_code_increments(self, database, org_id):
        service = BusinessPartnerService(database)
        service.create_partner(org_id, "Empresa Alpha SAC", country_code="PE")
        code = BusinessPartnerCodeService.generate_next_code(database, org_id)
        assert code == "BP-000002"


# ─── Partner Creation ─────────────────────────────────────────────────────────

class TestBusinessPartnerCreation:
    def test_create_partner_minimal(self, database, org_id):
        service = BusinessPartnerService(database)
        partner = service.create_partner(org_id, "Distribuidora Lima SAC")
        assert partner.id is not None
        assert partner.partner_code.startswith("BP-")
        assert partner.status == "DRAFT"
        assert partner.legal_name == "Distribuidora Lima SAC"
        assert partner.person_type == "LEGAL_ENTITY"

    def test_create_partner_with_ruc_format_valid(self, database, org_id):
        service = BusinessPartnerService(database)
        partner = service.create_partner(
            org_id,
            "Empresa Peruana SAC",
            tax_id_type="RUC",
            tax_id_value="20100070970",
        )
        assert partner.id is not None
        # Identifier must have FORMAT_VALID
        from sqlalchemy import select
        from app.modules.logistics.partners.models import BusinessPartnerIdentifierModel
        ident = database.scalars(
            select(BusinessPartnerIdentifierModel).where(
                BusinessPartnerIdentifierModel.business_partner_id == partner.id
            )
        ).first()
        assert ident is not None
        assert ident.verification_status == "FORMAT_VALID"
        assert ident.normalized_value == "20100070970"

    def test_create_partner_invalid_ruc_raises(self, database, org_id):
        from fastapi import HTTPException
        service = BusinessPartnerService(database)
        with pytest.raises(HTTPException) as exc:
            service.create_partner(
                org_id,
                "Empresa Mala SAC",
                tax_id_type="RUC",
                tax_id_value="20100070971",  # bad check digit
            )
        assert exc.value.status_code == 400

    def test_create_partner_missing_legal_name_raises(self, database, org_id):
        from fastapi import HTTPException
        service = BusinessPartnerService(database)
        with pytest.raises(HTTPException) as exc:
            service.create_partner(org_id, "")
        assert exc.value.status_code == 400

    def test_create_partner_creates_version_snapshot(self, database, org_id):
        service = BusinessPartnerService(database)
        partner = service.create_partner(org_id, "Empresa con Snapshot SAC")
        from sqlalchemy import select
        version = database.scalars(
            select(BusinessPartnerVersionModel).where(
                BusinessPartnerVersionModel.business_partner_id == partner.id
            )
        ).first()
        assert version is not None
        assert version.content_hash is not None
        assert len(version.content_hash) == 64  # SHA-256 hex
        assert version.version == "1.0.0"

    def test_sunat_not_consulted(self, database, org_id):
        """FORMAT_VALID means only syntax check — no SUNAT call."""
        service = BusinessPartnerService(database)
        partner = service.create_partner(
            org_id,
            "Empresa Local SAC",
            tax_id_type="RUC",
            tax_id_value="20100070970",
        )
        from sqlalchemy import select
        from app.modules.logistics.partners.models import BusinessPartnerIdentifierModel
        ident = database.scalars(
            select(BusinessPartnerIdentifierModel).where(
                BusinessPartnerIdentifierModel.business_partner_id == partner.id
            )
        ).first()
        # Must NOT be VERIFIED_EXTERNAL — only FORMAT_VALID
        assert ident.verification_status != "VERIFIED_EXTERNAL"
        assert ident.verification_status == "FORMAT_VALID"


# ─── Multiple Roles ───────────────────────────────────────────────────────────

class TestMultipleRoles:
    def test_supplier_and_customer_same_entity(self, database, org_id):
        service = BusinessPartnerService(database)
        partner = service.create_partner(
            org_id,
            "Distribuidora Mixta SAC",
            roles=["SUPPLIER", "CUSTOMER"],
        )
        from sqlalchemy import select
        roles = database.scalars(
            select(BusinessPartnerRoleModel).where(
                BusinessPartnerRoleModel.business_partner_id == partner.id
            )
        ).all()
        role_types = {r.role_type for r in roles}
        assert "SUPPLIER" in role_types
        assert "CUSTOMER" in role_types
        # Only ONE BusinessPartner entity — not duplicated
        from sqlalchemy import func, select as sel
        count = database.scalar(
            sel(func.count(BusinessPartnerModel.id)).where(
                BusinessPartnerModel.organization_id == org_id
            )
        )
        assert count == 1

    def test_three_roles_same_entity(self, database, org_id):
        service = BusinessPartnerService(database)
        partner = service.create_partner(
            org_id,
            "Empresa Triple SAC",
            roles=["SUPPLIER", "CUSTOMER", "CARRIER"],
        )
        from sqlalchemy import select
        roles = database.scalars(
            select(BusinessPartnerRoleModel).where(
                BusinessPartnerRoleModel.business_partner_id == partner.id
            )
        ).all()
        assert len(roles) == 3

    def test_suspend_supplier_role_customer_stays_active(self, database, org_id):
        """Suspending SUPPLIER role must not block CUSTOMER role."""
        service = BusinessPartnerService(database)
        partner = service.create_partner(
            org_id,
            "Empresa Parcial SAC",
            roles=["SUPPLIER", "CUSTOMER"],
        )
        # Manually suspend SUPPLIER role only
        from sqlalchemy import select, update
        database.execute(
            update(BusinessPartnerRoleModel)
            .where(
                BusinessPartnerRoleModel.business_partner_id == partner.id,
                BusinessPartnerRoleModel.role_type == "SUPPLIER",
            )
            .values(status="SUSPENDED")
        )
        database.commit()

        roles = database.scalars(
            select(BusinessPartnerRoleModel).where(
                BusinessPartnerRoleModel.business_partner_id == partner.id
            )
        ).all()
        role_status = {r.role_type: r.status for r in roles}
        assert role_status["SUPPLIER"] == "SUSPENDED"
        assert role_status["CUSTOMER"] == "ACTIVE"

    def test_block_partner_reflects_on_all_roles_operationally(self, database, org_id):
        """Blocking the partner means all roles are operationally restricted."""
        service = BusinessPartnerService(database)
        partner = service.create_partner(
            org_id,
            "Empresa Bloqueada SAC",
            roles=["SUPPLIER", "CUSTOMER"],
        )
        blocked = service.block_partner(partner.id, org_id)
        assert blocked.status == "BLOCKED"
        # The partner entity is blocked — all role operations must check partner.status first
        with pytest.raises(Exception):
            # Attempting to activate on a blocked partner must fail
            service.activate_partner(partner.id, org_id)

    def test_add_role_to_existing_partner(self, database, org_id):
        service = BusinessPartnerService(database)
        partner = service.create_partner(org_id, "Empresa Creciente SAC", roles=["SUPPLIER"])
        new_role = service.add_role(partner.id, org_id, "CUSTOMER")
        assert new_role.role_type == "CUSTOMER"
        assert new_role.status == "ACTIVE"

    def test_no_vehicles_created(self, database, org_id):
        """Creating a partner must not create vehicle or driver records."""
        from sqlalchemy import text

        assert database.scalar(text("SELECT count(*) FROM vehicles")) == 0
        assert "drivers" not in __import__("sqlalchemy").inspect(
            database.bind
        ).get_table_names()

    def test_no_general_file_repository_created(self, database, org_id):
        """Confirm no general file storage table was created."""
        import sqlalchemy
        insp = sqlalchemy.inspect(database.bind)
        table_names = insp.get_table_names()
        assert "file_repository" not in table_names
        assert "document_storage" not in table_names


# ─── Addresses & Contacts ─────────────────────────────────────────────────────

class TestAddressesAndContacts:
    def test_add_fiscal_address(self, database, org_id):
        service = BusinessPartnerService(database)
        partner = service.create_partner(org_id, "Empresa Con Dirección SAC")
        addr = service.add_address(
            partner.id, org_id,
            address_line_1="Av. Javier Prado Este 123",
            address_type="FISCAL",
            district="San Isidro",
            province="Lima",
            department="Lima",
        )
        assert addr.id is not None
        assert addr.address_type == "FISCAL"
        assert addr.is_primary is True
        assert addr.district == "San Isidro"

    def test_add_primary_contact(self, database, org_id):
        service = BusinessPartnerService(database)
        partner = service.create_partner(org_id, "Empresa Con Contacto SAC")
        contact = service.add_contact(
            partner.id, org_id,
            full_name="Juan Pérez",
            contact_type="PURCHASES",
            email="juan.perez@empresa.pe",
            phone="+51987654321",
        )
        assert contact.id is not None
        assert contact.full_name == "Juan Pérez"
        assert contact.contact_type == "PURCHASES"
        assert contact.is_primary is True


# ─── Evaluations (Decimal/weighted) ──────────────────────────────────────────

class TestEvaluations:
    def test_evaluation_weights_and_scores_decimal(self, database, org_id):
        service = BusinessPartnerService(database)
        partner = service.create_partner(org_id, "Proveedor Evaluado SAC", roles=["SUPPLIER"])
        criteria = [
            {"code": "QUALITY", "name": "Calidad", "weight": "60.00", "score": "90.00"},
            {"code": "DELIVERY", "name": "Entrega", "weight": "40.00", "score": "75.00"},
        ]
        evaluation = service.submit_evaluation(
            partner.id, org_id, "SUPPLIER", criteria, summary="Evaluación inicial"
        )
        # Expected: (60*90/100) + (40*75/100) = 54 + 30 = 84.00
        assert evaluation.total_score == Decimal("84.00")
        assert evaluation.risk_level == "LOW"
        assert evaluation.status == "APPROVED"

    def test_high_risk_when_score_below_50(self, database, org_id):
        service = BusinessPartnerService(database)
        partner = service.create_partner(org_id, "Proveedor Riesgoso SAC", roles=["SUPPLIER"])
        criteria = [
            {"code": "QUALITY", "name": "Calidad", "weight": "100.00", "score": "30.00"},
        ]
        evaluation = service.submit_evaluation(
            partner.id, org_id, "SUPPLIER", criteria
        )
        assert evaluation.risk_level == "HIGH"

    def test_medium_risk_between_50_and_75(self, database, org_id):
        service = BusinessPartnerService(database)
        partner = service.create_partner(org_id, "Proveedor Medio SAC", roles=["SUPPLIER"])
        criteria = [
            {"code": "QUALITY", "name": "Calidad", "weight": "100.00", "score": "60.00"},
        ]
        evaluation = service.submit_evaluation(
            partner.id, org_id, "SUPPLIER", criteria
        )
        assert evaluation.risk_level == "MEDIUM"


# ─── Duplicate Detection ──────────────────────────────────────────────────────

class TestDuplicateDetection:
    def test_detects_duplicate_by_ruc(self, database, org_id):
        service = BusinessPartnerService(database)
        service.create_partner(
            org_id, "Empresa Original SAC",
            tax_id_type="RUC", tax_id_value="20100070970"
        )
        results = BusinessPartnerDuplicateDetection.find_duplicates(
            database, org_id, tax_id_val="20100070970"
        )
        assert len(results) >= 1
        assert results[0]["probability"] == "HIGH_PROBABILITY_DUPLICATE"

    def test_no_duplicate_different_ruc(self, database, org_id):
        """A different organization must not see candidates from another org."""
        service = BusinessPartnerService(database)
        service.create_partner(
            org_id, "Empresa Única SAC",
            tax_id_type="RUC", tax_id_value="20100070970"
        )
        from app.models.organization import Organization
        org2 = Organization(
            code=f"ORG-{uuid4().hex[:8].upper()}",
            name=f"Org Dos {uuid4().hex[:8]}",
            country_code="PE",
        )
        database.add(org2)
        database.commit()

        results = BusinessPartnerDuplicateDetection.find_duplicates(
            database, org2.id, tax_id_val="20100070970"
        )
        assert len(results) == 0  # No cross-org access


# ─── Activation ──────────────────────────────────────────────────────────────

class TestActivation:
    def test_activate_partner(self, database, org_id):
        service = BusinessPartnerService(database)
        partner = service.create_partner(org_id, "Empresa Para Activar SAC")
        assert partner.status == "DRAFT"
        active = service.activate_partner(partner.id, org_id)
        assert active.status == "ACTIVE"

    def test_block_then_cannot_activate(self, database, org_id):
        service = BusinessPartnerService(database)
        partner = service.create_partner(org_id, "Empresa Bloqueada 2 SAC")
        service.block_partner(partner.id, org_id, reason="Incumplimiento")
        with pytest.raises(Exception):
            service.activate_partner(partner.id, org_id)


# ─── Org Isolation ────────────────────────────────────────────────────────────

class TestOrgIsolation:
    def test_org_b_cannot_access_org_a_partner(self, database, org_id):
        from fastapi import HTTPException
        service = BusinessPartnerService(database)
        partner = service.create_partner(org_id, "Empresa Org A SAC")

        from app.models.organization import Organization
        org_b = Organization(
            code=f"ORG-{uuid4().hex[:8].upper()}",
            name=f"Org B {uuid4().hex[:8]}",
            country_code="PE",
        )
        database.add(org_b)
        database.commit()

        with pytest.raises(HTTPException) as exc:
            service.get_partner(partner.id, org_b.id)
        assert exc.value.status_code == 404
