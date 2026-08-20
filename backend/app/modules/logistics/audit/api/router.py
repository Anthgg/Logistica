"""Audit API router — query, detail, export, integrity verification."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.modules.logistics.auth_dependencies import require_permission
from app.models.user import User
from app.modules.logistics.audit.schemas import (
    AuditEventDetailResponse,
    AuditEventSummaryResponse,
    IntegrityCheckResponse,
)
from app.modules.logistics.audit.service import audit_service
from app.schemas.common import PaginatedResponse


def create_audit_event_router() -> APIRouter:
    router = APIRouter()

    @router.get("/audit-events", response_model=PaginatedResponse[AuditEventSummaryResponse])
    def list_audit_events(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        event_code: str | None = Query(None),
        category: str | None = Query(None),
        severity: str | None = Query(None),
        result: str | None = Query(None),
        actor_user_id: UUID | None = Query(None),
        organization_id: UUID | None = Query(None),
        branch_id: UUID | None = Query(None),
        warehouse_id: UUID | None = Query(None),
        resource_type: str | None = Query(None),
        resource_id: str | None = Query(None),
        correlation_id: str | None = Query(None),
    ):
        from math import ceil
        items, total = audit_service.list(
            db, page=page, page_size=page_size,
            event_code=event_code, category=category, severity=severity, result=result,
            actor_user_id=actor_user_id, organization_id=organization_id,
            branch_id=branch_id, warehouse_id=warehouse_id,
            resource_type=resource_type, resource_id=resource_id,
            correlation_id=correlation_id,
        )
        return PaginatedResponse(
            items=[AuditEventSummaryResponse.model_validate(e) for e in items],
            page=page, page_size=page_size, total=total,
            total_pages=ceil(total / page_size) if page_size else 0,
        )

    @router.get("/audit-events/{event_id}", response_model=AuditEventDetailResponse)
    def get_audit_event(
        event_id: UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        event = audit_service.get_by_id(db, event_id)
        if not event:
            from app.core.exceptions import ApplicationError
            raise ApplicationError("AUDIT_EVENT_NOT_FOUND", "El evento de auditoría no existe.", 404)
        return AuditEventDetailResponse.model_validate(event)

    @router.get(
        "/audit-events/by-resource/{resource_type}/{resource_id}",
        response_model=PaginatedResponse[AuditEventSummaryResponse],
    )
    def list_by_resource(
        resource_type: str,
        resource_id: str,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        from math import ceil
        items, total = audit_service.list_by_resource(db, resource_type, resource_id, page=page, page_size=page_size)
        return PaginatedResponse(
            items=[AuditEventSummaryResponse.model_validate(e) for e in items],
            page=page, page_size=page_size, total=total,
            total_pages=ceil(total / page_size) if page_size else 0,
        )

    @router.get(
        "/audit-events/by-correlation/{correlation_id}",
        response_model=PaginatedResponse[AuditEventSummaryResponse],
    )
    def list_by_correlation(
        correlation_id: str,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        from math import ceil
        items, total = audit_service.list_by_correlation(db, correlation_id, page=page, page_size=page_size)
        return PaginatedResponse(
            items=[AuditEventSummaryResponse.model_validate(e) for e in items],
            page=page, page_size=page_size, total=total,
            total_pages=ceil(total / page_size) if page_size else 0,
        )

    @router.post(
        "/audit-events/{event_id}/verify-integrity",
        response_model=IntegrityCheckResponse,
        # Verificar la integridad de un evento es una lectura sobre su sello de
        # auditoría; exige el mismo permiso que consultarla.
        dependencies=[Depends(require_permission("logistics.audit.read"))],
    )
    def verify_integrity(
        event_id: UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        result = audit_service.verify_integrity(db, event_id)
        return IntegrityCheckResponse(**result)

    return router