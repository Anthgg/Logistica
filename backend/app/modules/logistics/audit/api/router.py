import logging
from datetime import UTC, datetime
from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.database.session import get_db
from app.modules.logistics.audit.schemas import (
    AuditEventDetailResponse,
    AuditEventSummaryResponse,
    IntegrityCheckResponse,
)
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.auth_dependencies import get_logistics_principal, require_permission
from app.modules.logistics.organization.scope import (
    allowed_organization_ids,
    assert_can_access_organization,
)
from app.modules.logistics.principal import LogisticsPrincipal
from app.schemas.common import PaginatedResponse

logger = logging.getLogger(__name__)


def create_audit_event_router() -> APIRouter:
    router = APIRouter()

    @router.get(
        "/audit-events",
        response_model=PaginatedResponse[AuditEventSummaryResponse],
        dependencies=[Depends(require_permission("logistics.audit.read"))],
    )
    def list_audit_events(
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(get_logistics_principal),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        event_code: str | None = Query(None),
        category: str | None = Query(None),
        severity: str | None = Query(None),
        result: str | None = Query(None),
        action: str | None = Query(None),
        actor_user_id: UUID | None = Query(None),
        organization_id: UUID | None = Query(None),
        branch_id: UUID | None = Query(None),
        warehouse_id: UUID | None = Query(None),
        resource_type: str | None = Query(None),
        resource_id: str | None = Query(None),
        correlation_id: str | None = Query(None),
        request_id: str | None = Query(None),
        date_from: datetime | None = Query(None),
        date_to: datetime | None = Query(None),
        search: str | None = Query(None),
    ):
        allowed_orgs = allowed_organization_ids(principal)
        items, total = audit_service.list(
            db,
            page=page,
            page_size=page_size,
            event_code=event_code,
            category=category,
            severity=severity,
            result=result,
            action=action,
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
            request_id=request_id,
            date_from=date_from,
            date_to=date_to,
            search=search,
            allowed_org_ids=allowed_orgs,
        )
        return PaginatedResponse(
            items=[AuditEventSummaryResponse.model_validate(e) for e in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if page_size else 0,
        )

    @router.get(
        "/audit-events/export",
        dependencies=[Depends(require_permission("logistics.audit.export"))],
    )
    def export_audit_events(
        request: Request,
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(get_logistics_principal),
        event_code: str | None = Query(None),
        category: str | None = Query(None),
        severity: str | None = Query(None),
        result: str | None = Query(None),
        action: str | None = Query(None),
        actor_user_id: UUID | None = Query(None),
        organization_id: UUID | None = Query(None),
        branch_id: UUID | None = Query(None),
        warehouse_id: UUID | None = Query(None),
        resource_type: str | None = Query(None),
        resource_id: str | None = Query(None),
        correlation_id: str | None = Query(None),
        request_id: str | None = Query(None),
        date_from: datetime | None = Query(None),
        date_to: datetime | None = Query(None),
        search: str | None = Query(None),
    ):
        allowed_orgs = allowed_organization_ids(principal)
        has_sensitive_ip = principal.has_permission("logistics.audit.read_sensitive")
        csv_content, row_count = audit_service.export_csv(
            db,
            include_sensitive_ip=has_sensitive_ip,
            event_code=event_code,
            category=category,
            severity=severity,
            result=result,
            action=action,
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
            request_id=request_id,
            date_from=date_from,
            date_to=date_to,
            search=search,
            allowed_org_ids=allowed_orgs,
        )

        # Audit the export action
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        req_id = request.headers.get("x-request-id")
        corr_id = request.headers.get("x-correlation-id")
        try:
            audit_service.write_event(
                db,
                AuditEventCommand(
                    event_code="logistics.audit.exported",
                    actor_user_id=principal.user_id,
                    actor_display_name=principal.full_name,
                    session_id=principal.session_id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    request_id=req_id,
                    correlation_id=corr_id,
                    action="export",
                    result="success",
                    severity="high",
                    resource_type="audit",
                    metadata={
                        "row_count": row_count,
                        "date_from": date_from.isoformat() if date_from else None,
                        "date_to": date_to.isoformat() if date_to else None,
                        "event_code": event_code,
                        "category": category,
                        "search": search,
                    },
                ),
            )
            db.commit()
        except SQLAlchemyError as exc:
            logger.warning("No se pudo registrar evento de auditoría de exportación: %s", exc)
            db.rollback()

        filename = f'audit-events-{datetime.now(UTC).strftime("%Y-%m-%d")}.csv'
        return Response(
            content=csv_content.encode("utf-8-sig"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @router.get(
        "/audit-events/{event_id}",
        response_model=AuditEventDetailResponse,
        dependencies=[Depends(require_permission("logistics.audit.read"))],
    )
    def get_audit_event(
        event_id: UUID,
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(get_logistics_principal),
    ):
        event = audit_service.get_by_id(db, event_id)
        if not event:
            raise ApplicationError("AUDIT_EVENT_NOT_FOUND", "El evento de auditoría no existe.", 404)

        if event.organization_id:
            assert_can_access_organization(principal, event.organization_id)

        resp = AuditEventDetailResponse.model_validate(event)
        if not principal.has_permission("logistics.audit.read_sensitive") and resp.ip_address:
            resp.ip_address = "[REDACTED]"
        return resp

    @router.get(
        "/audit-events/by-resource/{resource_type}/{resource_id}",
        response_model=PaginatedResponse[AuditEventSummaryResponse],
        dependencies=[Depends(require_permission("logistics.audit.read"))],
    )
    def list_by_resource(
        resource_type: str,
        resource_id: str,
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(get_logistics_principal),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        allowed_orgs = allowed_organization_ids(principal)
        items, total = audit_service.list(
            db,
            resource_type=resource_type,
            resource_id=resource_id,
            page=page,
            page_size=page_size,
            allowed_org_ids=allowed_orgs,
        )
        return PaginatedResponse(
            items=[AuditEventSummaryResponse.model_validate(e) for e in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if page_size else 0,
        )

    @router.get(
        "/audit-events/by-correlation/{correlation_id}",
        response_model=PaginatedResponse[AuditEventSummaryResponse],
        dependencies=[Depends(require_permission("logistics.audit.read"))],
    )
    def list_by_correlation(
        correlation_id: str,
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(get_logistics_principal),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        allowed_orgs = allowed_organization_ids(principal)
        items, total = audit_service.list(
            db,
            correlation_id=correlation_id,
            page=page,
            page_size=page_size,
            allowed_org_ids=allowed_orgs,
        )
        return PaginatedResponse(
            items=[AuditEventSummaryResponse.model_validate(e) for e in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if page_size else 0,
        )

    @router.post(
        "/audit-events/{event_id}/verify-integrity",
        response_model=IntegrityCheckResponse,
        dependencies=[Depends(require_permission("logistics.audit.read"))],
    )
    def verify_integrity(
        event_id: UUID,
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(get_logistics_principal),
    ):
        event = audit_service.get_by_id(db, event_id)
        if not event:
            raise ApplicationError("AUDIT_EVENT_NOT_FOUND", "El evento de auditoría no existe.", 404)
        if event.organization_id:
            assert_can_access_organization(principal, event.organization_id)
        result = audit_service.verify_integrity(db, event_id)
        return IntegrityCheckResponse(**result)

    return router