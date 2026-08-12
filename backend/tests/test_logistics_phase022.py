"""Tests for Phase 022 — Warehouses & Locations Hierarchy."""

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import SessionLocal, engine
from app.models.branch import Branch
from app.models.organization import Organization
from app.models.warehouse import Warehouse
from app.modules.logistics.rbac.models_assignment import LogisticsRoleAssignment
from app.modules.logistics.rbac.models_role import LogisticsRole
from app.modules.logistics.warehouses.bulk_generation_service import WarehouseLocationBulkService
from app.modules.logistics.warehouses.code_service import WarehouseLocationCodeService
from app.modules.logistics.warehouses.hierarchy_policy import WarehouseLocationHierarchyPolicy
from app.modules.logistics.warehouses.location_service import WarehouseLocationService
from app.modules.logistics.warehouses.models import (
    WarehouseLocationCodeAliasModel,
    WarehouseLocationModel,
)
from app.modules.logistics.warehouses.schemas import (
    WarehouseCreate,
    WarehouseLocationBulkPreviewRequest,
    WarehouseLocationCreate,
)
from app.modules.logistics.warehouses.validators import (
    validate_location_segment,
    validate_warehouse_code,
)
from tests.support import authenticate


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def setup_domain(db_session: Session):
    org = db_session.query(Organization).filter_by(code="ORG_W22").first()
    if not org:
        org = Organization(
            id=uuid4(),
            code="ORG_W22",
            name="Organización Logística W22",
            country_code="PE",
            status="ACTIVE",
        )
        db_session.add(org)
        db_session.flush()

    branch = db_session.query(Branch).filter_by(code="SED_W22").first()
    if not branch:
        branch = Branch(
            id=uuid4(),
            organization_id=org.id,
            code="SED_W22",
            name="Sede Principal W22",
            status="active",
        )
        db_session.add(branch)
        db_session.flush()

    db_session.commit()
    return {"org": org, "branch": branch}


class TestWarehouseValidators:
    def test_warehouse_code_validation(self):
        ok, res = validate_warehouse_code("ALM01")
        assert ok is True
        assert res == "ALM01"

        ok, _ = validate_warehouse_code("a")  # too short
        assert ok is False

        ok, _ = validate_warehouse_code("ALM 01")  # space not allowed
        assert ok is False

    def test_location_segment_validation(self):
        ok, res = validate_location_segment("z01")
        assert ok is True
        assert res == "Z01"

        ok, _ = validate_location_segment("")
        assert ok is False


class TestHierarchyPolicy:
    def test_parent_child_matrix(self):
        ok, _ = WarehouseLocationHierarchyPolicy.validate_parent_child("ZONE", None)
        assert ok is True

        ok, _ = WarehouseLocationHierarchyPolicy.validate_parent_child("AISLE", "ZONE")
        assert ok is True

        ok, _ = WarehouseLocationHierarchyPolicy.validate_parent_child("LEVEL", "ZONE")  # Invalid parent
        assert ok is False


class TestWarehouseAndLocationServices:
    def test_warehouse_and_location_creation_and_move(self, db_session: Session, setup_domain: dict):
        org = setup_domain["org"]
        branch = setup_domain["branch"]

        # 1. Create Warehouse
        wh_code = f"W{uuid4().hex[:6].upper()}"
        wh = Warehouse(
            id=uuid4(),
            organization_id=org.id,
            branch_id=branch.id,
            code=wh_code,
            name="Almacén Central Test",
            address="Av. Industrial 123",
            warehouse_type="GENERAL",
            status="ACTIVE",
            layout_status="DRAFT",
        )
        db_session.add(wh)
        db_session.flush()

        loc_service = WarehouseLocationService(db_session)

        # 2. Create Zone (root)
        z1 = loc_service.create_location(
            organization_id=org.id,
            req=WarehouseLocationCreate(
                warehouse_id=wh.id,
                location_type="ZONE",
                code="Z01",
                name="Zona Seca 01",
            ),
        )
        assert z1.full_code == f"{wh_code}-Z01"
        assert z1.depth == 1

        # 3. Create Aisle under Zone
        a1 = loc_service.create_location(
            organization_id=org.id,
            req=WarehouseLocationCreate(
                warehouse_id=wh.id,
                parent_location_id=z1.id,
                location_type="AISLE",
                code="A01",
                name="Pasillo 01",
            ),
        )
        assert a1.full_code == f"{wh_code}-Z01-A01"
        assert a1.depth == 2

        # 4. Create Zone 02
        z2 = loc_service.create_location(
            organization_id=org.id,
            req=WarehouseLocationCreate(
                warehouse_id=wh.id,
                location_type="ZONE",
                code="Z02",
                name="Zona Fría 02",
            ),
        )

        # 5. Move Aisle 01 to Zone 02
        preview = loc_service.move_preview(org.id, a1.id, z2.id)
        assert preview.is_move_allowed is True
        assert preview.proposed_full_code == f"{wh_code}-Z02-A01"

        moved_a1 = loc_service.move_location(org.id, a1.id, z2.id, reason="Reorganización física")
        assert moved_a1.full_code == f"{wh_code}-Z02-A01"

        # Verify Code Alias created
        alias = db_session.scalars(
            select(WarehouseLocationCodeAliasModel).where(WarehouseLocationCodeAliasModel.location_id == a1.id)
        ).first()
        assert alias is not None
        assert alias.previous_full_code == f"{wh_code}-Z01-A01"
        assert alias.new_full_code == f"{wh_code}-Z02-A01"

    def test_bulk_generation_preview(self, db_session: Session, setup_domain: dict):
        org = setup_domain["org"]
        branch = setup_domain["branch"]

        wh = Warehouse(
            id=uuid4(),
            organization_id=org.id,
            branch_id=branch.id,
            code=f"WBULK{uuid4().hex[:4].upper()}",
            name="Almacén Masivo",
            address="Av. Masiva 456",
            warehouse_type="GENERAL",
        )
        db_session.add(wh)
        db_session.flush()

        bulk_service = WarehouseLocationBulkService(db_session)
        req = WarehouseLocationBulkPreviewRequest(
            warehouse_id=wh.id,
            zone_code="Z01",
            aisle_count=2,
            aisle_start=1,
            aisle_end=2,
            rack_count=2,
            rack_start=1,
            rack_end=2,
            level_count=2,
            level_start=1,
            level_end=2,
            position_count=2,
            position_start=1,
            position_end=2,
        )

        preview = bulk_service.generate_preview(org.id, req)
        assert preview["total_nodes"] == 16  # 2 * 2 * 2 * 2
        assert len(preview["sample_codes"]) == 10
        assert preview["allowed"] is True


class TestSecurityAndApiEndpoints:
    def test_unauthenticated_requests_return_401(self):
        client = TestClient(app)
        res = client.get("/api/logistics/warehouses")
        assert res.status_code == 401

    def test_authenticated_warehouse_list(self, db_session: Session, setup_domain: dict):
        client = TestClient(app)
        org = setup_domain["org"]
        user, auth_headers = authenticate(client, db_session, role="admin")

        role = db_session.scalar(select(LogisticsRole).where(LogisticsRole.code == "ADMIN_LOGISTICA_W22"))
        if not role:
            role = LogisticsRole(id=uuid4(), code="ADMIN_LOGISTICA_W22", name="Admin W22", description="Admin W22", is_system=True, status="active")
            db_session.add(role)
            db_session.flush()

        assignment = db_session.scalar(
            select(LogisticsRoleAssignment).where(
                and_(
                    LogisticsRoleAssignment.user_id == user.id,
                    LogisticsRoleAssignment.role_id == role.id,
                )
            )
        )
        if not assignment:
            assignment = LogisticsRoleAssignment(
                id=uuid4(),
                user_id=user.id,
                role_id=role.id,
                scope_type="ORGANIZATION",
                organization_id=org.id,
                status="active",
                assigned_by=user.id,
            )
            db_session.add(assignment)
            db_session.commit()

        res = client.get("/api/logistics/warehouses", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

