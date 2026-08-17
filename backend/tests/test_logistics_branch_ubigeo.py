"""Tests for Branch location normalization with UBIGEO and coordinate validations."""

from uuid import UUID, uuid4

import pytest

from app.models.branch import Branch
from app.models.organization import Organization
from app.modules.logistics.geography.models import GeoDepartment, GeoDistrict, GeoProvince
from app.modules.logistics.rbac.models_assignment import LogisticsRoleAssignment
from app.modules.logistics.rbac.models_permission import LogisticsPermission
from app.modules.logistics.rbac.models_role import LogisticsRole
from app.modules.logistics.rbac.models_role_permission import LogisticsRolePermission
from tests.support import authenticate

BRANCH_PERMISSIONS = [
    "logistics.organizations.read",
    "logistics.branches.read",
    "logistics.branches.create",
    "logistics.branches.update",
]


def _seed_geo(db):
    if not db.query(GeoDepartment).filter(GeoDepartment.code == "15").first():
        db.add(GeoDepartment(code="15", name="Lima"))
        db.add(GeoProvince(code="1501", department_code="15", name="Lima"))
        db.add(GeoDistrict(code="150122", province_code="1501", department_code="15", name="Miraflores"))
        db.add(GeoDistrict(code="150131", province_code="1501", department_code="15", name="San Isidro"))
    if not db.query(GeoDepartment).filter(GeoDepartment.code == "04").first():
        db.add(GeoDepartment(code="04", name="Arequipa"))
        db.add(GeoProvince(code="0401", department_code="04", name="Arequipa"))
        db.add(GeoDistrict(code="040101", province_code="0401", department_code="04", name="Arequipa"))
    db.flush()


def _setup_scoped_env(client, database):
    _seed_geo(database)
    user, headers = authenticate(client, database)

    # Create org
    org = Organization(
        code=f"GEO-ORG-{uuid4().hex[:6].upper()}",
        name="Org Geo Test",
        country_code="PE",
        timezone="America/Lima",
    )
    database.add(org)
    database.flush()

    # Permissions & role
    role = LogisticsRole(code=f"geo-role-{uuid4().hex[:6]}", name="Geo Role", description="Geo")
    database.add(role)
    database.flush()

    for code in BRANCH_PERMISSIONS:
        perm = database.query(LogisticsPermission).filter(LogisticsPermission.code == code).first()
        if not perm:
            res, act = code.split(".")[1], code.split(".")[-1]
            perm = LogisticsPermission(
                code=code, resource=res, action=act, name=code, description=code,
                category="structure", requires_step_up=False,
            )
            database.add(perm)
            database.flush()
        database.add(LogisticsRolePermission(role_id=role.id, permission_id=perm.id))

    database.add(
        LogisticsRoleAssignment(
            user_id=user.id,
            role_id=role.id,
            scope_type="organization",
            organization_id=org.id,
            status="active",
        )
    )
    database.flush()

    return {"headers": headers, "org": org}


def test_create_branch_with_valid_ubigeo_persists(client, database):
    env = _setup_scoped_env(client, database)
    payload = {
        "code": f"BR-{uuid4().hex[:6].upper()}",
        "name": "Sede Miraflores",
        "timezone": "America/Lima",
        "ubigeo_code": "150122",
        "address_text": "Av. Larco 1234",
        "latitude": -12.1215,
        "longitude": -77.0298,
    }
    response = client.post(
        f"/api/logistics/organizations/{env['org'].id}/branches",
        headers=env["headers"],
        json=payload,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["ubigeo_code"] == "150122"
    assert body["address_text"] == "Av. Larco 1234"
    assert float(body["latitude"]) == pytest.approx(-12.1215)
    assert float(body["longitude"]) == pytest.approx(-77.0298)

    # Check derived ubigeo hierarchy
    assert body["ubigeo"] is not None
    assert body["ubigeo"]["code"] == "150122"
    assert body["ubigeo"]["department_name"] == "Lima"
    assert body["ubigeo"]["province_name"] == "Lima"
    assert body["ubigeo"]["district_name"] == "Miraflores"
    assert body["ubigeo"]["formatted"] == "Miraflores, Lima, Lima"

    # Verify in DB
    database.expire_all()
    row = database.get(Branch, UUID(body["id"]))
    assert row.ubigeo_code == "150122"


def test_create_branch_with_nonexistent_ubigeo_is_422(client, database):
    env = _setup_scoped_env(client, database)
    payload = {
        "code": f"BR-{uuid4().hex[:6].upper()}",
        "name": "Sede Invalida",
        "timezone": "America/Lima",
        "ubigeo_code": "999999",
    }
    response = client.post(
        f"/api/logistics/organizations/{env['org'].id}/branches",
        headers=env["headers"],
        json=payload,
    )
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "UBIGEO_NOT_FOUND"


def test_create_branch_with_malformed_ubigeo_code_is_422(client, database):
    env = _setup_scoped_env(client, database)
    payload = {
        "code": f"BR-{uuid4().hex[:6].upper()}",
        "name": "Sede Malformada",
        "timezone": "America/Lima",
        "ubigeo_code": "1501",  # only 4 chars
    }
    response = client.post(
        f"/api/logistics/organizations/{env['org'].id}/branches",
        headers=env["headers"],
        json=payload,
    )
    assert response.status_code == 422, response.text


def test_update_branch_ubigeo_updates_hierarchy(client, database):
    env = _setup_scoped_env(client, database)
    create_res = client.post(
        f"/api/logistics/organizations/{env['org'].id}/branches",
        headers=env["headers"],
        json={
            "code": f"BR-{uuid4().hex[:6].upper()}",
            "name": "Sede Inicial",
            "timezone": "America/Lima",
            "ubigeo_code": "150122",
        },
    )
    assert create_res.status_code == 201
    branch_id = create_res.json()["id"]

    # Update to Arequipa (040101)
    update_res = client.patch(
        f"/api/logistics/branches/{branch_id}",
        headers=env["headers"],
        json={"ubigeo_code": "040101", "name": "Sede Arequipa"},
    )
    assert update_res.status_code == 200, update_res.text
    body = update_res.json()
    assert body["ubigeo_code"] == "040101"
    assert body["ubigeo"]["department_name"] == "Arequipa"
    assert body["ubigeo"]["district_name"] == "Arequipa"


def test_create_branch_with_invalid_coordinates_is_422(client, database):
    env = _setup_scoped_env(client, database)
    # Latitude > 90
    r1 = client.post(
        f"/api/logistics/organizations/{env['org'].id}/branches",
        headers=env["headers"],
        json={"code": "BADLAT", "name": "Bad Lat", "latitude": 95.0},
    )
    assert r1.status_code == 422

    # Longitude < -180
    r2 = client.post(
        f"/api/logistics/organizations/{env['org'].id}/branches",
        headers=env["headers"],
        json={"code": "BADLNG", "name": "Bad Lng", "longitude": -185.0},
    )
    assert r2.status_code == 422


def test_branch_list_includes_derived_ubigeo(client, database):
    env = _setup_scoped_env(client, database)
    client.post(
        f"/api/logistics/organizations/{env['org'].id}/branches",
        headers=env["headers"],
        json={
            "code": f"BR-{uuid4().hex[:6].upper()}",
            "name": "Sede Con Ubigeo",
            "timezone": "America/Lima",
            "ubigeo_code": "150131",
        },
    )
    list_res = client.get(
        f"/api/logistics/organizations/{env['org'].id}/branches",
        headers=env["headers"],
    )
    assert list_res.status_code == 200, list_res.text
    items = list_res.json()["items"]
    branch_item = next((b for b in items if b["ubigeo_code"] == "150131"), None)
    assert branch_item is not None
    assert branch_item["ubigeo"]["district_name"] == "San Isidro"
    assert branch_item["ubigeo"]["formatted"] == "San Isidro, Lima, Lima"
