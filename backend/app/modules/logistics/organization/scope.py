"""Alcance de tenant para la estructura organizacional (F004).

F004 no diseña permisos ni roles: eso pertenece a F006. Lo que F004 sí posee es el
ENFORCEMENT del catálogo ya existente y del aislamiento por organización sobre sus
propias rutas.

La propiedad se deriva siempre de datos persistidos:

    Warehouse.branch_id -> Branch.organization_id

Nunca de un ``organization_id`` que envíe el cliente.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.models.branch import Branch
from app.models.warehouse import Warehouse
from app.modules.logistics.principal import LogisticsPrincipal

FORBIDDEN_ORGANIZATION = "No tiene acceso a esta organización."


def allowed_organization_ids(principal: LogisticsPrincipal) -> list[UUID] | None:
    """IDs de organización visibles, o ``None`` cuando el alcance es global.

    Devolver ``None`` (no una lista vacía) es lo que distingue "sin restricción" de
    "sin ninguna organización asignada"; el repositorio trata la lista vacía como un
    filtro que no deja pasar nada.
    """
    if principal.is_platform_admin:
        return None
    if not principal.organization_ids:
        # Contrato preexistente: un principal sin ámbitos declarados no está acotado.
        # Ver LogisticsPrincipal.can_access_organization.
        return None
    return [UUID(str(value)) for value in principal.organization_ids]


def assert_can_access_organization(principal: LogisticsPrincipal, organization_id: UUID) -> None:
    if not principal.can_access_organization(organization_id):
        raise ApplicationError("FORBIDDEN", FORBIDDEN_ORGANIZATION, 403)


def assert_can_access_branch(principal: LogisticsPrincipal, branch: Branch) -> None:
    """La sede se autoriza por la organización que tiene persistida."""
    assert_can_access_organization(principal, branch.organization_id)


def assert_can_access_warehouse(
    db: Session, principal: LogisticsPrincipal, warehouse: Warehouse
) -> None:
    """El almacén se autoriza por la organización de su sede.

    Los almacenes heredados sin sede ni organización (semilla demo) no pertenecen a
    ningún tenant, así que solo un administrador de plataforma puede alcanzarlos.
    """
    if principal.is_platform_admin:
        return

    organization_id = warehouse.organization_id
    if organization_id is None and warehouse.branch_id is not None:
        branch = db.get(Branch, warehouse.branch_id)
        organization_id = branch.organization_id if branch else None

    if organization_id is None:
        raise ApplicationError("FORBIDDEN", FORBIDDEN_ORGANIZATION, 403)

    assert_can_access_organization(principal, organization_id)
