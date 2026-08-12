"""Logistics 'me' endpoints — authenticated user's logistics context."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.csrf import verify_csrf
from app.modules.logistics.auth_dependencies import (
    get_logistics_principal,
    require_logistics_principal,
)
from app.modules.logistics.me_schemas import (
    LogisticsContextChangeRequest,
    LogisticsContextChangeResponse,
    LogisticsMeContext,
    LogisticsMeResponse,
    LogisticsMeSession,
    LogisticsMeUser,
)
from app.modules.logistics.principal import LogisticsPrincipal


def create_me_router() -> APIRouter:
    router = APIRouter()

    @router.get("/me", response_model=LogisticsMeResponse)
    def get_logistics_me(
        principal: LogisticsPrincipal = Depends(require_logistics_principal),
    ):
        """Return the authenticated user's logistics context.

        This complements /auth/me — it does not replace it.
        Users without logistics permissions get enabled=false
        instead of a 403, so the frontend can show a clean state.
        """
        return LogisticsMeResponse(
            user=LogisticsMeUser(
                id=principal.user_id,
                display_name=principal.full_name,
                email=principal.email,
                platform_role=principal.platform_role,
                is_active=principal.is_active,
            ),
            session=LogisticsMeSession(
                id=principal.session_id,
                device_id=principal.device_id,
                expires_at=principal.session_expires_at,
                authentication_level=principal.authentication_level,
                risk_score=principal.risk_score,
            ),
            logistics=LogisticsMeContext(
                enabled=principal.logistics_enabled,
                roles=principal.role_codes,
                permissions=principal.permission_codes,
                sensitive_permissions=principal.sensitive_permissions,
                step_up_permissions=principal.step_up_permissions,
                organizations=principal.organization_ids,
                branches=principal.branch_ids,
                warehouses=principal.warehouse_ids,
                default_organization_id=principal.default_organization_id,
                default_branch_id=principal.default_branch_id,
                default_warehouse_id=principal.default_warehouse_id,
            ),
        )

    @router.post("/me/context", response_model=LogisticsContextChangeResponse)
    def change_logistics_context(
        data: LogisticsContextChangeRequest,
        principal: LogisticsPrincipal = Depends(require_logistics_principal),
        _csrf=Depends(verify_csrf),
    ):
        """Validate and set the user's logistics context.

        In Phase 008, this only validates the context — it does not
        persist a preference. The frontend can send the context with
        each request. A persisted preference can be added later.
        """
        # Validate organization access
        if data.organization_id and not principal.can_access_organization(data.organization_id):
            from app.core.exceptions import ApplicationError
            raise ApplicationError(
                "LOGISTICS_CONTEXT_DENIED",
                "No tiene acceso a la organización solicitada.",
                403,
            )

        # Validate branch access
        if data.branch_id and not principal.can_access_branch(data.branch_id):
            from app.core.exceptions import ApplicationError
            raise ApplicationError(
                "LOGISTICS_CONTEXT_DENIED",
                "No tiene acceso a la sede solicitada.",
                403,
            )

        # Validate warehouse access
        if data.warehouse_id and not principal.can_access_warehouse(data.warehouse_id):
            from app.core.exceptions import ApplicationError
            raise ApplicationError(
                "LOGISTICS_CONTEXT_DENIED",
                "No tiene acceso al almacén solicitado.",
                403,
            )

        return LogisticsContextChangeResponse(
            message="Contexto validado correctamente.",
            context=LogisticsMeContext(
                enabled=principal.logistics_enabled,
                roles=principal.role_codes,
                permissions=principal.permission_codes,
                sensitive_permissions=principal.sensitive_permissions,
                step_up_permissions=principal.step_up_permissions,
                organizations=principal.organization_ids,
                branches=principal.branch_ids,
                warehouses=principal.warehouse_ids,
                default_organization_id=str(data.organization_id) if data.organization_id else principal.default_organization_id,
                default_branch_id=str(data.branch_id) if data.branch_id else principal.default_branch_id,
                default_warehouse_id=str(data.warehouse_id) if data.warehouse_id else principal.default_warehouse_id,
            ),
        )

    return router