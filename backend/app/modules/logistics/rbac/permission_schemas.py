"""Permission schemas for Phase 006."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    resource: str
    action: str
    name: str
    description: str
    category: str
    risk_level: str
    is_sensitive: bool
    requires_reason: bool
    requires_step_up: bool
    is_system: bool
    status: str
    created_at: datetime
    updated_at: datetime


class RolePermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    role_id: UUID
    permission_id: UUID
    effect: str
    created_at: datetime


class EffectivePermissionsResponse(BaseModel):
    success: bool = True
    catalog_version: str
    user_id: UUID
    permissions: list[str]
    sensitive_permissions: list[str]
    step_up_permissions: list[str]
    roles: list[dict]


class AuthorizationCheckRequest(BaseModel):
    permission_code: str
    organization_id: UUID | None = None
    branch_id: UUID | None = None
    warehouse_id: UUID | None = None


class AuthorizationCheckResponse(BaseModel):
    success: bool = True
    allowed: bool
    permission_code: str
    reason: str | None = None