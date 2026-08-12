"""Integration and unit test suite for Phase 021 — Company Profile, Versioning, Signers & Preview."""

import io
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from PIL import Image
from sqlalchemy import select, and_

from app.models.organization import Organization
from app.models.branch import Branch
from app.models.user import User
from app.models.device import Device
from app.models.session import UserSession
from app.core.security import create_access_token, hash_session_token
from app.core.config import settings

from app.database.base import Base
from app.database.session import SessionLocal, engine

from tests.support import authenticate

from app.modules.logistics.rbac.models_role import LogisticsRole
from app.modules.logistics.rbac.models_assignment import LogisticsRoleAssignment
from app.modules.logistics.documents.models import DocumentFamilyModel, DocumentTypeModel
from app.modules.logistics.company_profile.models import (
    OrganizationProfileModel,
    OrganizationProfileVersionModel,
    OrganizationAddressModel,
    OrganizationContactModel,
    OrganizationAssetModel,
    AuthorizedSignerModel,
    OrganizationDocumentSettingsModel,
    OrganizationNumberingDisplayPolicyModel,
)
from app.modules.logistics.company_profile.company_profile_service import CompanyProfileService
from app.modules.logistics.company_profile.address_contact_service import AddressContactService
from app.modules.logistics.company_profile.asset_service import AssetService
from app.modules.logistics.company_profile.signer_service import SignerService
from app.modules.logistics.company_profile.numbering_policy_service import NumberingPolicyService
from app.modules.logistics.company_profile.snapshot_provider import InstitutionalSnapshotProvider
from app.modules.logistics.company_profile.validators import (
    validate_peruvian_ruc,
    validate_numbering_display_pattern,
    validate_and_sanitize_image,
)
from app.modules.logistics.company_profile.schemas import (
    OrganizationProfileUpdate,
    OrganizationAddressCreate,
    OrganizationContactCreate,
    AuthorizedSignerCreate,
    NumberingDisplayPolicyCreate,
)


@pytest.fixture(scope="module")
def app():
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture(scope="module")
def client(app):
    from fastapi.testclient import TestClient
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


@pytest.fixture
def seed_phase021_data(db_session):
    """Seed test Organization and Branch for Phase 021."""
    org_id = uuid4()
    org = Organization(
        id=org_id,
        code=f"ORG-{uuid4().hex[:6]}",
        name="EMPRESA MODELO PERÚ S.A.C.",
        country_code="PE",
        timezone="America/Lima",
    )
    db_session.add(org)

    branch_id = uuid4()
    branch = Branch(
        id=branch_id,
        organization_id=org_id,
        code="LIM-MAIN",
        name="Sede Principal Lima",
        status="active",
    )
    db_session.add(branch)

    user = User(
        email=f"admin-{uuid4().hex[:6]}@empresa.test",
        password_hash="hash-ficticio",
        full_name="Admin Institucional",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    device = Device(user_id=user.id, device_identifier=f"device-{uuid4().hex[:6]}", browser="pytest")
    db_session.add(device)
    db_session.flush()

    session_id = uuid4()
    session_token = create_access_token(user.id, session_id)
    session = UserSession(
        id=session_id,
        user_id=user.id,
        device_id=device.id,
        token_hash=hash_session_token(session_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    # Seed DocumentFamily and DocumentType for preview test
    fam = db_session.scalars(select(DocumentFamilyModel).where(DocumentFamilyModel.code == "OUTBOUND")).first()
    if not fam:
        fam = DocumentFamilyModel(id=uuid4(), code="OUTBOUND", name="Salidas")
        db_session.add(fam)
        db_session.flush()

    dt = db_session.scalars(select(DocumentTypeModel).where(DocumentTypeModel.code == "PED")).first()
    if not dt:
        dt = DocumentTypeModel(
            id=uuid4(),
            code="PED",
            name="Pedido de Salida",
            short_name="PED",
            family_id=fam.id,
            origin_type="INTERNAL_GENERATED",
            owner_module="outbound",
            resource_type="outbound_order",
            operation_type="issue",
            requires_signature=True,
        )
        db_session.add(dt)
        db_session.flush()

    db_session.commit()

    return {
        "org_id": org_id,
        "branch_id": branch_id,
        "user": user,
        "session_token": session_token,
    }


class TestPeruvianRucValidator:
    def test_valid_rucs(self):
        # Valid 20 prefix RUC
        valid, msg = validate_peruvian_ruc("20123456786")
        assert valid is True

        # Valid 10 prefix RUC
        valid, msg = validate_peruvian_ruc("10456789019")
        assert valid is True

    def test_invalid_rucs(self):
        # Invalid length
        valid, msg = validate_peruvian_ruc("2012345678")
        assert valid is False
        assert "11 dígitos" in msg

        # Invalid prefix
        valid, msg = validate_peruvian_ruc("30123456789")
        assert valid is False
        assert "Prefijo de RUC inválido" in msg

        # Bad check digit
        valid, msg = validate_peruvian_ruc("20123456780")
        assert valid is False
        assert "dígito de verificación inválido" in msg


class TestNumberingDisplayPatternValidator:
    def test_valid_patterns(self):
        valid, msg = validate_numbering_display_pattern("{TYPE}-{SITE}-{YEAR}-{SEQUENCE}", 6)
        assert valid is True

        valid, msg = validate_numbering_display_pattern("DOC-{YEAR}/{SEQUENCE}", 8)
        assert valid is True

    def test_invalid_patterns(self):
        # Missing sequence
        valid, msg = validate_numbering_display_pattern("{TYPE}-{SITE}-{YEAR}", 6)
        assert valid is False
        assert "SEQUENCE" in msg

        # Invalid token
        valid, msg = validate_numbering_display_pattern("{TYPE}-{INVALID}-{SEQUENCE}", 6)
        assert valid is False
        assert "Token no permitido" in msg

        # Malicious code attempt
        valid, msg = validate_numbering_display_pattern("{SEQUENCE}<script>alert(1)</script>", 6)
        assert valid is False
        assert "no permitidas" in msg


class TestImageSecuritySanitizer:
    def test_valid_png_sanitizing(self):
        # Generate valid PNG in memory
        img = Image.new("RGB", (200, 100), color="blue")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        raw_bytes = img_byte_arr.getvalue()

        res = validate_and_sanitize_image(raw_bytes, "logo.png", "DOCUMENT_LOGO")
        assert res["mime_type"] == "image/png"
        assert res["width"] == 200
        assert res["height"] == 100
        assert len(res["file_hash"]) == 64

    def test_invalid_svg_rejection(self):
        svg_bytes = b"<svg xmlns='http://www.w3.org/2000/svg'><text>Logo</text></svg>"
        with pytest.raises(ValueError, match="SVG no está permitido"):
            validate_and_sanitize_image(svg_bytes, "logo.svg", "DOCUMENT_LOGO")

    def test_corrupted_file_rejection(self):
        fake_bytes = b"NOT_A_REAL_IMAGE_HEADER_1234567890"
        with pytest.raises(ValueError, match="Formato de imagen no soportado"):
            validate_and_sanitize_image(fake_bytes, "logo.png", "DOCUMENT_LOGO")


class TestCompanyProfileAndVersioning:
    def test_company_profile_crud_and_versioning(self, db_session, seed_phase021_data):
        org_id = seed_phase021_data["org_id"]
        user_id = seed_phase021_data["user"].id
        srv = CompanyProfileService(db_session)

        # Get default
        profile = srv.get_profile_or_create_default(org_id, user_id)
        assert profile.legal_name == "EMPRESA MODELO PERÚ S.A.C."
        assert profile.profile_status == "DRAFT"

        # Update profile with valid RUC
        update_req = OrganizationProfileUpdate(
            legal_name="EMPRESA LOGÍSTICA PERÚ S.A.C.",
            trade_name="LOGÍSTICA PERÚ",
            ruc="20123456786",
            website="https://logisticaperu.test",
        )
        updated_profile = srv.update_profile(org_id, update_req, user_id)
        assert updated_profile.legal_name == "EMPRESA LOGÍSTICA PERÚ S.A.C."
        assert updated_profile.website == "https://logisticaperu.test"

        # Create version
        ver1 = srv.create_version(org_id, user_id)
        assert ver1.version == "1.0.0"
        assert ver1.status == "DRAFT"
        assert len(ver1.content_hash) == 64

        # Activate version
        active_ver = srv.activate_version(org_id, ver1.id, reason="Aprobación inicial de ficha", actor_id=user_id)
        assert active_ver.status == "ACTIVE"
        assert updated_profile.active_version_id == active_ver.id
        assert updated_profile.profile_status == "ACTIVE"

        # Create second version
        ver2 = srv.create_version(org_id, user_id)
        assert ver2.version == "1.0.1"


class TestAddressesAndContacts:
    def test_addresses_primary_behavior(self, db_session, seed_phase021_data):
        org_id = seed_phase021_data["org_id"]
        branch_id = seed_phase021_data["branch_id"]
        srv = AddressContactService(db_session)

        # Create address 1
        addr1 = srv.create_address(
            org_id,
            OrganizationAddressCreate(
                branch_id=branch_id,
                address_type="LEGAL",
                label="Oficina Principal",
                address_line="Av. República de Panamá 3505, San Isidro",
                district="San Isidro",
                province="Lima",
                department="Lima",
                is_primary=True,
            ),
        )
        assert addr1.is_primary is True

        # Create address 2 set as primary
        addr2 = srv.create_address(
            org_id,
            OrganizationAddressCreate(
                branch_id=branch_id,
                address_type="LEGAL",
                label="Nueva Sede Fiscal",
                address_line="Av. Canaval y Moreyra 480",
                district="San Isidro",
                province="Lima",
                department="Lima",
                is_primary=True,
            ),
        )
        db_session.refresh(addr1)
        assert addr2.is_primary is True
        assert addr1.is_primary is False

    def test_contacts_crud(self, db_session, seed_phase021_data):
        org_id = seed_phase021_data["org_id"]
        srv = AddressContactService(db_session)

        cnt = srv.create_contact(
            org_id,
            OrganizationContactCreate(
                contact_type="DISPATCH",
                label="Jefe de Despacho",
                full_name="Carlos Mendoza",
                email="despacho@empresa.com",
                phone="+51 987654321",
                is_primary=True,
                show_in_documents=True,
            ),
        )
        assert cnt.contact_type == "DISPATCH"
        assert cnt.email == "despacho@empresa.com"

        contacts = srv.list_contacts(org_id)
        assert len(contacts) == 1


class TestSignerResolution:
    def test_signer_authorization_resolution(self, db_session, seed_phase021_data):
        org_id = seed_phase021_data["org_id"]
        branch_id = seed_phase021_data["branch_id"]

        signer_srv = SignerService(db_session)

        # Create active signer with limit
        signer = signer_srv.create_signer(
            org_id,
            AuthorizedSignerCreate(
                full_name="Ing. Roberto Gómez",
                position_title="Gerente de Operaciones",
                department="Logística",
                authorization_type="MANAGEMENT",
                can_sign_all_branches=True,
                document_family_scope=["OUTBOUND"],
                document_type_scope=["PED"],
                max_amount=Decimal("50000.00"),
                currency_code="PEN",
            ),
        )
        assert signer.status == "ACTIVE"

        # Resolve for valid scope
        res = signer_srv.resolve_authorized_signer(
            organization_id=org_id,
            branch_id=branch_id,
            document_family="OUTBOUND",
            document_type_code="PED",
            amount=Decimal("15000.00"),
            currency_code="PEN",
        )
        assert res["authorization_status"] == "AUTHORIZED"
        assert res["signer"]["full_name"] == "Ing. Roberto Gómez"

        # Resolve for amount exceeding limit
        res_exceed = signer_srv.resolve_authorized_signer(
            organization_id=org_id,
            branch_id=branch_id,
            document_family="OUTBOUND",
            document_type_code="PED",
            amount=Decimal("100000.00"),
            currency_code="PEN",
        )
        assert res_exceed["authorization_status"] == "NO_AUTHORIZED_SIGNER"
        assert len(res_exceed["warnings"]) > 0


class TestPreviewAndSnapshotImmutability:
    def test_institutional_preview_and_snapshot(self, client, db_session, seed_phase021_data):
        org_id = seed_phase021_data["org_id"]
        branch_id = seed_phase021_data["branch_id"]

        # Authenticate client
        user, auth_headers = authenticate(client, db_session, role="admin")

        role = db_session.scalar(select(LogisticsRole).where(LogisticsRole.code == "ADMIN_LOGISTICA"))
        if not role:
            role = LogisticsRole(id=uuid4(), code="ADMIN_LOGISTICA", name="Admin Logística", description="Administrador General de Logística", is_system=True, status="active")
            db_session.add(role)
            db_session.flush()

        assignment = LogisticsRoleAssignment(
            id=uuid4(),
            user_id=user.id,
            role_id=role.id,
            scope_type="ORGANIZATION",
            organization_id=org_id,
            status="active",
            assigned_by=user.id,
        )
        db_session.add(assignment)
        db_session.commit()

        # 1. Preview document
        response = client.post(
            "/api/logistics/company-profile/document-preview",
            json={
                "doc_type_code": "PED",
                "branch_id": str(branch_id),
                "custom_data": {"test": "preview"},
            },
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        assert response.headers["content-type"] == "application/pdf"

        # 2. Institutional snapshot provider
        provider = InstitutionalSnapshotProvider(db_session)
        snap = provider.capture_snapshot(org_id)
        assert snap["legal_name"] == "EMPRESA MODELO PERÚ S.A.C."
        assert "institutional_payload" in snap
        assert len(snap["content_hash"]) == 64
