"""Retry-safe maintenance jobs for Phase 036."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import date, datetime, timedelta
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.logistics.documents.application.lifecycle_service import (
    DocumentLifecycleService,
)
from app.modules.logistics.documents.models import (
    DocumentArtifactModel,
    DocumentInstanceModel,
)
from app.modules.logistics.inbound.arrival_notices.application.services.common import (
    json_safe,
    utc_now,
)
from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
    ArrivalNoticeExpectedLineModel,
    ArrivalNoticeModel,
    ArrivalNoticeOutboxEventModel,
    ArrivalNoticeTransportDocumentModel,
    InboundExpectedQuantityAllocationModel,
)
from app.modules.logistics.inbound.reception_calendar.infrastructure.persistence.models import (
    ReceptionAppointmentHoldModel,
    ReceptionAppointmentModel,
    ReceptionAppointmentPackageJobModel,
    WarehouseReceptionBlackoutModel,
)


def _enqueue_once(
    db: Session,
    *,
    organization_id,
    aggregate_type: str,
    aggregate_id,
    event_type: str,
    payload: dict,
    deduplication_key: str,
) -> bool:
    existing = db.scalar(
        select(ArrivalNoticeOutboxEventModel.id).where(
            ArrivalNoticeOutboxEventModel.organization_id == organization_id,
            ArrivalNoticeOutboxEventModel.deduplication_key == deduplication_key,
        )
    )
    if existing:
        return False
    db.add(
        ArrivalNoticeOutboxEventModel(
            organization_id=organization_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=json_safe(payload),
            deduplication_key=deduplication_key,
        )
    )
    return True


def expire_reception_holds(db: Session, *, batch_size: int = 500) -> int:
    now = utc_now()
    holds = list(
        db.scalars(
            select(ReceptionAppointmentHoldModel)
            .where(
                ReceptionAppointmentHoldModel.status == "ACTIVE",
                ReceptionAppointmentHoldModel.expires_at <= now,
            )
            .order_by(ReceptionAppointmentHoldModel.expires_at)
            .with_for_update(skip_locked=True)
            .limit(batch_size)
        )
    )
    for hold in holds:
        hold.status = "EXPIRED"
        _enqueue_once(
            db,
            organization_id=hold.organization_id,
            aggregate_type="RECEPTION_APPOINTMENT_HOLD",
            aggregate_id=hold.id,
            event_type="ReceptionAppointmentHoldExpired",
            payload={
                "hold_id": hold.id,
                "arrival_notice_id": hold.arrival_notice_id,
                "expired_at": now,
            },
            deduplication_key=f"reception-hold:{hold.id}:expired",
        )
    db.flush()
    return len(holds)


def mark_elapsed_appointment_windows(db: Session, *, batch_size: int = 500) -> int:
    now = utc_now()
    appointments = list(
        db.scalars(
            select(ReceptionAppointmentModel)
            .where(
                ReceptionAppointmentModel.status == "CONFIRMED",
                ReceptionAppointmentModel.slot_end < now,
                ReceptionAppointmentModel.window_elapsed_at.is_(None),
            )
            .order_by(ReceptionAppointmentModel.slot_end)
            .with_for_update(skip_locked=True)
            .limit(batch_size)
        )
    )
    for appointment in appointments:
        appointment.window_elapsed_at = now
        appointment.row_version += 1
        _enqueue_once(
            db,
            organization_id=appointment.organization_id,
            aggregate_type="RECEPTION_APPOINTMENT",
            aggregate_id=appointment.id,
            event_type="ReceptionAppointmentWindowElapsed",
            payload={
                "appointment_id": appointment.id,
                "slot_end": appointment.slot_end,
                "window_elapsed_at": now,
                "status_unchanged": appointment.status,
            },
            deduplication_key=f"appointment:{appointment.id}:window-elapsed",
        )
    db.flush()
    return len(appointments)


def publish_arrival_notice_outbox(
    db: Session,
    *,
    batch_size: int = 200,
    publisher: Callable[[ArrivalNoticeOutboxEventModel], None] | None = None,
) -> int:
    """Publish through the local boundary; external brokers can replace it."""

    now = utc_now()
    events = list(
        db.scalars(
            select(ArrivalNoticeOutboxEventModel)
            .where(
                ArrivalNoticeOutboxEventModel.status.in_(["PENDING", "FAILED"]),
                ArrivalNoticeOutboxEventModel.available_at <= now,
            )
            .order_by(ArrivalNoticeOutboxEventModel.created_at)
            .with_for_update(skip_locked=True)
            .limit(batch_size)
        )
    )
    for event in events:
        try:
            if publisher is not None:
                publisher(event)
            event.attempt_count += 1
            event.status = "PUBLISHED"
            event.processed_at = now
            event.last_error = None
        except Exception as exc:  # pragma: no cover - adapter boundary
            event.status = "FAILED"
            event.last_error = str(exc)[:2000]
            event.available_at = now + timedelta(
                minutes=min(60, 2 ** min(event.attempt_count, 6))
            )
    db.flush()
    return len(events)


def enqueue_reception_appointment_reminders(
    db: Session,
    *,
    horizon_minutes: int = 1440,
    batch_size: int = 500,
) -> int:
    """Persist reminder intents; delivery remains behind the outbox adapter."""

    now = utc_now()
    cutoff = now + timedelta(minutes=horizon_minutes)
    appointments = list(
        db.scalars(
            select(ReceptionAppointmentModel)
            .where(
                ReceptionAppointmentModel.status == "CONFIRMED",
                ReceptionAppointmentModel.slot_start > now,
                ReceptionAppointmentModel.slot_start <= cutoff,
            )
            .order_by(ReceptionAppointmentModel.slot_start)
            .limit(batch_size)
        )
    )
    created = 0
    for appointment in appointments:
        created += int(
            _enqueue_once(
                db,
                organization_id=appointment.organization_id,
                aggregate_type="RECEPTION_APPOINTMENT",
                aggregate_id=appointment.id,
                event_type="ReceptionAppointmentReminderRequested",
                payload={
                    "appointment_id": appointment.id,
                    "slot_start": appointment.slot_start,
                    "horizon_minutes": horizon_minutes,
                },
                deduplication_key=(
                    f"appointment:{appointment.id}:reminder:{horizon_minutes}"
                ),
            )
        )
    db.flush()
    return created


def detect_pending_appointment_documents(
    db: Session, *, batch_size: int = 500
) -> int:
    appointments = list(
        db.scalars(
            select(ReceptionAppointmentModel)
            .where(
                ReceptionAppointmentModel.status == "CONFIRMED",
                ReceptionAppointmentModel.document_instance_id.is_(None),
            )
            .order_by(ReceptionAppointmentModel.slot_start)
            .limit(batch_size)
        )
    )
    created = 0
    for appointment in appointments:
        created += int(
            _enqueue_once(
                db,
                organization_id=appointment.organization_id,
                aggregate_type="RECEPTION_APPOINTMENT",
                aggregate_id=appointment.id,
                event_type="ReceptionAppointmentDocumentPending",
                payload={
                    "appointment_id": appointment.id,
                    "arrival_notice_id": appointment.arrival_notice_id,
                },
                deduplication_key=f"appointment:{appointment.id}:document-pending",
            )
        )
    db.flush()
    return created


def detect_driver_license_expirations(
    db: Session,
    *,
    days_ahead: int = 30,
    batch_size: int = 500,
) -> int:
    """Use only the declared snapshot; this is not an external verification."""

    today = utc_now().date()
    cutoff = today + timedelta(days=days_ahead)
    appointments = list(
        db.scalars(
            select(ReceptionAppointmentModel)
            .where(
                ReceptionAppointmentModel.status.in_(
                    {"PROPOSED", "PENDING_CONFIRMATION", "CONFIRMED"}
                ),
                ReceptionAppointmentModel.slot_end >= utc_now(),
                ReceptionAppointmentModel.driver_reference_snapshot.is_not(None),
            )
            .order_by(ReceptionAppointmentModel.slot_start)
            .limit(batch_size)
        )
    )
    created = 0
    for appointment in appointments:
        snapshot = appointment.driver_reference_snapshot or {}
        raw_expiration = snapshot.get("license_expiration")
        try:
            expiration = date.fromisoformat(raw_expiration) if raw_expiration else None
        except (TypeError, ValueError):
            expiration = None
        if expiration is None or expiration > cutoff:
            continue
        created += int(
            _enqueue_once(
                db,
                organization_id=appointment.organization_id,
                aggregate_type="RECEPTION_APPOINTMENT",
                aggregate_id=appointment.id,
                event_type="ReceptionDriverLicenseExpiring",
                payload={
                    "appointment_id": appointment.id,
                    "driver_id": snapshot.get("driver_id"),
                    "declared_expiration": expiration,
                    "already_expired": expiration < today,
                    "source": "ARRIVAL_NOTICE_SNAPSHOT",
                },
                deduplication_key=(
                    f"appointment:{appointment.id}:driver-license:{expiration.isoformat()}"
                ),
            )
        )
    db.flush()
    return created


def detect_vehicle_verification_expirations(
    db: Session, *, batch_size: int = 500
) -> int:
    """Detect expiration from the captured vehicle snapshot without claiming validation."""

    now = utc_now()
    appointments = list(
        db.scalars(
            select(ReceptionAppointmentModel)
            .where(
                ReceptionAppointmentModel.status.in_(
                    {"PROPOSED", "PENDING_CONFIRMATION", "CONFIRMED"}
                ),
                ReceptionAppointmentModel.slot_end >= now,
                ReceptionAppointmentModel.vehicle_reference_snapshot.is_not(None),
            )
            .order_by(ReceptionAppointmentModel.slot_start)
            .limit(batch_size)
        )
    )
    created = 0
    for appointment in appointments:
        snapshot = appointment.vehicle_reference_snapshot or {}
        raw_expiration = snapshot.get("verification_expiration")
        try:
            expiration = (
                datetime.fromisoformat(raw_expiration) if raw_expiration else None
            )
        except (TypeError, ValueError):
            expiration = None
        if expiration is None:
            continue
        if expiration.tzinfo is None:
            expiration = expiration.replace(tzinfo=now.tzinfo)
        if expiration > appointment.slot_start:
            continue
        created += int(
            _enqueue_once(
                db,
                organization_id=appointment.organization_id,
                aggregate_type="RECEPTION_APPOINTMENT",
                aggregate_id=appointment.id,
                event_type="ReceptionVehicleVerificationExpired",
                payload={
                    "appointment_id": appointment.id,
                    "vehicle_id": snapshot.get("vehicle_id"),
                    "plate": snapshot.get("plate"),
                    "declared_expiration": expiration,
                    "source": "ARRIVAL_NOTICE_SNAPSHOT",
                },
                deduplication_key=(
                    f"appointment:{appointment.id}:vehicle-verification:"
                    f"{expiration.isoformat()}"
                ),
            )
        )
    db.flush()
    return created


def detect_blackout_affected_appointments(
    db: Session, *, batch_size: int = 500
) -> int:
    now = utc_now()
    appointments = list(
        db.scalars(
            select(ReceptionAppointmentModel)
            .where(
                ReceptionAppointmentModel.status.in_(
                    {"PROPOSED", "PENDING_CONFIRMATION", "CONFIRMED"}
                ),
                ReceptionAppointmentModel.slot_end >= now,
            )
            .order_by(ReceptionAppointmentModel.slot_start)
            .limit(batch_size)
        )
    )
    created = 0
    for appointment in appointments:
        blackout = db.scalar(
            select(WarehouseReceptionBlackoutModel).where(
                WarehouseReceptionBlackoutModel.calendar_id
                == appointment.calendar_id,
                WarehouseReceptionBlackoutModel.status == "ACTIVE",
                WarehouseReceptionBlackoutModel.starts_at < appointment.slot_end,
                WarehouseReceptionBlackoutModel.ends_at > appointment.slot_start,
            )
        )
        if blackout is None:
            continue
        created += int(
            _enqueue_once(
                db,
                organization_id=appointment.organization_id,
                aggregate_type="RECEPTION_APPOINTMENT",
                aggregate_id=appointment.id,
                event_type="ReceptionAppointmentAffectedByBlackout",
                payload={
                    "appointment_id": appointment.id,
                    "blackout_id": blackout.id,
                    "slot_start": appointment.slot_start,
                    "slot_end": appointment.slot_end,
                },
                deduplication_key=(
                    f"appointment:{appointment.id}:blackout:{blackout.id}"
                ),
            )
        )
    db.flush()
    return created


def retry_failed_outbox_events(db: Session, *, batch_size: int = 200) -> int:
    now = utc_now()
    events = list(
        db.scalars(
            select(ArrivalNoticeOutboxEventModel)
            .where(
                ArrivalNoticeOutboxEventModel.status == "FAILED",
                ArrivalNoticeOutboxEventModel.available_at <= now,
            )
            .order_by(ArrivalNoticeOutboxEventModel.available_at)
            .with_for_update(skip_locked=True)
            .limit(batch_size)
        )
    )
    for event in events:
        event.status = "PENDING"
    db.flush()
    return len(events)


def cleanup_external_portal_sessions(db: Session, *, batch_size: int = 500) -> int:
    """Stable scheduler hook while the optional external portal remains disabled."""

    del db, batch_size
    return 0


def reconcile_expected_quantity_allocations(
    db: Session, *, batch_size: int = 500
) -> int:
    allocations = list(
        db.scalars(
            select(InboundExpectedQuantityAllocationModel)
            .where(
                InboundExpectedQuantityAllocationModel.status.in_({"HELD", "ACTIVE"})
            )
            .order_by(InboundExpectedQuantityAllocationModel.created_at)
            .with_for_update(skip_locked=True)
            .limit(batch_size)
        )
    )
    changed = 0
    active_notice_statuses = {
        "SUBMITTED",
        "UNDER_REVIEW",
        "REQUIRES_CHANGES",
        "APPROVED",
        "READY_FOR_SCHEDULING",
        "SCHEDULED",
        "CONFIRMED",
    }
    for allocation in allocations:
        notice = db.get(ArrivalNoticeModel, allocation.arrival_notice_id)
        line = db.get(ArrivalNoticeExpectedLineModel, allocation.expected_line_id)
        if notice is None or line is None:
            continue
        target_status = allocation.status
        if notice.status == "CANCELLED" or line.status == "CANCELLED":
            target_status = "RELEASED"
        elif allocation.status == "HELD" and notice.status in active_notice_statuses:
            target_status = "ACTIVE"
        if target_status != allocation.status:
            allocation.status = target_status
            changed += 1
    db.flush()
    return changed


def process_appointment_package_jobs(db: Session, *, batch_size: int = 20) -> int:
    jobs = list(
        db.scalars(
            select(ReceptionAppointmentPackageJobModel)
            .where(
                ReceptionAppointmentPackageJobModel.status.in_(["PENDING", "FAILED"]),
                ReceptionAppointmentPackageJobModel.available_at <= utc_now(),
            )
            .order_by(ReceptionAppointmentPackageJobModel.created_at)
            .with_for_update(skip_locked=True)
            .limit(batch_size)
        )
    )
    lifecycle = DocumentLifecycleService(db)
    completed = 0
    for job in jobs:
        job.status = "PROCESSING"
        job.attempt_count += 1
        db.flush()
        try:
            appointment = db.get(ReceptionAppointmentModel, job.appointment_id)
            if appointment is None or not appointment.document_instance_id:
                raise ValueError("La cita no tiene CIT emitida.")
            document = db.get(
                DocumentInstanceModel, appointment.document_instance_id
            )
            if (
                document is None
                or document.status != "ISSUED"
                or not document.authoritative_artifact_id
            ):
                raise ValueError("La CIT todavía no está emitida.")
            cit_artifact = db.get(
                DocumentArtifactModel, document.authoritative_artifact_id
            )
            if cit_artifact is None:
                raise ValueError("No existe el artefacto autoritativo de la CIT.")
            cit_bytes = lifecycle.storage.get(cit_artifact.storage_key)
            transport_documents = list(
                db.scalars(
                    select(ArrivalNoticeTransportDocumentModel).where(
                        ArrivalNoticeTransportDocumentModel.revision_id
                        == appointment.arrival_notice_revision_id,
                        ArrivalNoticeTransportDocumentModel.status == "ACTIVE",
                    )
                )
            )
            manifest = {
                "schema_version": "phase-036.1",
                "appointment_id": str(appointment.id),
                "appointment_code": appointment.appointment_code,
                "cit": {
                    "document_id": str(document.id),
                    "artifact_id": str(cit_artifact.id),
                    "filename": cit_artifact.filename,
                    "sha256": cit_artifact.file_hash,
                },
                "transport_documents": [
                    {
                        "id": str(item.id),
                        "kind": item.document_kind,
                        "reference": item.normalized_reference,
                        "verification_status": item.verification_status,
                        "file_asset_id": (
                            str(item.file_asset_id) if item.file_asset_id else None
                        ),
                    }
                    for item in transport_documents
                ],
            }
            buffer = io.BytesIO()
            with zipfile.ZipFile(
                buffer, mode="w", compression=zipfile.ZIP_DEFLATED
            ) as archive:
                archive.writestr(cit_artifact.filename, cit_bytes)
                archive.writestr(
                    "manifest.json",
                    json.dumps(manifest, ensure_ascii=False, indent=2).encode(),
                )
            package_bytes = buffer.getvalue()
            file_hash = hashlib.sha256(package_bytes).hexdigest()
            filename = (
                f"PAQUETE_{appointment.appointment_code or appointment.id}.zip"
            )
            storage_key = (
                f"documents/{appointment.organization_id}/appointment-packages/"
                f"{job.id}/{filename}"
            )
            lifecycle.storage.put(storage_key, package_bytes)
            artifact = DocumentArtifactModel(
                document_id=document.id,
                snapshot_id=document.current_snapshot_id,
                artifact_type="PACKAGE_ZIP",
                representation_status="ACTIVE",
                mime_type="application/zip",
                filename=filename,
                storage_provider=settings.STORAGE_PROVIDER,
                storage_key=storage_key,
                size_bytes=len(package_bytes),
                file_hash=file_hash,
                content_hash=file_hash,
                template_version="phase-036.1",
                renderer_version="zipfile",
                generated_by=job.created_by,
                is_authoritative=False,
                is_sensitive=True,
                metadata_data={"package_job_id": str(job.id)},
            )
            db.add(artifact)
            db.flush()
            job.artifact_id = artifact.id
            job.manifest = manifest
            job.status = "COMPLETED"
            job.completed_at = utc_now()
            job.last_error = None
            completed += 1
        except Exception as exc:  # pragma: no cover - storage/runtime boundary
            job.status = "FAILED"
            job.last_error = str(exc)[:2000]
            job.available_at = utc_now() + timedelta(
                minutes=min(60, 2 ** min(job.attempt_count, 6))
            )
    db.flush()
    return completed


__all__ = [
    "cleanup_external_portal_sessions",
    "detect_blackout_affected_appointments",
    "detect_driver_license_expirations",
    "detect_pending_appointment_documents",
    "detect_vehicle_verification_expirations",
    "enqueue_reception_appointment_reminders",
    "expire_reception_holds",
    "mark_elapsed_appointment_windows",
    "process_appointment_package_jobs",
    "publish_arrival_notice_outbox",
    "reconcile_expected_quantity_allocations",
    "retry_failed_outbox_events",
]
