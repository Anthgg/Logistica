"""F005.1 — códigos automáticos, catálogos y geografía derivada.

Cubre lo que la fase corrige: el usuario deja de inventar códigos y de escribir a
mano la ubicación de un almacén, que ahora sale de su sede.
"""

import threading
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.entity_code_counter import EntityCodeCounter
from app.modules.logistics.organization.code_generator import entity_code_generator
from app.modules.logistics.rbac.models_assignment import LogisticsRoleAssignment
from app.modules.logistics.rbac.models_permission import LogisticsPermission
from app.modules.logistics.rbac.models_role import LogisticsRole
from app.modules.logistics.rbac.models_role_permission import LogisticsRolePermission
from tests.support import authenticate

PERMISSIONS = [
    "logistics.organizations.read",
    "logistics.organizations.create",
    "logistics.branches.read",
    "logistics.branches.create",
    "logistics.warehouses.read",
    "logistics.warehouses.create",
]


def _permission(database, code: str) -> LogisticsPermission:
    perm = database.query(LogisticsPermission).filter(LogisticsPermission.code == code).first()
    if perm is None:
        parts = code.split(".")
        perm = LogisticsPermission(
            code=code,
            resource=parts[1] if len(parts) > 1 else code,
            action=parts[-1],
            name=code,
            description=code,
            category="structure",
            requires_step_up=False,
        )
        database.add(perm)
    perm.requires_step_up = False
    database.flush()
    return perm


@pytest.fixture
def actor(client, database):
    user, headers = authenticate(client, database, role="operator")
    role = LogisticsRole(
        code=f"F0051_{uuid4().hex[:8].upper()}",
        name="Rol F005.1",
        description="Rol de prueba",
        role_type="custom",
        is_system=False,
        status="active",
    )
    database.add(role)
    database.flush()
    for code in PERMISSIONS:
        database.add(
            LogisticsRolePermission(role_id=role.id, permission_id=_permission(database, code).id)
        )
    database.add(
        LogisticsRoleAssignment(user_id=user.id, role_id=role.id, scope_type="global")
    )
    database.flush()
    return {"user": user, "headers": headers}


def _org_payload(**overrides) -> dict:
    payload = {"name": "Organización F005.1", "country_code": "PE", "timezone": "America/Lima"}
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Códigos automáticos
# ---------------------------------------------------------------------------

def test_organization_code_is_generated_when_absent(client, actor):
    response = client.post("/api/logistics/organizations", headers=actor["headers"], json=_org_payload())
    assert response.status_code == 201, response.text
    code = response.json()["code"]
    assert code.startswith("ORG")
    assert len(code) == 9 and code[3:].isdigit()


def test_organization_codes_increment(client, actor):
    first = client.post("/api/logistics/organizations", headers=actor["headers"], json=_org_payload())
    second = client.post("/api/logistics/organizations", headers=actor["headers"], json=_org_payload())
    assert first.status_code == 201 and second.status_code == 201
    assert int(second.json()["code"][3:]) == int(first.json()["code"][3:]) + 1


def test_explicit_code_is_still_accepted(client, actor):
    """Compatibilidad: un cliente antiguo que envía código sigue funcionando."""
    response = client.post(
        "/api/logistics/organizations", headers=actor["headers"], json=_org_payload(code="MANUAL01")
    )
    assert response.status_code == 201, response.text
    assert response.json()["code"] == "MANUAL01"


def test_branch_code_is_generated(client, database, actor):
    org = client.post("/api/logistics/organizations", headers=actor["headers"], json=_org_payload())
    response = client.post(
        f"/api/logistics/organizations/{org.json()['id']}/branches",
        headers=actor["headers"],
        json={"name": "Sede sin código", "timezone": "America/Lima"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["code"].startswith("SED")


def test_warehouse_code_is_generated_and_f022_compatible(client, database, actor):
    org = client.post("/api/logistics/organizations", headers=actor["headers"], json=_org_payload())
    branch = client.post(
        f"/api/logistics/organizations/{org.json()['id']}/branches",
        headers=actor["headers"],
        json={"name": "Sede", "timezone": "America/Lima"},
    )
    response = client.post(
        f"/api/logistics/branches/{branch.json()['id']}/warehouses",
        headers=actor["headers"],
        json={"name": "Almacén sin código", "warehouse_type": "general"},
    )
    assert response.status_code == 201, response.text
    code = response.json()["code"]
    # F022 valida los códigos de almacén con ^[A-Z0-9]{2,20}$: un guion lo rompería.
    assert code.startswith("ALM")
    assert code.isalnum() and code.isupper() and 2 <= len(code) <= 20


def test_generated_codes_are_unique_across_entities(client, database, actor):
    org = client.post("/api/logistics/organizations", headers=actor["headers"], json=_org_payload())
    branch = client.post(
        f"/api/logistics/organizations/{org.json()['id']}/branches",
        headers=actor["headers"],
        json={"name": "Sede", "timezone": "America/Lima"},
    )
    warehouse = client.post(
        f"/api/logistics/branches/{branch.json()['id']}/warehouses",
        headers=actor["headers"],
        json={"name": "Almacén", "warehouse_type": "general"},
    )
    codes = {org.json()["code"], branch.json()["code"], warehouse.json()["code"]}
    assert len(codes) == 3


# ---------------------------------------------------------------------------
# Concurrencia — PostgreSQL real, sin simular el bloqueo
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    "sqlite" in str(SessionLocal.kw.get("bind", "")).lower(),
    reason="El bloqueo de fila requiere PostgreSQL.",
)
def test_concurrent_generation_produces_no_duplicates():
    """20 reservas simultáneas del mismo contador deben dar 20 códigos distintos.

    Cada hilo abre su propia sesión y confirma: es el escenario que `COUNT(*) + 1`
    resuelve mal.
    """
    entity_type = f"test_{uuid4().hex[:8]}"
    results: list[str] = []
    errors: list[Exception] = []
    lock = threading.Lock()

    def reserve() -> None:
        session = SessionLocal()
        try:
            code = entity_code_generator.next_code(session, "organization")
            session.commit()
            with lock:
                results.append(code)
        except Exception as exc:  # noqa: BLE001 - el test existe para capturar cualquier fallo del bloqueo
            session.rollback()
            with lock:
                errors.append(exc)
        finally:
            session.close()

    threads = [threading.Thread(target=reserve) for _ in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, f"Errores durante la generación concurrente: {errors[:3]}"
    assert len(results) == 20
    assert len(set(results)) == 20, "Se repitió un código bajo concurrencia"
    del entity_type


# ---------------------------------------------------------------------------
# Catálogos
# ---------------------------------------------------------------------------

def test_country_catalog_returns_iso_codes(client, actor):
    response = client.get("/api/logistics/catalogs/countries", headers=actor["headers"])
    assert response.status_code == 200, response.text
    codes = {item["code"] for item in response.json()}
    assert "PE" in codes
    assert all(len(code) == 2 for code in codes)


def test_timezone_catalog_can_filter_by_country(client, actor):
    response = client.get(
        "/api/logistics/catalogs/timezones?country_code=PE", headers=actor["headers"]
    )
    assert response.status_code == 200, response.text
    codes = {item["code"] for item in response.json()}
    assert "America/Lima" in codes
    assert "America/Santiago" not in codes


def test_warehouse_type_catalog_matches_validator(client, actor):
    response = client.get("/api/logistics/catalogs/warehouse-types", headers=actor["headers"])
    assert response.status_code == 200, response.text
    codes = {item["code"] for item in response.json()}
    assert codes == {"general", "receiving", "dispatch", "quarantine", "returns", "transit"}


def test_catalogs_require_session(client):
    assert client.get("/api/logistics/catalogs/countries").status_code == 401


def test_invalid_country_is_422(client, actor):
    response = client.post(
        "/api/logistics/organizations", headers=actor["headers"], json=_org_payload(country_code="XX")
    )
    assert response.status_code == 422, response.text


def test_invalid_timezone_is_422(client, actor):
    response = client.post(
        "/api/logistics/organizations",
        headers=actor["headers"],
        json=_org_payload(timezone="Marte/Olympus"),
    )
    assert response.status_code == 422, response.text


def test_invalid_warehouse_type_is_422(client, actor):
    org = client.post("/api/logistics/organizations", headers=actor["headers"], json=_org_payload())
    branch = client.post(
        f"/api/logistics/organizations/{org.json()['id']}/branches",
        headers=actor["headers"],
        json={"name": "Sede", "timezone": "America/Lima"},
    )
    response = client.post(
        f"/api/logistics/branches/{branch.json()['id']}/warehouses",
        headers=actor["headers"],
        json={"name": "Almacén", "warehouse_type": "inventado"},
    )
    assert response.status_code == 422, response.text


# ---------------------------------------------------------------------------
# Geografía derivada — el caso crítico de la fase
# ---------------------------------------------------------------------------

def _ensure_district(database, ubigeo: str, district: str, province: str, department: str) -> None:
    """Siembra la jerarquía geográfica que el test necesita.

    El catálogo se carga en la migración, que corre sobre `public`; la suite usa su
    propio esquema, así que aquí llega vacío.
    """
    from app.modules.logistics.geography.models import (
        GeoDepartment,
        GeoDistrict,
        GeoProvince,
    )

    dep_code, prov_code = ubigeo[:2], ubigeo[:4]
    if database.get(GeoDepartment, dep_code) is None:
        database.add(GeoDepartment(code=dep_code, name=department))
        database.flush()
    if database.get(GeoProvince, prov_code) is None:
        database.add(
            GeoProvince(code=prov_code, department_code=dep_code, name=province)
        )
        database.flush()
    if database.get(GeoDistrict, ubigeo) is None:
        database.add(
            GeoDistrict(
                code=ubigeo,
                province_code=prov_code,
                department_code=dep_code,
                name=district,
            )
        )
        database.flush()


def _branch_with_ubigeo(client, database, actor, ubigeo: str):
    known = {
        "150122": ("Miraflores", "Lima", "Lima"),
        "150101": ("Lima", "Lima", "Lima"),
    }
    _ensure_district(database, ubigeo, *known[ubigeo])
    org = client.post("/api/logistics/organizations", headers=actor["headers"], json=_org_payload())
    branch = client.post(
        f"/api/logistics/organizations/{org.json()['id']}/branches",
        headers=actor["headers"],
        json={"name": "Sede Lima", "timezone": "America/Lima", "ubigeo_code": ubigeo},
    )
    assert branch.status_code == 201, branch.text
    return branch.json()


def test_warehouse_inherits_location_from_branch(client, database, actor):
    branch = _branch_with_ubigeo(client, database, actor, "150122")  # Miraflores, Lima, Lima
    response = client.post(
        f"/api/logistics/branches/{branch['id']}/warehouses",
        headers=actor["headers"],
        json={"name": "Almacén heredado", "warehouse_type": "general"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["district"] == "Miraflores"
    assert body["province"] == "Lima"
    assert body["department"] == "Lima"


def test_warehouse_ignores_contradictory_geography(client, database, actor):
    """El caso crítico: una sede en Lima no puede tener un almacén en Arequipa."""
    branch = _branch_with_ubigeo(client, database, actor, "150122")
    response = client.post(
        f"/api/logistics/branches/{branch['id']}/warehouses",
        headers=actor["headers"],
        json={
            "name": "Almacén contradictorio",
            "warehouse_type": "general",
            "department": "Arequipa",
            "province": "Arequipa",
            "district": "Cayma",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    # Lo enviado por el cliente se descarta: manda la sede.
    assert body["department"] == "Lima"
    assert body["district"] == "Miraflores"


def test_warehouse_without_branch_ubigeo_keeps_submitted_text(client, database, actor):
    """Transición: las sedes sin UBIGEO no dejan inoperativa el alta de almacenes."""
    org = client.post("/api/logistics/organizations", headers=actor["headers"], json=_org_payload())
    branch = client.post(
        f"/api/logistics/organizations/{org.json()['id']}/branches",
        headers=actor["headers"],
        json={"name": "Sede sin ubigeo", "timezone": "America/Lima"},
    )
    response = client.post(
        f"/api/logistics/branches/{branch.json()['id']}/warehouses",
        headers=actor["headers"],
        json={
            "name": "Almacén legacy",
            "warehouse_type": "general",
            "department": "Lima",
            "province": "Lima",
            "district": "Ate",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["district"] == "Ate"


def test_warehouse_no_longer_requires_geography(client, database, actor):
    """El formulario ya no pide distrito/provincia/departamento: no son obligatorios."""
    branch = _branch_with_ubigeo(client, database, actor, "150101")
    response = client.post(
        f"/api/logistics/branches/{branch['id']}/warehouses",
        headers=actor["headers"],
        json={"name": "Sin geografía", "warehouse_type": "general"},
    )
    assert response.status_code == 201, response.text


def test_warehouse_address_is_still_its_own(client, database, actor):
    """La dirección del almacén no es la de la sede: se conserva tal cual."""
    branch = _branch_with_ubigeo(client, database, actor, "150122")
    response = client.post(
        f"/api/logistics/branches/{branch['id']}/warehouses",
        headers=actor["headers"],
        json={
            "name": "Almacén con dirección",
            "warehouse_type": "general",
            "address": "Nave B — Puerta 4",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["address"] == "Nave B — Puerta 4"


# ---------------------------------------------------------------------------
# Contador
# ---------------------------------------------------------------------------

def test_counter_row_is_created_on_demand(client, database, actor):
    client.post("/api/logistics/organizations", headers=actor["headers"], json=_org_payload())
    counter = database.scalars(
        select(EntityCodeCounter).where(EntityCodeCounter.entity_type == "organization")
    ).first()
    assert counter is not None
    assert counter.next_value >= 2
