"""Administración de roles logísticos — Fase 005.

Extiende el RBAC existente con lo que faltaba: crear, editar, activar/desactivar
roles **personalizados** y componer sus permisos. No introduce un segundo sistema de
roles: reutiliza `logistics_roles`, `logistics_permissions`,
`logistics_role_permissions` y `logistics_role_conflict_rules`.

Tres invariantes de seguridad gobiernan todo lo que hay aquí:

1. **Los roles del sistema no se editan.** `is_system=True` identifica el catálogo
   que provee la plataforma; la API nunca lo modifica ni permite crear roles con esa
   marca, porque sería una casilla que cualquiera puede activar.
2. **Nadie concede lo que no tiene.** Un actor solo puede otorgar a un rol permisos
   que él mismo posee. Sin esto, quien administra roles se auto-promociona en dos
   pasos: crea un rol con permisos superiores y se lo asigna.
3. **La separación de funciones se comprueba al componer**, no solo al asignar. Un
   rol que reúna originar y aprobar la misma operación es un conflicto aunque nadie
   lo tenga asignado todavía.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.modules.logistics.audit.service import AuditEventCommand, AuditService
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.rbac.models_permission import LogisticsPermission
from app.modules.logistics.rbac.models_role import LogisticsRole
from app.modules.logistics.rbac.models_role_permission import LogisticsRolePermission
from app.modules.logistics.rbac.permission_repository import (
    PermissionRepository,
    RolePermissionRepository,
)
from app.modules.logistics.rbac.repository import RoleRepository
from app.modules.logistics.rbac.schemas import (
    RoleCreate,
    RoleMatrixPermission,
    RoleMatrixResponse,
    RoleMatrixRole,
    RolePermissionsUpdate,
    RoleStatusUpdate,
    RoleUpdate,
)
from app.modules.logistics.rbac.sod import check_permission_composition

#: Prefijo de los códigos generados para roles personalizados. Mantenerlos
#: distinguibles evita que un rol creado por un administrador se confunda con uno
#: del catálogo de plataforma cuando se leen logs o seeds.
CUSTOM_ROLE_CODE_PREFIX = "LOGISTICS_CUSTOM_"


class RoleAdminService:
    def __init__(self) -> None:
        self.roles = RoleRepository()
        self.permissions = PermissionRepository()
        self.role_permissions = RolePermissionRepository()
        self.audit = AuditService()

    # ------------------------------------------------------------------
    # Guardas
    # ------------------------------------------------------------------
    @staticmethod
    def _assert_not_system(role: LogisticsRole) -> None:
        if role.is_system:
            raise ApplicationError(
                "ROLE_IS_SYSTEM",
                f"El rol '{role.code}' pertenece al catálogo del sistema y no se puede modificar.",
                409,
            )

    @staticmethod
    def normalize_code(raw: str) -> str:
        """Código estable, en mayúsculas y sin caracteres fuera de A-Z0-9_."""
        cleaned = "".join(ch for ch in raw.strip().upper() if ch.isalnum() or ch == "_")
        if not cleaned:
            raise ApplicationError("ROLE_CODE_INVALID", "El código de rol no es válido.", 422)
        if cleaned.startswith(CUSTOM_ROLE_CODE_PREFIX):
            return cleaned
        return f"{CUSTOM_ROLE_CODE_PREFIX}{cleaned}"

    def _resolve_permissions(self, db: Session, codes: list[str]) -> list[LogisticsPermission]:
        unique = list(dict.fromkeys(code.strip() for code in codes if code.strip()))
        if not unique:
            return []
        found = (
            db.query(LogisticsPermission)
            .filter(LogisticsPermission.code.in_(unique))
            .all()
        )
        known = {p.code for p in found}
        missing = [code for code in unique if code not in known]
        if missing:
            raise ApplicationError(
                "PERMISSION_NOT_FOUND",
                f"Permisos inexistentes en el catálogo: {', '.join(sorted(missing)[:5])}.",
                422,
            )
        return found

    @staticmethod
    def _assert_no_escalation(principal: LogisticsPrincipal, codes: list[str]) -> None:
        """Un actor no puede conceder permisos que él mismo no posee.

        F006 retiró la excepción por rol de plataforma: eximir al administrador de
        esta comprobación deja abierta la escalada en dos pasos que el guard existe
        para impedir.
        """
        held = set(principal.permission_codes)
        exceeding = sorted(set(codes) - held)
        if exceeding:
            raise ApplicationError(
                "PRIVILEGE_ESCALATION_DENIED",
                (
                    "No puede otorgar permisos que usted mismo no tiene: "
                    f"{', '.join(exceeding[:5])}."
                ),
                403,
            )

    @staticmethod
    def _assert_no_sod_conflict(
        db: Session, codes: list[str], *, exclude_role_id: UUID | None = None
    ) -> None:
        conflicts = check_permission_composition(
            db, set(codes), exclude_role_id=exclude_role_id
        )
        if not conflicts:
            return
        first = conflicts[0]
        raise ApplicationError(
            "SOD_CONFLICT",
            (
                f"Conflicto de separación de funciones entre {first.role_a_code} y "
                f"{first.role_b_code}: {first.reason}"
            ),
            409,
        )

    # ------------------------------------------------------------------
    # Auditoría
    # ------------------------------------------------------------------
    def _audit(
        self,
        db: Session,
        principal: LogisticsPrincipal,
        event_code: str,
        role: LogisticsRole,
        *,
        description: str,
        payload: dict | None = None,
    ) -> None:
        self.audit.write_event(
            db,
            AuditEventCommand(
                event_code=event_code,
                category="security",
                description=description,
                payload=payload,
                actor_user_id=principal.user_id,
                actor_display_name=principal.full_name,
                actor_role_codes=list(principal.role_codes),
                resource_type="logistics_role",
                resource_id=str(role.id),
                resource_code=role.code,
                severity="warning",
            ),
        )

    # ------------------------------------------------------------------
    # Operaciones
    # ------------------------------------------------------------------
    def create(self, db: Session, data: RoleCreate, principal: LogisticsPrincipal) -> LogisticsRole:
        code = self.normalize_code(data.code)
        if self.roles.get_by_code(db, code):
            raise ApplicationError(
                "ROLE_CODE_ALREADY_EXISTS", f"Ya existe un rol con el código '{code}'.", 409
            )

        permissions = self._resolve_permissions(db, data.permission_codes)
        codes = [p.code for p in permissions]
        self._assert_no_escalation(principal, codes)
        self._assert_no_sod_conflict(db, codes)

        role = self.roles.create(
            db,
            code=code,
            name=data.name.strip(),
            description=data.description.strip(),
            role_type="custom",
            # Nunca desde el cliente: los roles creados por la API son personalizados.
            is_system=False,
            status="active",
        )
        if permissions:
            self.role_permissions.set_role_permissions(db, role.id, [p.id for p in permissions])

        self._audit(
            db, principal, "logistics.role.created", role,
            description=f"Rol personalizado '{code}' creado con {len(codes)} permisos.",
            payload={"permission_count": len(codes)},
        )
        return role

    def update(
        self, db: Session, role_id: UUID, data: RoleUpdate, principal: LogisticsPrincipal
    ) -> LogisticsRole:
        role = self._get_or_404(db, role_id)
        self._assert_not_system(role)

        values = data.model_dump(exclude_unset=True)
        # El código es el identificador estable del rol: cambiarlo rompería seeds,
        # asignaciones y cualquier referencia externa.
        values.pop("code", None)
        for key, value in values.items():
            if value is not None:
                setattr(role, key, value.strip() if isinstance(value, str) else value)
        db.flush()

        self._audit(
            db, principal, "logistics.role.updated", role,
            description=f"Rol '{role.code}' actualizado.",
            payload={"fields": sorted(values)},
        )
        return role

    def change_status(
        self, db: Session, role_id: UUID, data: RoleStatusUpdate, principal: LogisticsPrincipal
    ) -> LogisticsRole:
        role = self._get_or_404(db, role_id)
        self._assert_not_system(role)
        role.status = data.status
        db.flush()

        event = "logistics.role.activated" if data.status == "active" else "logistics.role.deactivated"
        self._audit(
            db, principal, event, role,
            description=f"Rol '{role.code}' cambiado a estado {data.status}.",
        )
        return role

    def replace_permissions(
        self,
        db: Session,
        role_id: UUID,
        data: RolePermissionsUpdate,
        principal: LogisticsPrincipal,
    ) -> list[str]:
        """Sustituye el conjunto completo de permisos del rol.

        Se resuelve todo antes de escribir: si un permiso no existe, si el actor no
        puede concederlo o si la combinación rompe la separación de funciones, no se
        toca ninguna fila. Un rol a medio actualizar es peor que uno sin actualizar.
        """
        role = self._get_or_404(db, role_id)
        self._assert_not_system(role)

        permissions = self._resolve_permissions(db, data.permission_codes)
        codes = [p.code for p in permissions]
        self._assert_no_escalation(principal, codes)
        self._assert_no_sod_conflict(db, codes, exclude_role_id=role.id)

        self.role_permissions.set_role_permissions(db, role.id, [p.id for p in permissions])

        self._audit(
            db, principal, "logistics.role.permissions_updated", role,
            description=f"Permisos del rol '{role.code}' actualizados a {len(codes)}.",
            payload={"permission_count": len(codes)},
        )
        return sorted(codes)

    # ------------------------------------------------------------------
    # Matriz
    # ------------------------------------------------------------------
    def matrix(self, db: Session) -> RoleMatrixResponse:
        """Roles, permisos y sus asignaciones en una sola respuesta."""
        roles = db.query(LogisticsRole).order_by(LogisticsRole.code).all()
        permissions = (
            db.query(LogisticsPermission)
            .filter(LogisticsPermission.status == "active")
            .order_by(LogisticsPermission.code)
            .all()
        )

        # Una única consulta para todos los vínculos: hacerlo por rol convertiría la
        # matriz en tantas consultas como roles haya.
        rows = (
            db.query(LogisticsRolePermission.role_id, LogisticsPermission.code)
            .join(
                LogisticsPermission,
                LogisticsPermission.id == LogisticsRolePermission.permission_id,
            )
            .all()
        )
        by_role: dict[UUID, list[str]] = {}
        for role_id, code in rows:
            by_role.setdefault(role_id, []).append(code)

        return RoleMatrixResponse(
            roles=[
                RoleMatrixRole(
                    id=role.id,
                    code=role.code,
                    name=role.name,
                    role_type=role.role_type,
                    is_system=role.is_system,
                    status=role.status,
                    permission_codes=sorted(by_role.get(role.id, [])),
                )
                for role in roles
            ],
            permissions=[
                RoleMatrixPermission(
                    code=perm.code,
                    name=perm.name,
                    description=perm.description,
                    group=_permission_group(perm.code),
                    resource=perm.resource,
                    action=perm.action,
                    is_sensitive=perm.is_sensitive,
                    requires_step_up=perm.requires_step_up,
                )
                for perm in permissions
            ],
            total_mappings=len(rows),
        )

    # ------------------------------------------------------------------
    def _get_or_404(self, db: Session, role_id: UUID) -> LogisticsRole:
        role = self.roles.get_by_id(db, role_id)
        if not role:
            raise ApplicationError("LOGISTICS_ROLE_NOT_FOUND", "El rol no existe.", 404)
        return role


def _permission_group(code: str) -> str:
    """Segmento de dominio del permiso, para agrupar en la UI.

    `logistics.warehouses.read` -> `warehouses`. El código canónico no se altera.
    """
    parts = code.split(".")
    return parts[1] if len(parts) >= 3 else parts[0]
