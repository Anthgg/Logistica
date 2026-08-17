"""RBAC Pydantic schemas for logistics roles and assignments."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Role ---
class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    name: str
    description: str
    role_type: str
    is_system: bool
    status: str
    created_at: datetime
    updated_at: datetime


class RoleScopeRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    role_id: UUID
    allowed_scope_type: str
    created_at: datetime


# --- Assignment ---
class RoleAssignmentCreate(BaseModel):
    user_id: UUID
    role_id: UUID
    scope_type: str
    organization_id: UUID | None = None
    branch_id: UUID | None = None
    warehouse_id: UUID | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class RoleAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    role_id: UUID
    scope_type: str
    organization_id: UUID | None
    branch_id: UUID | None
    warehouse_id: UUID | None
    status: str
    starts_at: datetime | None
    ends_at: datetime | None
    assigned_by: UUID | None
    assigned_at: datetime
    revoked_by: UUID | None
    revoked_at: datetime | None
    revocation_reason: str | None
    created_at: datetime
    updated_at: datetime


class RoleAssignmentRevoke(BaseModel):
    revocation_reason: str = Field(min_length=1, max_length=500)


class RoleAssignmentDateUpdate(BaseModel):
    starts_at: datetime | None = None
    ends_at: datetime | None = None


# --- Effective roles ---
class EffectiveRoleResponse(BaseModel):
    role_code: str
    role_name: str
    scope_type: str
    organization_id: UUID | None
    branch_id: UUID | None
    warehouse_id: UUID | None
    expires_at: datetime | None


class EffectiveRolesResponse(BaseModel):
    success: bool = True
    user_id: UUID
    roles: list[EffectiveRoleResponse]


# --- Conflict ---
class RoleConflictValidationResponse(BaseModel):
    success: bool = True
    has_conflict: bool
    conflict_type: str | None = None
    description: str | None = None
    role_a_code: str | None = None
    role_b_code: str | None = None

# --- Role write operations (F005) ---
class RoleCreate(BaseModel):
    """Alta de rol personalizado.

    `is_system` no es un campo del contrato: los roles creados por la API son
    siempre personalizados. Permitir que el cliente lo eligiera convertiría la
    protección de roles del sistema en una casilla que cualquiera puede marcar.
    """

    code: str = Field(min_length=3, max_length=50)
    name: str = Field(min_length=3, max_length=100)
    description: str = Field(default="", max_length=500)
    permission_codes: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    """El código es el identificador estable del rol: no se edita."""

    name: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class RoleStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|inactive)$")


class RolePermissionsUpdate(BaseModel):
    """Reemplaza el conjunto completo de permisos del rol, de forma atómica."""

    permission_codes: list[str]


class RoleMatrixRole(BaseModel):
    id: UUID
    code: str
    name: str
    role_type: str
    is_system: bool
    status: str
    permission_codes: list[str]


class RoleMatrixPermission(BaseModel):
    code: str
    name: str
    description: str
    #: Primer segmento tras `logistics.`, para agrupar en la UI sin tocar el código.
    group: str
    resource: str
    action: str
    is_sensitive: bool
    requires_step_up: bool


class RoleMatrixResponse(BaseModel):
    """Matriz completa en una sola respuesta.

    Construir la matriz con una petición por rol obligaría al frontend a hacer
    tantas llamadas como roles existan.
    """

    roles: list[RoleMatrixRole]
    permissions: list[RoleMatrixPermission]
    total_mappings: int


class SodConflictDetail(BaseModel):
    rule_code: str
    role_a_code: str
    role_b_code: str
    reason: str
    conflicting_permissions: list[str]
