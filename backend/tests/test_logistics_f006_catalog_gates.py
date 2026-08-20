"""F006 PR 2 — invariantes del catálogo y compatibilidad de estados heredados.

Tres cosas que esta fase deja fijadas:

* el catálogo es coherente consigo mismo y con el código que lo referencia;
* el step-up tiene una sola autoridad, no dos listas que se contradicen;
* una asignación sembrada con `ACTIVE` en mayúsculas sigue concediendo permisos.

El último caso no es teórico: hay una fila así en producción. La comparación exacta
la descartaba en silencio, que es la peor forma de perder un permiso — sin error y
sin traza.
"""

from uuid import uuid4

import pytest

from app.models.organization import Organization
from app.modules.logistics.rbac.models_assignment import LogisticsRoleAssignment
from app.modules.logistics.rbac.models_permission import LogisticsPermission
from app.modules.logistics.rbac.models_role import LogisticsRole
from app.modules.logistics.rbac.models_role_permission import LogisticsRolePermission
from tests.support import authenticate


# ---------------------------------------------------------------------------
# Coherencia del catálogo
# ---------------------------------------------------------------------------

def test_no_duplicate_permission_codes() -> None:
    import collections

    from app.modules.logistics.rbac.permission_catalog import PERMISSIONS

    codes = [str(p["code"]) for p in PERMISSIONS]
    duplicates = sorted(c for c, n in collections.Counter(codes).items() if n > 1)
    assert not duplicates, f"códigos duplicados: {duplicates}"


def test_permission_codes_are_case_normalized() -> None:
    """`Inventory.Read` e `inventory.read` no pueden convivir como dos permisos."""
    import collections

    from app.modules.logistics.rbac.permission_catalog import PERMISSIONS

    codes = [str(p["code"]) for p in PERMISSIONS]
    assert all(c == c.lower() for c in codes), "hay códigos con mayúsculas"
    collisions = sorted(c for c, n in collections.Counter(c.lower() for c in codes).items() if n > 1)
    assert not collisions, f"colisiones al ignorar mayúsculas: {collisions}"


def test_every_permission_carries_required_metadata() -> None:
    from app.modules.logistics.rbac.permission_catalog import PERMISSIONS

    required = ("code", "resource", "action", "name", "description", "category", "risk_level")
    missing = [
        f"{p.get('code', '<sin código>')}:{key}"
        for p in PERMISSIONS
        for key in required
        if not p.get(key)
    ]
    assert not missing, f"metadata ausente: {missing[:10]}"


def test_risk_levels_use_the_declared_vocabulary() -> None:
    from app.modules.logistics.rbac.permission_catalog import PERMISSIONS

    allowed = {"low", "medium", "high", "critical"}
    unexpected = sorted({str(p["risk_level"]) for p in PERMISSIONS} - allowed)
    assert not unexpected, f"riesgos fuera del vocabulario: {unexpected}"


def test_no_unknown_permission_references_in_code() -> None:
    """Cubre las cuatro vías de referencia, no solo `require_permission`.

    Mirar una sola dejó pasar dos permisos inexistentes hasta PR 2: se consultaban con
    `has_permission`, y como no existían, la comprobación devolvía siempre False y la
    capacidad quedaba inalcanzable en silencio.
    """
    import pathlib
    import re

    from app.modules.logistics.rbac.permission_catalog import PERMISSIONS

    patterns = [
        re.compile(rf"{name}\(\s*[\"']([^\"']+)[\"']")
        for name in ("require_permission", "require_capability", "has_permission", "has_any_permission")
    ]
    catalog = {str(p["code"]) for p in PERMISSIONS}
    referenced: set[str] = set()
    for file in (pathlib.Path(__file__).resolve().parents[1] / "app").rglob("*.py"):
        if "__pycache__" in str(file):
            continue
        text = file.read_text(encoding="utf-8", errors="replace")
        for pattern in patterns:
            referenced.update(m.group(1) for m in pattern.finditer(text))

    unknown = sorted(referenced - catalog)
    assert not unknown, f"referencias a permisos inexistentes: {unknown}"


# ---------------------------------------------------------------------------
# Step-up: una sola autoridad
# ---------------------------------------------------------------------------

def test_every_step_up_permission_has_a_policy() -> None:
    from app.modules.logistics.rbac.permission_catalog import PERMISSIONS
    from app.modules.logistics.security.step_up_policy import POLICY_CATALOG

    required = {str(p["code"]) for p in PERMISSIONS if p.get("requires_step_up")}
    missing = sorted(required - set(POLICY_CATALOG))
    assert not missing, f"permisos con step-up sin política: {missing}"


def test_policy_and_catalog_cannot_disagree() -> None:
    """Toda política corresponde a un permiso real del catálogo.

    Antes había cuatro entradas cuyo permiso declaraba `requires_step_up=False`: un
    guard exigía prueba reforzada y el otro no, para la misma operación.
    """
    from app.modules.logistics.rbac.permission_catalog import PERMISSIONS
    from app.modules.logistics.security.step_up_policy import POLICY_CATALOG

    catalog = {str(p["code"]) for p in PERMISSIONS}
    orphan_policies = sorted(set(POLICY_CATALOG) - catalog)
    assert not orphan_policies, f"políticas sobre permisos inexistentes: {orphan_policies}"


def test_synthesized_policies_keep_the_existing_convention() -> None:
    from app.modules.logistics.security.step_up_policy import (
        POLICY_CATALOG,
        StepUpFactor,
    )

    for code, entry in POLICY_CATALOG.items():
        assert entry.required_factors, f"{code} no exige ningún factor"
        assert entry.fail_closed is True, f"{code} no falla cerrado"
        assert StepUpFactor.COMBINED_FACE_PAD in entry.required_factors, code


# ---------------------------------------------------------------------------
# Matriz de roles
# ---------------------------------------------------------------------------

def test_role_matrix_covers_exactly_the_system_roles() -> None:
    from app.modules.logistics.rbac.catalog import SYSTEM_ROLES
    from app.modules.logistics.rbac.permission_catalog import ROLE_PERMISSION_MATRIX

    system_roles = {str(r["code"]) for r in SYSTEM_ROLES}
    assert system_roles - set(ROLE_PERMISSION_MATRIX) == set()
    assert set(ROLE_PERMISSION_MATRIX) - system_roles == set()
    empty = sorted(code for code, perms in ROLE_PERMISSION_MATRIX.items() if not perms)
    assert not empty, f"roles sin permisos: {empty}"


def test_matrix_only_grants_permissions_that_exist() -> None:
    from app.modules.logistics.rbac.permission_catalog import (
        PERMISSIONS,
        ROLE_PERMISSION_MATRIX,
    )

    catalog = {str(p["code"]) for p in PERMISSIONS}
    unknown = sorted(
        {code for perms in ROLE_PERMISSION_MATRIX.values() for code in perms} - catalog
    )
    assert not unknown, f"la matriz concede permisos inexistentes: {unknown}"


def test_auditor_role_is_not_granted_mutating_permissions() -> None:
    """Un auditor que puede modificar deja de ser una comprobación independiente."""
    from app.modules.logistics.rbac.permission_catalog import ROLE_PERMISSION_MATRIX

    mutating = {"create", "update", "delete", "approve", "adjust", "revoke", "activate"}
    offending = sorted(
        code
        for code in ROLE_PERMISSION_MATRIX["LOGISTICS_AUDITOR"]
        if code.rsplit(".", 1)[-1] in mutating
    )
    assert not offending, f"el auditor tiene permisos mutadores: {offending}"


# ---------------------------------------------------------------------------
# Estado heredado de las asignaciones
# ---------------------------------------------------------------------------

def _role_with_permission(database, code: str) -> LogisticsRole:
    permission = database.query(LogisticsPermission).filter(
        LogisticsPermission.code == code
    ).first()
    if permission is None:
        parts = code.split(".")
        permission = LogisticsPermission(
            code=code,
            resource=parts[1] if len(parts) > 1 else code,
            action=parts[-1],
            name=code,
            description=code,
            category="logistics",
        )
        database.add(permission)
        database.flush()
    role = LogisticsRole(
        code=f"F006B_{uuid4().hex[:8].upper()}",
        name="Rol de prueba F006 PR2",
        description="Rol de la regresión de estados heredados",
        role_type="custom",
        is_system=False,
        status="active",
    )
    database.add(role)
    database.flush()
    database.add(LogisticsRolePermission(role_id=role.id, permission_id=permission.id))
    database.flush()
    return role


@pytest.mark.parametrize("stored_status", ["active", "ACTIVE", "Active"])
def test_assignment_status_is_read_case_insensitively(client, database, stored_status):
    """Una asignación sembrada con otro uso de mayúsculas sigue concediendo permisos.

    En producción existe una fila con `ACTIVE`. La comparación exacta la ignoraba, y
    el usuario perdía ese rol sin ningún error visible.
    """
    user, headers = authenticate(client, database, role="operator")
    role = _role_with_permission(database, "logistics.drivers.read")
    database.add(
        LogisticsRoleAssignment(
            user_id=user.id, role_id=role.id, scope_type="global", status=stored_status
        )
    )
    database.flush()

    assert client.get("/api/logistics/drivers", headers=headers).status_code not in (401, 403)


def test_api_writes_canonical_lowercase_status(client, database):
    """La escritura sigue produciendo el valor canónico, no uno cualquiera."""
    from app.modules.logistics.rbac.catalog import AssignmentStatus

    assert AssignmentStatus.ACTIVE.value == "active"

    user, _headers = authenticate(client, database, role="operator")
    role = _role_with_permission(database, "logistics.drivers.read")
    assignment = LogisticsRoleAssignment(
        user_id=user.id, role_id=role.id, scope_type="global", status="active"
    )
    database.add(assignment)
    database.flush()
    assert assignment.status == assignment.status.lower()


def test_revoked_assignment_does_not_grant(client, database):
    """La normalización no debe ablandar el resto de estados."""
    user, headers = authenticate(client, database, role="operator")
    role = _role_with_permission(database, "logistics.drivers.read")
    database.add(
        LogisticsRoleAssignment(
            user_id=user.id, role_id=role.id, scope_type="global", status="revoked"
        )
    )
    database.flush()

    assert client.get("/api/logistics/drivers", headers=headers).status_code == 403


# ---------------------------------------------------------------------------
# Autorización de las operaciones cerradas en PR 2
# ---------------------------------------------------------------------------

NEWLY_GUARDED = [
    ("POST", "/api/logistics/role-assignments", "logistics.role_assignments.create"),
    ("POST", "/api/logistics/files/upload-sessions", "logistics.files.upload"),
    ("POST", "/api/logistics/evidence", "logistics.files.evidence.create"),
]


@pytest.mark.parametrize(("method", "path", "_perm"), NEWLY_GUARDED, ids=[p for _, p, _ in NEWLY_GUARDED])
def test_newly_guarded_without_session_is_401(client, method, path, _perm):
    assert client.request(method, path, json={}).status_code == 401


@pytest.mark.parametrize(("method", "path", "_perm"), NEWLY_GUARDED, ids=[p for _, p, _ in NEWLY_GUARDED])
def test_newly_guarded_without_permission_is_403(client, database, method, path, _perm):
    _user, headers = authenticate(client, database, role="operator")
    assert client.request(method, path, headers=headers, json={}).status_code == 403


def test_platform_admin_still_needs_the_permission(client, database):
    """El bypass retirado en PR 1 no vuelve por la puerta de atrás en PR 2."""
    _user, headers = authenticate(client, database, role="admin")
    assert client.post("/api/logistics/role-assignments", headers=headers, json={}).status_code == 403


def test_evidence_second_mount_is_guarded_too(client, database):
    """El router de evidencia se expone bajo dos prefijos; ambos deben exigir permiso."""
    _user, headers = authenticate(client, database, role="operator")
    for path in ("/api/logistics/evidence", "/api/logistics/files/evidence"):
        assert client.post(path, headers=headers, json={}).status_code == 403, path


def _organization(database) -> Organization:
    organization = Organization(
        code=f"F6B{uuid4().hex[:8].upper()}",
        name="Organización de prueba F006 PR2",
        status="active",
        country_code="PE",
    )
    database.add(organization)
    database.flush()
    return organization


def test_scope_is_still_enforced_after_the_catalog_changes(client, database):
    user, headers = authenticate(client, database, role="operator")
    role = _role_with_permission(database, "logistics.drivers.read")
    database.add(
        LogisticsRoleAssignment(
            user_id=user.id,
            role_id=role.id,
            scope_type="organization",
            organization_id=_organization(database).id,
            status="active",
        )
    )
    database.flush()

    foreign = dict(headers)
    foreign["X-Org-Id"] = str(_organization(database).id)
    assert client.get("/api/logistics/drivers", headers=foreign).status_code == 403
