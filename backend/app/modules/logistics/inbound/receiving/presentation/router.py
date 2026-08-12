"""HTTP contract for Phase 039. No endpoint posts inventory or formal differences."""
from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission, resolve_organization_id, verify_csrf
from app.modules.logistics.inbound.arrival_notices.application.services.idempotency import get_idempotent_response, save_idempotent_response
from app.modules.logistics.principal import LogisticsPrincipal

from ..application.services import InboundReceivingService, now, row_dict
from ..domain.errors import receiving_error
from ..domain.services import canonical_hash, strict_decimal
from ..infrastructure.persistence.models import (
    InboundExpirationObservationModel, InboundLotObservationModel, InboundReceiptExpectedLineModel,
    InboundReceiptModel, InboundReceiptPauseModel, InboundReceiptProgressProjectionModel,
    InboundReceivedLineModel, InboundScanCompensationEventModel, InboundScanEventModel,
    InboundScanSessionModel, InboundSerialObservationModel, ReceptionDifferenceCandidateModel,
    ReceivingValidationResultModel, UnresolvedInboundScanModel,
)
from .schemas import *  # noqa: F403

router = APIRouter(tags=["Inbound Receiving (Phase 039)"])
IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)]


def org(principal: LogisticsPrincipal) -> UUID: return resolve_organization_id(principal)
def as_dict(row: object) -> dict: return jsonable_encoder(row_dict(row))


def command(db: Session, principal: LogisticsPrincipal, key: str, operation: str, payload: dict, execute):
    organization_id = org(principal); encoded = jsonable_encoder(payload); replay = get_idempotent_response(db, organization_id, operation, key, encoded)
    if replay is not None: return replay
    value = execute()
    if isinstance(value, dict): response = jsonable_encoder(value)
    elif isinstance(value, (list, tuple)): response = jsonable_encoder([row_dict(item) if hasattr(item, "__table__") else item for item in value])
    else: response = jsonable_encoder(row_dict(value))
    save_idempotent_response(db, organization_id, principal.user_id, operation, key, encoded, response); db.commit(); return value


def receipt_for(db: Session, principal: LogisticsPrincipal, receipt_id: UUID, lock: bool = False): return InboundReceivingService(db).receipt(receipt_id, org(principal), lock=lock)
def line_for(db: Session, principal: LogisticsPrincipal, line_id: UUID, lock: bool = False):
    query = select(InboundReceivedLineModel).join(InboundReceiptModel, InboundReceiptModel.active_revision_id == InboundReceivedLineModel.receipt_revision_id).where(InboundReceivedLineModel.id == line_id, InboundReceiptModel.organization_id == org(principal))
    if lock: query = query.with_for_update()
    row = db.scalar(query)
    if not row: raise receiving_error("INBOUND_RECEIPT_LINE_NOT_FOUND", "Línea recibida no encontrada.", 404)
    return row


@router.get("/inbound-receipts", response_model=InboundReceiptListResponse)
def list_receipts(search: str | None = None, receipt_code: str | None = None, cpv_code: str | None = Query(default=None, alias="CPV_code"), cit_code: str | None = Query(default=None, alias="CIT_code"), purchase_order_code: str | None = None, supplier_id: UUID | None = None, carrier_id: UUID | None = None, warehouse_id: UUID | None = None, dock_id: UUID | None = None, unloading_operation_id: UUID | None = None, receipt_status: str | None = Query(default=None, alias="status"), completion_classification: str | None = None, product_id: UUID | None = None, sku: str | None = Query(default=None, alias="SKU"), barcode: str | None = None, lot: str | None = None, serial: str | None = None, expiration_from: date | None = None, expiration_to: date | None = None, started_from: datetime | None = None, started_to: datetime | None = None, completed_from: datetime | None = None, completed_to: datetime | None = None, partial: bool | None = None, total: bool | None = None, has_unresolved_scans: bool | None = None, has_validation_errors: bool | None = None, has_difference_candidates: bool | None = None, has_expired_items: bool | None = None, has_duplicate_serials: bool | None = None, operator_user_id: UUID | None = None, mine: bool = False, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), sort_by: str = "created_at", sort_direction: str = "desc", principal=Depends(require_permission("logistics.inbound_receipts.read")), db: Session = Depends(get_db)):
    query = select(InboundReceiptModel).where(InboundReceiptModel.organization_id == org(principal))
    if warehouse_id: query = query.where(InboundReceiptModel.warehouse_id == warehouse_id)
    if unloading_operation_id: query = query.where(InboundReceiptModel.unloading_operation_id == unloading_operation_id)
    if supplier_id: query = query.where(InboundReceiptModel.supplier_business_partner_id == supplier_id)
    if dock_id:
        from app.modules.logistics.inbound.dock_operations.infrastructure.persistence.models import InboundDockAssignmentModel
        query = query.where(InboundReceiptModel.dock_assignment_id.in_(select(InboundDockAssignmentModel.id).where(InboundDockAssignmentModel.dock_id == dock_id)))
    if receipt_code: query = query.where(InboundReceiptModel.normalized_receipt_code == receipt_code.strip().upper())
    if search: query = query.where(or_(InboundReceiptModel.receipt_code.ilike(f"%{search}%"), InboundReceiptModel.status.ilike(f"%{search}%")))
    if receipt_status: query = query.where(InboundReceiptModel.status == receipt_status)
    if completion_classification: query = query.where(InboundReceiptModel.completion_classification == completion_classification)
    if product_id: query = query.where(InboundReceiptModel.active_revision_id.in_(select(InboundReceiptExpectedLineModel.receipt_revision_id).where(InboundReceiptExpectedLineModel.product_id == product_id)))
    if sku: query = query.where(InboundReceiptModel.active_revision_id.in_(select(InboundReceiptExpectedLineModel.receipt_revision_id).where(InboundReceiptExpectedLineModel.sku_snapshot.ilike(sku))))
    if barcode:
        digest=hashlib.sha256(barcode.strip().encode()).hexdigest();query=query.where(InboundReceiptModel.id.in_(select(InboundScanEventModel.inbound_receipt_id).where(InboundScanEventModel.code_hash==digest)))
    if lot:
        digest=hashlib.sha256(lot.strip().upper().encode()).hexdigest();query=query.where(InboundReceiptModel.id.in_(select(InboundLotObservationModel.inbound_receipt_id).where(InboundLotObservationModel.lot_hash==digest)))
    if serial:
        digest=hashlib.sha256(serial.strip().encode()).hexdigest();query=query.where(InboundReceiptModel.id.in_(select(InboundSerialObservationModel.inbound_receipt_id).where(InboundSerialObservationModel.serial_hash==digest)))
    if expiration_from: query=query.where(InboundReceiptModel.id.in_(select(InboundExpirationObservationModel.inbound_receipt_id).where(InboundExpirationObservationModel.expiration_date>=expiration_from)))
    if expiration_to: query=query.where(InboundReceiptModel.id.in_(select(InboundExpirationObservationModel.inbound_receipt_id).where(InboundExpirationObservationModel.expiration_date<=expiration_to)))
    if partial: query = query.where(InboundReceiptModel.completion_classification.like("PARTIAL%"))
    if total: query = query.where(InboundReceiptModel.completion_classification.like("TOTAL%"))
    if has_unresolved_scans is not None: query = query.where((InboundReceiptModel.total_unresolved_scans > 0) == has_unresolved_scans)
    if has_validation_errors is not None: query = query.where((InboundReceiptModel.total_validation_errors > 0) == has_validation_errors)
    if has_difference_candidates is not None: query = query.where((InboundReceiptModel.total_difference_candidates > 0) == has_difference_candidates)
    if has_expired_items is not None: query=query.where(InboundReceiptModel.id.in_(select(InboundExpirationObservationModel.inbound_receipt_id).where(InboundExpirationObservationModel.validation_status=="EXPIRED")) if has_expired_items else ~InboundReceiptModel.id.in_(select(InboundExpirationObservationModel.inbound_receipt_id).where(InboundExpirationObservationModel.validation_status=="EXPIRED")))
    if has_duplicate_serials is not None: query=query.where(InboundReceiptModel.id.in_(select(InboundSerialObservationModel.inbound_receipt_id).where(InboundSerialObservationModel.duplicate_status!="UNIQUE_IN_RECEIPT")) if has_duplicate_serials else ~InboundReceiptModel.id.in_(select(InboundSerialObservationModel.inbound_receipt_id).where(InboundSerialObservationModel.duplicate_status!="UNIQUE_IN_RECEIPT")))
    if operator_user_id: query=query.where(InboundReceiptModel.started_by_user_id==operator_user_id)
    if mine: query = query.where(InboundReceiptModel.started_by_user_id == principal.user_id)
    if started_from: query = query.where(InboundReceiptModel.started_at >= started_from)
    if started_to: query = query.where(InboundReceiptModel.started_at <= started_to)
    if completed_from: query = query.where(InboundReceiptModel.completed_at >= completed_from)
    if completed_to: query = query.where(InboundReceiptModel.completed_at <= completed_to)
    allowed_sort = {"created_at", "started_at", "completed_at", "receipt_code", "status"}; column = getattr(InboundReceiptModel, sort_by if sort_by in allowed_sort else "created_at"); query = query.order_by(column.asc() if sort_direction.lower() == "asc" else column.desc())
    total_count = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0; rows = list(db.scalars(query.offset((page-1)*page_size).limit(page_size))); items=[]
    actions={"CREATED":["prepare","cancel"],"READY":["start","cancel"],"IN_PROGRESS":["scan","pause","validate","cancel"],"PAUSED":["resume","cancel"],"PARTIALLY_RECEIVED":["complete"],"FULLY_RECEIVED":["complete"],"REQUIRES_DIFFERENCE_REVIEW":["complete"]}
    from ..infrastructure.persistence.models import InboundReceiptRevisionModel
    for row in rows:
        projection=db.get(InboundReceiptProgressProjectionModel,row.id);revision=db.get(InboundReceiptRevisionModel,row.active_revision_id) if row.active_revision_id else None;source=revision.source_snapshot if revision else {};po_codes=[str(x.get("purchase_order_code")) for x in source.get("purchase_order_references",[]) if x.get("purchase_order_code")]
        if purchase_order_code and purchase_order_code not in po_codes: continue
        if cpv_code and str(source.get("cpv_code") or "").upper()!=cpv_code.upper(): continue
        if cit_code and str(source.get("cit_code") or "").upper()!=cit_code.upper(): continue
        items.append({"id":row.id,"receipt_code":row.receipt_code,"cpv_code":source.get("cpv_code"),"cit_code":source.get("cit_code"),"purchase_order_codes":po_codes,"supplier_summary":row.supplier_snapshot,"warehouse_summary":{"id":str(row.warehouse_id)},"dock_summary":{"assignment_id":str(row.dock_assignment_id)},"status":row.status,"completion_classification":row.completion_classification,"expected_line_count":row.total_expected_lines,"received_line_count":row.total_received_lines,"progress_percentage":projection.progress_percentage if projection else Decimal("0"),"unresolved_scan_count":row.total_unresolved_scans,"validation_error_count":row.total_validation_errors,"difference_candidate_count":row.total_difference_candidates,"started_at":row.started_at,"completed_at":row.completed_at,"operator_summary":row.started_by_snapshot,"integrity_status":"VALID" if row.content_hash else "NOT_FROZEN","capabilities":actions.get(row.status,[])})
    return {"items": items, "page": page, "page_size": page_size, "total": total_count}


@router.post("/inbound-receipts", response_model=InboundReceiptResponse, status_code=status.HTTP_201_CREATED)
def create_receipt(body: InboundReceiptCreate, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_receipts.create")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    return command(db, principal, idempotency_key, "phase039.receipt.create", body.model_dump(), lambda: InboundReceivingService(db).create_from_unloading(body.unloading_operation_id, principal, body.receipt_type, body.scan_mode_policy))


@router.post("/inbound-receipts/from-unloading-operation", response_model=InboundReceiptResponse, status_code=status.HTTP_201_CREATED)
def create_from_unloading(body: InboundReceiptFromUnloadingCreate, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_receipts.create")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return create_receipt(body, idempotency_key, principal, db, _csrf)


@router.get("/inbound-receipts/{receipt_id}", response_model=InboundReceiptDetail)
def get_receipt(receipt_id: UUID, principal=Depends(require_permission("logistics.inbound_receipts.read")), db: Session = Depends(get_db)): return receipt_for(db, principal, receipt_id)


@router.post("/inbound-receipts/{receipt_id}/prepare", response_model=InboundReceiptResponse)
def prepare_receipt(receipt_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_receipts.prepare")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return command(db, principal, idempotency_key, f"phase039.receipt.prepare:{receipt_id}", {}, lambda: InboundReceivingService(db).prepare(receipt_id, principal))


def transition(receipt_id, target, body, key, principal, db): return command(db, principal, key, f"phase039.receipt.{target.lower()}:{receipt_id}", body.model_dump() if body else {}, lambda: InboundReceivingService(db).transition(receipt_id, target, principal, body.reason if body else None))


@router.post("/inbound-receipts/{receipt_id}/start", response_model=InboundReceiptResponse)
def start_receipt(receipt_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_receipts.start")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return transition(receipt_id, "IN_PROGRESS", None, idempotency_key, principal, db)
@router.post("/inbound-receipts/{receipt_id}/pause", response_model=InboundReceiptResponse)
def pause_receipt(receipt_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_receipts.pause")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return transition(receipt_id, "PAUSED", body, idempotency_key, principal, db)
@router.post("/inbound-receipts/{receipt_id}/resume", response_model=InboundReceiptResponse)
def resume_receipt(receipt_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_receipts.resume")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return transition(receipt_id, "IN_PROGRESS", None, idempotency_key, principal, db)


@router.post("/inbound-receipts/{receipt_id}/validate", response_model=InboundReceiptValidationResponse)
def validate_receipt(receipt_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_receipts.validate")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return command(db, principal, idempotency_key, f"phase039.receipt.validate:{receipt_id}", {}, lambda: InboundReceivingService(db).validate(receipt_id, principal))
@router.post("/inbound-receipts/{receipt_id}/complete", response_model=InboundReceiptCompletionResponse)
def complete_receipt(receipt_id: UUID, body: InboundReceiptCompletionRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_receipts.complete")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return command(db, principal, idempotency_key, f"phase039.receipt.complete:{receipt_id}", body.model_dump(), lambda: InboundReceivingService(db).complete(receipt_id, principal, body.row_version))
@router.post("/inbound-receipts/{receipt_id}/cancel", response_model=InboundReceiptResponse)
def cancel_receipt(receipt_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_receipts.cancel")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return transition(receipt_id, "CANCELLED", body, idempotency_key, principal, db)


@router.get("/inbound-receipts/{receipt_id}/summary")
def receipt_summary(receipt_id: UUID, principal=Depends(require_permission("logistics.inbound_receipts.read")), db: Session = Depends(get_db)): return as_dict(receipt_for(db, principal, receipt_id))
@router.get("/inbound-receipts/{receipt_id}/progress", response_model=InboundReceiptProgressResponse)
def receipt_progress(receipt_id: UUID, principal=Depends(require_permission("logistics.inbound_receipts.read")), db: Session = Depends(get_db)):
    receipt = receipt_for(db, principal, receipt_id); projection = db.get(InboundReceiptProgressProjectionModel, receipt.id) or InboundReceivingService(db).recalculate(receipt); return projection
@router.get("/inbound-receipts/{receipt_id}/comparison", response_model=InboundReceiptComparisonResponse)
def receipt_comparison(receipt_id: UUID, principal=Depends(require_permission("logistics.inbound_receipts.read")), db: Session = Depends(get_db)):
    receipt = receipt_for(db, principal, receipt_id); expected = list(db.scalars(select(InboundReceiptExpectedLineModel).where(InboundReceiptExpectedLineModel.receipt_revision_id == receipt.active_revision_id))); received = {x.expected_line_id: x for x in db.scalars(select(InboundReceivedLineModel).where(InboundReceivedLineModel.receipt_revision_id == receipt.active_revision_id))}; lines=[]
    for line in expected:
        observed=received.get(line.id); quantity=Decimal(observed.received_base_quantity) if observed else Decimal("0"); lines.append({"expected_line_id":str(line.id),"ordered_base_quantity":str(line.ordered_base_quantity),"shipped_base_quantity":str(line.shipped_base_quantity) if line.shipped_base_quantity is not None else None,"received_base_quantity":str(quantity),"remaining_base_quantity":str(max(Decimal(line.ordered_base_quantity)-quantity,Decimal("0"))),"variance_base_quantity":str(quantity-Decimal(line.ordered_base_quantity)),"comparison_status":observed.comparison_status if observed else "UNDER_EXPECTED"})
    return {"receipt_id":receipt.id,"lines":lines,"completion_classification":receipt.completion_classification}
@router.get("/inbound-receipts/{receipt_id}/history")
def receipt_history(receipt_id: UUID, principal=Depends(require_permission("logistics.inbound_receipts.read_history")), db: Session = Depends(get_db)):
    receipt=receipt_for(db,principal,receipt_id); return {"receipt":as_dict(receipt),"scan_events":[as_dict(x) for x in db.scalars(select(InboundScanEventModel).where(InboundScanEventModel.inbound_receipt_id==receipt.id).order_by(InboundScanEventModel.server_sequence))],"pauses":[as_dict(x) for x in db.scalars(select(InboundReceiptPauseModel).where(InboundReceiptPauseModel.inbound_receipt_id==receipt.id))]}
@router.get("/inbound-receipts/{receipt_id}/capabilities", response_model=InboundReceiptCapabilities)
def receipt_capabilities(receipt_id: UUID, principal=Depends(require_permission("logistics.inbound_receipts.read")), db: Session = Depends(get_db)):
    receipt=receipt_for(db,principal,receipt_id); mapping={"CREATED":["prepare","cancel"],"READY":["start","cancel"],"IN_PROGRESS":["scan","pause","validate","cancel"],"PAUSED":["resume","cancel"],"PARTIALLY_RECEIVED":["complete"],"FULLY_RECEIVED":["complete"],"REQUIRES_DIFFERENCE_REVIEW":["complete"]}; return {"receipt_id":receipt.id,"actions":mapping.get(receipt.status,[])}
@router.get("/inbound-receipts/{receipt_id}/integrity", response_model=InboundReceiptIntegrityResponse)
def receipt_integrity(receipt_id: UUID, principal=Depends(require_permission("logistics.inbound_receipts.read_integrity")), db: Session = Depends(get_db)):
    receipt=receipt_for(db,principal,receipt_id)
    from ..infrastructure.persistence.models import InboundReceiptRevisionModel
    revision=db.get(InboundReceiptRevisionModel,receipt.active_revision_id);snapshot=revision.completion_snapshot if revision and revision.completion_snapshot else InboundReceivingService(db).snapshot(receipt);hashes={key:canonical_hash(value) for key,value in snapshot.items() if key not in {"receipt","captured_at"}};calculated=canonical_hash(snapshot);return {"receipt_id":receipt.id,"status":"VALID" if not receipt.content_hash or receipt.content_hash==calculated else "MISMATCH","hashes":hashes,"calculated_content_hash":calculated,"stored_content_hash":receipt.content_hash}
@router.get("/inbound-receipts/{receipt_id}/difference-preparation", response_model=ReceptionDifferencePreparationResponse)
def difference_preparation(receipt_id: UUID, principal=Depends(require_permission("logistics.reception_difference_candidates.read")), db: Session = Depends(get_db)):
    receipt=receipt_for(db,principal,receipt_id); comparison=receipt_comparison(receipt_id,principal,db); expected=[as_dict(x) for x in db.scalars(select(InboundReceiptExpectedLineModel).where(InboundReceiptExpectedLineModel.receipt_revision_id==receipt.active_revision_id))]; received=[as_dict(x) for x in db.scalars(select(InboundReceivedLineModel).where(InboundReceivedLineModel.receipt_revision_id==receipt.active_revision_id))]; candidates=[as_dict(x) for x in db.scalars(select(ReceptionDifferenceCandidateModel).where(ReceptionDifferenceCandidateModel.inbound_receipt_id==receipt.id))]; validation=db.scalar(select(ReceivingValidationResultModel).where(ReceivingValidationResultModel.inbound_receipt_id==receipt.id).order_by(ReceivingValidationResultModel.created_at.desc()))
    return {"inbound_receipt_id":receipt.id,"receipt_code":receipt.receipt_code,"receipt_revision_id":receipt.active_revision_id,"warehouse_id":receipt.warehouse_id,"supplier_summary":receipt.supplier_snapshot,"carrier_summary":receipt.carrier_snapshot,"unloading_operation_id":receipt.unloading_operation_id,"purchase_order_references":[],"expected_lines":expected,"received_lines":received,"comparison_results":comparison["lines"],"candidates":candidates,"validation_summary":validation.result if validation else {},"completion_snapshot_hash":receipt.content_hash,"future_capabilities":["PHASE_040_FORMALIZE_DIFFERENCES"]}


@router.get("/inbound-receipts/{receipt_id}/expected-lines", response_model=list[InboundReceiptExpectedLineResponse])
def expected_lines(receipt_id: UUID, principal=Depends(require_permission("logistics.inbound_receipts.read")), db: Session = Depends(get_db)):
    receipt=receipt_for(db,principal,receipt_id); return list(db.scalars(select(InboundReceiptExpectedLineModel).where(InboundReceiptExpectedLineModel.receipt_revision_id==receipt.active_revision_id).order_by(InboundReceiptExpectedLineModel.line_number)))
@router.get("/inbound-receipts/{receipt_id}/received-lines", response_model=list[InboundReceivedLineResponse])
def received_lines(receipt_id: UUID, principal=Depends(require_permission("logistics.inbound_receipts.read")), db: Session = Depends(get_db)):
    receipt=receipt_for(db,principal,receipt_id); return list(db.scalars(select(InboundReceivedLineModel).where(InboundReceivedLineModel.receipt_revision_id==receipt.active_revision_id)))
@router.get("/inbound-receipt-lines/{line_id}", response_model=InboundReceivedLineResponse)
def get_line(line_id: UUID, principal=Depends(require_permission("logistics.inbound_receipts.read")), db: Session = Depends(get_db)): return line_for(db,principal,line_id)
@router.post("/inbound-receipt-lines/{line_id}/apply-quantity", response_model=InboundReceivedLineResponse)
def apply_quantity(line_id: UUID, body: ApplyReceivedQuantityRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_receipt_scans.manual_entry")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    def execute():
        line=line_for(db,principal,line_id,True)
        if line.row_version!=body.row_version: raise receiving_error("INBOUND_RECEIPT_STALE_VERSION","La línea fue modificada.",409)
        expected=db.get(InboundReceiptExpectedLineModel,line.expected_line_id); quantity=strict_decimal(body.quantity); base=InboundReceivingService(db)._base_quantity(line.product_id,quantity,body.unit_id,expected.ordered_unit_id,expected.ordered_base_quantity/expected.ordered_quantity)
        if line.received_base_quantity+base>expected.maximum_receivable_base_quantity: raise receiving_error("INBOUND_RECEIPT_QUANTITY_EXCEEDED","La cantidad supera el saldo autorizado.",409)
        line.received_quantity+=quantity; line.received_base_quantity+=base; line.manual_entry_count+=1; line.row_version+=1;receipt=db.scalar(select(InboundReceiptModel).where(InboundReceiptModel.active_revision_id==line.receipt_revision_id));service=InboundReceivingService(db);service.recalculate(receipt);service.emit(receipt,principal,"logistics.inbound_receipt.manual_entry",resource_id=line.id,metadata={"quantity":str(quantity),"unit_id":str(body.unit_id)});return line
    return command(db,principal,idempotency_key,f"phase039.line.apply:{line_id}",body.model_dump(),execute)
@router.post("/inbound-receipt-lines/{line_id}/validate")
def validate_line(line_id: UUID, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_receipts.validate")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    line=line_for(db,principal,line_id); receipt=db.scalar(select(InboundReceiptModel).where(InboundReceiptModel.active_revision_id==line.receipt_revision_id)); return validate_receipt(receipt.id,idempotency_key,principal,db,_csrf)
@router.post("/inbound-receipt-lines/{line_id}/mark-for-review", response_model=InboundReceivedLineResponse)
def review_line(line_id: UUID, body: ReasonRequest, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_receipts.validate")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)):
    def execute(): line=line_for(db,principal,line_id,True); line.validation_status="REQUIRES_REVIEW"; line.notes=body.reason; line.row_version+=1; return line
    return command(db,principal,idempotency_key,f"phase039.line.review:{line_id}",body.model_dump(),execute)
@router.get("/inbound-receipt-lines/{line_id}/comparison")
def line_comparison(line_id: UUID, principal=Depends(require_permission("logistics.inbound_receipts.read")), db: Session = Depends(get_db)):
    line=line_for(db,principal,line_id); expected=db.get(InboundReceiptExpectedLineModel,line.expected_line_id); return {"line_id":line.id,"ordered_base_quantity":str(expected.ordered_base_quantity),"received_base_quantity":str(line.received_base_quantity),"variance_base_quantity":str(line.received_base_quantity-expected.ordered_base_quantity),"status":line.comparison_status}
@router.get("/inbound-receipt-lines/{line_id}/identifiers")
def line_identifiers(line_id: UUID, principal=Depends(require_permission("logistics.inbound_receipt_identifiers.read_sensitive")), db: Session = Depends(get_db)):
    line_for(db,principal,line_id); return {"lots":[as_dict(x) for x in db.scalars(select(InboundLotObservationModel).where(InboundLotObservationModel.received_line_id==line_id))],"serials":[as_dict(x) for x in db.scalars(select(InboundSerialObservationModel).where(InboundSerialObservationModel.received_line_id==line_id))],"expirations":[as_dict(x) for x in db.scalars(select(InboundExpirationObservationModel).where(InboundExpirationObservationModel.received_line_id==line_id))]}
@router.get("/inbound-receipt-lines/{line_id}/history")
def line_history(line_id: UUID, principal=Depends(require_permission("logistics.inbound_receipts.read_history")), db: Session = Depends(get_db)):
    line=line_for(db,principal,line_id); return [as_dict(x) for x in db.scalars(select(InboundScanEventModel).where(InboundScanEventModel.resolved_expected_line_id==line.expected_line_id).order_by(InboundScanEventModel.server_sequence))]


@router.get("/inbound-receipts/{receipt_id}/scan-sessions", response_model=list[InboundScanSessionResponse])
def scan_sessions(receipt_id: UUID, principal=Depends(require_permission("logistics.inbound_receipts.read")), db: Session = Depends(get_db)): receipt=receipt_for(db,principal,receipt_id); return list(db.scalars(select(InboundScanSessionModel).where(InboundScanSessionModel.inbound_receipt_id==receipt.id)))
@router.post("/inbound-receipts/{receipt_id}/scan-sessions", response_model=InboundScanSessionResponse, status_code=201)
def create_scan_session(receipt_id: UUID, body: InboundScanSessionCreate, idempotency_key: IdempotencyKey, principal=Depends(require_permission("logistics.inbound_receipt_scans.create")), db: Session = Depends(get_db), _csrf=Depends(verify_csrf)): return command(db,principal,idempotency_key,f"phase039.session.create:{receipt_id}",body.model_dump(),lambda:InboundReceivingService(db).session(receipt_id,principal,body.scanner_type,body.station_id,body.device_reference,body.client_session_reference))
@router.get("/inbound-scan-sessions/{session_id}", response_model=InboundScanSessionResponse)
def get_scan_session(session_id: UUID, principal=Depends(require_permission("logistics.inbound_receipts.read")), db: Session = Depends(get_db)):
    row=db.scalar(select(InboundScanSessionModel).where(InboundScanSessionModel.id==session_id,InboundScanSessionModel.organization_id==org(principal))); 
    if not row: raise receiving_error("INBOUND_SCAN_SESSION_NOT_FOUND","Sesión no encontrada.",404)
    return row
def session_transition(session_id,target,key,principal,db):
    def execute():
        row=get_scan_session(session_id,principal,db)
        allowed={"ACTIVE":{"PAUSED","COMPLETED","CANCELLED"},"PAUSED":{"ACTIVE","CANCELLED"}}
        if target not in allowed.get(row.status,set()): raise receiving_error("INBOUND_SCAN_SESSION_INACTIVE","Transición de sesión inválida.",409)
        row.status=target; row.last_activity_at=now(); row.row_version+=1
        if target=="COMPLETED": row.completed_at=now()
        if target=="CANCELLED": row.cancelled_at=now()
        return row
    return command(db,principal,key,f"phase039.session.{target.lower()}:{session_id}",{},execute)
@router.post("/inbound-scan-sessions/{session_id}/pause",response_model=InboundScanSessionResponse)
def pause_scan_session(session_id:UUID,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_scans.create")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):return session_transition(session_id,"PAUSED",idempotency_key,principal,db)
@router.post("/inbound-scan-sessions/{session_id}/resume",response_model=InboundScanSessionResponse)
def resume_scan_session(session_id:UUID,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_scans.create")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):return session_transition(session_id,"ACTIVE",idempotency_key,principal,db)
@router.post("/inbound-scan-sessions/{session_id}/complete",response_model=InboundScanSessionResponse)
def complete_scan_session(session_id:UUID,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_scans.create")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):return session_transition(session_id,"COMPLETED",idempotency_key,principal,db)
@router.post("/inbound-scan-sessions/{session_id}/cancel",response_model=InboundScanSessionResponse)
def cancel_scan_session(session_id:UUID,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_scans.create")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):return session_transition(session_id,"CANCELLED",idempotency_key,principal,db)


@router.post("/inbound-receipts/{receipt_id}/scan-events",response_model=InboundScanEventResponse,status_code=201)
def create_scan_event(receipt_id:UUID,body:InboundScanEventCreate,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_scans.create")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):return command(db,principal,idempotency_key,f"phase039.scan:{receipt_id}:{body.client_scan_id}",body.model_dump(),lambda:InboundReceivingService(db).scan(receipt_id,principal,body))
@router.post("/inbound-receipts/{receipt_id}/scan-events/batch",response_model=list[InboundScanEventResponse])
def create_scan_batch(receipt_id:UUID,body:InboundScanEventBatchCreate,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_scans.batch")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):
    def execute(): return [InboundReceivingService(db).scan(receipt_id,principal,event) for event in body.events]
    return command(db,principal,idempotency_key,f"phase039.scan.batch:{receipt_id}",body.model_dump(),execute)
@router.get("/inbound-receipts/{receipt_id}/scan-events",response_model=list[InboundScanEventResponse])
def list_scan_events(receipt_id:UUID,principal=Depends(require_permission("logistics.inbound_receipts.read")),db:Session=Depends(get_db)):receipt=receipt_for(db,principal,receipt_id);return list(db.scalars(select(InboundScanEventModel).where(InboundScanEventModel.inbound_receipt_id==receipt.id).order_by(InboundScanEventModel.server_sequence)))
@router.get("/inbound-scan-events/{event_id}",response_model=InboundScanEventResponse)
def get_scan_event(event_id:UUID,principal=Depends(require_permission("logistics.inbound_receipts.read")),db:Session=Depends(get_db)):
    row=db.scalar(select(InboundScanEventModel).where(InboundScanEventModel.id==event_id,InboundScanEventModel.organization_id==org(principal)))
    if not row:raise receiving_error("INBOUND_SCAN_EVENT_NOT_FOUND","Evento no encontrado.",404)
    return row
@router.post("/inbound-scan-events/{event_id}/compensate")
def compensate_scan(event_id:UUID,body:InboundScanCompensationRequest,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_scans.compensate")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):
    def execute():
        event=get_scan_event(event_id,principal,db)
        if event.status!="APPLIED":raise receiving_error("INBOUND_SCAN_COMPENSATION_INVALID","El evento no puede compensarse.",409)
        receipt=receipt_for(db,principal,event.inbound_receipt_id,True)
        if receipt.status=="COMPLETED":raise receiving_error("INBOUND_RECEIPT_NOT_EDITABLE","La revisión está congelada.",409)
        line=db.scalar(select(InboundReceivedLineModel).where(InboundReceivedLineModel.receipt_revision_id==event.receipt_revision_id,InboundReceivedLineModel.expected_line_id==event.resolved_expected_line_id).with_for_update())
        if line: line.received_quantity-=event.accepted_quantity;line.received_base_quantity-=event.accepted_base_quantity;line.row_version+=1
        compensation=InboundScanCompensationEventModel(id=uuid4(),original_scan_event_id=event.id,inbound_receipt_id=receipt.id,reason_code=body.reason_code,reason=body.reason,compensated_quantity=event.accepted_quantity,unit_id=event.accepted_unit_id,base_quantity=event.accepted_base_quantity,requested_by=principal.user_id,approved_by=principal.user_id,status="APPLIED");db.add(compensation);event.status="REVERSED_BY_COMPENSATION";service=InboundReceivingService(db);service.recalculate(receipt);service.emit(receipt,principal,"logistics.inbound_receipt.scan_compensated",resource_id=compensation.id,reason=body.reason,metadata={"scan_event_id":str(event.id)});return compensation
    return command(db,principal,idempotency_key,f"phase039.scan.compensate:{event_id}",body.model_dump(),execute)


@router.post("/inbound-receipts/{receipt_id}/resolve-code",response_model=ResolveInboundCodeResponse)
def resolve_code(receipt_id:UUID,body:ResolveInboundCodeRequest,principal=Depends(require_permission("logistics.inbound_receipts.read")),db:Session=Depends(get_db)):return InboundReceivingService(db).resolve_code(receipt_for(db,principal,receipt_id),body.raw_code,body.symbology)
@router.get("/inbound-receipts/{receipt_id}/unresolved-scans")
def unresolved_scans(receipt_id:UUID,principal=Depends(require_permission("logistics.inbound_receipts.read")),db:Session=Depends(get_db)):receipt=receipt_for(db,principal,receipt_id);return [as_dict(x) for x in db.scalars(select(UnresolvedInboundScanModel).where(UnresolvedInboundScanModel.inbound_receipt_id==receipt.id))]
def resolve_unresolved(scan_id,action,body,key,principal,db):
    def execute():
        row=db.scalar(select(UnresolvedInboundScanModel).join(InboundReceiptModel,InboundReceiptModel.id==UnresolvedInboundScanModel.inbound_receipt_id).where(UnresolvedInboundScanModel.id==scan_id,InboundReceiptModel.organization_id==org(principal)).with_for_update())
        if not row:raise receiving_error("INBOUND_RECEIPT_UNKNOWN_CODE","Escaneo no resuelto no encontrado.",404)
        row.status=action;row.resolution_type=action;row.resolved_product_id=getattr(body,"product_id",None);row.resolved_expected_line_id=getattr(body,"expected_line_id",None);row.reason=body.reason;row.resolved_by=principal.user_id;row.resolved_at=now();receipt=receipt_for(db,principal,row.inbound_receipt_id,True);receipt.total_unresolved_scans=max(0,receipt.total_unresolved_scans-1);return row
    return command(db,principal,key,f"phase039.unresolved.{action}:{scan_id}",body.model_dump(),execute)
@router.post("/inbound-receipts/{receipt_id}/resolve-unresolved-scan")
def resolve_unresolved_by_receipt(receipt_id:UUID,body:ResolveUnresolvedScanRequest,idempotency_key:IdempotencyKey,scan_id:UUID=Query(...),principal=Depends(require_permission("logistics.inbound_receipt_scans.resolve_unknown")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):receipt_for(db,principal,receipt_id);return resolve_unresolved(scan_id,"RESOLVED",body,idempotency_key,principal,db)
@router.post("/unresolved-inbound-scans/{scan_id}/associate-line")
def associate_line(scan_id:UUID,body:ResolveUnresolvedScanRequest,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_scans.resolve_unknown")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):return resolve_unresolved(scan_id,"ASSOCIATED_TO_LINE",body,idempotency_key,principal,db)
@router.post("/unresolved-inbound-scans/{scan_id}/associate-product")
def associate_product(scan_id:UUID,body:ResolveUnresolvedScanRequest,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_scans.resolve_unknown")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):return resolve_unresolved(scan_id,"ASSOCIATED_TO_PRODUCT",body,idempotency_key,principal,db)
@router.post("/unresolved-inbound-scans/{scan_id}/reject")
def reject_unresolved(scan_id:UUID,body:ResolveUnresolvedScanRequest,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_scans.resolve_unknown")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):return resolve_unresolved(scan_id,"REJECTED",body,idempotency_key,principal,db)
@router.post("/unresolved-inbound-scans/{scan_id}/mark-duplicate")
def duplicate_unresolved(scan_id:UUID,body:ResolveUnresolvedScanRequest,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_scans.resolve_unknown")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):return resolve_unresolved(scan_id,"DUPLICATE",body,idempotency_key,principal,db)


def observation_context(line_id,principal,db):
    line=line_for(db,principal,line_id);receipt=db.scalar(select(InboundReceiptModel).where(InboundReceiptModel.active_revision_id==line.receipt_revision_id));return line,receipt
@router.get("/inbound-receipt-lines/{line_id}/lot-observations",response_model=list[InboundLotObservationResponse])
def lots(line_id:UUID,principal=Depends(require_permission("logistics.inbound_receipts.read")),db:Session=Depends(get_db)):line_for(db,principal,line_id);return list(db.scalars(select(InboundLotObservationModel).where(InboundLotObservationModel.received_line_id==line_id)))
@router.post("/inbound-receipt-lines/{line_id}/lot-observations",response_model=InboundLotObservationResponse,status_code=201)
def add_lot(line_id:UUID,body:InboundLotObservationCreate,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_lots.capture")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):
    def execute():
        line,receipt=observation_context(line_id,principal,db);expected=db.get(InboundReceiptExpectedLineModel,line.expected_line_id);quantity=strict_decimal(body.quantity);service=InboundReceivingService(db);base=service._base_quantity(line.product_id,quantity,body.unit_id,expected.ordered_unit_id,expected.ordered_base_quantity/expected.ordered_quantity);normalized=body.lot_value.strip().upper();row=InboundLotObservationModel(id=uuid4(),inbound_receipt_id=receipt.id,receipt_revision_id=line.receipt_revision_id,received_line_id=line.id,expected_line_id=line.expected_line_id,product_id=line.product_id,lot_value=body.lot_value,normalized_lot_value=normalized,lot_hash=hashlib.sha256(normalized.encode()).hexdigest(),quantity=quantity,unit_id=body.unit_id,base_quantity=base,manufacturing_date=body.manufacturing_date,expiration_date=body.expiration_date,source=body.source,validation_status="VALID",captured_by=principal.user_id,captured_at=now());db.add(row);service.emit(receipt,principal,"logistics.inbound_receipt.lot_observed",resource_id=row.id,metadata={"received_line_id":str(line.id),"quantity":str(quantity),"unit_id":str(body.unit_id)});return row
    return command(db,principal,idempotency_key,f"phase039.lot:{line_id}",body.model_dump(),execute)
@router.get("/inbound-receipt-lines/{line_id}/serial-observations",response_model=list[InboundSerialObservationResponse])
def serials(line_id:UUID,principal=Depends(require_permission("logistics.inbound_receipt_identifiers.read_sensitive")),db:Session=Depends(get_db)):line_for(db,principal,line_id);return list(db.scalars(select(InboundSerialObservationModel).where(InboundSerialObservationModel.received_line_id==line_id)))
def add_serial_impl(line_id,body,principal,db):
    line,receipt=observation_context(line_id,principal,db);normalized=body.serial_value.strip();digest=hashlib.sha256(normalized.encode()).hexdigest();exists=db.scalar(select(InboundSerialObservationModel).where(InboundSerialObservationModel.inbound_receipt_id==receipt.id,InboundSerialObservationModel.serial_hash==digest,InboundSerialObservationModel.validation_status!="INVALIDATED"))
    if exists:raise receiving_error("INBOUND_RECEIPT_SERIAL_DUPLICATE","Serie duplicada dentro de la recepción.",409)
    row=InboundSerialObservationModel(id=uuid4(),inbound_receipt_id=receipt.id,receipt_revision_id=line.receipt_revision_id,received_line_id=line.id,expected_line_id=line.expected_line_id,product_id=line.product_id,normalized_serial_value=normalized,serial_hash=digest,source=body.source,validation_status="VALID",duplicate_status="UNIQUE_IN_RECEIPT",captured_by=principal.user_id,captured_at=now());db.add(row);InboundReceivingService(db).emit(receipt,principal,"logistics.inbound_receipt.serial_observed",resource_id=row.id,metadata={"received_line_id":str(line.id)});return row
@router.post("/inbound-receipt-lines/{line_id}/serial-observations",response_model=InboundSerialObservationResponse,status_code=201)
def add_serial(line_id:UUID,body:InboundSerialObservationCreate,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_serials.capture")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):return command(db,principal,idempotency_key,f"phase039.serial:{line_id}",body.model_dump(),lambda:add_serial_impl(line_id,body,principal,db))
@router.post("/inbound-receipt-lines/{line_id}/serial-observations/batch",response_model=list[InboundSerialObservationResponse])
def add_serial_batch(line_id:UUID,body:InboundSerialObservationBatchCreate,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_serials.capture")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):return command(db,principal,idempotency_key,f"phase039.serial.batch:{line_id}",body.model_dump(),lambda:[add_serial_impl(line_id,x,principal,db) for x in body.serials])
@router.get("/inbound-receipt-lines/{line_id}/expiration-observations",response_model=list[InboundExpirationObservationResponse])
def expirations(line_id:UUID,principal=Depends(require_permission("logistics.inbound_receipts.read")),db:Session=Depends(get_db)):line_for(db,principal,line_id);return list(db.scalars(select(InboundExpirationObservationModel).where(InboundExpirationObservationModel.received_line_id==line_id)))
@router.post("/inbound-receipt-lines/{line_id}/expiration-observations",response_model=InboundExpirationObservationResponse,status_code=201)
def add_expiration(line_id:UUID,body:InboundExpirationObservationCreate,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_expiration.capture")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):
    def execute():
        line,receipt=observation_context(line_id,principal,db);today=date.today();validation="EXPIRED" if body.expiration_date<today else "EXPIRES_TODAY" if body.expiration_date==today else "VALID";row=InboundExpirationObservationModel(id=uuid4(),inbound_receipt_id=receipt.id,received_line_id=line.id,product_id=line.product_id,manufacturing_date=body.manufacturing_date,expiration_date=body.expiration_date,source=body.source,validation_status=validation,policy_snapshot={},captured_by=principal.user_id,captured_at=now());db.add(row);service=InboundReceivingService(db);service.emit(receipt,principal,"logistics.inbound_receipt.expiration_observed",resource_id=row.id,metadata={"validation_status":validation});
        if validation=="EXPIRED":service.emit(receipt,principal,"logistics.inbound_receipt.expired_product_detected",resource_id=row.id)
        return row
    return command(db,principal,idempotency_key,f"phase039.expiration:{line_id}",body.model_dump(),execute)
@router.post("/inbound-serial-observations/{serial_id}/invalidate")
def invalidate_serial(serial_id:UUID,body:ReasonRequest,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_serials.capture")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):
    def execute():
        row=db.scalar(select(InboundSerialObservationModel).join(InboundReceiptModel,InboundReceiptModel.id==InboundSerialObservationModel.inbound_receipt_id).where(InboundSerialObservationModel.id==serial_id,InboundReceiptModel.organization_id==org(principal)).with_for_update())
        if not row:raise receiving_error("INBOUND_RECEIPT_SERIAL_NOT_FOUND","Serie observada no encontrada.",404)
        row.validation_status="INVALIDATED";return row
    return command(db,principal,idempotency_key,f"phase039.serial.invalidate:{serial_id}",body.model_dump(),execute)
@router.post("/inbound-lot-observations/{lot_id}/correct-via-revision")
def correct_lot(lot_id:UUID,body:ReasonRequest,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.inbound_receipt_lots.capture")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)): raise receiving_error("INBOUND_RECEIPT_REVISION_REQUIRED","La corrección requiere crear una nueva revisión de recepción.",409)


@router.get("/inbound-receipts/{receipt_id}/difference-candidates",response_model=list[ReceptionDifferenceCandidateResponse])
def candidates(receipt_id:UUID,principal=Depends(require_permission("logistics.reception_difference_candidates.read")),db:Session=Depends(get_db)):receipt=receipt_for(db,principal,receipt_id);return list(db.scalars(select(ReceptionDifferenceCandidateModel).where(ReceptionDifferenceCandidateModel.inbound_receipt_id==receipt.id)))
@router.get("/reception-difference-candidates/{candidate_id}",response_model=ReceptionDifferenceCandidateResponse)
def candidate(candidate_id:UUID,principal=Depends(require_permission("logistics.reception_difference_candidates.read")),db:Session=Depends(get_db)):
    row=db.scalar(select(ReceptionDifferenceCandidateModel).join(InboundReceiptModel,InboundReceiptModel.id==ReceptionDifferenceCandidateModel.inbound_receipt_id).where(ReceptionDifferenceCandidateModel.id==candidate_id,InboundReceiptModel.organization_id==org(principal)))
    if not row:raise receiving_error("RECEPTION_DIFFERENCE_CANDIDATE_NOT_FOUND","Candidato no encontrado.",404)
    return row
def candidate_transition(candidate_id,target,body,key,principal,db):
    def execute():
        row=candidate(candidate_id,principal,db);row.status=target;row.acknowledged_by=principal.user_id;row.acknowledged_at=now();row.dismissal_reason=body.reason if body else None;receipt=receipt_for(db,principal,row.inbound_receipt_id);code="logistics.inbound_receipt.difference_handover_ready" if target=="PREPARED_FOR_PHASE_040" else "logistics.inbound_receipt.difference_candidate_acknowledged";InboundReceivingService(db).emit(receipt,principal,code,resource_id=row.id,reason=body.reason if body else None,metadata={"status":target});return row
    return command(db,principal,key,f"phase039.candidate.{target}:{candidate_id}",body.model_dump() if body else {},execute)
@router.post("/reception-difference-candidates/{candidate_id}/acknowledge",response_model=ReceptionDifferenceCandidateResponse)
def acknowledge_candidate(candidate_id:UUID,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.reception_difference_candidates.acknowledge")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):return candidate_transition(candidate_id,"ACKNOWLEDGED",None,idempotency_key,principal,db)
@router.post("/reception-difference-candidates/{candidate_id}/dismiss",response_model=ReceptionDifferenceCandidateResponse)
def dismiss_candidate(candidate_id:UUID,body:ReasonRequest,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.reception_difference_candidates.dismiss")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):return candidate_transition(candidate_id,"DISMISSED_WITH_REASON",body,idempotency_key,principal,db)
@router.post("/reception-difference-candidates/{candidate_id}/prepare-for-phase-040",response_model=ReceptionDifferenceCandidateResponse)
def prepare_candidate(candidate_id:UUID,idempotency_key:IdempotencyKey,principal=Depends(require_permission("logistics.reception_difference_candidates.prepare")),db:Session=Depends(get_db),_csrf=Depends(verify_csrf)):return candidate_transition(candidate_id,"PREPARED_FOR_PHASE_040",None,idempotency_key,principal,db)
