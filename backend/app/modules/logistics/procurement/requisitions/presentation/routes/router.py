"""FastAPI router for Purchase Requisitions (Phase 031)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.pdf_response import (
    PDF_RESPONSE_SCHEMA,
    build_pdf_download_response,
    build_pdf_preview_response,
)
from app.database.session import get_db
from app.modules.logistics.auth_dependencies import (
    require_permission,
    resolve_organization_id,
)
from app.modules.logistics.principal import LogisticsPrincipal
from app.services.audit_service import AuditService
from app.modules.logistics.procurement.requisitions.application.services.comment_service import (
    comment_service,
)
from app.modules.logistics.procurement.requisitions.application.services.decision_service import (
    purchase_requisition_decision_service,
)
from app.modules.logistics.procurement.requisitions.application.services.document_service import (
    purchase_requisition_document_service,
)
from app.modules.logistics.procurement.requisitions.application.services.line_service import (
    purchase_requisition_line_service,
)
from app.modules.logistics.procurement.requisitions.application.services.requisition_service import (
    purchase_requisition_service,
)
from app.modules.logistics.procurement.requisitions.application.services.revision_service import (
    revision_service,
)
from app.modules.logistics.procurement.requisitions.application.services.submission_service import (
    purchase_requisition_submission_service,
)
from app.modules.logistics.procurement.requisitions.presentation.schemas.dto import (
    CapabilitiesResponse,
    CommentCreateRequest,
    CommentResponse,
    HistoryResponse,
    LineCreateRequest,
    LineReorderRequest,
    LineResponse,
    LineUpdateRequest,
    RequisitionApproveRequest,
    RequisitionCancelRequest,
    RequisitionCreateRequest,
    RequisitionListResponse,
    RequisitionRejectRequest,
    RequisitionResponse,
    RequisitionReturnRequest,
    RequisitionSubmitRequest,
    RequisitionUpdateRequest,
    RequisitionWithdrawRequest,
    RevisionSummary,
    ValidationResponse,
)

router = APIRouter(
    prefix="/procurement/requisitions",
    tags=["Logistics - Purchase Requisitions"],
)


# -------------------------------------------------------------------------
# Requisition Lifecycle Endpoints
# -------------------------------------------------------------------------


@router.post(
    "",
    response_model=RequisitionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new draft purchase requisition",
)
def create_requisition(
    data: RequisitionCreateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.create")),
    db: Session = Depends(get_db),
) -> RequisitionResponse:
    org_id = resolve_organization_id(principal)
    user_name = getattr(principal, "user_name", "Usuario Solicitante") or "Usuario Solicitante"
    pr = purchase_requisition_service.create_draft(
        db=db,
        org_id=org_id,
        branch_id=data.branch_id,
        user_id=principal.user_id,
        user_name=user_name,
        cost_center_id=data.cost_center_id,
        priority=data.priority,
        required_date=data.required_date,
        justification=data.justification,
        requester_area=data.requester_area,
        business_purpose=data.business_purpose,
        destination_warehouse_id=data.destination_warehouse_id,
        delivery_location_description=data.delivery_location_description,
    )
    db.commit()
    db.refresh(pr)
    return RequisitionResponse.model_validate(pr)


@router.get(
    "",
    response_model=RequisitionListResponse,
    summary="List purchase requisitions",
)
def list_requisitions(
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    cost_center_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    requester_user_id: UUID | None = Query(default=None),
    mine: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.read")),
    db: Session = Depends(get_db),
) -> RequisitionListResponse:
    org_id = resolve_organization_id(principal)
    items, total = purchase_requisition_service.list(
        db=db,
        org_id=org_id,
        status_filter=status_filter,
        priority=priority,
        cost_center_id=cost_center_id,
        branch_id=branch_id,
        requester_user_id=requester_user_id,
        mine=mine,
        current_user_id=principal.user_id,
        skip=skip,
        limit=limit,
    )
    return RequisitionListResponse(
        items=[RequisitionResponse.model_validate(i) for i in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{requisition_id}",
    response_model=RequisitionResponse,
    summary="Get purchase requisition details",
)
def get_requisition(
    requisition_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.read")),
    db: Session = Depends(get_db),
) -> RequisitionResponse:
    org_id = resolve_organization_id(principal)
    pr = purchase_requisition_service.get(db=db, requisition_id=requisition_id, org_id=org_id)
    return RequisitionResponse.model_validate(pr)


@router.patch(
    "/{requisition_id}",
    response_model=RequisitionResponse,
    summary="Update a draft purchase requisition",
)
def update_requisition(
    requisition_id: UUID,
    data: RequisitionUpdateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.edit")),
    db: Session = Depends(get_db),
) -> RequisitionResponse:
    org_id = resolve_organization_id(principal)
    fields = data.model_dump(exclude_unset=True)
    row_version = fields.pop("row_version")
    pr = purchase_requisition_service.update_draft(
        db=db,
        requisition_id=requisition_id,
        org_id=org_id,
        user_id=principal.user_id,
        expected_row_version=row_version,
        **fields,
    )
    db.commit()
    db.refresh(pr)
    return RequisitionResponse.model_validate(pr)


@router.get(
    "/{requisition_id}/capabilities",
    response_model=CapabilitiesResponse,
    summary="Get user capabilities for a requisition",
)
def get_capabilities(
    requisition_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.read")),
    db: Session = Depends(get_db),
) -> CapabilitiesResponse:
    org_id = resolve_organization_id(principal)
    caps = purchase_requisition_service.get_capabilities(
        db=db, requisition_id=requisition_id, org_id=org_id, user_id=principal.user_id
    )
    return CapabilitiesResponse(**caps)


@router.post(
    "/{requisition_id}/validate",
    response_model=ValidationResponse,
    summary="Validate draft requisition completeness",
)
def validate_requisition(
    requisition_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.read")),
    db: Session = Depends(get_db),
) -> ValidationResponse:
    org_id = resolve_organization_id(principal)
    res = purchase_requisition_submission_service.validate_draft(
        db=db, requisition_id=requisition_id, org_id=org_id
    )
    return ValidationResponse(**res)


@router.post(
    "/{requisition_id}/submit",
    response_model=RequisitionResponse,
    summary="Submit requisition for approval",
)
def submit_requisition(
    requisition_id: UUID,
    data: RequisitionSubmitRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.submit")),
    db: Session = Depends(get_db),
) -> RequisitionResponse:
    org_id = resolve_organization_id(principal)
    pr = purchase_requisition_submission_service.submit(
        db=db,
        requisition_id=requisition_id,
        org_id=org_id,
        user_id=principal.user_id,
        expected_row_version=data.row_version,
        idempotency_key=data.idempotency_key,
        override_duplicate_warning=data.override_duplicate_warning,
        duplicate_justification=data.duplicate_justification,
    )
    db.commit()
    db.refresh(pr)
    return RequisitionResponse.model_validate(pr)


# -------------------------------------------------------------------------
# Decision Endpoints
# -------------------------------------------------------------------------


@router.post(
    "/{requisition_id}/start-review",
    response_model=RequisitionResponse,
    summary="Start review of a submitted requisition",
)
def start_review(
    requisition_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.review")),
    db: Session = Depends(get_db),
) -> RequisitionResponse:
    org_id = resolve_organization_id(principal)
    pr = purchase_requisition_decision_service.start_review(
        db=db, requisition_id=requisition_id, org_id=org_id, user_id=principal.user_id
    )
    db.commit()
    db.refresh(pr)
    return RequisitionResponse.model_validate(pr)


@router.post(
    "/{requisition_id}/approve",
    response_model=RequisitionResponse,
    summary="Approve purchase requisition",
)
def approve_requisition(
    requisition_id: UUID,
    data: RequisitionApproveRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.approve")),
    db: Session = Depends(get_db),
) -> RequisitionResponse:
    org_id = resolve_organization_id(principal)
    pr = purchase_requisition_decision_service.approve(
        db=db,
        requisition_id=requisition_id,
        org_id=org_id,
        user_id=principal.user_id,
        reason=data.reason,
    )
    db.commit()
    db.refresh(pr)
    return RequisitionResponse.model_validate(pr)


@router.post(
    "/{requisition_id}/reject",
    response_model=RequisitionResponse,
    summary="Reject purchase requisition",
)
def reject_requisition(
    requisition_id: UUID,
    data: RequisitionRejectRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.approve")),
    db: Session = Depends(get_db),
) -> RequisitionResponse:
    org_id = resolve_organization_id(principal)
    pr = purchase_requisition_decision_service.reject(
        db=db,
        requisition_id=requisition_id,
        org_id=org_id,
        user_id=principal.user_id,
        reason=data.reason,
    )
    db.commit()
    db.refresh(pr)
    return RequisitionResponse.model_validate(pr)


@router.post(
    "/{requisition_id}/return",
    response_model=RequisitionResponse,
    summary="Return requisition for changes",
)
def return_requisition(
    requisition_id: UUID,
    data: RequisitionReturnRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.approve")),
    db: Session = Depends(get_db),
) -> RequisitionResponse:
    org_id = resolve_organization_id(principal)
    pr = purchase_requisition_decision_service.return_for_changes(
        db=db,
        requisition_id=requisition_id,
        org_id=org_id,
        user_id=principal.user_id,
        reason=data.reason,
    )
    db.commit()
    db.refresh(pr)
    return RequisitionResponse.model_validate(pr)


@router.post(
    "/{requisition_id}/withdraw",
    response_model=RequisitionResponse,
    summary="Withdraw submitted requisition",
)
def withdraw_requisition(
    requisition_id: UUID,
    data: RequisitionWithdrawRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.submit")),
    db: Session = Depends(get_db),
) -> RequisitionResponse:
    org_id = resolve_organization_id(principal)
    pr = purchase_requisition_decision_service.withdraw(
        db=db,
        requisition_id=requisition_id,
        org_id=org_id,
        user_id=principal.user_id,
        reason=data.reason,
    )
    db.commit()
    db.refresh(pr)
    return RequisitionResponse.model_validate(pr)


@router.post(
    "/{requisition_id}/cancel",
    response_model=RequisitionResponse,
    summary="Cancel requisition",
)
def cancel_requisition(
    requisition_id: UUID,
    data: RequisitionCancelRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.cancel")),
    db: Session = Depends(get_db),
) -> RequisitionResponse:
    org_id = resolve_organization_id(principal)
    pr = purchase_requisition_decision_service.cancel(
        db=db,
        requisition_id=requisition_id,
        org_id=org_id,
        user_id=principal.user_id,
        reason=data.reason,
    )
    db.commit()
    db.refresh(pr)
    return RequisitionResponse.model_validate(pr)


# -------------------------------------------------------------------------
# Line Management Endpoints
# -------------------------------------------------------------------------


@router.post(
    "/{requisition_id}/lines",
    response_model=LineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add product line to active revision",
)
def add_line(
    requisition_id: UUID,
    data: LineCreateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.edit")),
    db: Session = Depends(get_db),
) -> LineResponse:
    org_id = resolve_organization_id(principal)
    pr = purchase_requisition_service.get(db=db, requisition_id=requisition_id, org_id=org_id)
    if not pr.active_revision_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail={"code": "NO_ACTIVE_REVISION"})

    line = purchase_requisition_line_service.add_line(
        db=db,
        revision_id=pr.active_revision_id,
        org_id=org_id,
        user_id=principal.user_id,
        product_id=data.product_id,
        requested_quantity_str=data.requested_quantity,
        requested_unit_id=data.requested_unit_id,
        line_justification=data.line_justification,
        notes=data.notes,
        manufacturer_reference=data.manufacturer_reference,
        preferred_brand_reference=data.preferred_brand_reference,
        required_date=data.required_date,
        destination_warehouse_id=data.destination_warehouse_id,
        specifications=data.specifications,
        priority_override=data.priority_override,
    )
    db.commit()
    db.refresh(line)
    return LineResponse.model_validate(line)


@router.get(
    "/{requisition_id}/lines",
    response_model=list[LineResponse],
    summary="List lines of the active revision",
)
def get_lines(
    requisition_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.read")),
    db: Session = Depends(get_db),
) -> list[LineResponse]:
    org_id = resolve_organization_id(principal)
    pr = purchase_requisition_service.get(db=db, requisition_id=requisition_id, org_id=org_id)
    if not pr.active_revision_id:
        return []
    lines = purchase_requisition_line_service.get_lines(db=db, revision_id=pr.active_revision_id)
    return [LineResponse.model_validate(l) for l in lines]


@router.patch(
    "/{requisition_id}/lines/{line_id}",
    response_model=LineResponse,
    summary="Update a product line",
)
def update_line(
    requisition_id: UUID,
    line_id: UUID,
    data: LineUpdateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.edit")),
    db: Session = Depends(get_db),
) -> LineResponse:
    org_id = resolve_organization_id(principal)
    fields = data.model_dump(exclude_unset=True)
    if "requested_quantity" in fields:
        fields["requested_quantity_str"] = fields.pop("requested_quantity")
    line = purchase_requisition_line_service.update_line(
        db=db,
        line_id=line_id,
        org_id=org_id,
        user_id=principal.user_id,
        **fields,
    )
    db.commit()
    db.refresh(line)
    return LineResponse.model_validate(line)


@router.delete(
    "/{requisition_id}/lines/{line_id}",
    response_model=LineResponse,
    summary="Remove a line from active revision",
)
def remove_line(
    requisition_id: UUID,
    line_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.edit")),
    db: Session = Depends(get_db),
) -> LineResponse:
    org_id = resolve_organization_id(principal)
    line = purchase_requisition_line_service.remove_line(
        db=db, line_id=line_id, org_id=org_id, user_id=principal.user_id
    )
    db.commit()
    return LineResponse.model_validate(line)


@router.post(
    "/{requisition_id}/lines/reorder",
    response_model=list[LineResponse],
    summary="Reorder lines of active revision",
)
def reorder_lines(
    requisition_id: UUID,
    data: LineReorderRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.edit")),
    db: Session = Depends(get_db),
) -> list[LineResponse]:
    org_id = resolve_organization_id(principal)
    pr = purchase_requisition_service.get(db=db, requisition_id=requisition_id, org_id=org_id)
    if not pr.active_revision_id:
        return []
    lines = purchase_requisition_line_service.reorder_lines(
        db=db, revision_id=pr.active_revision_id, line_ids=data.line_ids, user_id=principal.user_id
    )
    db.commit()
    return [LineResponse.model_validate(l) for l in lines]


# -------------------------------------------------------------------------
# Revisions and History
# -------------------------------------------------------------------------


@router.get(
    "/{requisition_id}/revisions",
    response_model=list[RevisionSummary],
    summary="List revision history",
)
def list_revisions(
    requisition_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.read")),
    db: Session = Depends(get_db),
) -> list[RevisionSummary]:
    org_id = resolve_organization_id(principal)
    revs = revision_service.list_revisions(db=db, requisition_id=requisition_id, org_id=org_id)
    return [RevisionSummary.model_validate(r) for r in revs]


@router.get(
    "/{requisition_id}/history",
    response_model=HistoryResponse,
    summary="Get complete decision and state transition history",
)
def get_history(
    requisition_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.read")),
    db: Session = Depends(get_db),
) -> HistoryResponse:
    org_id = resolve_organization_id(principal)
    history = purchase_requisition_service.get_history(db=db, requisition_id=requisition_id, org_id=org_id)
    return HistoryResponse(
        requisition_id=requisition_id,
        history=[
            {
                "event": h["event"],
                "actor": h["actor"],
                "timestamp": h["timestamp"],
                "details": h["details"],
            }
            for h in history
        ],
    )


# -------------------------------------------------------------------------
# Comments
# -------------------------------------------------------------------------


@router.post(
    "/{requisition_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment to requisition",
)
def add_comment(
    requisition_id: UUID,
    data: CommentCreateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.comment")),
    db: Session = Depends(get_db),
) -> CommentResponse:
    org_id = resolve_organization_id(principal)
    c = comment_service.add_comment(
        db=db,
        requisition_id=requisition_id,
        org_id=org_id,
        user_id=principal.user_id,
        body=data.body,
        comment_type=data.comment_type,
        visibility=data.visibility,
    )
    db.commit()
    db.refresh(c)
    return CommentResponse.model_validate(c)


@router.get(
    "/{requisition_id}/comments",
    response_model=list[CommentResponse],
    summary="List comments of a requisition",
)
def list_comments(
    requisition_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.read")),
    db: Session = Depends(get_db),
) -> list[CommentResponse]:
    org_id = resolve_organization_id(principal)
    comments = comment_service.list_comments(
        db=db, requisition_id=requisition_id, org_id=org_id, user_id=principal.user_id
    )
    return [CommentResponse.model_validate(c) for c in comments]


# -------------------------------------------------------------------------
# Documents (PDF Preview & Issue)
# -------------------------------------------------------------------------


def _record_requisition_document_event(
    db: Session,
    principal: LogisticsPrincipal,
    requisition_id: UUID,
    pdf_bytes: bytes,
    *,
    downloaded: bool,
) -> None:
    """Record viewing vs downloading the requisition document as distinct events.

    Call only after the PDF has been validated, so a failed render is never
    recorded as a delivered document.
    """
    AuditService().record(
        db=db,
        event_type=(
            "logistics.purchase_requisition.document_downloaded"
            if downloaded
            else "logistics.document.preview_rendered"
        ),
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="purchase_requisition_document",
        resource_id=str(requisition_id),
        event_metadata={
            "requisition_id": str(requisition_id),
            "size_bytes": len(pdf_bytes),
            "delivery": "attachment" if downloaded else "inline",
        },
    )
    db.commit()


@router.get(
    "/{requisition_id}/document/preview",
    summary="Generate PDF preview (watermarked, non-official)",
    responses=PDF_RESPONSE_SCHEMA,
)
def preview_document(
    requisition_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.read")),
    db: Session = Depends(get_db),
) -> Response:
    org_id = resolve_organization_id(principal)
    pdf_bytes = purchase_requisition_document_service.preview(
        db=db, requisition_id=requisition_id, org_id=org_id, user_id=principal.user_id
    )
    response = build_pdf_preview_response(pdf_bytes, f"REQ-PREVIEW-{requisition_id}.pdf")
    _record_requisition_document_event(db, principal, requisition_id, pdf_bytes, downloaded=False)
    return response


@router.get(
    "/{requisition_id}/document/preview.pdf",
    summary="Download PDF preview (watermarked, non-official)",
    responses=PDF_RESPONSE_SCHEMA,
)
def download_document_preview(
    requisition_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.read")),
    db: Session = Depends(get_db),
) -> Response:
    """Same watermarked render as the preview, delivered as an explicit download."""
    org_id = resolve_organization_id(principal)
    pdf_bytes = purchase_requisition_document_service.preview(
        db=db, requisition_id=requisition_id, org_id=org_id, user_id=principal.user_id
    )
    response = build_pdf_download_response(pdf_bytes, f"REQ-PREVIEW-{requisition_id}.pdf")
    _record_requisition_document_event(db, principal, requisition_id, pdf_bytes, downloaded=True)
    return response


@router.post(
    "/{requisition_id}/document/issue",
    summary="Issue official document PDF for APPROVED requisition",
)
def issue_document(
    requisition_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.purchase_requisitions.issue")),
    db: Session = Depends(get_db),
) -> dict:
    org_id = resolve_organization_id(principal)
    result = purchase_requisition_document_service.issue_document(
        db=db, requisition_id=requisition_id, org_id=org_id, user_id=principal.user_id
    )
    db.commit()
    return result
