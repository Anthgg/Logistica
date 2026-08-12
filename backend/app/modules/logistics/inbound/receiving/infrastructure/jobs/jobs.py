"""Externally scheduled Phase 039 jobs; no in-process timers."""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.arrival_notices.infrastructure.jobs.jobs import (
    publish_arrival_notice_outbox,
)

from ...application.services import InboundReceivingService, now
from ..persistence.models import (
    InboundExpirationObservationModel,
    InboundReceiptExportJobModel,
    InboundReceiptModel,
    InboundScanEventModel,
    InboundScanSessionModel,
    InboundSerialObservationModel,
    PurchaseOrderReceiptProgressModel,
    UnresolvedInboundScanModel,
)


def expire_abandoned_sessions(db: Session, inactivity_minutes: int = 30) -> int:
    rows = list(db.scalars(select(InboundScanSessionModel).where(InboundScanSessionModel.status.in_(("ACTIVE", "PAUSED")), InboundScanSessionModel.last_activity_at < now() - timedelta(minutes=inactivity_minutes)).with_for_update(skip_locked=True)))
    for row in rows: row.status = "EXPIRED"
    db.commit(); return len(rows)


def recalculate_progress(db: Session, limit: int = 500) -> int:
    rows = list(db.scalars(select(InboundReceiptModel).where(~InboundReceiptModel.status.in_(("CANCELLED", "SUPERSEDED", "FAILED"))).limit(limit).with_for_update(skip_locked=True)))
    for row in rows: InboundReceivingService(db).recalculate(row)
    db.commit(); return len(rows)


def detect_unresolved_scans(db: Session, limit: int = 500) -> int:
    events = list(db.scalars(select(InboundScanEventModel).where(InboundScanEventModel.resolution_status.in_(("UNKNOWN_CODE", "AMBIGUOUS")), ~select(UnresolvedInboundScanModel.id).where(UnresolvedInboundScanModel.scan_event_id == InboundScanEventModel.id).exists()).limit(limit).with_for_update(skip_locked=True)))
    for event in events:
        db.add(UnresolvedInboundScanModel(inbound_receipt_id=event.inbound_receipt_id, scan_event_id=event.id, code_hash=event.code_hash, candidate_product_ids=[], status="OPEN"))
    db.commit(); return len(events)


def verify_integrity(db: Session, limit: int = 500) -> int:
    rows = list(db.scalars(select(InboundReceiptModel).where(InboundReceiptModel.status == "COMPLETED", InboundReceiptModel.content_hash.is_not(None)).limit(limit)))
    return sum(1 for row in rows if InboundReceivingService(db).snapshot(row))


def detect_duplicate_serials(db: Session, limit: int = 500) -> int:
    """Mark duplicate product/serial pairs across receipts; the DB index covers a receipt."""
    duplicate_keys = list(
        db.execute(
            select(
                InboundSerialObservationModel.product_id,
                InboundSerialObservationModel.serial_hash,
            )
            .where(InboundSerialObservationModel.validation_status != "INVALIDATED")
            .group_by(
                InboundSerialObservationModel.product_id,
                InboundSerialObservationModel.serial_hash,
            )
            .having(func.count(InboundSerialObservationModel.id) > 1)
            .limit(limit)
        )
    )
    changed = 0
    for product_id, serial_hash in duplicate_keys:
        rows = list(
            db.scalars(
                select(InboundSerialObservationModel)
                .where(
                    InboundSerialObservationModel.product_id == product_id,
                    InboundSerialObservationModel.serial_hash == serial_hash,
                    InboundSerialObservationModel.validation_status != "INVALIDATED",
                )
                .with_for_update(skip_locked=True)
            )
        )
        for row in rows:
            if row.duplicate_status != "DUPLICATE_DETECTED":
                row.duplicate_status = "DUPLICATE_DETECTED"
                changed += 1
    db.commit()
    return changed


def revalidate_expirations(db: Session, limit: int = 500) -> int:
    observations = list(
        db.scalars(
            select(InboundExpirationObservationModel)
            .order_by(InboundExpirationObservationModel.captured_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
    )
    changed = 0
    today = date.today()
    for observation in observations:
        status = "VALID"
        if observation.manufacturing_date and observation.manufacturing_date > observation.expiration_date:
            status = "DATE_ORDER_INVALID"
        elif observation.expiration_date < today:
            status = "EXPIRED"
        if observation.validation_status != status:
            observation.validation_status = status
            changed += 1
    db.commit()
    return changed


def reconcile_lines(db: Session) -> int: return recalculate_progress(db)


def recalculate_purchase_order_fulfillment(db: Session, limit: int = 500) -> int:
    rows = list(
        db.scalars(
            select(PurchaseOrderReceiptProgressModel)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
    )
    changed = 0
    for row in rows:
        ordered = Decimal(row.ordered_quantity)
        received = Decimal(row.cumulative_received_quantity)
        remaining = max(ordered - received, Decimal("0"))
        status = "NOT_RECEIVED" if received == 0 else (
            "FULLY_RECEIVED" if received >= ordered else "PARTIALLY_RECEIVED"
        )
        if Decimal(row.remaining_quantity) != remaining or row.fulfillment_status != status:
            row.remaining_quantity = remaining
            row.fulfillment_status = status
            changed += 1
    db.commit()
    return changed


def process_outbox(db: Session, batch_size: int = 200) -> int:
    processed = publish_arrival_notice_outbox(db, batch_size=batch_size)
    db.commit()
    return processed


def generate_exports(db: Session, limit: int = 100) -> int:
    """Fail pending jobs explicitly until an external file-asset adapter is configured."""
    rows = list(
        db.scalars(
            select(InboundReceiptExportJobModel)
            .where(InboundReceiptExportJobModel.status == "PENDING")
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
    )
    for row in rows:
        row.status = "FAILED"
        row.error_code = "EXPORT_ADAPTER_NOT_CONFIGURED"
        row.completed_at = now()
    db.commit()
    return len(rows)


def detect_long_open_receipts(db: Session) -> int: return db.scalar(select(func.count()).select_from(InboundReceiptModel).where(InboundReceiptModel.status.in_(("IN_PROGRESS", "PAUSED")), InboundReceiptModel.started_at < now() - timedelta(hours=12))) or 0


def detect_out_of_order_events(db: Session, limit: int = 500) -> int:
    """Count client sequence regressions; server ordering remains authoritative."""
    rows = list(
        db.execute(
            select(
                InboundScanEventModel.scan_session_id,
                InboundScanEventModel.client_sequence,
                InboundScanEventModel.server_sequence,
            )
            .where(InboundScanEventModel.client_sequence.is_not(None))
            .order_by(
                InboundScanEventModel.scan_session_id,
                InboundScanEventModel.server_sequence,
            )
            .limit(limit)
        )
    )
    last_by_session: dict[object, int] = {}
    regressions = 0
    for session_id, client_sequence, _ in rows:
        previous = last_by_session.get(session_id)
        if previous is not None and client_sequence <= previous:
            regressions += 1
        last_by_session[session_id] = client_sequence
    return regressions


PHASE_039_JOBS = {
    "expire_abandoned_sessions": expire_abandoned_sessions,
    "recalculate_progress": recalculate_progress,
    "detect_unresolved_scans": detect_unresolved_scans,
    "detect_duplicate_serials": detect_duplicate_serials,
    "revalidate_expirations": revalidate_expirations,
    "reconcile_lines": reconcile_lines,
    "recalculate_purchase_order_fulfillment": recalculate_purchase_order_fulfillment,
    "verify_integrity": verify_integrity,
    "process_outbox": process_outbox,
    "generate_exports": generate_exports,
    "detect_long_open_receipts": detect_long_open_receipts,
    "detect_out_of_order_events": detect_out_of_order_events,
}
