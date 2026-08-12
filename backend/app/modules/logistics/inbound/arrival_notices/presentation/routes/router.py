"""FastAPI routes for Phase 036 arrival notices."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Header, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import (
    require_permission,
    resolve_organization_id,
)
from app.modules.logistics.inbound.arrival_notices.application.services.arrival_notice_service import (
    ArrivalNoticeService,
)
from app.modules.logistics.inbound.arrival_notices.domain.errors.exceptions import (
    ArrivalNoticeNotEditable,
    ArrivalNoticeNotFound,
)
from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
    ArrivalNoticeExpectedLineModel,
    ArrivalNoticePurchaseOrderReferenceModel,
    ArrivalNoticeRevisionModel,
    ArrivalNoticeTransportDocumentModel,
)
from app.modules.logistics.inbound.arrival_notices.presentation.schemas.schemas import (
    ArrivalNoticeCancelRequest,
    ArrivalNoticeCreate,
    ArrivalNoticeDetail,
    ArrivalNoticeExpectedLineCreate,
    ArrivalNoticeExpectedLineResponse,
    ArrivalNoticeExpectedLineUpdate,
    ArrivalNoticeListResponse,
    ArrivalNoticeRequestChangesRequest,
    ArrivalNoticeResponse,
    ArrivalNoticeRevisionCreate,
    ArrivalNoticeRevisionResponse,
    ArrivalNoticeSubmitRequest,
    ArrivalNoticeSummary,
    ArrivalNoticeTransportDocumentCreate,
    ArrivalNoticeTransportDocumentResponse,
    ArrivalNoticeTransportDocumentUpdate,
    ArrivalNoticeTransportReadinessResponse,
    ArrivalNoticeUpdate,
    ArrivalNoticeValidationResponse,
    ArrivalNoticeVehicleReferenceRequest,
    ArrivalNoticeDriverReferenceRequest,
    CapabilityResponse,
    FormatVerificationResponse,
    TransportDocumentAssociateFileRequest,
)
from app.modules.logistics.principal import LogisticsPrincipal


router = APIRouter(tags=["Logistics - Arrival Notices"])


def _response(notice) -> dict:
    return ArrivalNoticeResponse.model_validate(notice).model_dump()


def _summary(service: ArrivalNoticeService, notice, codes: list[str], documents: int):
    return ArrivalNoticeSummary(
        **_response(notice),
        purchase_order_codes=codes,
        document_count=documents,
        warnings_count=0,
        capabilities=service.capabilities(notice),
    )


@router.get("/arrival-notices", response_model=ArrivalNoticeListResponse)
def list_arrival_notices(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    search: str | None = Query(default=None, max_length=160),
    supplier_id: UUID | None = None,
    carrier_id: UUID | None = None,
    warehouse_id: UUID | None = None,
    branch_id: UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    appointment_status: str | None = None,
    expected_from: date | None = None,
    expected_to: date | None = None,
    submission_channel: str | None = None,
    created_by: UUID | None = None,
    sort_by: str = Query(default="updated_at"),
    sort_direction: str = Query(default="desc", pattern="^(asc|desc)$"),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.read")
    ),
    db: Session = Depends(get_db),
):
    organization_id = resolve_organization_id(principal)
    service = ArrivalNoticeService(db)
    items, total = service.list_notices(
        organization_id,
        page=page,
        page_size=page_size,
        search=search,
        supplier_id=supplier_id,
        carrier_id=carrier_id,
        warehouse_id=warehouse_id,
        branch_id=branch_id,
        status=status_filter,
        appointment_status=appointment_status,
        expected_from=expected_from,
        expected_to=expected_to,
        submission_channel=submission_channel,
        created_by=created_by,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )
    revision_ids = [item.active_revision_id for item in items if item.active_revision_id]
    codes_by_revision: dict[UUID, list[str]] = {item: [] for item in revision_ids}
    document_count: dict[UUID, int] = {item: 0 for item in revision_ids}
    if revision_ids:
        for revision_id, code in db.execute(
            select(
                ArrivalNoticePurchaseOrderReferenceModel.arrival_notice_revision_id,
                ArrivalNoticePurchaseOrderReferenceModel.purchase_order_code,
            ).where(
                ArrivalNoticePurchaseOrderReferenceModel.arrival_notice_revision_id.in_(
                    revision_ids
                ),
                ArrivalNoticePurchaseOrderReferenceModel.status == "ACTIVE",
            )
        ):
            codes_by_revision[revision_id].append(code)
        for revision_id, count in db.execute(
            select(
                ArrivalNoticeTransportDocumentModel.revision_id,
                func.count(ArrivalNoticeTransportDocumentModel.id),
            )
            .where(
                ArrivalNoticeTransportDocumentModel.revision_id.in_(revision_ids),
                ArrivalNoticeTransportDocumentModel.status == "ACTIVE",
            )
            .group_by(ArrivalNoticeTransportDocumentModel.revision_id)
        ):
            document_count[revision_id] = int(count)
    return {
        "items": [
            _summary(
                service,
                item,
                codes_by_revision.get(item.active_revision_id, []),
                document_count.get(item.active_revision_id, 0),
            )
            for item in items
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.post(
    "/arrival-notices",
    response_model=ArrivalNoticeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_arrival_notice(
    payload: ArrivalNoticeCreate,
    correlation_id: str | None = Header(default=None, alias="X-Correlation-ID"),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.create")
    ),
    db: Session = Depends(get_db),
):
    organization_id = resolve_organization_id(principal)
    notice = ArrivalNoticeService(db).create_notice(
        organization_id=organization_id,
        actor_user_id=principal.user_id,
        session_id=getattr(principal, "session_id", None),
        correlation_id=correlation_id,
        data=payload.model_dump(),
    )
    db.commit()
    db.refresh(notice)
    return notice


@router.get("/arrival-notices/{arrival_notice_id}", response_model=ArrivalNoticeDetail)
def get_arrival_notice(
    arrival_notice_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.read")
    ),
    db: Session = Depends(get_db),
):
    organization_id = resolve_organization_id(principal)
    service = ArrivalNoticeService(db)
    notice = service.get(arrival_notice_id, organization_id)
    revisions = list(
        db.scalars(
            select(ArrivalNoticeRevisionModel)
            .where(ArrivalNoticeRevisionModel.arrival_notice_id == notice.id)
            .order_by(ArrivalNoticeRevisionModel.revision_number)
        )
    )
    return ArrivalNoticeDetail(
        **_response(notice),
        supplier_snapshot=notice.supplier_snapshot,
        carrier_snapshot=notice.carrier_snapshot,
        revisions=[
            ArrivalNoticeRevisionResponse.model_validate(item).model_dump()
            for item in revisions
        ],
    )


@router.patch("/arrival-notices/{arrival_notice_id}", response_model=ArrivalNoticeResponse)
def update_arrival_notice(
    arrival_notice_id: UUID,
    payload: ArrivalNoticeUpdate,
    correlation_id: str | None = Header(default=None, alias="X-Correlation-ID"),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.update")
    ),
    db: Session = Depends(get_db),
):
    notice = ArrivalNoticeService(db).update_notice(
        arrival_notice_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload.model_dump(exclude_unset=True),
        session_id=getattr(principal, "session_id", None),
        correlation_id=correlation_id,
    )
    db.commit()
    db.refresh(notice)
    return notice


@router.post(
    "/arrival-notices/{arrival_notice_id}/validate",
    response_model=ArrivalNoticeValidationResponse,
)
def validate_arrival_notice(
    arrival_notice_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.validate")
    ),
    db: Session = Depends(get_db),
):
    return ArrivalNoticeService(db).validate_notice(
        arrival_notice_id, resolve_organization_id(principal)
    )


@router.post("/arrival-notices/{arrival_notice_id}/submit", response_model=ArrivalNoticeResponse)
def submit_arrival_notice(
    arrival_notice_id: UUID,
    payload: ArrivalNoticeSubmitRequest,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.submit")
    ),
    db: Session = Depends(get_db),
):
    notice = ArrivalNoticeService(db).submit(
        arrival_notice_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload.idempotency_key,
    )
    db.commit()
    db.refresh(notice)
    return notice


def _transition(
    db: Session,
    principal: LogisticsPrincipal,
    arrival_notice_id: UUID,
    target: str,
    reason: str | None = None,
):
    notice = ArrivalNoticeService(db).transition(
        arrival_notice_id,
        resolve_organization_id(principal),
        principal.user_id,
        target,
        reason=reason,
    )
    db.commit()
    db.refresh(notice)
    return notice


@router.post(
    "/arrival-notices/{arrival_notice_id}/mark-under-review",
    response_model=ArrivalNoticeResponse,
)
def mark_under_review(
    arrival_notice_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.review")
    ),
    db: Session = Depends(get_db),
):
    return _transition(db, principal, arrival_notice_id, "UNDER_REVIEW")


@router.post(
    "/arrival-notices/{arrival_notice_id}/request-changes",
    response_model=ArrivalNoticeResponse,
)
def request_changes(
    arrival_notice_id: UUID,
    payload: ArrivalNoticeRequestChangesRequest,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.request_changes")
    ),
    db: Session = Depends(get_db),
):
    return _transition(
        db, principal, arrival_notice_id, "REQUIRES_CHANGES", payload.reason
    )


@router.post(
    "/arrival-notices/{arrival_notice_id}/mark-ready",
    response_model=ArrivalNoticeResponse,
)
def mark_ready(
    arrival_notice_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.mark_ready")
    ),
    db: Session = Depends(get_db),
):
    return _transition(db, principal, arrival_notice_id, "READY_FOR_SCHEDULING")


@router.post("/arrival-notices/{arrival_notice_id}/cancel", response_model=ArrivalNoticeResponse)
def cancel_arrival_notice(
    arrival_notice_id: UUID,
    payload: ArrivalNoticeCancelRequest,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.cancel")
    ),
    db: Session = Depends(get_db),
):
    notice = ArrivalNoticeService(db).cancel_notice(
        arrival_notice_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload.reason,
        payload.idempotency_key,
    )
    db.commit()
    db.refresh(notice)
    return notice


@router.post(
    "/arrival-notices/{arrival_notice_id}/copy",
    response_model=ArrivalNoticeResponse,
    status_code=status.HTTP_201_CREATED,
)
def copy_arrival_notice(
    arrival_notice_id: UUID,
    payload: ArrivalNoticeSubmitRequest,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.create")
    ),
    db: Session = Depends(get_db),
):
    notice = ArrivalNoticeService(db).copy_notice(
        arrival_notice_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload.idempotency_key,
    )
    db.commit()
    db.refresh(notice)
    return notice


@router.get("/arrival-notices/{arrival_notice_id}/history")
def get_arrival_notice_history(
    arrival_notice_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.read_history")
    ),
    db: Session = Depends(get_db),
):
    organization_id = resolve_organization_id(principal)
    notice = ArrivalNoticeService(db).get(arrival_notice_id, organization_id)
    revisions = list(
        db.scalars(
            select(ArrivalNoticeRevisionModel)
            .where(ArrivalNoticeRevisionModel.arrival_notice_id == notice.id)
            .order_by(ArrivalNoticeRevisionModel.revision_number)
        )
    )
    return [
        ArrivalNoticeRevisionResponse.model_validate(item).model_dump()
        for item in revisions
    ]


@router.get(
    "/arrival-notices/{arrival_notice_id}/capabilities",
    response_model=CapabilityResponse,
)
def get_arrival_notice_capabilities(
    arrival_notice_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.read")
    ),
    db: Session = Depends(get_db),
):
    organization_id = resolve_organization_id(principal)
    service = ArrivalNoticeService(db)
    notice = service.get(arrival_notice_id, organization_id)
    return {"capabilities": service.capabilities(notice)}


@router.get("/arrival-notices/{arrival_notice_id}/files")
def get_arrival_notice_files(
    arrival_notice_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notice_transport.read")
    ),
    db: Session = Depends(get_db),
):
    organization_id = resolve_organization_id(principal)
    notice = ArrivalNoticeService(db).get(arrival_notice_id, organization_id)
    documents = list(
        db.scalars(
            select(ArrivalNoticeTransportDocumentModel).where(
                ArrivalNoticeTransportDocumentModel.revision_id
                == notice.active_revision_id,
                ArrivalNoticeTransportDocumentModel.status == "ACTIVE",
                ArrivalNoticeTransportDocumentModel.file_asset_id.is_not(None),
            )
        )
    )
    return [
        {
            "transport_document_id": item.id,
            "file_asset_id": item.file_asset_id,
            "document_kind": item.document_kind,
        }
        for item in documents
    ]


@router.get("/arrival-notices/{arrival_notice_id}/source-orders")
def get_arrival_notice_source_orders(
    arrival_notice_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.read")
    ),
    db: Session = Depends(get_db),
):
    organization_id = resolve_organization_id(principal)
    service = ArrivalNoticeService(db)
    notice = service.get(arrival_notice_id, organization_id)
    return {"purchase_order_codes": service.source_order_codes(notice.active_revision_id)}


@router.get(
    "/arrival-notices/{arrival_notice_id}/transport-readiness",
    response_model=ArrivalNoticeTransportReadinessResponse,
)
def get_arrival_notice_transport_readiness(
    arrival_notice_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notice_transport.read")
    ),
    db: Session = Depends(get_db),
):
    return ArrivalNoticeService(db).transport_readiness(
        arrival_notice_id, resolve_organization_id(principal)
    )


@router.get(
    "/arrival-notices/{arrival_notice_id}/revisions",
    response_model=list[ArrivalNoticeRevisionResponse],
)
def list_arrival_notice_revisions(
    arrival_notice_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.read")
    ),
    db: Session = Depends(get_db),
):
    organization_id = resolve_organization_id(principal)
    ArrivalNoticeService(db).get(arrival_notice_id, organization_id)
    return list(
        db.scalars(
            select(ArrivalNoticeRevisionModel)
            .where(ArrivalNoticeRevisionModel.arrival_notice_id == arrival_notice_id)
            .order_by(ArrivalNoticeRevisionModel.revision_number)
        )
    )


@router.post(
    "/arrival-notices/{arrival_notice_id}/revisions",
    response_model=ArrivalNoticeRevisionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_arrival_notice_revision(
    arrival_notice_id: UUID,
    payload: ArrivalNoticeRevisionCreate,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.update")
    ),
    db: Session = Depends(get_db),
):
    revision = ArrivalNoticeService(db).create_revision(
        arrival_notice_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload.change_summary,
        payload.idempotency_key,
    )
    db.commit()
    db.refresh(revision)
    return revision


@router.get(
    "/arrival-notice-revisions/{revision_id}",
    response_model=ArrivalNoticeRevisionResponse,
)
def get_arrival_notice_revision(
    revision_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.read")
    ),
    db: Session = Depends(get_db),
):
    return ArrivalNoticeService(db).get_revision(
        revision_id, resolve_organization_id(principal)
    )


@router.get(
    "/arrival-notice-revisions/{revision_id}/lines",
    response_model=list[ArrivalNoticeExpectedLineResponse],
)
def list_arrival_notice_lines(
    revision_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.read")
    ),
    db: Session = Depends(get_db),
):
    organization_id = resolve_organization_id(principal)
    ArrivalNoticeService(db).get_revision(revision_id, organization_id)
    return list(
        db.scalars(
            select(ArrivalNoticeExpectedLineModel)
            .where(
                ArrivalNoticeExpectedLineModel.arrival_notice_revision_id
                == revision_id
            )
            .order_by(ArrivalNoticeExpectedLineModel.line_number)
        )
    )


@router.post(
    "/arrival-notice-revisions/{revision_id}/lines",
    response_model=ArrivalNoticeExpectedLineResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_arrival_notice_line(
    revision_id: UUID,
    payload: ArrivalNoticeExpectedLineCreate,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.update")
    ),
    db: Session = Depends(get_db),
):
    line = ArrivalNoticeService(db).add_line(
        revision_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload.model_dump(),
    )
    db.commit()
    db.refresh(line)
    return line


@router.patch(
    "/arrival-notice-lines/{line_id}",
    response_model=ArrivalNoticeExpectedLineResponse,
)
def update_arrival_notice_line(
    line_id: UUID,
    payload: ArrivalNoticeExpectedLineUpdate,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.update")
    ),
    db: Session = Depends(get_db),
):
    line = ArrivalNoticeService(db).update_line(
        line_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload.model_dump(exclude_unset=True),
    )
    db.commit()
    db.refresh(line)
    return line


@router.post(
    "/arrival-notice-lines/{line_id}/cancel",
    response_model=ArrivalNoticeExpectedLineResponse,
)
def cancel_arrival_notice_line(
    line_id: UUID,
    reason: str = Body(embed=True, min_length=10, max_length=2000),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.update")
    ),
    db: Session = Depends(get_db),
):
    line = ArrivalNoticeService(db).cancel_line(
        line_id, resolve_organization_id(principal), principal.user_id, reason
    )
    db.commit()
    db.refresh(line)
    return line


@router.post("/arrival-notice-lines/reorder")
def reorder_arrival_notice_lines(
    revision_id: UUID = Body(),
    line_ids: list[UUID] = Body(),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.update")
    ),
    db: Session = Depends(get_db),
):
    organization_id = resolve_organization_id(principal)
    revision = ArrivalNoticeService(db).get_revision(
        revision_id, organization_id, lock=True
    )
    if revision.status != "EDITABLE":
        raise ArrivalNoticeNotEditable("La revisión está congelada.")
    lines = list(
        db.scalars(
            select(ArrivalNoticeExpectedLineModel).where(
                ArrivalNoticeExpectedLineModel.arrival_notice_revision_id
                == revision.id,
                ArrivalNoticeExpectedLineModel.id.in_(line_ids),
            )
        )
    )
    if len(lines) != len(line_ids):
        raise ArrivalNoticeNotFound("Una o más líneas no pertenecen a la revisión.")
    mapping = {line_id: index + 1 for index, line_id in enumerate(line_ids)}
    for line in lines:
        line.line_number = mapping[line.id]
    db.commit()
    return {"revision_id": revision.id, "line_ids": line_ids}


@router.post("/arrival-notice-lines/validate")
def validate_arrival_notice_lines(
    revision_id: UUID = Body(embed=True),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notices.validate")
    ),
    db: Session = Depends(get_db),
):
    organization_id = resolve_organization_id(principal)
    revision = ArrivalNoticeService(db).get_revision(revision_id, organization_id)
    lines = list(
        db.scalars(
            select(ArrivalNoticeExpectedLineModel).where(
                ArrivalNoticeExpectedLineModel.arrival_notice_revision_id
                == revision.id,
                ArrivalNoticeExpectedLineModel.status == "EXPECTED",
            )
        )
    )
    errors = []
    if not lines:
        errors.append({"code": "EXPECTED_LINE_REQUIRED"})
    return {"valid": not errors, "line_count": len(lines), "errors": errors}


@router.put("/arrival-notice-revisions/{revision_id}/vehicle-reference")
def set_arrival_notice_vehicle(
    revision_id: UUID,
    payload: ArrivalNoticeVehicleReferenceRequest,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notice_transport.manage")
    ),
    db: Session = Depends(get_db),
):
    reference = ArrivalNoticeService(db).set_vehicle_reference(
        revision_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload.model_dump(),
    )
    db.commit()
    return {
        "id": reference.id,
        "vehicle_id": reference.vehicle_id,
        "plate": reference.plate_snapshot,
        "source_type": reference.source_type,
    }


@router.put("/arrival-notice-revisions/{revision_id}/driver-reference")
def set_arrival_notice_driver(
    revision_id: UUID,
    payload: ArrivalNoticeDriverReferenceRequest,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notice_transport.manage")
    ),
    db: Session = Depends(get_db),
):
    reference = ArrivalNoticeService(db).set_driver_reference(
        revision_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload.model_dump(),
    )
    db.commit()
    return {
        "id": reference.id,
        "driver_id": reference.driver_id,
        "full_name": reference.full_name_snapshot,
        "source_type": reference.source_type,
    }


@router.get(
    "/arrival-notice-revisions/{revision_id}/transport-documents",
    response_model=list[ArrivalNoticeTransportDocumentResponse],
)
def list_transport_documents(
    revision_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notice_transport.read")
    ),
    db: Session = Depends(get_db),
):
    organization_id = resolve_organization_id(principal)
    ArrivalNoticeService(db).get_revision(revision_id, organization_id)
    return list(
        db.scalars(
            select(ArrivalNoticeTransportDocumentModel).where(
                ArrivalNoticeTransportDocumentModel.revision_id == revision_id
            )
        )
    )


@router.post(
    "/arrival-notice-revisions/{revision_id}/transport-documents",
    response_model=ArrivalNoticeTransportDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transport_document(
    revision_id: UUID,
    payload: ArrivalNoticeTransportDocumentCreate,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notice_transport.manage")
    ),
    db: Session = Depends(get_db),
):
    document = ArrivalNoticeService(db).add_transport_document(
        revision_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload.model_dump(),
    )
    db.commit()
    db.refresh(document)
    return document


@router.patch(
    "/arrival-transport-documents/{document_id}",
    response_model=ArrivalNoticeTransportDocumentResponse,
)
def update_transport_document(
    document_id: UUID,
    payload: ArrivalNoticeTransportDocumentUpdate,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notice_transport.manage")
    ),
    db: Session = Depends(get_db),
):
    organization_id = resolve_organization_id(principal)
    service = ArrivalNoticeService(db)
    document = service._transport_document_for_org(document_id, organization_id)
    revision = service.get_revision(document.revision_id, organization_id)
    if revision.status != "EDITABLE":
        raise ArrivalNoticeNotEditable("La revisión está congelada.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(document, field, value)
    if payload.series is not None or payload.number is not None:
        from app.modules.logistics.inbound.arrival_notices.application.services.common import (
            normalize_document_reference,
        )

        document.normalized_reference = normalize_document_reference(
            document.series, document.number
        )
        document.verification_status = "NOT_VERIFIED"
    db.commit()
    db.refresh(document)
    return document


@router.post(
    "/arrival-transport-documents/{document_id}/archive",
    response_model=ArrivalNoticeTransportDocumentResponse,
)
def archive_transport_document(
    document_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notice_transport.manage")
    ),
    db: Session = Depends(get_db),
):
    organization_id = resolve_organization_id(principal)
    service = ArrivalNoticeService(db)
    document = service._transport_document_for_org(document_id, organization_id)
    revision = service.get_revision(document.revision_id, organization_id)
    if revision.status != "EDITABLE":
        raise ArrivalNoticeNotEditable("La revisión está congelada.")
    document.status = "ARCHIVED"
    db.commit()
    db.refresh(document)
    return document


@router.post(
    "/arrival-transport-documents/{document_id}/verify-format",
    response_model=FormatVerificationResponse,
)
def verify_transport_document_format(
    document_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notice_transport.manage")
    ),
    db: Session = Depends(get_db),
):
    document = ArrivalNoticeService(db).verify_document_format(
        document_id, resolve_organization_id(principal)
    )
    db.commit()
    return {
        "document_id": document.id,
        "verification_status": document.verification_status,
        "external_verification_performed": False,
    }


@router.post(
    "/arrival-transport-documents/{document_id}/associate-file",
    response_model=ArrivalNoticeTransportDocumentResponse,
)
def associate_transport_document_file(
    document_id: UUID,
    payload: TransportDocumentAssociateFileRequest,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.arrival_notice_transport.manage")
    ),
    db: Session = Depends(get_db),
):
    document = ArrivalNoticeService(db).associate_document_file(
        document_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload.file_asset_id,
    )
    db.commit()
    db.refresh(document)
    return document


__all__ = ["router"]
