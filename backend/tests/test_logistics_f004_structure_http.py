"""F004 — regresión HTTP de la estructura organizacional.

Organization -> Branch -> Warehouse, atravesando router y dependencias reales.

Nada aquí sustituye ``require_permission`` ni ``get_logistics_principal``: los
principals se construyen sembrando RBAC de verdad (permiso, rol, asignación con
ámbito) para que un fallo en el enforcement se note.
"""

from uuid import UUID, uuid4

import pytest

from app.models.branch import Branch
from app.models.organization import Organization
from app.models.warehouse import Warehouse
from app.modules.logistics.rbac.models_assignment import LogisticsRoleAssignment
from app.modules.logistics.rbac.models_permission import LogisticsPermission
from app.modules.logistics.rbac.models_role import LogisticsRole
from app.modules.logistics.rbac.models_role_permission import LogisticsRolePermission
from tests.support import authenticate

F004_PERMISSIONS = [
    "logistics.organizations.read",
    "logistics.organizations.create",
    "logistics.organizations.update",
    "logistics.organizations.change_status",
    "logistics.branches.read",
    "logistics.branches.create",
    "logistics.branches.update",
    "logistics.branches.change_status",
    "logistics.warehouses.read",
    "logistics.warehouses.create",
    "logistics.warehouses.change_status",
    "logistics.warehouses.set_default",
]


# ---------------------------------------------------------------------------
# Andamiaje: RBAC real, no simulado
# ---------------------------------------------------------------------------

def _permission(
    database, code: str, *, requires_step_up: bool | None = None
) -> LogisticsPermission:
    """Permiso del catálogo, creado si falta.

    `requires_step_up` se fija explícitamente cuando el test depende de él: la base
    de CI arranca con `logistics_permissions` vacía y la de desarrollo con el
    catálogo sembrado, así que dar por supuesto el valor hace que el mismo test
    responda 403 en un sitio y 409 en el otro.
    """
    perm = database.query(LogisticsPermission).filter(LogisticsPermission.code == code).first()
    if perm is None:
        resource, action = code.split(".")[1], code.split(".")[-1]
        perm = LogisticsPermission(
            code=code,
            resource=resource,
            action=action,
            name=code,
            description=code,
            category="structure",
            requires_step_up=False,
        )
        database.add(perm)
    if requires_step_up is not None:
        perm.requires_step_up = requires_step_up
    database.flush()
    return perm


def _role_with(database, codes: list[str]) -> LogisticsRole:
    role = LogisticsRole(
        code=f"f004-role-{uuid4().hex[:8]}",
        name="Rol F004 de prueba",
        description="Rol sembrado por la suite F004",
    )
    database.add(role)
    database.flush()
    for code in codes:
        database.add(
            LogisticsRolePermission(role_id=role.id, permission_id=_permission(database, code).id)
        )
    database.flush()
    return role


def _organization(database, code: str | None = None) -> Organization:
    org = Organization(
        code=code or f"F004-{uuid4().hex[:8].upper()}",
        name="Organización F004",
        country_code="PE",
        timezone="America/Lima",
    )
    database.add(org)
    database.flush()
    return org


def _branch(database, organization: Organization, code: str | None = None) -> Branch:
    branch = Branch(
        organization_id=organization.id,
        code=code or f"S{uuid4().hex[:6].upper()}",
        name="Sede F004",
        timezone="America/Lima",
    )
    database.add(branch)
    database.flush()
    return branch


def _grant(database, user, role: LogisticsRole, organization: Organization) -> None:
    database.add(
        LogisticsRoleAssignment(
            user_id=user.id,
            role_id=role.id,
            scope_type="organization",
            organization_id=organization.id,
        )
    )
    database.flush()


@pytest.fixture
def scoped(client, database):
    """Usuario NO administrador con todos los permisos F004 sobre UNA organización.

    Se acompaña de una segunda organización ajena para poder comprobar el
    aislamiento por tenant sin inventar identificadores.
    """
    user, headers = authenticate(client, database, role="operator")
    own = _organization(database)
    foreign = _organization(database)
    _grant(database, user, _role_with(database, F004_PERMISSIONS), own)
    return {
        "user": user,
        "headers": headers,
        "own": own,
        "foreign": foreign,
        "own_branch": _branch(database, own),
        "foreign_branch": _branch(database, foreign),
    }


def _warehouse_payload(code: str | None = None) -> dict:
    """Cuerpo exacto que envía el formulario: sin `branch_id`, que va en la ruta."""
    return {
        "code": code or f"WH{uuid4().hex[:8].upper()}",
        "name": "Almacén F004",
        "warehouse_type": "general",
        "address": "Av. Estructura 100",
        "district": "Ate",
        "province": "Lima",
        "department": "Lima",
    }


# ---------------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "path",
    [
        "/api/logistics/organizations",
        "/api/logistics/organizations/00000000-0000-0000-0000-000000000001",
        "/api/logistics/organizations/00000000-0000-0000-0000-000000000001/branches",
        "/api/logistics/branches/00000000-0000-0000-0000-000000000001",
        "/api/logistics/branches/00000000-0000-0000-0000-000000000001/warehouses",
    ],
)
def test_unauthenticated_is_401(client, path):
    assert client.get(path).status_code == 401


# ---------------------------------------------------------------------------
# Permisos: el catálogo existente se aplica de verdad
# ---------------------------------------------------------------------------

def test_organization_list_without_permission_is_403(client, database):
    _, headers = authenticate(client, database, role="operator")
    response = client.get("/api/logistics/organizations", headers=headers)
    assert response.status_code == 403, response.text


def test_organization_update_without_permission_is_403(client, database):
    user, headers = authenticate(client, database, role="operator")
    org = _organization(database)
    _grant(database, user, _role_with(database, ["logistics.organizations.read"]), org)
    response = client.patch(
        f"/api/logistics/organizations/{org.id}",
        headers=headers,
        json={"name": "No debería pasar"},
    )
    assert response.status_code == 403, response.text


def test_branch_create_without_permission_is_403(client, database):
    user, headers = authenticate(client, database, role="operator")
    org = _organization(database)
    _grant(database, user, _role_with(database, ["logistics.branches.read"]), org)
    response = client.post(
        f"/api/logistics/organizations/{org.id}/branches",
        headers=headers,
        json={"code": "SED1", "name": "Sede", "timezone": "America/Lima"},
    )
    assert response.status_code == 403, response.text


# ---------------------------------------------------------------------------
# Organización
# ---------------------------------------------------------------------------

def test_organization_list_only_returns_allowed_scope(client, scoped):
    response = client.get("/api/logistics/organizations", headers=scoped["headers"])
    assert response.status_code == 200, response.text
    body = response.json()
    returned = {item["id"] for item in body["items"]}
    assert str(scoped["own"].id) in returned
    assert str(scoped["foreign"].id) not in returned


def test_organization_list_is_paginated_envelope(client, scoped):
    body = client.get("/api/logistics/organizations", headers=scoped["headers"]).json()
    assert set(body) >= {"items", "page", "page_size", "total", "total_pages"}
    assert isinstance(body["items"], list)


def test_organization_detail_allowed(client, scoped):
    response = client.get(
        f"/api/logistics/organizations/{scoped['own'].id}", headers=scoped["headers"]
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(scoped["own"].id)


def test_organization_detail_foreign_is_403(client, scoped):
    response = client.get(
        f"/api/logistics/organizations/{scoped['foreign'].id}", headers=scoped["headers"]
    )
    assert response.status_code == 403, response.text


def test_organization_update_persists(client, database, scoped):
    response = client.patch(
        f"/api/logistics/organizations/{scoped['own'].id}",
        headers=scoped["headers"],
        json={"name": "Organización Renombrada F004"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Organización Renombrada F004"
    database.expire_all()
    assert database.get(Organization, scoped["own"].id).name == "Organización Renombrada F004"


def test_organization_update_foreign_is_403(client, scoped):
    response = client.patch(
        f"/api/logistics/organizations/{scoped['foreign'].id}",
        headers=scoped["headers"],
        json={"name": "Ajena"},
    )
    assert response.status_code == 403, response.text


def test_organization_status_change_requires_step_up_when_catalog_demands_it(
    client, database, scoped
):
    """En el catálogo real `logistics.organizations.change_status` es critical con
    ``requires_step_up = true``. Tener el permiso no basta: sin prueba de verificación
    reforzada la respuesta es 403 STEP_UP_REQUIRED.

    F004 no relaja esa política; el catálogo pertenece a F006. El test fija el flag
    en vez de suponerlo, para que valga igual en CI y en desarrollo.
    """
    _permission(database, "logistics.organizations.change_status", requires_step_up=True)
    response = client.patch(
        f"/api/logistics/organizations/{scoped['own'].id}/status",
        headers=scoped["headers"],
        json={"status": "inactive"},
    )
    assert response.status_code == 403, response.text
    assert response.json()["error"]["code"] == "STEP_UP_REQUIRED"


def test_organization_status_change_persists_without_step_up(client, database, scoped):
    """Sin step-up y sin sedes activas, el cambio de estado llega hasta la fila."""
    _permission(database, "logistics.organizations.change_status", requires_step_up=False)
    org = _organization(database)
    _grant(database, scoped["user"], _role_with(database, F004_PERMISSIONS), org)
    response = client.patch(
        f"/api/logistics/organizations/{org.id}/status",
        headers=scoped["headers"],
        json={"status": "inactive"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "inactive"
    database.expire_all()
    assert database.get(Organization, org.id).status == "inactive"


def test_organization_status_change_with_active_branches_is_409(client, database, scoped):
    """La organización de `scoped` tiene una sede activa: desactivarla es un conflicto."""
    _permission(database, "logistics.organizations.change_status", requires_step_up=False)
    response = client.patch(
        f"/api/logistics/organizations/{scoped['own'].id}/status",
        headers=scoped["headers"],
        json={"status": "inactive"},
    )
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "ORGANIZATION_INACTIVE_CONFLICT"


def test_organization_status_foreign_is_403(client, scoped):
    response = client.patch(
        f"/api/logistics/organizations/{scoped['foreign'].id}/status",
        headers=scoped["headers"],
        json={"status": "inactive"},
    )
    assert response.status_code == 403, response.text
    assert response.status_code != 500


def test_organization_nonexistent_is_404(client, scoped):
    response = client.get(
        f"/api/logistics/organizations/{uuid4()}", headers=scoped["headers"]
    )
    assert response.status_code in (403, 404)
    assert response.status_code != 500


# ---------------------------------------------------------------------------
# Sede
# ---------------------------------------------------------------------------

def test_branch_list_allowed(client, scoped):
    response = client.get(
        f"/api/logistics/organizations/{scoped['own'].id}/branches",
        headers=scoped["headers"],
    )
    assert response.status_code == 200, response.text
    assert str(scoped["own_branch"].id) in {i["id"] for i in response.json()["items"]}


def test_branch_list_foreign_org_is_403(client, scoped):
    response = client.get(
        f"/api/logistics/organizations/{scoped['foreign'].id}/branches",
        headers=scoped["headers"],
    )
    assert response.status_code == 403, response.text


def test_branch_create_persists(client, database, scoped):
    response = client.post(
        f"/api/logistics/organizations/{scoped['own'].id}/branches",
        headers=scoped["headers"],
        json={
            "code": "UATSEDE",
            "name": "Sede creada por HTTP",
            "timezone": "America/Lima",
            "address_text": "Av. Sede 200",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["organization_id"] == str(scoped["own"].id)
    assert body["status"] == "active"
    assert database.get(Branch, UUID(body["id"])) is not None


def test_branch_create_duplicate_code_is_409(client, scoped):
    payload = {"code": "DUPSEDE", "name": "Sede", "timezone": "America/Lima"}
    first = client.post(
        f"/api/logistics/organizations/{scoped['own'].id}/branches",
        headers=scoped["headers"],
        json=payload,
    )
    assert first.status_code == 201, first.text
    second = client.post(
        f"/api/logistics/organizations/{scoped['own'].id}/branches",
        headers=scoped["headers"],
        json=payload,
    )
    assert second.status_code == 409, second.text


def test_branch_create_missing_required_field_is_422(client, scoped):
    response = client.post(
        f"/api/logistics/organizations/{scoped['own'].id}/branches",
        headers=scoped["headers"],
        json={"name": "Sin código"},
    )
    assert response.status_code == 422, response.text


def test_branch_create_foreign_org_is_403(client, scoped):
    response = client.post(
        f"/api/logistics/organizations/{scoped['foreign'].id}/branches",
        headers=scoped["headers"],
        json={"code": "AJENA", "name": "Sede ajena", "timezone": "America/Lima"},
    )
    assert response.status_code == 403, response.text


def test_branch_update_persists(client, database, scoped):
    response = client.patch(
        f"/api/logistics/branches/{scoped['own_branch'].id}",
        headers=scoped["headers"],
        json={"name": "Sede Renombrada"},
    )
    assert response.status_code == 200, response.text
    database.expire_all()
    assert database.get(Branch, scoped["own_branch"].id).name == "Sede Renombrada"


def test_branch_detail_foreign_is_403(client, scoped):
    response = client.get(
        f"/api/logistics/branches/{scoped['foreign_branch'].id}", headers=scoped["headers"]
    )
    assert response.status_code == 403, response.text


def test_branch_deactivate_persists(client, database, scoped):
    response = client.patch(
        f"/api/logistics/branches/{scoped['own_branch'].id}/status",
        headers=scoped["headers"],
        json={"status": "inactive"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "inactive"
    database.expire_all()
    assert database.get(Branch, scoped["own_branch"].id).status == "inactive"


def test_branch_reactivate_persists(client, database, scoped):
    branch_id = scoped["own_branch"].id
    client.patch(
        f"/api/logistics/branches/{branch_id}/status",
        headers=scoped["headers"],
        json={"status": "inactive"},
    )
    response = client.patch(
        f"/api/logistics/branches/{branch_id}/status",
        headers=scoped["headers"],
        json={"status": "active"},
    )
    assert response.status_code == 200, response.text
    database.expire_all()
    assert database.get(Branch, branch_id).status == "active"


def test_branch_deactivate_foreign_is_403(client, scoped):
    response = client.patch(
        f"/api/logistics/branches/{scoped['foreign_branch'].id}/status",
        headers=scoped["headers"],
        json={"status": "inactive"},
    )
    assert response.status_code == 403, response.text


def test_branch_deactivate_with_active_warehouse_is_409(client, scoped):
    created = client.post(
        f"/api/logistics/branches/{scoped['own_branch'].id}/warehouses",
        headers=scoped["headers"],
        json=_warehouse_payload(),
    )
    assert created.status_code == 201, created.text
    response = client.patch(
        f"/api/logistics/branches/{scoped['own_branch'].id}/status",
        headers=scoped["headers"],
        json={"status": "inactive"},
    )
    assert response.status_code == 409, response.text


# ---------------------------------------------------------------------------
# Almacén estructural
# ---------------------------------------------------------------------------

def test_warehouse_create_derives_organization_from_branch(client, database, scoped):
    response = client.post(
        f"/api/logistics/branches/{scoped['own_branch'].id}/warehouses",
        headers=scoped["headers"],
        json=_warehouse_payload("UATF004WH"),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    # El invariante que hacía invisibles a los almacenes: la organización se deriva
    # de la sede, nunca del cliente.
    assert body["organization_id"] == str(scoped["own"].id)
    assert body["branch_id"] == str(scoped["own_branch"].id)
    row = database.get(Warehouse, UUID(body["id"]))
    assert row.organization_id == scoped["own"].id
    assert row.branch_id == scoped["own_branch"].id


def test_warehouse_create_ignores_client_supplied_scope(client, database, scoped):
    """Ni `organization_id` ni `branch_id` del cuerpo mandan sobre la ruta."""
    payload = _warehouse_payload()
    payload["organization_id"] = str(scoped["foreign"].id)
    payload["branch_id"] = str(scoped["foreign_branch"].id)
    response = client.post(
        f"/api/logistics/branches/{scoped['own_branch'].id}/warehouses",
        headers=scoped["headers"],
        json=payload,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["organization_id"] == str(scoped["own"].id)
    assert body["branch_id"] == str(scoped["own_branch"].id)


def test_warehouse_create_without_branch_id_in_body_succeeds(client, scoped):
    """Regresión del 422 que encontró el navegador.

    El formulario no envía `branch_id` porque la sede va en la ruta. El esquema lo
    exigía igualmente y devolvía 422 a la única petición que la UI sabe construir.
    """
    payload = _warehouse_payload("NOBRANCHID")
    assert "branch_id" not in payload
    response = client.post(
        f"/api/logistics/branches/{scoped['own_branch'].id}/warehouses",
        headers=scoped["headers"],
        json=payload,
    )
    assert response.status_code == 201, response.text


def test_warehouse_create_foreign_branch_is_403(client, scoped):
    response = client.post(
        f"/api/logistics/branches/{scoped['foreign_branch'].id}/warehouses",
        headers=scoped["headers"],
        json=_warehouse_payload(),
    )
    assert response.status_code == 403, response.text


def test_warehouse_create_duplicate_code_is_409(client, scoped):
    payload = _warehouse_payload("DUPWH004")
    first = client.post(
        f"/api/logistics/branches/{scoped['own_branch'].id}/warehouses",
        headers=scoped["headers"],
        json=payload,
    )
    assert first.status_code == 201, first.text
    second = client.post(
        f"/api/logistics/branches/{scoped['own_branch'].id}/warehouses",
        headers=scoped["headers"],
        json=payload,
    )
    assert second.status_code == 409, second.text


def test_warehouse_create_missing_required_field_is_422(client, scoped):
    response = client.post(
        f"/api/logistics/branches/{scoped['own_branch'].id}/warehouses",
        headers=scoped["headers"],
        json={"code": "SOLOCODE"},
    )
    assert response.status_code == 422, response.text


def test_warehouse_create_invalid_type_is_422(client, scoped):
    payload = _warehouse_payload()
    payload["warehouse_type"] = "no-existe"
    response = client.post(
        f"/api/logistics/branches/{scoped['own_branch'].id}/warehouses",
        headers=scoped["headers"],
        json=payload,
    )
    assert response.status_code == 422, response.text


def test_warehouse_create_under_inactive_branch_is_409(client, scoped):
    client.patch(
        f"/api/logistics/branches/{scoped['own_branch'].id}/status",
        headers=scoped["headers"],
        json={"status": "inactive"},
    )
    response = client.post(
        f"/api/logistics/branches/{scoped['own_branch'].id}/warehouses",
        headers=scoped["headers"],
        json=_warehouse_payload(),
    )
    assert response.status_code == 409, response.text


def test_warehouse_list_by_branch_is_paginated_and_contains_created(client, scoped):
    created = client.post(
        f"/api/logistics/branches/{scoped['own_branch'].id}/warehouses",
        headers=scoped["headers"],
        json=_warehouse_payload("LISTWH004"),
    )
    assert created.status_code == 201, created.text
    response = client.get(
        f"/api/logistics/branches/{scoped['own_branch'].id}/warehouses",
        headers=scoped["headers"],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) >= {"items", "page", "page_size", "total", "total_pages"}
    assert created.json()["id"] in {i["id"] for i in body["items"]}


def test_warehouse_list_foreign_branch_is_403(client, scoped):
    response = client.get(
        f"/api/logistics/branches/{scoped['foreign_branch'].id}/warehouses",
        headers=scoped["headers"],
    )
    assert response.status_code == 403, response.text


def test_warehouse_detail_returns_structural_dto(client, scoped):
    created = client.post(
        f"/api/logistics/branches/{scoped['own_branch'].id}/warehouses",
        headers=scoped["headers"],
        json=_warehouse_payload("DETWH004"),
    )
    assert created.status_code == 201, created.text
    warehouse_id = created.json()["id"]
    response = client.get(
        f"/api/logistics/branches/{scoped['own_branch'].id}/warehouses/{warehouse_id}",
        headers=scoped["headers"],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) >= {
        "id", "organization_id", "branch_id", "code", "name", "warehouse_type",
        "address", "district", "province", "department", "capacity",
        "is_default", "is_active", "created_at", "updated_at",
    }
    assert body["organization_id"] == str(scoped["own"].id)


def test_warehouse_detail_foreign_branch_is_403(client, scoped):
    response = client.get(
        f"/api/logistics/branches/{scoped['foreign_branch'].id}/warehouses/{uuid4()}",
        headers=scoped["headers"],
    )
    assert response.status_code == 403, response.text


def test_warehouse_detail_of_other_branch_is_400(client, scoped):
    created = client.post(
        f"/api/logistics/branches/{scoped['own_branch'].id}/warehouses",
        headers=scoped["headers"],
        json=_warehouse_payload("XBRWH004"),
    )
    assert created.status_code == 201, created.text
    # Misma organización, sede distinta: el almacén no pertenece a esa sede.
    second_branch = client.post(
        f"/api/logistics/organizations/{scoped['own'].id}/branches",
        headers=scoped["headers"],
        json={"code": "SEDE2", "name": "Segunda sede", "timezone": "America/Lima"},
    )
    assert second_branch.status_code == 201, second_branch.text
    response = client.get(
        f"/api/logistics/branches/{second_branch.json()['id']}/warehouses/{created.json()['id']}",
        headers=scoped["headers"],
    )
    assert response.status_code == 400, response.text


def test_warehouse_status_keeps_status_and_is_active_consistent(client, database, scoped):
    created = client.post(
        f"/api/logistics/branches/{scoped['own_branch'].id}/warehouses",
        headers=scoped["headers"],
        json=_warehouse_payload("STWH004"),
    )
    assert created.status_code == 201, created.text
    warehouse_id = created.json()["id"]
    response = client.patch(
        f"/api/logistics/warehouses/{warehouse_id}/status",
        headers=scoped["headers"],
        json={"status": "inactive"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["is_active"] is False
    database.expire_all()
    row = database.get(Warehouse, UUID(warehouse_id))
    assert row.is_active is False
    assert row.status == "INACTIVE"


def test_warehouse_status_foreign_is_403(client, database, scoped):
    foreign_wh = Warehouse(
        organization_id=scoped["foreign"].id,
        branch_id=scoped["foreign_branch"].id,
        code=f"FGN{uuid4().hex[:8].upper()}",
        name="Almacén ajeno",
        warehouse_type="general",
    )
    database.add(foreign_wh)
    database.flush()
    response = client.patch(
        f"/api/logistics/warehouses/{foreign_wh.id}/status",
        headers=scoped["headers"],
        json={"status": "inactive"},
    )
    assert response.status_code == 403, response.text


# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------

def test_mutation_without_csrf_header_is_rejected(client, scoped):
    response = client.patch(
        f"/api/logistics/organizations/{scoped['own'].id}",
        json={"name": "Sin CSRF"},
    )
    assert response.status_code in (401, 403), response.text
    assert response.status_code != 500
