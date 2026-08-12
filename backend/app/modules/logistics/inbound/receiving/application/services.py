from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import ArrivalNoticeExpectedLineModel, ArrivalNoticeModel, ArrivalNoticeOutboxEventModel, ArrivalNoticePurchaseOrderReferenceModel, ArrivalNoticeRevisionModel
from app.modules.logistics.audit.service import AuditEventCommand, AuditService
from app.modules.logistics.inbound.dock_operations.application.services.unloading_services import ReceivingScanPreparationService
from app.modules.logistics.inbound.dock_operations.infrastructure.persistence.models import InboundDockAssignmentModel, UnloadingOperationModel
from app.modules.logistics.products.models import ProductIdentifierModel, ProductModel, ProductTrackingPolicyModel
from app.modules.logistics.procurement.purchase_orders.infrastructure.persistence.models import PurchaseOrderLineModel
from app.modules.logistics.units.conversion_engine import UnitConversionEngine
from app.modules.logistics.units.models import ProductPackagingDefinitionModel, ProductUnitConfigurationModel, UnitConversionRuleModel, UnitOfMeasureModel
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.auth_dependencies import resolve_organization_id

from ..domain.enums import ReceiptStatus, RevisionStatus, ScanEventStatus, ScanSessionStatus
from ..domain.errors import receiving_error
from ..domain.services import BarcodeParserRegistry, canonical_hash, require_receipt_transition, strict_decimal
from ..infrastructure.persistence.models import (
    InboundExpirationObservationModel, InboundLotObservationModel, InboundReceiptExpectedLineModel,
    InboundReceiptModel, InboundReceiptPauseModel, InboundReceiptProgressProjectionModel,
    InboundReceiptPolicyModel,
    InboundReceiptRevisionModel, InboundReceivedLineModel, InboundScanCompensationEventModel,
    InboundScanEventModel, InboundScanSessionModel, InboundSerialObservationModel,
    PurchaseOrderReceiptProgressModel, ReceptionDifferenceCandidateModel, ReceivingValidationResultModel,
    UnresolvedInboundScanModel,
)


def now() -> datetime:
    return datetime.now(timezone.utc)


def actor(principal: LogisticsPrincipal) -> dict[str, str]:
    return {"user_id": str(principal.user_id), "display_name": principal.full_name, "email": principal.email}


def row_dict(row: object) -> dict:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


class ProductIdentifierResolver:
    def __init__(self, db: Session): self.db = db

    def resolve(self, organization_id: UUID, normalized_code: str, revision_id: UUID | None = None) -> dict:
        products = list(self.db.scalars(select(ProductModel).where(ProductModel.organization_id == organization_id, ProductModel.status.in_(("ACTIVE", "APPROVED", "PUBLISHED")), or_(ProductModel.normalized_sku == normalized_code.upper(), ProductModel.sku == normalized_code))))
        identifiers = list(self.db.scalars(select(ProductIdentifierModel).where(ProductIdentifierModel.organization_id == organization_id, ProductIdentifierModel.normalized_value == normalized_code, ProductIdentifierModel.status == "ACTIVE")))
        by_id = {p.id: p for p in products}
        for identifier in identifiers:
            product = self.db.get(ProductModel, identifier.product_id)
            if product and product.organization_id == organization_id and product.lifecycle_status == "ACTIVE": by_id[product.id] = product
        candidates = list(by_id.values())
        if len(candidates) != 1:
            return {"resolution_status": "AMBIGUOUS" if candidates else "UNKNOWN_CODE", "product_id": None, "product_version_id": None, "expected_line_id": None, "candidate_product_ids": [x.id for x in candidates]}
        product = candidates[0]
        expected = None
        if revision_id:
            expected = self.db.scalar(select(InboundReceiptExpectedLineModel).where(InboundReceiptExpectedLineModel.receipt_revision_id == revision_id, InboundReceiptExpectedLineModel.product_id == product.id))
        return {"resolution_status": "RESOLVED_TO_EXPECTED_LINE" if expected else "RESOLVED_TO_PRODUCT_ONLY", "product_id": product.id, "product_version_id": product.active_version_id, "expected_line_id": expected.id if expected else None, "candidate_product_ids": []}


class InboundReceivingService:
    def __init__(self, db: Session): self.db = db

    def emit(self, receipt: InboundReceiptModel, principal: LogisticsPrincipal, event_code: str, *, resource_id: UUID | None = None, metadata: dict | None = None, reason: str | None = None) -> None:
        event_id = uuid4(); occurred = now(); safe_metadata = metadata or {}
        self.db.add(ArrivalNoticeOutboxEventModel(id=event_id, organization_id=receipt.organization_id, aggregate_type="INBOUND_RECEIPT", aggregate_id=receipt.id, event_type=event_code, payload={"receipt_id": str(receipt.id), "warehouse_id": str(receipt.warehouse_id), "occurred_at": occurred.isoformat(), **safe_metadata}, deduplication_key=f"phase039:{receipt.id}:{event_code}:{event_id}", status="PENDING"))
        AuditService().write_event(self.db, AuditEventCommand(event_code=event_code, actor_user_id=principal.user_id, actor_display_name=principal.full_name, actor_role_codes=principal.role_codes, session_id=principal.session_id, device_id=principal.device_id, authentication_level=principal.authentication_level, correlation_id=principal.correlation_id, ip_address=principal.ip_address, user_agent=principal.user_agent, organization_id=receipt.organization_id, branch_id=receipt.branch_id, warehouse_id=receipt.warehouse_id, resource_type="inbound_receipt", resource_id=str(resource_id or receipt.id), action=event_code.rsplit(".", 1)[-1], reason_text=reason, metadata=safe_metadata, source_module="logistics.inbound.receiving", source_service=self.__class__.__name__))

    def receipt(self, receipt_id: UUID, organization_id: UUID, *, lock: bool = False) -> InboundReceiptModel:
        query = select(InboundReceiptModel).where(InboundReceiptModel.id == receipt_id, InboundReceiptModel.organization_id == organization_id)
        if lock: query = query.with_for_update()
        receipt = self.db.scalar(query)
        if not receipt: raise receiving_error("INBOUND_RECEIPT_NOT_FOUND", "Recepción no encontrada.", 404)
        return receipt

    def policy(self, receipt: InboundReceiptModel) -> InboundReceiptPolicyModel | None:
        timestamp = now()
        return self.db.scalar(select(InboundReceiptPolicyModel).where(InboundReceiptPolicyModel.organization_id == receipt.organization_id, or_(InboundReceiptPolicyModel.warehouse_id == receipt.warehouse_id, InboundReceiptPolicyModel.warehouse_id.is_(None)), InboundReceiptPolicyModel.effective_from <= timestamp, or_(InboundReceiptPolicyModel.effective_to.is_(None), InboundReceiptPolicyModel.effective_to > timestamp)).order_by(InboundReceiptPolicyModel.warehouse_id.desc().nullslast(), InboundReceiptPolicyModel.version.desc()).limit(1))

    @staticmethod
    def maximum_receivable(remaining: Decimal, policy: InboundReceiptPolicyModel | None) -> Decimal:
        if not policy or not policy.over_receipt_allowed: return remaining
        tolerance = Decimal(policy.over_receipt_tolerance_value or 0)
        if policy.over_receipt_tolerance_type == "ABSOLUTE_QUANTITY": return remaining + tolerance
        if policy.over_receipt_tolerance_type == "PERCENTAGE": return remaining + (remaining * tolerance / Decimal("100"))
        return remaining

    def create_from_unloading(self, operation_id: UUID, principal: LogisticsPrincipal, receipt_type: str, scan_mode_policy: dict) -> InboundReceiptModel:
        organization_id = resolve_organization_id(principal)
        operation = self.db.scalar(select(UnloadingOperationModel).where(UnloadingOperationModel.id == operation_id, UnloadingOperationModel.organization_id == organization_id).with_for_update())
        if not operation: raise receiving_error("INBOUND_RECEIPT_SOURCE_INVALID", "Descarga no encontrada.", 404)
        if operation.status != "COMPLETED" or not operation.completed_at: raise receiving_error("INBOUND_RECEIPT_UNLOADING_NOT_COMPLETED", "La descarga debe estar completada.", 409)
        existing = self.db.scalar(select(InboundReceiptModel).where(InboundReceiptModel.unloading_operation_id == operation.id, ~InboundReceiptModel.status.in_(("COMPLETED", "CANCELLED", "SUPERSEDED", "FAILED"))))
        if existing: raise receiving_error("INBOUND_RECEIPT_ALREADY_EXISTS", "Ya existe una recepción activa para la descarga.", 409)
        assignment = self.db.get(InboundDockAssignmentModel, operation.dock_assignment_id)
        preparation = ReceivingScanPreparationService(self.db).get(operation)
        po_refs = preparation.get("purchase_order_references") or []
        supplier_id = None
        if operation.arrival_notice_id:
            notice = self.db.get(ArrivalNoticeModel, operation.arrival_notice_id)
            if notice and notice.active_revision_id:
                supplier_id = self.db.scalar(select(ArrivalNoticePurchaseOrderReferenceModel.supplier_business_partner_id).where(ArrivalNoticePurchaseOrderReferenceModel.arrival_notice_revision_id == notice.active_revision_id).limit(1))
        code = f"INRCV-{now().year}-{uuid4().hex[:12].upper()}"
        receipt = InboundReceiptModel(id=uuid4(), organization_id=organization_id, branch_id=assignment.branch_id, warehouse_id=operation.warehouse_id, receipt_code=code, normalized_receipt_code=code, unloading_operation_id=operation.id, dock_assignment_id=operation.dock_assignment_id, gate_check_in_id=operation.gate_check_in_id, appointment_id=operation.appointment_id, arrival_notice_id=operation.arrival_notice_id, supplier_business_partner_id=supplier_id, supplier_snapshot=preparation.get("supplier_summary") or {}, carrier_snapshot=preparation.get("carrier_summary"), status="CREATED", receipt_type=receipt_type if len(po_refs) <= 1 else "MULTI_PURCHASE_ORDER_RECEIPT", scan_mode_policy=scan_mode_policy)
        self.db.add(receipt); self.db.flush(); self.emit(receipt, principal, "logistics.inbound_receipt.created"); return receipt

    def prepare(self, receipt_id: UUID, principal: LogisticsPrincipal) -> InboundReceiptModel:
        org = resolve_organization_id(principal); receipt = self.receipt(receipt_id, org, lock=True); require_receipt_transition(receipt.status, "PREPARING"); receipt.status = "PREPARING"
        operation = self.db.get(UnloadingOperationModel, receipt.unloading_operation_id); source = ReceivingScanPreparationService(self.db).get(operation)
        revision = InboundReceiptRevisionModel(id=uuid4(), inbound_receipt_id=receipt.id, revision_number=receipt.current_revision_number + 1, status="EDITABLE", source_snapshot=jsonable_encoder(source), created_by=principal.user_id)
        self.db.add(revision); self.db.flush()
        notice = self.db.get(ArrivalNoticeModel, receipt.arrival_notice_id) if receipt.arrival_notice_id else None
        source_revision = self.db.get(ArrivalNoticeRevisionModel, notice.active_revision_id) if notice and notice.active_revision_id else None
        policy = self.policy(receipt)
        rows = list(self.db.scalars(select(ArrivalNoticeExpectedLineModel).where(ArrivalNoticeExpectedLineModel.arrival_notice_revision_id == source_revision.id))) if source_revision else []
        for row in rows:
            po_ref = self.db.get(ArrivalNoticePurchaseOrderReferenceModel, row.purchase_order_reference_id)
            po_line = self.db.get(PurchaseOrderLineModel, row.purchase_order_line_id)
            if not po_line or po_line.purchase_order_revision_id != po_ref.purchase_order_revision_id:
                raise receiving_error("INBOUND_RECEIPT_SOURCE_INVALID", "La línea de aviso no coincide con la revisión de la orden de compra.", 409)
            previous = self.db.scalar(select(PurchaseOrderReceiptProgressModel).where(PurchaseOrderReceiptProgressModel.organization_id == receipt.organization_id, PurchaseOrderReceiptProgressModel.purchase_order_line_id == po_line.id))
            previous_quantity = Decimal(previous.cumulative_received_quantity) if previous else Decimal("0")
            ordered_quantity = Decimal(po_line.ordered_quantity)
            ordered_base_quantity = Decimal(po_line.base_quantity) if po_line.base_quantity is not None else Decimal(row.expected_base_quantity)
            remaining_quantity = max(ordered_quantity - previous_quantity, Decimal("0"))
            remaining_base = max(ordered_base_quantity - (Decimal(previous_quantity) * ordered_base_quantity / ordered_quantity), Decimal("0"))
            tracking = self.db.scalar(select(ProductTrackingPolicyModel).where(ProductTrackingPolicyModel.product_id == row.product_id)) if row.product_id else None
            packages = list(self.db.scalars(select(ProductPackagingDefinitionModel).where(ProductPackagingDefinitionModel.product_id == row.product_id, ProductPackagingDefinitionModel.status == "ACTIVE"))) if row.product_id else []
            max_quantity = self.maximum_receivable(remaining_quantity, policy); factor = ordered_base_quantity / ordered_quantity
            self.db.add(InboundReceiptExpectedLineModel(id=uuid4(), receipt_revision_id=revision.id, purchase_order_id=po_ref.purchase_order_id, purchase_order_revision_id=po_ref.purchase_order_revision_id, purchase_order_line_id=row.purchase_order_line_id, arrival_notice_expected_line_id=row.id, product_id=po_line.product_id or row.product_id, product_version_id=po_line.product_version_id or row.product_version_id, line_number=po_line.line_number, sku_snapshot=po_line.sku_snapshot or row.sku_snapshot, product_name_snapshot=po_line.product_name_snapshot, ordered_quantity=ordered_quantity, ordered_unit_id=po_line.ordered_unit_id or row.expected_unit_id, ordered_base_quantity=ordered_base_quantity, shipped_quantity=row.expected_quantity, shipped_unit_id=row.expected_unit_id, shipped_base_quantity=row.expected_base_quantity, previously_received_quantity=previous_quantity, previously_received_base_quantity=ordered_base_quantity-remaining_base, maximum_receivable_quantity=max_quantity, maximum_receivable_base_quantity=max_quantity*factor, tracking_policy_snapshot=row_dict(tracking) if tracking else {}, packaging_snapshot=[jsonable_encoder(row_dict(p)) for p in packages], status="OPEN"))
        self.db.flush(); receipt.active_revision_id = revision.id; receipt.current_revision_number = revision.revision_number; receipt.total_expected_lines = len(rows); receipt.status = "READY"; revision.expected_lines_snapshot = [jsonable_encoder(row_dict(x)) for x in self.db.scalars(select(InboundReceiptExpectedLineModel).where(InboundReceiptExpectedLineModel.receipt_revision_id == revision.id))]; revision.content_hash = canonical_hash(revision.expected_lines_snapshot); self.recalculate(receipt); self.emit(receipt, principal, "logistics.inbound_receipt.prepared", metadata={"revision_id": str(revision.id), "expected_line_count": len(rows)}); return receipt

    def transition(self, receipt_id: UUID, target: str, principal: LogisticsPrincipal, reason: str | None = None) -> InboundReceiptModel:
        receipt = self.receipt(receipt_id, resolve_organization_id(principal), lock=True); require_receipt_transition(receipt.status, target); timestamp = now(); receipt.status = target; receipt.row_version += 1
        if target == "IN_PROGRESS" and not receipt.started_at: receipt.started_at = timestamp; receipt.started_by_user_id = principal.user_id; receipt.started_by_snapshot = actor(principal)
        if target == "PAUSED": self.db.add(InboundReceiptPauseModel(id=uuid4(), inbound_receipt_id=receipt.id, reason_code="OTHER", reason=reason or "Pausa operativa", started_at=timestamp, started_by=principal.user_id, status="ACTIVE"))
        if target == "CANCELLED": receipt.cancelled_at = timestamp; receipt.cancelled_by_user_id = principal.user_id; receipt.cancellation_reason = reason
        event_codes = {"IN_PROGRESS": "logistics.inbound_receipt.started" if receipt.started_at == timestamp else "logistics.inbound_receipt.resumed", "PAUSED": "logistics.inbound_receipt.paused", "CANCELLED": "logistics.inbound_receipt.cancelled"}
        if target in event_codes: self.emit(receipt, principal, event_codes[target], reason=reason)
        return receipt

    def session(self, receipt_id: UUID, principal: LogisticsPrincipal, scanner_type: str, station_id: UUID | None, device_reference: str | None, client_reference: str | None) -> InboundScanSessionModel:
        receipt = self.receipt(receipt_id, resolve_organization_id(principal), lock=True)
        if receipt.status != "IN_PROGRESS": raise receiving_error("INBOUND_RECEIPT_STATUS_INVALID", "La recepción debe estar en progreso.", 409)
        timestamp = now(); session = InboundScanSessionModel(id=uuid4(), organization_id=receipt.organization_id, inbound_receipt_id=receipt.id, receipt_revision_id=receipt.active_revision_id, warehouse_id=receipt.warehouse_id, station_id=station_id, device_reference_hash=hashlib.sha256(device_reference.encode()).hexdigest() if device_reference else None, scanner_type=scanner_type, status="ACTIVE", operator_user_id=principal.user_id, operator_snapshot=actor(principal), started_at=timestamp, last_activity_at=timestamp, client_session_reference=client_reference)
        self.db.add(session); self.db.flush(); self.emit(receipt, principal, "logistics.inbound_receipt.scan_session_started", resource_id=session.id, metadata={"scan_session_id": str(session.id)}); return session

    def resolve_code(self, receipt: InboundReceiptModel, raw_code: str, symbology: str | None) -> dict:
        parsed = BarcodeParserRegistry.parse(raw_code, symbology); resolved = ProductIdentifierResolver(self.db).resolve(receipt.organization_id, parsed.normalized_code, receipt.active_revision_id)
        return {"normalized_code": parsed.normalized_code, "code_hash": hashlib.sha256(parsed.normalized_code.encode()).hexdigest(), "parse_status": str(parsed.parse_status), "symbology": parsed.symbology, "parsed_elements": parsed.elements, **resolved}

    def scan(self, receipt_id: UUID, principal: LogisticsPrincipal, body) -> InboundScanEventModel:
        receipt = self.receipt(receipt_id, resolve_organization_id(principal), lock=True)
        if receipt.status != "IN_PROGRESS": raise receiving_error("INBOUND_RECEIPT_STATUS_INVALID", "La recepción no admite escaneos.", 409)
        session = self.db.scalar(select(InboundScanSessionModel).where(InboundScanSessionModel.id == body.scan_session_id, InboundScanSessionModel.inbound_receipt_id == receipt.id).with_for_update())
        if not session or session.status != "ACTIVE": raise receiving_error("INBOUND_SCAN_SESSION_INACTIVE", "La sesión de escaneo no está activa.", 409)
        duplicate = self.db.scalar(select(InboundScanEventModel).where(InboundScanEventModel.scan_session_id == session.id, InboundScanEventModel.client_scan_id == body.client_scan_id))
        result = self.resolve_code(receipt, body.raw_code, body.symbology); quantity = strict_decimal(body.requested_quantity); accepted = Decimal("0"); base = Decimal("0"); unit_id = body.requested_unit_id
        if duplicate:
            if duplicate.code_hash != result["code_hash"] or duplicate.requested_quantity != quantity or duplicate.requested_unit_id != body.requested_unit_id:
                raise receiving_error("IDEMPOTENCY_CONFLICT", "client_scan_id fue reutilizado con otro payload.", 409)
            return duplicate
        expected = self.db.get(InboundReceiptExpectedLineModel, result["expected_line_id"]) if result["expected_line_id"] else None
        received = self.db.scalar(select(InboundReceivedLineModel).where(InboundReceivedLineModel.receipt_revision_id == receipt.active_revision_id, InboundReceivedLineModel.product_id == result["product_id"]).with_for_update()) if result["product_id"] else None
        if expected:
            unit_id = unit_id or expected.ordered_unit_id; base = self._base_quantity(expected.product_id, quantity, unit_id, expected.ordered_unit_id, expected.ordered_base_quantity / expected.ordered_quantity)
            accepted = quantity
            if not received:
                policy = expected.tracking_policy_snapshot or {}
                received = InboundReceivedLineModel(id=uuid4(), receipt_revision_id=receipt.active_revision_id, expected_line_id=expected.id, product_id=expected.product_id, product_version_id=expected.product_version_id, resolution_status="RESOLVED_TO_EXPECTED_LINE", received_quantity=Decimal("0"), received_unit_id=unit_id, received_base_quantity=Decimal("0"), scan_count=0, manual_entry_count=0, lot_capture_required=bool(policy.get("lot_control")), serial_capture_required=bool(policy.get("serial_control")), expiration_capture_required=policy.get("expiration_control", "NONE") != "NONE", validation_status="NOT_VALIDATED", comparison_status="NOT_COMPARED")
                self.db.add(received); self.db.flush()
            if received.received_base_quantity + base > expected.maximum_receivable_base_quantity: raise receiving_error("INBOUND_RECEIPT_QUANTITY_EXCEEDED", "La cantidad supera el saldo autorizado.", 409)
            received.received_quantity += quantity; received.received_base_quantity += base; received.scan_count += 1; received.row_version += 1
        sequence = (self.db.scalar(select(func.max(InboundScanEventModel.server_sequence)).where(InboundScanEventModel.inbound_receipt_id == receipt.id)) or 0) + 1; timestamp = now(); status = "APPLIED" if expected else "RECORDED"
        event = InboundScanEventModel(id=uuid4(), organization_id=receipt.organization_id, inbound_receipt_id=receipt.id, receipt_revision_id=receipt.active_revision_id, scan_session_id=session.id, client_scan_id=body.client_scan_id, client_sequence=body.client_sequence, server_sequence=sequence, normalized_code=result["normalized_code"], code_hash=result["code_hash"], symbology=result["symbology"], parser_code=result["symbology"], parser_version="1", parse_status=result["parse_status"], parsed_elements=result["parsed_elements"], resolution_status=result["resolution_status"], resolved_product_id=result["product_id"], resolved_product_version_id=result["product_version_id"], resolved_expected_line_id=result["expected_line_id"], requested_quantity=quantity, requested_unit_id=body.requested_unit_id, accepted_quantity=accepted, accepted_unit_id=unit_id, accepted_base_quantity=base, scan_source=body.scan_source, client_captured_at=body.client_captured_at, received_at=timestamp, processed_at=timestamp, operator_user_id=principal.user_id, validation_summary={}, status=status)
        self.db.add(event); session.last_activity_at = timestamp
        if not expected:
            self.db.add(UnresolvedInboundScanModel(id=uuid4(), inbound_receipt_id=receipt.id, scan_event_id=event.id, code_hash=result["code_hash"], candidate_product_ids=[str(x) for x in result["candidate_product_ids"]], status="OPEN")); receipt.total_unresolved_scans += 1
        self.db.flush(); self.recalculate(receipt); self.emit(receipt, principal, "logistics.inbound_receipt.code_scanned", resource_id=event.id, metadata={"scan_event_id": str(event.id), "result": status}); self.emit(receipt, principal, "logistics.inbound_receipt.code_resolved" if expected else "logistics.inbound_receipt.code_unresolved", resource_id=event.id); return event

    def _base_quantity(self, product_id: UUID, quantity: Decimal, source_unit_id: UUID, target_unit_id: UUID, fallback_factor: Decimal) -> Decimal:
        if source_unit_id == target_unit_id: return quantity * fallback_factor
        rule = self.db.scalar(select(UnitConversionRuleModel).where(UnitConversionRuleModel.product_id == product_id, UnitConversionRuleModel.source_unit_id == source_unit_id, UnitConversionRuleModel.target_unit_id == target_unit_id, UnitConversionRuleModel.status == "ACTIVE"))
        if not rule: raise receiving_error("INBOUND_RECEIPT_CONVERSION_MISSING", "No existe una conversión aprobada para la unidad.", 409)
        source = self.db.get(UnitOfMeasureModel, source_unit_id); target = self.db.get(UnitOfMeasureModel, target_unit_id)
        result = UnitConversionEngine.convert(quantity, source.code, target.code, Decimal(rule.multiplier), [source.code, target.code], precision=target.decimal_precision, rounding_policy=rule.rounding_policy, integer_only_target=target.integer_only)
        return Decimal(result["rounded_result"])

    def validate(self, receipt_id: UUID, principal: LogisticsPrincipal) -> dict:
        receipt = self.receipt(receipt_id, resolve_organization_id(principal), lock=True)
        self.emit(receipt, principal, "logistics.inbound_receipt.validation_started")
        if receipt.status == "IN_PROGRESS": require_receipt_transition(receipt.status, "VALIDATING"); receipt.status = "VALIDATING"
        unresolved = self.db.scalar(select(func.count()).select_from(UnresolvedInboundScanModel).where(UnresolvedInboundScanModel.inbound_receipt_id == receipt.id, UnresolvedInboundScanModel.status == "OPEN")) or 0
        lines = list(self.db.scalars(select(InboundReceiptExpectedLineModel).where(InboundReceiptExpectedLineModel.receipt_revision_id == receipt.active_revision_id)))
        received = {x.expected_line_id: x for x in self.db.scalars(select(InboundReceivedLineModel).where(InboundReceivedLineModel.receipt_revision_id == receipt.active_revision_id))}
        incomplete = under = over = identifier_errors = expiration_errors = 0
        errors = (["UNRESOLVED_SCANS"] if unresolved else [])
        for line in lines:
            observed = received.get(line.id); qty = observed.received_base_quantity if observed else Decimal("0")
            if qty == 0: incomplete += 1
            if qty < line.ordered_base_quantity: under += 1
            elif qty > line.ordered_base_quantity: over += 1
            if observed:
                observed.comparison_status = "EXACT_EXPECTED" if qty == line.ordered_base_quantity else ("UNDER_EXPECTED" if qty < line.ordered_base_quantity else "OVER_EXPECTED")
                lots = list(self.db.scalars(select(InboundLotObservationModel).where(InboundLotObservationModel.received_line_id == observed.id, InboundLotObservationModel.validation_status != "INVALIDATED")))
                serials = list(self.db.scalars(select(InboundSerialObservationModel).where(InboundSerialObservationModel.received_line_id == observed.id, InboundSerialObservationModel.validation_status != "INVALIDATED")))
                expirations = list(self.db.scalars(select(InboundExpirationObservationModel).where(InboundExpirationObservationModel.received_line_id == observed.id)))
                observed.lot_capture_complete = not observed.lot_capture_required or sum((Decimal(x.base_quantity) for x in lots), Decimal("0")) == Decimal(observed.received_base_quantity)
                observed.serial_capture_complete = not observed.serial_capture_required or Decimal(len(serials)) == Decimal(observed.received_base_quantity)
                observed.expiration_capture_complete = not observed.expiration_capture_required or bool(expirations)
                identifier_errors += int(not observed.lot_capture_complete) + int(not observed.serial_capture_complete)
                line_expiration_errors = int(not observed.expiration_capture_complete) + sum(1 for x in expirations if x.validation_status in {"EXPIRED", "DATE_ORDER_INVALID", "REQUIRED_MISSING"})
                expiration_errors += line_expiration_errors
                observed.validation_status = "VALID" if observed.lot_capture_complete and observed.serial_capture_complete and observed.expiration_capture_complete and not line_expiration_errors else "INVALID"
        if identifier_errors: errors.append("IDENTIFIER_CAPTURE_INCOMPLETE")
        if expiration_errors: errors.append("EXPIRATION_INVALID")
        result = {"validation_status": "INVALID" if errors else "VALID_WITH_WARNINGS" if incomplete or over else "VALID", "blocking_errors": errors, "warnings": (["INCOMPLETE_LINES"] if incomplete else []) + (["OVER_RECEIVED_LINES"] if over else []), "unresolved_scans": unresolved, "incomplete_lines": incomplete, "over_received_lines": over, "under_received_lines": under, "identifier_errors": identifier_errors, "expiration_errors": expiration_errors, "difference_candidates": 0, "completion_options": [] if errors else ["PARTIAL", "TOTAL"], "server_time": now()}
        result["validation_hash"] = canonical_hash(result); self.db.add(ReceivingValidationResultModel(id=uuid4(), inbound_receipt_id=receipt.id, receipt_revision_id=receipt.active_revision_id, validation_status=result["validation_status"], result=jsonable_encoder(result), validation_hash=result["validation_hash"], validated_by=principal.user_id)); receipt.total_validation_errors = len(errors); receipt.status = "REQUIRES_CORRECTION" if errors else ("PARTIALLY_RECEIVED" if under else "FULLY_RECEIVED"); self._create_difference_candidates(receipt, lines, received, principal); self.recalculate(receipt); self.emit(receipt, principal, "logistics.inbound_receipt.validation_failed" if errors else ("logistics.inbound_receipt.partially_received" if under else "logistics.inbound_receipt.fully_received"), metadata={"validation_hash": result["validation_hash"]}); return result

    def _create_difference_candidates(self, receipt, lines, received, principal):
        for line in lines:
            observed = received.get(line.id); qty = observed.received_base_quantity if observed else Decimal("0"); variance = qty - line.ordered_base_quantity
            if variance == 0: continue
            kind = "SHORTAGE_CANDIDATE" if variance < 0 else "OVERAGE_CANDIDATE"
            exists = self.db.scalar(select(ReceptionDifferenceCandidateModel).where(ReceptionDifferenceCandidateModel.inbound_receipt_id == receipt.id, ReceptionDifferenceCandidateModel.expected_line_id == line.id, ReceptionDifferenceCandidateModel.candidate_type == kind, ReceptionDifferenceCandidateModel.status.in_(("OPEN", "ACKNOWLEDGED", "PREPARED_FOR_PHASE_040"))))
            if not exists:
                candidate = ReceptionDifferenceCandidateModel(id=uuid4(), organization_id=receipt.organization_id, inbound_receipt_id=receipt.id, receipt_revision_id=receipt.active_revision_id, expected_line_id=line.id, received_line_id=observed.id if observed else None, candidate_type=kind, severity="HIGH" if variance > 0 else "MEDIUM", expected_value={"base_quantity": str(line.ordered_base_quantity)}, observed_value={"base_quantity": str(qty)}, variance_quantity=variance, unit_id=line.ordered_unit_id, evidence_file_ids=[], status="OPEN", detected_at=now(), detected_by_service="ReceivingValidationService")
                self.db.add(candidate); self.emit(receipt, principal, "logistics.inbound_receipt.difference_candidate_created", resource_id=candidate.id, metadata={"candidate_type": kind, "variance_quantity": str(variance)})
        self.db.flush(); receipt.total_difference_candidates = self.db.scalar(select(func.count()).select_from(ReceptionDifferenceCandidateModel).where(ReceptionDifferenceCandidateModel.inbound_receipt_id == receipt.id, ReceptionDifferenceCandidateModel.status.in_(("OPEN", "ACKNOWLEDGED", "PREPARED_FOR_PHASE_040")))) or 0

    def complete(self, receipt_id: UUID, principal: LogisticsPrincipal, row_version: int) -> dict:
        receipt = self.receipt(receipt_id, resolve_organization_id(principal), lock=True)
        if receipt.row_version != row_version: raise receiving_error("INBOUND_RECEIPT_STALE_VERSION", "La recepción fue modificada por otra sesión.", 409)
        if receipt.status not in {"PARTIALLY_RECEIVED", "FULLY_RECEIVED", "REQUIRES_DIFFERENCE_REVIEW"}: raise receiving_error("INBOUND_RECEIPT_VALIDATION_FAILED", "La recepción debe validarse antes de cerrar.", 409)
        active_sessions = self.db.scalar(select(func.count()).select_from(InboundScanSessionModel).where(InboundScanSessionModel.inbound_receipt_id == receipt.id, InboundScanSessionModel.status == "ACTIVE")) or 0
        if active_sessions: raise receiving_error("INBOUND_SCAN_SESSION_INACTIVE", "Complete o cancele las sesiones de escaneo activas.", 409)
        classification = "TOTAL" if receipt.status == "FULLY_RECEIVED" else "PARTIAL"
        if receipt.total_difference_candidates: classification += "_WITH_DIFFERENCE_CANDIDATES"
        timestamp = now(); revision = self.db.get(InboundReceiptRevisionModel, receipt.active_revision_id)
        snapshot = self.snapshot(receipt); content_hash = canonical_hash(snapshot); revision.received_lines_snapshot = snapshot["received_lines"]; revision.identifier_capture_snapshot = snapshot["identifiers"]; revision.validation_snapshot = snapshot["validation_results"]; revision.difference_candidate_snapshot = snapshot["difference_candidates"]; revision.completion_snapshot = snapshot; revision.content_hash = content_hash; revision.status = "FROZEN"; revision.frozen_at = timestamp
        receipt.status = "COMPLETED"; receipt.completed_at = timestamp; receipt.completed_by_user_id = principal.user_id; receipt.completed_by_snapshot = actor(principal); receipt.completion_classification = classification; receipt.content_hash = content_hash; receipt.row_version += 1
        expected_lines = list(self.db.scalars(select(InboundReceiptExpectedLineModel).where(InboundReceiptExpectedLineModel.receipt_revision_id == receipt.active_revision_id)))
        received_by_expected = {line.expected_line_id: line for line in self.db.scalars(select(InboundReceivedLineModel).where(InboundReceivedLineModel.receipt_revision_id == receipt.active_revision_id))}
        for expected in expected_lines:
            received = received_by_expected.get(expected.id); current_quantity = Decimal(received.received_quantity) if received else Decimal("0")
            progress = self.db.scalar(select(PurchaseOrderReceiptProgressModel).where(PurchaseOrderReceiptProgressModel.organization_id == receipt.organization_id, PurchaseOrderReceiptProgressModel.purchase_order_line_id == expected.purchase_order_line_id).with_for_update())
            if not progress:
                progress = PurchaseOrderReceiptProgressModel(id=uuid4(), organization_id=receipt.organization_id, purchase_order_id=expected.purchase_order_id, purchase_order_line_id=expected.purchase_order_line_id, ordered_quantity=expected.ordered_quantity, cumulative_received_quantity=Decimal("0"), remaining_quantity=expected.ordered_quantity, receipt_count=0)
                self.db.add(progress)
            progress.cumulative_received_quantity += current_quantity; progress.remaining_quantity = max(Decimal(progress.ordered_quantity) - Decimal(progress.cumulative_received_quantity), Decimal("0")); progress.receipt_count += 1; progress.last_receipt_at = timestamp; progress.pending_difference_review = bool(receipt.total_difference_candidates)
            progress.fulfillment_status = "OVER_RECEIVED_REVIEW" if progress.cumulative_received_quantity > progress.ordered_quantity else ("QUANTITY_RECEIVED" if progress.remaining_quantity == 0 else "PARTIALLY_RECEIVED" if progress.cumulative_received_quantity > 0 else "NOT_RECEIVED")
        self.emit(receipt, principal, "logistics.inbound_receipt.completed", metadata={"classification": classification, "content_hash": content_hash})
        return {"receipt_id": receipt.id, "status": receipt.status, "completion_classification": classification, "completed_at": timestamp, "content_hash": content_hash, "phase_040_ready": bool(receipt.total_difference_candidates)}

    def snapshot(self, receipt: InboundReceiptModel) -> dict:
        revision_id = receipt.active_revision_id
        def rows(model, condition): return [jsonable_encoder(row_dict(x)) for x in self.db.scalars(select(model).where(condition))]
        return {"canonicalization_version": "1", "receipt": jsonable_encoder(row_dict(receipt)), "expected_lines": rows(InboundReceiptExpectedLineModel, InboundReceiptExpectedLineModel.receipt_revision_id == revision_id), "received_lines": rows(InboundReceivedLineModel, InboundReceivedLineModel.receipt_revision_id == revision_id), "scan_sessions": rows(InboundScanSessionModel, InboundScanSessionModel.receipt_revision_id == revision_id), "scan_events": rows(InboundScanEventModel, InboundScanEventModel.receipt_revision_id == revision_id), "identifiers": {"lots": rows(InboundLotObservationModel, InboundLotObservationModel.receipt_revision_id == revision_id), "serials": rows(InboundSerialObservationModel, InboundSerialObservationModel.receipt_revision_id == revision_id), "expirations": rows(InboundExpirationObservationModel, InboundExpirationObservationModel.inbound_receipt_id == receipt.id)}, "validation_results": rows(ReceivingValidationResultModel, ReceivingValidationResultModel.receipt_revision_id == revision_id), "difference_candidates": rows(ReceptionDifferenceCandidateModel, ReceptionDifferenceCandidateModel.receipt_revision_id == revision_id), "captured_at": now().isoformat()}

    def recalculate(self, receipt: InboundReceiptModel) -> InboundReceiptProgressProjectionModel:
        expected = list(self.db.scalars(select(InboundReceiptExpectedLineModel).where(InboundReceiptExpectedLineModel.receipt_revision_id == receipt.active_revision_id))) if receipt.active_revision_id else []
        received = list(self.db.scalars(select(InboundReceivedLineModel).where(InboundReceivedLineModel.receipt_revision_id == receipt.active_revision_id))) if receipt.active_revision_id else []
        ordered = sum((Decimal(x.ordered_base_quantity) for x in expected), Decimal("0")); shipped = sum((Decimal(x.shipped_base_quantity or 0) for x in expected), Decimal("0")); observed = sum((Decimal(x.received_base_quantity) for x in received), Decimal("0")); completed = sum(1 for x in received if x.comparison_status == "EXACT_EXPECTED"); percent = (Decimal(completed) * Decimal("100") / Decimal(len(expected))) if expected else Decimal("0")
        projection = self.db.get(InboundReceiptProgressProjectionModel, receipt.id) or InboundReceiptProgressProjectionModel(receipt_id=receipt.id)
        projection.expected_line_count=len(expected); projection.started_line_count=len(received); projection.completed_line_count=completed; projection.ordered_base_total=ordered; projection.shipped_base_total=shipped; projection.received_base_total=observed; projection.unresolved_scan_count=receipt.total_unresolved_scans; projection.validation_error_count=receipt.total_validation_errors; projection.warning_count=0; projection.difference_candidate_count=receipt.total_difference_candidates; projection.scan_event_count=self.db.scalar(select(func.count()).select_from(InboundScanEventModel).where(InboundScanEventModel.inbound_receipt_id == receipt.id)) or 0; projection.compensated_scan_count=self.db.scalar(select(func.count()).select_from(InboundScanCompensationEventModel).where(InboundScanCompensationEventModel.inbound_receipt_id == receipt.id)) or 0; projection.progress_percentage=percent if not receipt.total_validation_errors else min(percent, Decimal("99.99")); projection.data_quality_status="COMPLETE" if completed == len(expected) and not receipt.total_validation_errors else "PARTIAL"; projection.calculated_at=now(); projection.projection_version=(projection.projection_version or 0)+1
        self.db.add(projection); receipt.total_received_lines=len(received); return projection


# Explicit application-service names form the public architecture.  They share
# the same transactional core so validation and locking rules cannot diverge.
class _ReceivingFacade:
    def __init__(self, db: Session):
        self.db = db
        self.core = InboundReceivingService(db)


class InboundReceiptService(InboundReceivingService): pass
class InboundReceiptSourceService(_ReceivingFacade): pass
class InboundReceiptExpectedLineService(_ReceivingFacade): pass
class InboundScanSessionService(_ReceivingFacade): pass
class ReceivingScanService(_ReceivingFacade): pass
class ReceivingBatchScanService(_ReceivingFacade): pass
class ReceivingManualEntryService(_ReceivingFacade): pass
class ReceivingQuantityService(_ReceivingFacade): pass
class ReceivingLotCaptureService(_ReceivingFacade): pass
class ReceivingSerialCaptureService(_ReceivingFacade): pass
class ReceivingExpirationService(_ReceivingFacade): pass
class ReceivingLineMatchService(_ReceivingFacade): pass
class ReceivingDuplicateDetectionService(_ReceivingFacade): pass


class BarcodeNormalizationService:
    @staticmethod
    def normalize(raw_code: str, symbology: str | None = None) -> str:
        return BarcodeParserRegistry.parse(raw_code, symbology).normalized_code


class BarcodeResolutionService(_ReceivingFacade):
    def resolve(self, receipt: InboundReceiptModel, raw_code: str, symbology: str | None = None) -> dict:
        return self.core.resolve_code(receipt, raw_code, symbology)


class ReceivingUnitConversionService(_ReceivingFacade):
    def convert(self, product_id: UUID, quantity: Decimal, source_unit_id: UUID, target_unit_id: UUID, fallback_factor: Decimal) -> Decimal:
        return self.core._base_quantity(product_id, quantity, source_unit_id, target_unit_id, fallback_factor)


class InboundReceiptValidator(_ReceivingFacade):
    def validate(self, receipt_id: UUID, principal: LogisticsPrincipal) -> dict:
        return self.core.validate(receipt_id, principal)


class ReceivingValidationService(InboundReceiptValidator): pass


class ReceivingCompletionService(_ReceivingFacade):
    def complete(self, receipt_id: UUID, principal: LogisticsPrincipal, row_version: int) -> dict:
        return self.core.complete(receipt_id, principal, row_version)


class ReceivingProgressProjectionService(_ReceivingFacade):
    def calculate(self, receipt: InboundReceiptModel) -> InboundReceiptProgressProjectionModel:
        return self.core.recalculate(receipt)


class ReceivingSnapshotProvider(_ReceivingFacade):
    def capture(self, receipt: InboundReceiptModel) -> dict:
        return self.core.snapshot(receipt)


class ReceivingIntegrityService(_ReceivingFacade):
    def verify(self, receipt: InboundReceiptModel) -> dict:
        revision = self.db.get(InboundReceiptRevisionModel, receipt.active_revision_id)
        snapshot = revision.completion_snapshot if revision and revision.completion_snapshot else self.core.snapshot(receipt)
        calculated = canonical_hash(snapshot)
        return {"status": "VALID" if not receipt.content_hash or receipt.content_hash == calculated else "MISMATCH", "calculated_content_hash": calculated, "stored_content_hash": receipt.content_hash}


class ReceivingComparisonService(_ReceivingFacade): pass
class ReceivingDifferenceCandidateService(_ReceivingFacade): pass


class ReceptionDifferencePreparationService(_ReceivingFacade):
    """Read-only handoff; formalization belongs exclusively to Phase 040."""

    def get(self, receipt: InboundReceiptModel) -> dict:
        snapshot = self.core.snapshot(receipt)
        return {"inbound_receipt_id": receipt.id, "receipt_code": receipt.receipt_code, "receipt_revision_id": receipt.active_revision_id, "warehouse_id": receipt.warehouse_id, "supplier_summary": receipt.supplier_snapshot, "carrier_summary": receipt.carrier_snapshot, "unloading_operation_id": receipt.unloading_operation_id, "expected_lines": snapshot["expected_lines"], "received_lines": snapshot["received_lines"], "candidates": snapshot["difference_candidates"], "completion_snapshot_hash": receipt.content_hash, "future_capabilities": ["PHASE_040_FORMALIZE_DIFFERENCES"]}
