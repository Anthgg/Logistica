"""Tests for Peruvian Geography and UBIGEO API endpoints."""

from app.modules.logistics.geography.models import GeoDepartment, GeoDistrict, GeoProvince
from tests.support import authenticate


def _seed_sample_geo(db):
    """Seed sample geography if not already populated."""
    if not db.query(GeoDepartment).filter(GeoDepartment.code == "15").first():
        dept = GeoDepartment(code="15", name="Lima")
        db.add(dept)
        prov = GeoProvince(code="1501", department_code="15", name="Lima")
        db.add(prov)
        dist = GeoDistrict(code="150122", province_code="1501", department_code="15", name="Miraflores")
        db.add(dist)
        dist2 = GeoDistrict(code="150101", province_code="1501", department_code="15", name="Lima")
        db.add(dist2)
        db.flush()


def test_unauthenticated_geography_endpoints_are_401(client):
    r1 = client.get("/api/logistics/geography/departments")
    assert r1.status_code in (401, 403)

    r2 = client.get("/api/logistics/geography/departments/15/provinces")
    assert r2.status_code in (401, 403)

    r3 = client.get("/api/logistics/geography/provinces/1501/districts")
    assert r3.status_code in (401, 403)

    r4 = client.get("/api/logistics/geography/districts/150122")
    assert r4.status_code in (401, 403)


def test_list_departments(client, database):
    _seed_sample_geo(database)
    _, headers = authenticate(client, database)
    response = client.get("/api/logistics/geography/departments", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    codes = [d["code"] for d in data]
    assert "15" in codes


def test_list_provinces_by_department(client, database):
    _seed_sample_geo(database)
    _, headers = authenticate(client, database)
    response = client.get("/api/logistics/geography/departments/15/provinces", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    codes = [p["code"] for p in data]
    assert "1501" in codes
    assert all(p["department_code"] == "15" for p in data)


def test_list_provinces_invalid_department_returns_empty(client, database):
    _, headers = authenticate(client, database)
    response = client.get("/api/logistics/geography/departments/99/provinces", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == []


def test_list_districts_by_province(client, database):
    _seed_sample_geo(database)
    _, headers = authenticate(client, database)
    response = client.get("/api/logistics/geography/provinces/1501/districts", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    codes = [d["code"] for d in data]
    assert "150122" in codes
    assert all(d["province_code"] == "1501" for d in data)


def test_list_districts_invalid_province_returns_empty(client, database):
    _, headers = authenticate(client, database)
    response = client.get("/api/logistics/geography/provinces/9999/districts", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == []


def test_get_district_by_ubigeo_success(client, database):
    _seed_sample_geo(database)
    _, headers = authenticate(client, database)
    response = client.get("/api/logistics/geography/districts/150122", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["code"] == "150122"
    assert body["department_code"] == "15"
    assert body["department_name"] == "Lima"
    assert body["province_code"] == "1501"
    assert body["province_name"] == "Lima"
    assert body["district_name"] == "Miraflores"
    assert body["formatted"] == "Miraflores, Lima, Lima"


def test_get_district_by_invalid_ubigeo_is_404(client, database):
    _, headers = authenticate(client, database)
    response = client.get("/api/logistics/geography/districts/999999", headers=headers)
    assert response.status_code == 404, response.text
    assert response.json()["error"]["code"] in ("UBIGEO_NOT_FOUND", "RESOURCE_NOT_FOUND")
