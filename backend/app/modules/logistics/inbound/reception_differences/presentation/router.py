"""HTTP contract for Phase 040 - Reception Differences."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission, resolve_organization_id, verify_csrf
from app.modules.logistics.inbound.arrival_notices.application.services.idempotency import (
    get_idempotent_response, save_idempotent_response,
)
from app.modules.logistics.principal import LogisticsPrincipal

from ..application.queries.get_case import get_case_query, get_case_summary
from ..application.queries.get_evidence import get_evidence_query, get_item_evidence_query
from ..application.queries.get_items import get_items_query, get_item_query
from ..application.queries.get_responsibility import get_responsibility_query, get_single_responsibility_query
from ..application.queries.list_cases import list_cases_query
from ..application.services.acknowledgement_service import ReceptionDifferenceAcknowledgementService
from ..application.services.approval_service import ReceptionDifferenceApprovalService
from ..application.services.case_service import ReceptionDifferenceCaseService
from ..application.services.claim_preparation import FutureClaimPreparationService
from ..application.services.document_service import ReceptionDifferenceDocumentService
from ..application.services.evidence_service import ReceptionDifferenceEvidenceService
from ..application.services.formalization_service import ReceptionDifferenceCandidateFormalizationService
from ..application.services.integrity_service import ReceptionDifferenceIntegrityService
from ..application.services.item_service import ReceptionDifferenceItemService
from ..application.services.manual_creation_service import ManualReceptionDifferenceService
from ..application.services.quality_preparation import QualityInspectionPreparationService
from ..application.services.quarantine_recommendation import FutureQuarantineRecommendationService
from ..application.services.responsibility_service import ReceptionDifferenceResponsibilityService
from ..application.services.review_service import ReceptionDifferenceReviewService
from ..application.services.validation_service import ReceptionDifferenceValidationService
from ..domain.errors import reception_difference_error
from ..infrastructure.persistence.models import (
    ReceptionDifferenceAcknowledgementModel,
    ReceptionDifferenceApprovalModel,
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceDocumentPackageModel,
    ReceptionDifferenceEvidenceLinkModel,
    ReceptionDifferenceItemModel,
    ReceptionDifferenceResponsiblePartyModel,
    ReceptionDifferenceReviewModel,
)
from .schemas import *  # noqa: F403

router = APIRouter(tags=["Reception Differences (Phase 040)"])
IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)]


def org(principal: LogisticsPrincipal) -> UUID: return resolve_organization_id(principal)


def command(db: Session, principal: LogisticsPrincipal, key: str, operation: str, payload: dict, execute):
    organization_id = org(principal)
    encoded = jsonable_encoder(payload)
    replay = get_idempotent_response(db, organization_id, operation, key, encoded)
    if replay is not None:
        return replay
    value = execute()
    if isinstance(value, dict):
        response = jsonable_encoder(value)
    elif isinstance(value, (list, tuple)):
        response = jsonable_encoder([
            jsonable_encoder({c.name: getattr(item, c.name) for c in item.__table__.columns}) if hasattr(item, "__table__") else item
            for item in value
        ])
    else:
        response = jsonable_encoder({c.name: getattr(value, c.name) for c in value.__table__.columns})
    save_idempotent_response(db, organization_id, principal.user_id, operation, key, encoded, response)
    db.commit()
    return value


def case_for(db: Session, principal: LogisticsPrincipal, case_id: UUID) -> ReceptionDifferenceCaseModel:
    return get_case_query(db, case_id, org(principal))


def item_for(db: Session, principal: LogisticsPrincipal, item_id: UUID) -> ReceptionDifferenceItemModel:
    return get_item_query(db, item_id, org(principal))


# ──────────────────────────────────────────────────────────────────────────────
# Cases (15)
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/reception-difference-cases", response_model=ReceptionDifferenceCaseListResponse)
def list_cases(
    search: str | None = None, case_code: str | None = None, receipt_code: str | None = None,
    supplier_id: UUID | None = None, carrier_id: UUID | None = None, warehouse_id: UUID | None = None,
    product_id: UUID | None = None, difference_type: str | None = None, category: str | None = None,
    severity: str | None = None, status: str | None = None, responsibility_status: str | None = None,
    has_photos: bool | None = None, has_critical_items: bool | None = None, has_disputes: bool | None = None,
    created_from: str | None = None, created_to: str | None = None, mine: bool = False,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    sort_by: str = "created_at", sort_direction: str = "desc",
    principal=Depends(require_permission("logistics.reception_difference_cases.read")),
    db: Session = Depends(get_db),
):
    from datetime import datetime as _dt
    filters = {}
    if status: filters["status"] = status
    if severity: filters["severity"] = severity
    if warehouse_id: filters["warehouse_id"] = warehouse_id
    if supplier_id: filters["supplier_id"] = supplier_id
    if has_critical_items is not None: filters["has_critical_items"] = has_critical_items
    if has_disputes is not None: filters["has_disputes"] = has_disputes
    cf = _dt.fromisoformat(created_from) if created_from else None
    ct = _dt.fromisoformat(created_to) if created_to else None
    rows, total = list_cases_query(
        db, org(principal), search=search, status=status, severity=severity,
        warehouse_id=warehouse_id, supplier_id=supplier_id, carrier_id=carrier_id,
        receipt_id=None, difference_type=difference_type, has_disputes=has_disputes,
        has_critical_items=has_critical_items, created_from=cf, created_to=ct,
        page=page, page_size=page_size, sort_by=sort_by, sort_direction=sort_direction,
    )
    items = [{
        "id": r.id, "case_code": r.case_code, "inbound_receipt_id": r.inbound_receipt_id,
        "status": r.status, "source_type": r.source_type, "severity": r.severity,
        "item_count": r.item_count, "open_item_count": r.open_item_count,
        "critical_item_count": r.critical_item_count, "evidence_count": r.evidence_count,
        "responsibility_status": r.responsibility_status, "created_at": r.created_at, "updated_at": r.updated_at,
    } for r in rows]
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.get("/reception-difference-cases/summary")
def get_cases_summary(
    principal=Depends(require_permission("logistics.reception_difference_cases.read")),
    db: Session = Depends(get_db),
):
    organization_id = org(principal)
    terminal_statuses = ("CLOSED", "CANCELLED", "SUPERSEDED")

    case_counts = db.execute(
        select(
            func.count(ReceptionDifferenceCaseModel.id)
            .filter(ReceptionDifferenceCaseModel.status.notin_(terminal_statuses))
            .label("open_cases"),
            func.count(ReceptionDifferenceCaseModel.id)
            .filter(ReceptionDifferenceCaseModel.severity == "CRITICAL")
            .label("critical_differences"),
        ).where(ReceptionDifferenceCaseModel.organization_id == organization_id)
    ).one()

    missing_document_types = (
        "DOCUMENT_MISSING",
        "GUIDE_MISSING",
        "CERTIFICATE_MISSING",
        "PACKING_LIST_MISSING",
    )
    item_counts = db.execute(
        select(
            func.count(ReceptionDifferenceItemModel.id)
            .filter(ReceptionDifferenceItemModel.difference_type == "SHORTAGE")
            .label("shortages"),
            func.count(ReceptionDifferenceItemModel.id)
            .filter(ReceptionDifferenceItemModel.difference_type == "OVERAGE")
            .label("overages"),
            func.count(ReceptionDifferenceItemModel.id)
            .filter(ReceptionDifferenceItemModel.difference_type.in_(("PRODUCT_DAMAGED", "PACKAGING_DAMAGED")))
            .label("damages"),
            func.count(ReceptionDifferenceItemModel.id)
            .filter(ReceptionDifferenceItemModel.difference_type.in_(missing_document_types))
            .label("missing_documents"),
        )
        .join(
            ReceptionDifferenceCaseModel,
            ReceptionDifferenceCaseModel.id == ReceptionDifferenceItemModel.difference_case_id,
        )
        .where(
            ReceptionDifferenceCaseModel.organization_id == organization_id,
            ReceptionDifferenceCaseModel.status.notin_(("CANCELLED", "SUPERSEDED")),
        )
    ).one()

    return {
        "open_cases": int(case_counts.open_cases or 0),
        "critical_differences": int(case_counts.critical_differences or 0),
        "shortages": int(item_counts.shortages or 0),
        "overages": int(item_counts.overages or 0),
        "damages": int(item_counts.damages or 0),
        "missing_documents": int(item_counts.missing_documents or 0),
    }


@router.post("/reception-difference-cases", response_model=ReceptionDifferenceCaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    body: ReceptionDifferenceCaseCreate, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_cases.create")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    def execute():
        svc = ReceptionDifferenceCaseService(db)
        from sqlalchemy import select
        from ..infrastructure.persistence.models import InboundReceiptModel
        receipt = db.scalar(select(InboundReceiptModel).where(InboundReceiptModel.id == body.inbound_receipt_id, InboundReceiptModel.organization_id == org(principal)))
        if not receipt:
            raise reception_difference_error("INBOUND_RECEIPT_NOT_FOUND", "Recepción no encontrada.", 404)
        return svc.create_case(
            organization_id=org(principal), branch_id=receipt.branch_id, warehouse_id=receipt.warehouse_id,
            inbound_receipt_id=body.inbound_receipt_id, receipt_revision_id=receipt.active_revision_id,
            source_type=body.source_type, supplier_snapshot=receipt.supplier_snapshot or {},
            carrier_snapshot=receipt.carrier_snapshot, unloading_operation_id=receipt.unloading_operation_id,
            gate_check_in_id=None, appointment_id=None, arrival_notice_id=None, principal=principal,
        )
    return command(db, principal, idempotency_key, "phase040.case.create", body.model_dump(), execute)


@router.post("/reception-difference-cases/from-receipt", response_model=ReceptionDifferenceCaseResponse, status_code=status.HTTP_201_CREATED)
def create_from_receipt(
    body: ReceptionDifferenceCaseFromReceiptCreate, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_cases.create")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    def execute():
        svc = ReceptionDifferenceCaseService(db)
        from sqlalchemy import select
        from ..infrastructure.persistence.models import InboundReceiptModel
        receipt = db.scalar(select(InboundReceiptModel).where(InboundReceiptModel.id == body.inbound_receipt_id, InboundReceiptModel.organization_id == org(principal)))
        if not receipt:
            raise reception_difference_error("INBOUND_RECEIPT_NOT_FOUND", "Recepción no encontrada.", 404)
        revision_id = body.receipt_revision_id or receipt.active_revision_id
        return svc.create_case(
            organization_id=org(principal), branch_id=receipt.branch_id, warehouse_id=receipt.warehouse_id,
            inbound_receipt_id=body.inbound_receipt_id, receipt_revision_id=revision_id,
            source_type=body.source_type, supplier_snapshot=receipt.supplier_snapshot or {},
            carrier_snapshot=receipt.carrier_snapshot, unloading_operation_id=receipt.unloading_operation_id,
            gate_check_in_id=None, appointment_id=None, arrival_notice_id=None, principal=principal,
        )
    return command(db, principal, idempotency_key, "phase040.case.create_from_receipt", body.model_dump(), execute)


@router.get("/reception-difference-cases/{case_id}", response_model=ReceptionDifferenceCaseDetail)
def get_case(case_id: UUID, principal=Depends(require_permission("logistics.reception_difference_cases.read")), db: Session = Depends(get_db)):
    case = case_for(db, principal, case_id)
    items = [jsonable_encoder({c.name: getattr(i, c.name) for c in ReceptionDifferenceItemModel.__table__.columns}) for i in db.scalars(select(ReceptionDifferenceItemModel).where(ReceptionDifferenceItemModel.difference_case_id == case.id))]
    evidence = [jsonable_encoder({c.name: getattr(e, c.name) for c in ReceptionDifferenceEvidenceLinkModel.__table__.columns}) for e in db.scalars(select(ReceptionDifferenceEvidenceLinkModel).where(ReceptionDifferenceEvidenceLinkModel.difference_case_id == case.id))]
    resp = [jsonable_encoder({c.name: getattr(r, c.name) for c in ReceptionDifferenceResponsiblePartyModel.__table__.columns}) for r in db.scalars(select(ReceptionDifferenceResponsiblePartyModel).where(ReceptionDifferenceResponsiblePartyModel.difference_case_id == case.id))]
    reviews = [jsonable_encoder({c.name: getattr(r, c.name) for c in ReceptionDifferenceReviewModel.__table__.columns}) for r in db.scalars(select(ReceptionDifferenceReviewModel).where(ReceptionDifferenceReviewModel.difference_case_id == case.id))]
    approvals = [jsonable_encoder({c.name: getattr(a, c.name) for c in ReceptionDifferenceApprovalModel.__table__.columns}) for a in db.scalars(select(ReceptionDifferenceApprovalModel).where(ReceptionDifferenceApprovalModel.difference_case_id == case.id))]
    acks = [jsonable_encoder({c.name: getattr(a, c.name) for c in ReceptionDifferenceAcknowledgementModel.__table__.columns}) for a in db.scalars(select(ReceptionDifferenceAcknowledgementModel).where(ReceptionDifferenceAcknowledgementModel.difference_case_id == case.id))]
    metrics = jsonable_encoder({c.name: getattr(case, c.name) for c in ReceptionDifferenceCaseModel.__table__.columns})
    return {
        **jsonable_encoder({c.name: getattr(case, c.name) for c in ReceptionDifferenceCaseModel.__table__.columns}),
        "case_revisions": [], "items": items, "evidence_links": evidence,
        "responsible_parties": resp, "reviews": reviews, "approvals": approvals,
        "acknowledgements": acks, "metrics": metrics,
    }


@router.patch("/reception-difference-cases/{case_id}", response_model=ReceptionDifferenceCaseResponse)
def update_case(
    case_id: UUID, body: ReceptionDifferenceCaseUpdate, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_cases.update")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    def execute():
        return ReceptionDifferenceCaseService(db).update_case(case_id, org(principal), principal, **body.model_dump(exclude_unset=True))
    return command(db, principal, idempotency_key, f"phase040.case.update:{case_id}", body.model_dump(), execute)


@router.post("/reception-difference-cases/{case_id}/validate")
def validate_case(case_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_cases.read")), db: Session = Depends(get_db)):
    return command(db, principal, idempotency_key, f"phase040.case.validate:{case_id}", {}, lambda: ReceptionDifferenceValidationService(db).validate(case_id, org(principal)))


@router.post("/reception-difference-cases/{case_id}/submit")
def submit_case(case_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_cases.submit")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return command(db, principal, idempotency_key, f"phase040.case.submit:{case_id}", {}, lambda: ReceptionDifferenceCaseService(db).transition_case(case_id, "SUBMITTED_FOR_REVIEW", principal))


@router.post("/reception-difference-cases/{case_id}/start-review")
def start_review(case_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_cases.review")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return command(db, principal, idempotency_key, f"phase040.case.start_review:{case_id}", {}, lambda: ReceptionDifferenceCaseService(db).transition_case(case_id, "UNDER_REVIEW", principal))


@router.post("/reception-difference-cases/{case_id}/request-changes")
def request_changes(case_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_cases.review")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return command(db, principal, idempotency_key, f"phase040.case.request_changes:{case_id}", body.model_dump(), lambda: ReceptionDifferenceCaseService(db).transition_case(case_id, "UNDER_PREPARATION", principal, reason=body.reason))


@router.post("/reception-difference-cases/{case_id}/mark-ready-for-approval")
def mark_ready_for_approval(case_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_cases.approve")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return command(db, principal, idempotency_key, f"phase040.case.mark_ready:{case_id}", {}, lambda: ReceptionDifferenceCaseService(db).transition_case(case_id, "READY_FOR_APPROVAL", principal))


@router.post("/reception-difference-cases/{case_id}/approve")
def approve_case(case_id: UUID, body: ReceptionDifferenceApprovalDecisionRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_cases.approve")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    def execute():
        svc = ReceptionDifferenceApprovalService(db)
        approval = svc.create_approval_decision(case_id, body.decision, body.reason, org(principal), principal)
        case_svc = ReceptionDifferenceCaseService(db)
        if body.decision == "APPROVE_FOR_ISSUE":
            case_svc.transition_case(case_id, "APPROVED", principal)
        elif body.decision == "REQUEST_CHANGES":
            case_svc.transition_case(case_id, "UNDER_PREPARATION", principal, reason=body.reason)
        elif body.decision == "REJECT_CASE":
            case_svc.transition_case(case_id, "CANCELLED", principal, reason=body.reason)
        return approval
    return command(db, principal, idempotency_key, f"phase040.case.approve:{case_id}", body.model_dump(), execute)


@router.post("/reception-difference-cases/{case_id}/cancel")
def cancel_case(case_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_cases.cancel")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return command(db, principal, idempotency_key, f"phase040.case.cancel:{case_id}", body.model_dump(), lambda: ReceptionDifferenceCaseService(db).transition_case(case_id, "CANCELLED", principal, reason=body.reason))


@router.post("/reception-difference-cases/{case_id}/close")
def close_case(case_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_cases.close")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return command(db, principal, idempotency_key, f"phase040.case.close:{case_id}", {}, lambda: ReceptionDifferenceCaseService(db).transition_case(case_id, "CLOSED", principal))


@router.get("/reception-difference-cases/{case_id}/history")
def case_history(case_id: UUID, principal=Depends(require_permission("logistics.reception_difference_cases.read")), db: Session = Depends(get_db)):
    return command(db, principal, f"phase040.case.history:{case_id}", f"phase040.case.history:{case_id}", {}, lambda: ReceptionDifferenceCaseService(db).get_history(case_id, org(principal)))


@router.get("/reception-difference-cases/{case_id}/capabilities")
def case_capabilities(case_id: UUID, principal=Depends(require_permission("logistics.reception_difference_cases.read")), db: Session = Depends(get_db)):
    return command(db, principal, f"phase040.case.capabilities:{case_id}", f"phase040.case.capabilities:{case_id}", {}, lambda: ReceptionDifferenceCaseService(db).get_capabilities(case_id, org(principal)))


@router.get("/reception-difference-cases/{case_id}/integrity")
def case_integrity(case_id: UUID, principal=Depends(require_permission("logistics.reception_difference_cases.read")), db: Session = Depends(get_db)):
    return command(db, principal, f"phase040.case.integrity:{case_id}", f"phase040.case.integrity:{case_id}", {}, lambda: ReceptionDifferenceCaseService(db).get_integrity(case_id, org(principal)))


# ──────────────────────────────────────────────────────────────────────────────
# Items (10)
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/reception-difference-cases/{case_id}/items")
def list_items(case_id: UUID, principal=Depends(require_permission("logistics.reception_difference_items.read")), db: Session = Depends(get_db)):
    return command(db, principal, f"phase040.items.list:{case_id}", f"phase040.items.list:{case_id}", {}, lambda: get_items_query(db, case_id, org(principal)))


@router.post("/reception-difference-cases/{case_id}/items", status_code=status.HTTP_201_CREATED)
def create_item(
    case_id: UUID, body: ReceptionDifferenceItemCreate, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_items.create")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    def execute():
        case = case_for(db, principal, case_id)
        return ManualReceptionDifferenceService(db).create_manual_item(
            case_id=case_id, organization_id=org(principal), difference_type=body.difference_type,
            title=body.title, description=body.description, product_id=body.product_id,
            severity=body.severity, observed_quantity=body.expected_quantity or "0",
            observed_unit_id=body.observed_unit_id, principal=principal,
        )
    return command(db, principal, idempotency_key, f"phase040.item.create:{case_id}", body.model_dump(), execute)


@router.post("/reception-difference-cases/{case_id}/formalize-candidates")
def formalize_candidates(
    case_id: UUID, body: ReceptionDifferenceFormalizeCandidatesRequest, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_items.create")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    return command(db, principal, idempotency_key, f"phase040.formalize:{case_id}", body.model_dump(),
                   lambda: ReceptionDifferenceCandidateFormalizationService(db).formalize_candidates(case_id, body.candidate_ids, org(principal), principal))


@router.post("/reception-difference-candidates/{candidate_id}/formalize")
def formalize_single(
    candidate_id: UUID, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_items.create")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    def execute():
        from sqlalchemy import select
        from ..infrastructure.persistence.models import ReceptionDifferenceCandidateModel
        candidate = db.get(ReceptionDifferenceCandidateModel, candidate_id)
        if not candidate:
            raise reception_difference_error("RECEPTION_DIFFERENCE_CANDIDATE_NOT_FOUND", "Candidato no encontrado.", 404)
        return ReceptionDifferenceCandidateFormalizationService(db).formalize_single_candidate(
            candidate_id, candidate.inbound_receipt_id, org(principal), principal,
        )
    return command(db, principal, idempotency_key, f"phase040.formalize_single:{candidate_id}", {}, execute)


@router.get("/reception-difference-items/{item_id}", response_model=ReceptionDifferenceItemResponse)
def get_item(item_id: UUID, principal=Depends(require_permission("logistics.reception_difference_items.read")), db: Session = Depends(get_db)):
    return get_item_query(db, item_id, org(principal))


@router.patch("/reception-difference-items/{item_id}", response_model=ReceptionDifferenceItemResponse)
def update_item(
    item_id: UUID, body: ReceptionDifferenceItemUpdate, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_items.update")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    return command(db, principal, idempotency_key, f"phase040.item.update:{item_id}", body.model_dump(),
                   lambda: ReceptionDifferenceItemService(db).update_item(item_id, org(principal), **body.model_dump(exclude_unset=True)))


@router.post("/reception-difference-items/{item_id}/validate")
def validate_item(item_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_items.read")), db: Session = Depends(get_db)):
    def execute():
        item = get_item_query(db, item_id, org(principal))
        return ReceptionDifferenceValidationService(db).validate(item.difference_case_id, org(principal))
    return command(db, principal, idempotency_key, f"phase040.item.validate:{item_id}", {}, execute)


@router.post("/reception-difference-items/{item_id}/dismiss")
def dismiss_item(item_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_items.dismiss")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return command(db, principal, idempotency_key, f"phase040.item.dismiss:{item_id}", body.model_dump(),
                   lambda: ReceptionDifferenceItemService(db).dismiss_item(item_id, org(principal), body.reason, principal))


@router.post("/reception-difference-items/{item_id}/mark-follow-up-required")
def mark_follow_up(item_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_items.update")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    def execute():
        item = get_item_query(db, item_id, org(principal))
        item.requires_evidence = True
        item.row_version += 1
        db.flush()
        return item
    return command(db, principal, idempotency_key, f"phase040.item.follow_up:{item_id}", {}, execute)


@router.post("/reception-difference-items/{item_id}/supersede")
def supersede_item(item_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_items.update")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return command(db, principal, idempotency_key, f"phase040.item.supersede:{item_id}", {},
                   lambda: ReceptionDifferenceItemService(db).supersede_item(item_id, org(principal), principal))


# ──────────────────────────────────────────────────────────────────────────────
# Evidence (7)
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/reception-difference-cases/{case_id}/evidence")
def list_evidence(case_id: UUID, principal=Depends(require_permission("logistics.reception_difference_evidence.read")), db: Session = Depends(get_db)):
    return command(db, principal, f"phase040.evidence.list:{case_id}", f"phase040.evidence.list:{case_id}", {},
                   lambda: get_evidence_query(db, case_id, org(principal)))


@router.post("/reception-difference-cases/{case_id}/evidence-links", status_code=status.HTTP_201_CREATED)
def link_evidence(
    case_id: UUID, body: ReceptionDifferenceEvidenceLinkCreate, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_evidence.create")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    return command(db, principal, idempotency_key, f"phase040.evidence.link:{case_id}", body.model_dump(),
                   lambda: ReceptionDifferenceEvidenceService(db).link_evidence(
                       case_id=case_id, item_id=body.difference_item_id, file_asset_id=body.file_asset_id,
                       file_version_id=None, evidence_type=body.evidence_type,
                       classification=body.classification or "STANDARD",
                       description=body.description, captured_at=body.captured_at, principal=principal,
                   ))


@router.get("/reception-difference-items/{item_id}/evidence")
def list_item_evidence(item_id: UUID, principal=Depends(require_permission("logistics.reception_difference_evidence.read")), db: Session = Depends(get_db)):
    return command(db, principal, f"phase040.evidence.item:{item_id}", f"phase040.evidence.item:{item_id}", {},
                   lambda: get_item_evidence_query(db, item_id, org(principal)))


@router.post("/reception-difference-items/{item_id}/evidence-links", status_code=status.HTTP_201_CREATED)
def link_item_evidence(
    item_id: UUID, body: ReceptionDifferenceEvidenceLinkCreate, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_evidence.create")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    def execute():
        item = get_item_query(db, item_id, org(principal))
        return ReceptionDifferenceEvidenceService(db).link_evidence(
            case_id=item.difference_case_id, item_id=item_id, file_asset_id=body.file_asset_id,
            file_version_id=None, evidence_type=body.evidence_type,
            classification=body.classification or "STANDARD",
            description=body.description, captured_at=body.captured_at, principal=principal,
        )
    return command(db, principal, idempotency_key, f"phase040.evidence.link_item:{item_id}", body.model_dump(), execute)


@router.post("/reception-difference-cases/{case_id}/photo-upload-sessions", status_code=status.HTTP_201_CREATED)
def create_photo_session(case_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_evidence.create")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    def execute():
        case_for(db, principal, case_id)
        from uuid import uuid4 as _uuid4
        session_id = _uuid4()
        return {"session_id": str(session_id), "case_id": str(case_id), "status": "PENDING", "upload_url": f"/api/v1/photo-sessions/{session_id}/upload"}
    return command(db, principal, idempotency_key, f"phase040.photo_session:{case_id}", {}, execute)


@router.post("/reception-difference-items/{item_id}/photo-upload-sessions", status_code=status.HTTP_201_CREATED)
def create_item_photo_session(item_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_evidence.create")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    def execute():
        item = get_item_query(db, item_id, org(principal))
        from uuid import uuid4 as _uuid4
        session_id = _uuid4()
        return {"session_id": str(session_id), "item_id": str(item_id), "case_id": str(item.difference_case_id), "status": "PENDING", "upload_url": f"/api/v1/photo-sessions/{session_id}/upload"}
    return command(db, principal, idempotency_key, f"phase040.photo_session_item:{item_id}", {}, execute)


@router.post("/reception-difference-evidence/{evidence_link_id}/archive")
def archive_evidence(evidence_link_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_evidence.update")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return command(db, principal, idempotency_key, f"phase040.evidence.archive:{evidence_link_id}", {},
                   lambda: ReceptionDifferenceEvidenceService(db).archive_evidence(evidence_link_id, org(principal), principal))


# ──────────────────────────────────────────────────────────────────────────────
# Responsibility (7)
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/reception-difference-cases/{case_id}/responsible-parties")
def list_responsible(case_id: UUID, principal=Depends(require_permission("logistics.reception_difference_responsibility.read")), db: Session = Depends(get_db)):
    return command(db, principal, f"phase040.resp.list:{case_id}", f"phase040.resp.list:{case_id}", {},
                   lambda: get_responsibility_query(db, case_id, org(principal)))


@router.post("/reception-difference-cases/{case_id}/responsible-parties", status_code=status.HTTP_201_CREATED)
def create_responsible(
    case_id: UUID, body: ReceptionDifferenceResponsiblePartyCreate, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_responsibility.create")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    return command(db, principal, idempotency_key, f"phase040.resp.create:{case_id}", body.model_dump(),
                   lambda: ReceptionDifferenceResponsibilityService(db).propose_responsible(
                       case_id=case_id, item_id=None, party_type=body.party_type,
                       business_partner_id=body.business_partner_id, user_id=body.user_id,
                       responsibility_role=body.responsibility_role or "PRIMARY",
                       notes=body.notes, allocation_percentage=float(body.allocation_percentage) if body.allocation_percentage else None,
                       principal=principal,
                   ))


@router.patch("/reception-difference-responsible-parties/{responsibility_id}")
def update_responsible(
    responsibility_id: UUID, body: ReceptionDifferenceResponsiblePartyUpdate, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_responsibility.update")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    def execute():
        party = get_single_responsibility_query(db, responsibility_id, org(principal))
        if body.responsibility_role is not None: party.responsibility_role = body.responsibility_role
        if body.notes is not None: party.notes = body.notes
        if body.allocation_percentage is not None: party.allocation_percentage = body.allocation_percentage
        db.flush()
        return party
    return command(db, principal, idempotency_key, f"phase040.resp.update:{responsibility_id}", body.model_dump(), execute)


@router.post("/reception-difference-responsible-parties/{responsibility_id}/review")
def review_responsible(
    responsibility_id: UUID, body: ReceptionDifferenceResponsibilityReviewRequest, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_responsibility.review")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    return command(db, principal, idempotency_key, f"phase040.resp.review:{responsibility_id}", body.model_dump(),
                   lambda: ReceptionDifferenceResponsibilityService(db).review_responsible(responsibility_id, org(principal), principal, body.review_notes))


@router.post("/reception-difference-responsible-parties/{responsibility_id}/acknowledge")
def acknowledge_responsible(responsibility_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_responsibility.acknowledge")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return command(db, principal, idempotency_key, f"phase040.resp.ack:{responsibility_id}", {},
                   lambda: ReceptionDifferenceResponsibilityService(db).acknowledge_responsible(responsibility_id, org(principal), principal))


@router.post("/reception-difference-responsible-parties/{responsibility_id}/dispute")
def dispute_responsible(
    responsibility_id: UUID, body: ReceptionDifferenceResponsibilityDisputeRequest, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_responsibility.dispute")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    return command(db, principal, idempotency_key, f"phase040.resp.dispute:{responsibility_id}", body.model_dump(),
                   lambda: ReceptionDifferenceResponsibilityService(db).dispute_responsible(responsibility_id, org(principal), body.dispute_reason, principal))


@router.post("/reception-difference-responsible-parties/{responsibility_id}/supersede")
def supersede_responsible(responsibility_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_responsibility.update")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return command(db, principal, idempotency_key, f"phase040.resp.supersede:{responsibility_id}", {},
                   lambda: ReceptionDifferenceResponsibilityService(db).mark_undetermined(responsibility_id, org(principal), principal))


# ──────────────────────────────────────────────────────────────────────────────
# Reviews & Approvals (6)
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/reception-difference-cases/{case_id}/reviews")
def list_reviews(case_id: UUID, principal=Depends(require_permission("logistics.reception_difference_reviews.read")), db: Session = Depends(get_db)):
    def execute():
        case_for(db, principal, case_id)
        return list(db.scalars(select(ReceptionDifferenceReviewModel).where(ReceptionDifferenceReviewModel.difference_case_id == case_id)))
    return command(db, principal, f"phase040.reviews.list:{case_id}", f"phase040.reviews.list:{case_id}", {}, execute)


@router.post("/reception-difference-cases/{case_id}/reviews", status_code=status.HTTP_201_CREATED)
def create_review(
    case_id: UUID, body: ReceptionDifferenceReviewCreate, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_reviews.create")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    return command(db, principal, idempotency_key, f"phase040.review.create:{case_id}", body.model_dump(),
                   lambda: ReceptionDifferenceReviewService(db).create_review(case_id, body.review_type, org(principal), principal))


@router.post("/reception-difference-reviews/{review_id}/start")
def start_review_endpoint(review_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_reviews.update")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return command(db, principal, idempotency_key, f"phase040.review.start:{review_id}", {},
                   lambda: ReceptionDifferenceReviewService(db).start_review(review_id, org(principal), principal))


@router.post("/reception-difference-reviews/{review_id}/request-changes")
def request_review_changes(
    review_id: UUID, body: ReceptionDifferenceReviewCompleteRequest, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_reviews.update")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    return command(db, principal, idempotency_key, f"phase040.review.changes:{review_id}", body.model_dump(),
                   lambda: ReceptionDifferenceReviewService(db).request_changes(review_id, org(principal), body.model_dump(), principal))


@router.post("/reception-difference-reviews/{review_id}/complete")
def complete_review(
    review_id: UUID, body: ReceptionDifferenceReviewCompleteRequest, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_reviews.update")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    return command(db, principal, idempotency_key, f"phase040.review.complete:{review_id}", body.model_dump(),
                   lambda: ReceptionDifferenceReviewService(db).complete_review(
                       review_id, org(principal), body.findings, body.blocking_issues,
                       body.requested_changes, body.recommendation, principal))


@router.get("/reception-difference-cases/{case_id}/approvals")
def list_approvals(case_id: UUID, principal=Depends(require_permission("logistics.reception_difference_approvals.read")), db: Session = Depends(get_db)):
    def execute():
        case_for(db, principal, case_id)
        return list(db.scalars(select(ReceptionDifferenceApprovalModel).where(ReceptionDifferenceApprovalModel.difference_case_id == case_id).order_by(ReceptionDifferenceApprovalModel.approval_level)))
    return command(db, principal, f"phase040.approvals.list:{case_id}", f"phase040.approvals.list:{case_id}", {}, execute)


# ──────────────────────────────────────────────────────────────────────────────
# Acknowledgements (7)
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/reception-difference-cases/{case_id}/acknowledgements")
def list_acknowledgements(case_id: UUID, principal=Depends(require_permission("logistics.reception_difference_acknowledgements.read")), db: Session = Depends(get_db)):
    return command(db, principal, f"phase040.acks.list:{case_id}", f"phase040.acks.list:{case_id}", {},
                   lambda: ReceptionDifferenceAcknowledgementService(db).list_acknowledgements(case_id, org(principal)))


@router.post("/reception-difference-cases/{case_id}/acknowledgements", status_code=status.HTTP_201_CREATED)
def create_acknowledgement(
    case_id: UUID, body: ReceptionDifferenceAcknowledgementCreate, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_acknowledgements.create")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    return command(db, principal, idempotency_key, f"phase040.ack.create:{case_id}", body.model_dump(),
                   lambda: ReceptionDifferenceAcknowledgementService(db).create_acknowledgement(
                       case_id=case_id, party_type=body.party_type,
                       business_partner_id=body.business_partner_id,
                       acknowledgement_type=body.acknowledgement_type,
                       statement=body.statement, source_channel=body.source_channel or "API",
                       principal=principal,
                   ))


@router.post("/reception-difference-cases/{case_id}/acknowledge-copy")
def acknowledge_copy(
    case_id: UUID, body: ReceptionDifferenceAcknowledgementCreate, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_acknowledgements.create")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    return command(db, principal, idempotency_key, f"phase040.ack.copy:{case_id}", body.model_dump(),
                   lambda: ReceptionDifferenceAcknowledgementService(db).create_acknowledgement(
                       case_id=case_id, party_type=body.party_type,
                       business_partner_id=body.business_partner_id,
                       acknowledgement_type="COPY",
                       statement=body.statement or "Acuse de recibo del documento",
                       source_channel=body.source_channel or "API", principal=principal,
                   ))


@router.post("/reception-difference-cases/{case_id}/acknowledge-facts")
def acknowledge_facts(
    case_id: UUID, body: ReceptionDifferenceAcknowledgementCreate, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_acknowledgements.create")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    return command(db, principal, idempotency_key, f"phase040.ack.facts:{case_id}", body.model_dump(),
                   lambda: ReceptionDifferenceAcknowledgementService(db).create_acknowledgement(
                       case_id=case_id, party_type=body.party_type,
                       business_partner_id=body.business_partner_id,
                       acknowledgement_type="FACTS",
                       statement=body.statement or "Reconocimiento de los hechos",
                       source_channel=body.source_channel or "API", principal=principal,
                   ))


@router.post("/reception-difference-cases/{case_id}/acknowledge-responsibility")
def acknowledge_responsibility(
    case_id: UUID, body: ReceptionDifferenceAcknowledgementCreate, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_acknowledgements.create")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    return command(db, principal, idempotency_key, f"phase040.ack.resp:{case_id}", body.model_dump(),
                   lambda: ReceptionDifferenceAcknowledgementService(db).create_acknowledgement(
                       case_id=case_id, party_type=body.party_type,
                       business_partner_id=body.business_partner_id,
                       acknowledgement_type="RESPONSIBILITY",
                       statement=body.statement or "Reconocimiento de responsabilidad",
                       source_channel=body.source_channel or "API", principal=principal,
                   ))


@router.post("/reception-difference-cases/{case_id}/dispute-facts")
def dispute_facts(
    case_id: UUID, body: ReceptionDifferenceAcknowledgementCreate, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_acknowledgements.dispute")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    return command(db, principal, idempotency_key, f"phase040.ack.dispute_facts:{case_id}", body.model_dump(),
                   lambda: ReceptionDifferenceAcknowledgementService(db).create_acknowledgement(
                       case_id=case_id, party_type=body.party_type,
                       business_partner_id=body.business_partner_id,
                       acknowledgement_type="DISPUTE_FACTS",
                       statement=body.statement or "Impugnación de hechos",
                       source_channel=body.source_channel or "API", principal=principal,
                   ))


@router.post("/reception-difference-cases/{case_id}/dispute-responsibility")
def dispute_responsibility(
    case_id: UUID, body: ReceptionDifferenceAcknowledgementCreate, idempotency_key: IdempotencyKey,
    principal=Depends(require_permission("logistics.reception_difference_acknowledgements.dispute")),
    db: Session = Depends(get_db), _csrf=Depends(verify_csrf),
):
    return command(db, principal, idempotency_key, f"phase040.ack.dispute_resp:{case_id}", body.model_dump(),
                   lambda: ReceptionDifferenceAcknowledgementService(db).create_acknowledgement(
                       case_id=case_id, party_type=body.party_type,
                       business_partner_id=body.business_partner_id,
                       acknowledgement_type="DISPUTE_RESPONSIBILITY",
                       statement=body.statement or "Impugnación de responsabilidad",
                       source_channel=body.source_channel or "API", principal=principal,
                   ))


# ──────────────────────────────────────────────────────────────────────────────
# Documents (8)
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/reception-difference-cases/{case_id}/preview")
def preview_document(case_id: UUID, principal=Depends(require_permission("logistics.reception_difference_documents.read")), db: Session = Depends(get_db)):
    return command(db, principal, f"phase040.doc.preview:{case_id}", f"phase040.doc.preview:{case_id}", {},
                   lambda: ReceptionDifferenceDocumentService(db).preview(case_id, org(principal)))


@router.post("/reception-difference-cases/{case_id}/issue-document")
def issue_document(case_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_documents.issue")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    def execute():
        result = ReceptionDifferenceDocumentService(db).issue_document(case_id, org(principal), principal)
        ReceptionDifferenceCaseService(db).transition_case(case_id, "ISSUED", principal)
        return result
    return command(db, principal, idempotency_key, f"phase040.doc.issue:{case_id}", {}, execute)


@router.get("/reception-difference-cases/{case_id}/document")
def get_document(case_id: UUID, principal=Depends(require_permission("logistics.reception_difference_documents.read")), db: Session = Depends(get_db)):
    def execute():
        case = case_for(db, principal, case_id)
        return {"case_id": str(case.id), "document_instance_id": str(case.document_instance_id) if case.document_instance_id else None, "status": "ISSUED" if case.document_instance_id else "NOT_ISSUED", "issued_at": case.issued_at.isoformat() if case.issued_at else None}
    return command(db, principal, f"phase040.doc.get:{case_id}", f"phase040.doc.get:{case_id}", {}, execute)


@router.post("/reception-difference-cases/{case_id}/cancel-document")
def cancel_document(case_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_documents.cancel")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return command(db, principal, idempotency_key, f"phase040.doc.cancel:{case_id}", body.model_dump(),
                   lambda: ReceptionDifferenceDocumentService(db).cancel_document(case_id, org(principal), body.reason, principal))


@router.post("/reception-difference-cases/{case_id}/reprint")
def reprint_document(case_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_documents.read")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return command(db, principal, idempotency_key, f"phase040.doc.reprint:{case_id}", body.model_dump(),
                   lambda: ReceptionDifferenceDocumentService(db).reprint(case_id, org(principal), principal))


@router.post("/reception-difference-cases/{case_id}/package", status_code=status.HTTP_201_CREATED)
def create_package(case_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.reception_difference_documents.package")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return command(db, principal, idempotency_key, f"phase040.doc.package:{case_id}", {},
                   lambda: ReceptionDifferenceDocumentService(db).create_package(case_id, org(principal), principal))


@router.get("/reception-difference-packages/{package_id}")
def get_package(package_id: UUID, principal=Depends(require_permission("logistics.reception_difference_documents.read")), db: Session = Depends(get_db)):
    def execute():
        row = db.get(ReceptionDifferenceDocumentPackageModel, package_id)
        if not row:
            raise reception_difference_error("RECEPTION_DIFFERENCE_PACKAGE_NOT_FOUND", "Paquete no encontrado.", 404)
        return jsonable_encoder({c.name: getattr(row, c.name) for c in ReceptionDifferenceDocumentPackageModel.__table__.columns})
    return command(db, principal, f"phase040.doc.package_get:{package_id}", f"phase040.doc.package_get:{package_id}", {}, execute)


@router.get("/reception-difference-packages/{package_id}/download")
def download_package(package_id: UUID, principal=Depends(require_permission("logistics.reception_difference_documents.read")), db: Session = Depends(get_db)):
    def execute():
        row = db.get(ReceptionDifferenceDocumentPackageModel, package_id)
        if not row:
            raise reception_difference_error("RECEPTION_DIFFERENCE_PACKAGE_NOT_FOUND", "Paquete no encontrado.", 404)
        return {"package_id": str(row.id), "status": row.status, "download_url": f"/api/v1/reception-difference-packages/{package_id}/file", "file_asset_id": str(row.file_asset_id) if row.file_asset_id else None}
    return command(db, principal, f"phase040.doc.package_dl:{package_id}", f"phase040.doc.package_dl:{package_id}", {}, execute)


# ──────────────────────────────────────────────────────────────────────────────
# Future Preparation (3)
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/reception-difference-cases/{case_id}/quality-preparation")
def quality_preparation(case_id: UUID, principal=Depends(require_permission("logistics.reception_difference_cases.read")), db: Session = Depends(get_db)):
    return command(db, principal, f"phase040.quality_prep:{case_id}", f"phase040.quality_prep:{case_id}", {},
                   lambda: QualityInspectionPreparationService(db).get_preparation(case_id, org(principal)))


@router.get("/reception-difference-cases/{case_id}/quarantine-recommendations")
def quarantine_recommendations(case_id: UUID, principal=Depends(require_permission("logistics.reception_difference_cases.read")), db: Session = Depends(get_db)):
    return command(db, principal, f"phase040.quarantine:{case_id}", f"phase040.quarantine:{case_id}", {},
                   lambda: FutureQuarantineRecommendationService(db).get_recommendations(case_id, org(principal)))


@router.get("/reception-difference-cases/{case_id}/claim-preparation")
def claim_preparation(case_id: UUID, principal=Depends(require_permission("logistics.reception_difference_cases.read")), db: Session = Depends(get_db)):
    return command(db, principal, f"phase040.claim_prep:{case_id}", f"phase040.claim_prep:{case_id}", {},
                   lambda: FutureClaimPreparationService(db).get_preparation(case_id, org(principal)))
