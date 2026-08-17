"""F005 — regresión HTTP de administración de roles logísticos.

Cubre el gap real de la fase: crear, editar y activar/desactivar roles
personalizados, componer sus permisos, la matriz y la separación de funciones.

El RBAC se siembra de verdad (permiso -> rol -> asignación con ámbito): nada aquí
sustituye `require_permission` ni `get_logistics_principal`, así que un fallo en el
enforcement se nota.
"""

from uuid import uuid4

import pytest

from app.modules.logistics.rbac.models_conflict import LogisticsRoleConflictRule
from app.modules.logistics.rbac.models_permission import LogisticsPermission
from app.modules.logistics.rbac.models_role import LogisticsRole
from app.modules.logistics.rbac.models_role_permission import LogisticsRolePermission
from app.modules.logistics.rbac.models_assignment import LogisticsRoleAssignment
from tests.support import authenticate

ROLE_ADMIN_PERMISSIONS = [
    "logistics.roles.read",
    "logistics.role_permissions.read",
    "logistics.role_permissions.update",
]


# ---------------------------------------------------------------------------
# Andamiaje RBAC real
# ---------------------------------------------------------------------------

def _permission(database, code: str, *, requires_step_up: bool = False) -> LogisticsPermission:
    perm = database.query(LogisticsPermission).filter(LogisticsPermission.code == code).first()
    if perm is None:
        parts = code.split(".")
        perm = LogisticsPermission(
            code=code,
            resource=parts[1] if len(parts) > 1 else code,
            action=parts[-1],
            name=code,
            description=code,
            category="rbac",
        )
        database.add(perm)
    # Se fija explícitamente: la base de CI arranca sin catálogo y la de desarrollo
    # con él sembrado, así que suponerlo hace que el mismo test responda distinto.
    perm.requires_step_up = requires_step_up
    database.flush()
    return perm


def _role(database, code: str, *, is_system: bool = False, permissions: list[str] | None = None) -> LogisticsRole:
    role = LogisticsRole(
        code=code,
        name=f"Rol {code}",
        description="Rol de prueba F005",
        role_type="system" if is_system else "custom",
        is_system=is_system,
        status="active",
    )
    database.add(role)
    database.flush()
    for perm_code in permissions or []:
        database.add(
            LogisticsRolePermission(role_id=role.id, permission_id=_permission(database, perm_code).id)
        )
    database.flush()
    return role


def _grant(database, user, permissions: list[str]) -> LogisticsRole:
    """Da al usuario un rol con esos permisos, mediante asignación real."""
    role = _role(database, f"GRANT_{uuid4().hex[:8].upper()}", permissions=permissions)
    database.add(
        LogisticsRoleAssignment(user_id=user.id, role_id=role.id, scope_type="global")
    )
    database.flush()
    return role


@pytest.fixture
def admin(client, database):
    """Actor NO administrador de plataforma con los permisos de administración RBAC."""
    user, headers = authenticate(client, database, role="operator")
    _grant(database, user, ROLE_ADMIN_PERMISSIONS)
    return {"user": user, "headers": headers}


def _payload(code: str | None = None, permissions: list[str] | None = None) -> dict:
    return {
        "code": code or f"SUP{uuid4().hex[:6].upper()}",
        "name": "Supervisor de prueba",
        "description": "Rol creado por la suite F005",
        "permission_codes": permissions if permissions is not None else ROLE_ADMIN_PERMISSIONS,
    }


# ---------------------------------------------------------------------------
# Autenticación y autorización
# ---------------------------------------------------------------------------

def test_create_role_unauthenticated_is_401(client):
    assert client.post("/api/logistics/roles", json=_payload()).status_code == 401


def test_matrix_unauthenticated_is_401(client):
    assert client.get("/api/logistics/roles-matrix").status_code == 401


def test_create_role_without_permission_is_403(client, database):
    _, headers = authenticate(client, database, role="operator")
    response = client.post("/api/logistics/roles", headers=headers, json=_payload())
    assert response.status_code == 403, response.text


def test_update_role_without_permission_is_403(client, database, admin):
    created = client.post("/api/logistics/roles", headers=admin["headers"], json=_payload())
    assert created.status_code == 201, created.text
    _, other_headers = authenticate(client, database, role="operator")
    response = client.patch(
        f"/api/logistics/roles/{created.json()['id']}",
        headers=other_headers,
        json={"name": "Renombrado sin permiso"},
    )
    assert response.status_code == 403, response.text


# ---------------------------------------------------------------------------
# CRUD de roles personalizados
# ---------------------------------------------------------------------------

def test_create_custom_role_persists(client, database, admin):
    response = client.post("/api/logistics/roles", headers=admin["headers"], json=_payload("RECEIVSUP"))
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["code"] == "LOGISTICS_CUSTOM_RECEIVSUP"
    # Un rol creado por la API nunca es del sistema.
    assert body["is_system"] is False
    assert body["role_type"] == "custom"
    assert body["status"] == "active"
    assert database.get(LogisticsRole, body["id"]) is not None


def test_create_role_ignores_client_supplied_is_system(client, admin):
    payload = _payload()
    payload["is_system"] = True
    payload["role_type"] = "system"
    response = client.post("/api/logistics/roles", headers=admin["headers"], json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["is_system"] is False


def test_create_role_duplicate_code_is_409(client, admin):
    payload = _payload("DUPLICADO")
    assert client.post("/api/logistics/roles", headers=admin["headers"], json=payload).status_code == 201
    second = client.post("/api/logistics/roles", headers=admin["headers"], json=payload)
    assert second.status_code == 409, second.text
    assert second.json()["error"]["code"] == "ROLE_CODE_ALREADY_EXISTS"


def test_create_role_with_unknown_permission_is_422(client, admin):
    payload = _payload(permissions=["logistics.no.existe"])
    response = client.post("/api/logistics/roles", headers=admin["headers"], json=payload)
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "PERMISSION_NOT_FOUND"


def test_create_role_missing_name_is_422(client, admin):
    response = client.post("/api/logistics/roles", headers=admin["headers"], json={"code": "SINNOMBRE"})
    assert response.status_code == 422, response.text


def test_update_custom_role_persists(client, database, admin):
    created = client.post("/api/logistics/roles", headers=admin["headers"], json=_payload())
    role_id = created.json()["id"]
    response = client.patch(
        f"/api/logistics/roles/{role_id}", headers=admin["headers"], json={"name": "Nombre nuevo"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Nombre nuevo"
    database.expire_all()
    assert database.get(LogisticsRole, role_id).name == "Nombre nuevo"


def test_update_does_not_change_code(client, database, admin):
    created = client.post("/api/logistics/roles", headers=admin["headers"], json=_payload("ESTABLE"))
    role_id = created.json()["id"]
    original = created.json()["code"]
    response = client.patch(
        f"/api/logistics/roles/{role_id}",
        headers=admin["headers"],
        json={"name": "Otro", "code": "SECUESTRADO"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["code"] == original


def test_deactivate_and_reactivate_custom_role(client, database, admin):
    created = client.post("/api/logistics/roles", headers=admin["headers"], json=_payload())
    role_id = created.json()["id"]

    off = client.patch(
        f"/api/logistics/roles/{role_id}/status", headers=admin["headers"], json={"status": "inactive"}
    )
    assert off.status_code == 200, off.text
    assert off.json()["status"] == "inactive"

    on = client.patch(
        f"/api/logistics/roles/{role_id}/status", headers=admin["headers"], json={"status": "active"}
    )
    assert on.status_code == 200, on.text
    database.expire_all()
    assert database.get(LogisticsRole, role_id).status == "active"


def test_role_not_found_is_404(client, admin):
    response = client.patch(
        f"/api/logistics/roles/{uuid4()}",
        headers=admin["headers"],
        json={"name": "Nombre válido"},
    )
    assert response.status_code == 404, response.text


# ---------------------------------------------------------------------------
# Protección de roles del sistema
# ---------------------------------------------------------------------------

def test_system_role_cannot_be_updated(client, database, admin):
    system_role = _role(database, f"SYS_{uuid4().hex[:6].upper()}", is_system=True)
    response = client.patch(
        f"/api/logistics/roles/{system_role.id}", headers=admin["headers"], json={"name": "Intento"}
    )
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "ROLE_IS_SYSTEM"


def test_system_role_cannot_be_deactivated(client, database, admin):
    system_role = _role(database, f"SYS_{uuid4().hex[:6].upper()}", is_system=True)
    response = client.patch(
        f"/api/logistics/roles/{system_role.id}/status",
        headers=admin["headers"],
        json={"status": "inactive"},
    )
    assert response.status_code == 409, response.text


def test_system_role_permissions_cannot_be_replaced(client, database, admin):
    system_role = _role(database, f"SYS_{uuid4().hex[:6].upper()}", is_system=True)
    response = client.put(
        f"/api/logistics/roles/{system_role.id}/permissions",
        headers=admin["headers"],
        json={"permission_codes": ROLE_ADMIN_PERMISSIONS},
    )
    assert response.status_code == 409, response.text


# ---------------------------------------------------------------------------
# Composición de permisos
# ---------------------------------------------------------------------------

def test_replace_permissions_is_atomic_and_persists(client, database, admin):
    created = client.post("/api/logistics/roles", headers=admin["headers"], json=_payload(permissions=[]))
    role_id = created.json()["id"]

    response = client.put(
        f"/api/logistics/roles/{role_id}/permissions",
        headers=admin["headers"],
        json={"permission_codes": ROLE_ADMIN_PERMISSIONS},
    )
    assert response.status_code == 200, response.text
    assert sorted(response.json()) == sorted(ROLE_ADMIN_PERMISSIONS)
    stored = (
        database.query(LogisticsRolePermission)
        .filter(LogisticsRolePermission.role_id == role_id)
        .count()
    )
    assert stored == len(ROLE_ADMIN_PERMISSIONS)


def test_replace_permissions_rolls_back_on_unknown_permission(client, database, admin):
    created = client.post("/api/logistics/roles", headers=admin["headers"], json=_payload())
    role_id = created.json()["id"]
    before = (
        database.query(LogisticsRolePermission)
        .filter(LogisticsRolePermission.role_id == role_id)
        .count()
    )

    response = client.put(
        f"/api/logistics/roles/{role_id}/permissions",
        headers=admin["headers"],
        json={"permission_codes": ROLE_ADMIN_PERMISSIONS + ["logistics.no.existe"]},
    )
    assert response.status_code == 422, response.text
    database.expire_all()
    after = (
        database.query(LogisticsRolePermission)
        .filter(LogisticsRolePermission.role_id == role_id)
        .count()
    )
    # Ni una fila tocada: un rol a medio actualizar es peor que uno sin actualizar.
    assert after == before


def test_replace_permissions_with_empty_list_clears_them(client, database, admin):
    created = client.post("/api/logistics/roles", headers=admin["headers"], json=_payload())
    role_id = created.json()["id"]
    response = client.put(
        f"/api/logistics/roles/{role_id}/permissions",
        headers=admin["headers"],
        json={"permission_codes": []},
    )
    assert response.status_code == 200, response.text
    assert response.json() == []


# ---------------------------------------------------------------------------
# Escalación de privilegios
# ---------------------------------------------------------------------------

def test_cannot_grant_permission_the_actor_lacks(client, database, admin):
    _permission(database, "logistics.documents.cancel")
    response = client.post(
        "/api/logistics/roles",
        headers=admin["headers"],
        json=_payload(permissions=ROLE_ADMIN_PERMISSIONS + ["logistics.documents.cancel"]),
    )
    assert response.status_code == 403, response.text
    assert response.json()["error"]["code"] == "PRIVILEGE_ESCALATION_DENIED"


def test_cannot_escalate_through_permission_replacement(client, database, admin):
    _permission(database, "logistics.audit.read_sensitive")
    created = client.post("/api/logistics/roles", headers=admin["headers"], json=_payload())
    response = client.put(
        f"/api/logistics/roles/{created.json()['id']}/permissions",
        headers=admin["headers"],
        json={"permission_codes": ["logistics.audit.read_sensitive"]},
    )
    assert response.status_code == 403, response.text


# ---------------------------------------------------------------------------
# Separación de funciones
# ---------------------------------------------------------------------------

def _sod_pair(database):
    """Dos roles enfrentados con permisos exclusivos a cada lado."""
    shared = "logistics.roles.read"
    originate = "logistics.f005test.originate"
    approve = "logistics.f005test.approve"
    role_a = _role(database, f"ORIG_{uuid4().hex[:6].upper()}", permissions=[shared, originate])
    role_b = _role(database, f"APPR_{uuid4().hex[:6].upper()}", permissions=[shared, approve])
    database.add(
        LogisticsRoleConflictRule(
            role_a_id=role_a.id,
            role_b_id=role_b.id,
            conflict_type="originate_approve",
            description="Quien origina no puede aprobar.",
            status="active",
        )
    )
    database.flush()
    return originate, approve, shared


def test_composition_without_conflict_is_accepted(client, database, admin):
    originate, _approve, shared = _sod_pair(database)
    _grant(database, admin["user"], [originate, shared])
    response = client.post(
        "/api/logistics/roles",
        headers=admin["headers"],
        json=_payload(permissions=[originate, shared]),
    )
    assert response.status_code == 201, response.text


def test_composition_with_conflict_is_409_sod(client, database, admin):
    originate, approve, shared = _sod_pair(database)
    _grant(database, admin["user"], [originate, approve, shared])
    response = client.post(
        "/api/logistics/roles",
        headers=admin["headers"],
        json=_payload(permissions=[originate, approve]),
    )
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "SOD_CONFLICT"


def test_sod_conflict_also_blocks_permission_replacement(client, database, admin):
    originate, approve, shared = _sod_pair(database)
    _grant(database, admin["user"], [originate, approve, shared])
    created = client.post(
        "/api/logistics/roles", headers=admin["headers"], json=_payload(permissions=[originate])
    )
    assert created.status_code == 201, created.text
    response = client.put(
        f"/api/logistics/roles/{created.json()['id']}/permissions",
        headers=admin["headers"],
        json={"permission_codes": [originate, approve]},
    )
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "SOD_CONFLICT"


def test_shared_permission_alone_is_not_a_conflict(client, database, admin):
    """Compartir un permiso común a ambos roles no es reunir potestades opuestas."""
    _originate, _approve, shared = _sod_pair(database)
    response = client.post(
        "/api/logistics/roles", headers=admin["headers"], json=_payload(permissions=[shared])
    )
    assert response.status_code == 201, response.text


def test_unrelated_roles_are_unaffected_by_sod(client, database, admin):
    _sod_pair(database)
    response = client.post(
        "/api/logistics/roles",
        headers=admin["headers"],
        json=_payload(permissions=ROLE_ADMIN_PERMISSIONS),
    )
    assert response.status_code == 201, response.text


# ---------------------------------------------------------------------------
# Matriz
# ---------------------------------------------------------------------------

def test_matrix_returns_roles_permissions_and_mappings(client, database, admin):
    created = client.post("/api/logistics/roles", headers=admin["headers"], json=_payload("MATRIZ"))
    assert created.status_code == 201, created.text

    response = client.get("/api/logistics/roles-matrix", headers=admin["headers"])
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"roles", "permissions", "total_mappings"}

    codes = {role["code"] for role in body["roles"]}
    assert "LOGISTICS_CUSTOM_MATRIZ" in codes
    assert body["total_mappings"] >= len(ROLE_ADMIN_PERMISSIONS)

    custom = next(r for r in body["roles"] if r["code"] == "LOGISTICS_CUSTOM_MATRIZ")
    assert sorted(custom["permission_codes"]) == sorted(ROLE_ADMIN_PERMISSIONS)


def test_matrix_groups_permissions_without_altering_codes(client, database, admin):
    _permission(database, "logistics.warehouses.read")
    response = client.get("/api/logistics/roles-matrix", headers=admin["headers"])
    assert response.status_code == 200, response.text
    perms = {p["code"]: p for p in response.json()["permissions"]}
    entry = perms.get("logistics.warehouses.read")
    assert entry is not None
    # El agrupamiento es un campo extra; el código canónico no se toca.
    assert entry["group"] == "warehouses"
    assert entry["code"] == "logistics.warehouses.read"


def test_matrix_marks_system_roles(client, database, admin):
    system_role = _role(database, f"SYS_{uuid4().hex[:6].upper()}", is_system=True)
    response = client.get("/api/logistics/roles-matrix", headers=admin["headers"])
    entry = next(r for r in response.json()["roles"] if r["code"] == system_role.code)
    assert entry["is_system"] is True


# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------

def test_role_creation_without_csrf_is_rejected(client, admin):
    response = client.post("/api/logistics/roles", json=_payload())
    assert response.status_code in (401, 403), response.text
    assert response.status_code != 500
