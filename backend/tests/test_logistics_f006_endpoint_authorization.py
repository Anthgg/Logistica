"""F006 PR 1 — regresión de autorización de los endpoints que estaban abiertos.

Cuatro módulos logísticos —conductores, verificación de vehículos, aprobaciones de
compra y órdenes de compra— no tenían ninguna dependencia de autenticación. En
producción respondían 200 sin sesión, y 33 de sus 48 operaciones eran mutadoras.

La identidad, además, la ponía el cliente por tres vías distintas: las cabeceras
``X-Actor-Id``/``X-Org-Id`` con dos UUID fijos de respaldo, el parámetro de consulta
``user_id`` en aprobaciones, y una organización aceptada sin validar. Aquí se fija
que ninguna de las tres vuelva.

El RBAC se siembra de verdad (permiso → rol → asignación con ámbito): nada sustituye
a `require_permission` ni a `get_logistics_principal`, así que un fallo de enforcement
se nota.
"""

from uuid import uuid4

import pytest

from app.models.organization import Organization
from app.modules.logistics.rbac.models_assignment import LogisticsRoleAssignment
from app.modules.logistics.rbac.models_permission import LogisticsPermission
from app.modules.logistics.rbac.models_role import LogisticsRole
from app.modules.logistics.rbac.models_role_permission import LogisticsRolePermission
from tests.support import authenticate

#: Operaciones que estaban abiertas, con el permiso que ahora exigen. Se cubre una
#: por módulo y método: el objetivo es el enforcement, no repetir 48 veces lo mismo.
GUARDED_READS = [
    ("/api/logistics/drivers", "logistics.drivers.read"),
    ("/api/logistics/driver-license-categories", "logistics.drivers.read"),
    ("/api/logistics/vehicle-verification-sources", "logistics.vehicles.read"),
    ("/api/logistics/procurement-approvals/policies", "logistics.procurement_approval_policies.read"),
]

GUARDED_WRITES = [
    ("/api/logistics/drivers", "logistics.drivers.create"),
    ("/api/logistics/driver-license-categories/seed", "logistics.drivers.update"),
    ("/api/logistics/vehicle-verification-sources/seed", "logistics.vehicles.update"),
    ("/api/logistics/procurement-approvals/policies", "logistics.procurement_approval_policies.create"),
]


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
            category="logistics",
        )
        database.add(perm)
    # Se fija explícitamente: la base de CI arranca sin catálogo sembrado y la de
    # desarrollo con él, así que darlo por supuesto hace que el mismo test responda
    # distinto en cada entorno.
    perm.requires_step_up = requires_step_up
    database.flush()
    return perm


def _organization(database) -> Organization:
    """Organización real: `logistics_role_assignments.organization_id` tiene FK."""
    org = Organization(
        code=f"F006{uuid4().hex[:8].upper()}",
        name="Organización de prueba F006",
        status="active",
        country_code="PE",
    )
    database.add(org)
    database.flush()
    return org


def _grant(database, user, permissions: list[str], *, scope_type: str = "global",
           organization_id=None, requires_step_up: bool = False) -> LogisticsRole:
    role = LogisticsRole(
        code=f"F006_{uuid4().hex[:8].upper()}",
        name="Rol de prueba F006",
        description="Rol creado por la regresión de autorización F006",
        role_type="custom",
        is_system=False,
        status="active",
    )
    database.add(role)
    database.flush()
    for code in permissions:
        database.add(
            LogisticsRolePermission(
                role_id=role.id,
                permission_id=_permission(database, code, requires_step_up=requires_step_up).id,
            )
        )
    database.add(
        LogisticsRoleAssignment(
            user_id=user.id,
            role_id=role.id,
            scope_type=scope_type,
            organization_id=organization_id,
            status="active",
        )
    )
    database.flush()
    return role


# ---------------------------------------------------------------------------
# Sin sesión: 401
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("path", "_perm"), GUARDED_READS, ids=[p for p, _ in GUARDED_READS])
def test_guarded_read_without_session_is_401(client, path, _perm):
    assert client.get(path).status_code == 401


@pytest.mark.parametrize(("path", "_perm"), GUARDED_WRITES, ids=[p for p, _ in GUARDED_WRITES])
def test_guarded_write_without_session_is_401(client, path, _perm):
    assert client.post(path, json={}).status_code == 401


def test_purchase_order_approval_without_session_is_401(client):
    """La operación más grave de las que estaban abiertas: aprobar una compra."""
    response = client.post(f"/api/logistics/procurement/purchase-orders/{uuid4()}/approve", json={})
    assert response.status_code == 401


def test_approval_decision_without_session_is_401(client):
    response = client.post(
        f"/api/logistics/procurement-approvals/assignments/{uuid4()}/decision", json={}
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Con sesión pero sin el permiso: 403
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("path", "_perm"), GUARDED_READS, ids=[p for p, _ in GUARDED_READS])
def test_guarded_read_without_permission_is_403(client, database, path, _perm):
    _user, headers = authenticate(client, database, role="operator")
    assert client.get(path, headers=headers).status_code == 403


@pytest.mark.parametrize(("path", "_perm"), GUARDED_WRITES, ids=[p for p, _ in GUARDED_WRITES])
def test_guarded_write_without_permission_is_403(client, database, path, _perm):
    _user, headers = authenticate(client, database, role="operator")
    assert client.post(path, headers=headers, json={}).status_code == 403


def test_unrelated_permission_does_not_open_the_endpoint(client, database):
    """Tener permisos no basta: tiene que ser el permiso correcto."""
    user, headers = authenticate(client, database, role="operator")
    _grant(database, user, ["logistics.warehouses.read"])
    assert client.get("/api/logistics/drivers", headers=headers).status_code == 403


# ---------------------------------------------------------------------------
# Con el permiso: pasa el guard
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("path", "perm"), GUARDED_READS, ids=[p for p, _ in GUARDED_READS])
def test_guarded_read_with_permission_is_allowed(client, database, path, perm):
    user, headers = authenticate(client, database, role="operator")
    _grant(database, user, [perm])
    # Lo que se comprueba es la autorización, no el resultado de negocio: basta con
    # que deje de ser 401/403.
    assert client.get(path, headers=headers).status_code not in (401, 403)


# ---------------------------------------------------------------------------
# El rol de plataforma ya no concede nada
# ---------------------------------------------------------------------------

def test_platform_admin_without_permission_is_403(client, database):
    """El bypass `if user.role == "admin": return user` se retiró en F006.

    Un administrador de plataforma sin el permiso en su catálogo efectivo recibe 403
    como cualquier otro. Antes entraba a todo, y de paso se saltaba el step-up.
    """
    _user, headers = authenticate(client, database, role="admin")
    assert client.get("/api/logistics/drivers", headers=headers).status_code == 403


def test_platform_admin_with_permission_is_allowed(client, database):
    user, headers = authenticate(client, database, role="admin")
    _grant(database, user, ["logistics.drivers.read"])
    assert client.get("/api/logistics/drivers", headers=headers).status_code not in (401, 403)


# ---------------------------------------------------------------------------
# Identidad y ámbito: ya no los pone el cliente
# ---------------------------------------------------------------------------

def test_actor_header_does_not_grant_access(client):
    """`X-Actor-Id` era la identidad del actor y bastaba enviarla."""
    response = client.get(
        "/api/logistics/drivers",
        headers={"X-Actor-Id": str(uuid4()), "X-Org-Id": str(uuid4())},
    )
    assert response.status_code == 401


def test_organization_header_outside_scope_is_403(client, database):
    """`X-Org-Id` se aceptaba tal cual: se podía operar sobre la organización de otro."""
    user, headers = authenticate(client, database, role="operator")
    own_org = _organization(database).id
    _grant(database, user, ["logistics.drivers.read"], scope_type="organization", organization_id=own_org)

    foreign = dict(headers)
    foreign["X-Org-Id"] = str(_organization(database).id)
    assert client.get("/api/logistics/drivers", headers=foreign).status_code == 403


def test_organization_header_inside_scope_is_allowed(client, database):
    user, headers = authenticate(client, database, role="operator")
    own_org = _organization(database).id
    _grant(database, user, ["logistics.drivers.read"], scope_type="organization", organization_id=own_org)

    allowed = dict(headers)
    allowed["X-Org-Id"] = str(own_org)
    assert client.get("/api/logistics/drivers", headers=allowed).status_code not in (401, 403)


# ---------------------------------------------------------------------------
# Step-up
# ---------------------------------------------------------------------------

def test_step_up_permission_without_proof_is_rejected(client, database):
    """Tener el permiso no basta cuando el catálogo exige verificación reforzada."""
    user, headers = authenticate(client, database, role="operator")
    _grant(database, user, ["logistics.drivers.create"], requires_step_up=True)

    response = client.post("/api/logistics/drivers", headers=headers, json={})
    assert response.status_code == 403
    assert response.json()["error"]["code"] in {"STEP_UP_REQUIRED", "STEP_UP_PROOF_NOT_FOUND"}


def test_step_up_is_not_bypassed_by_platform_admin(client, database):
    """El bypass saltaba también el step-up, no solo el permiso."""
    user, headers = authenticate(client, database, role="admin")
    _grant(database, user, ["logistics.drivers.create"], requires_step_up=True)

    response = client.post("/api/logistics/drivers", headers=headers, json={})
    assert response.status_code == 403
    assert response.json()["error"]["code"] in {"STEP_UP_REQUIRED", "STEP_UP_PROOF_NOT_FOUND"}
