"""Schema for GET /api/logistics/me response."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LogisticsMeUser(BaseModel):
    id: UUID
    display_name: str
    email: str
    platform_role: str
    is_active: bool


class LogisticsMeSession(BaseModel):
    id: UUID
    device_id: UUID | None
    expires_at: datetime
    authentication_level: str
    risk_score: float | None


class LogisticsMeContext(BaseModel):
    enabled: bool
    roles: list[str]
    permissions: list[str]
    sensitive_permissions: list[str]
    step_up_permissions: list[str]
    organizations: list[str]
    branches: list[str]
    warehouses: list[str]
    default_organization_id: str | None
    default_branch_id: str | None
    default_warehouse_id: str | None


class LogisticsMeResponse(BaseModel):
    success: bool = True
    user: LogisticsMeUser
    session: LogisticsMeSession
    logistics: LogisticsMeContext


class LogisticsContextChangeRequest(BaseModel):
    organization_id: UUID | None = None
    branch_id: UUID | None = None
    warehouse_id: UUID | None = None


class LogisticsContextChangeResponse(BaseModel):
    success: bool = True
    message: str
    context: LogisticsMeContext