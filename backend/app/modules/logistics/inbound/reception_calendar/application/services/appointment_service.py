"""Concurrency-safe holds and reception-appointment lifecycle."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.arrival_notices.application.services.arrival_notice_service import (
    ArrivalNoticeService,
)
from app.modules.logistics.inbound.arrival_notices.application.services.common import (
    content_hash,
    enqueue_event,
    get_notice_for_org,
    json_safe,
    utc_now,
    write_audit,
)
from app.modules.logistics.inbound.arrival_notices.application.services.idempotency import (
    get_idempotent_response,
    save_idempotent_response,
)
from app.modules.logistics.inbound.arrival_notices.domain.errors.exceptions import (
    ArrivalNoticeStatusInvalid,
    ArrivalNoticeTransportIncomplete,
    IdempotencyConflict,
    ReceptionAppointmentAlreadyConfirmed,
    ReceptionAppointmentCancellationBlocked,
    ReceptionAppointmentConflict,
    ReceptionAppointmentHoldExpired,
    ReceptionAppointmentRescheduleNotAllowed,
    ReceptionCalendarInactive,
    ReceptionCalendarNotFound,
    ReceptionSlotCapacityExceeded,
    ReceptionSlotUnavailable,
)
from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
    ArrivalNoticeDriverReferenceModel,
    ArrivalNoticeExpectedLineModel,
    ArrivalNoticeModel,
    ArrivalNoticeRevisionModel,
    ArrivalNoticeTransportDocumentModel,
    ArrivalNoticeVehicleReferenceModel,
)
from app.modules.logistics.inbound.reception_calendar.application.services.calendar_service import (
    ReceptionCalendarService,
)
from app.modules.logistics.inbound.reception_calendar.infrastructure.persistence.models import (
    ReceptionAppointmentHistoryModel,
    ReceptionAppointmentHoldModel,
    ReceptionAppointmentModel,
    ReceptionAppointmentPackageJobModel,
    WarehouseReceptionBlackoutModel,
    WarehouseReceptionCalendarModel,
    WarehouseReceptionOperatingWindowModel,
)


_CAPACITY_STATUSES = {
    "PROPOSED",
    "PENDING_CONFIRMATION",
    "CONFIRMED",
    "RESCHEDULE_REQUESTED",
}


class ReceptionAppointmentService:
    def __init__(self, db: Session):
        self.db = db
        self.calendar_service = ReceptionCalendarService(db)
        self.notice_service = ArrivalNoticeService(db)

    def get_hold(
        self,
        hold_id: UUID,
        organization_id: UUID,
        *,
        lock: bool = False,
    ) -> ReceptionAppointmentHoldModel:
        stmt = select(ReceptionAppointmentHoldModel).where(
            ReceptionAppointmentHoldModel.id == hold_id,
            ReceptionAppointmentHoldModel.organization_id == organization_id,
        )
        if lock:
            stmt = stmt.with_for_update()
        hold = self.db.scalar(stmt)
        if hold is None:
            raise ReceptionAppointmentHoldExpired("El hold no existe o ya no es accesible.")
        self._expire_hold_if_needed(hold)
        return hold

    def _expire_hold_if_needed(self, hold: ReceptionAppointmentHoldModel) -> None:
        if hold.status == "ACTIVE" and hold.expires_at <= utc_now():
            hold.status = "EXPIRED"
            self.db.flush()

    def get(
        self,
        appointment_id: UUID,
        organization_id: UUID,
        *,
        lock: bool = False,
    ) -> ReceptionAppointmentModel:
        stmt = select(ReceptionAppointmentModel).where(
            ReceptionAppointmentModel.id == appointment_id,
            ReceptionAppointmentModel.organization_id == organization_id,
        )
        if lock:
            stmt = stmt.with_for_update()
        appointment = self.db.scalar(stmt)
        if appointment is None:
            raise ReceptionCalendarNotFound("La cita de recepción no existe.")
        return appointment

    def list(
        self,
        organization_id: UUID,
        *,
        warehouse_id: UUID | None = None,
        status: str | None = None,
        arrival_notice_id: UUID | None = None,
    ) -> list[ReceptionAppointmentModel]:
        stmt = select(ReceptionAppointmentModel).where(
            ReceptionAppointmentModel.organization_id == organization_id
        )
        if warehouse_id:
            stmt = stmt.where(ReceptionAppointmentModel.warehouse_id == warehouse_id)
        if status:
            stmt = stmt.where(ReceptionAppointmentModel.status == status.upper())
        if arrival_notice_id:
            stmt = stmt.where(
                ReceptionAppointmentModel.arrival_notice_id == arrival_notice_id
            )
        return list(
            self.db.scalars(
                stmt.order_by(
                    ReceptionAppointmentModel.slot_start,
                    ReceptionAppointmentModel.created_at,
                )
            )
        )

    def create_hold(
        self,
        organization_id: UUID,
        actor_user_id: UUID,
        payload,
    ) -> ReceptionAppointmentHoldModel:
        request_payload = payload.model_dump()
        cached = get_idempotent_response(
            self.db,
            organization_id,
            "phase036.reception_hold.create",
            payload.idempotency_key,
            request_payload,
        )
        if cached:
            return self.get_hold(UUID(cached["hold_id"]), organization_id)
        calendar = self.calendar_service.get(
            payload.calendar_id, organization_id, lock=True
        )
        notice = get_notice_for_org(
            self.db, payload.arrival_notice_id, organization_id, lock=True
        )
        if calendar.status != "ACTIVE":
            raise ReceptionCalendarInactive("El calendario no está activo.")
        if calendar.warehouse_id != notice.warehouse_id:
            raise ReceptionAppointmentConflict(
                "El calendario y el aviso pertenecen a almacenes distintos."
            )
        if notice.status != "READY_FOR_SCHEDULING":
            raise ArrivalNoticeStatusInvalid(
                "El aviso debe estar READY_FOR_SCHEDULING para reservar una franja."
            )
        active_hold = self.db.scalar(
            select(ReceptionAppointmentHoldModel)
            .where(
                ReceptionAppointmentHoldModel.arrival_notice_id == notice.id,
                ReceptionAppointmentHoldModel.status == "ACTIVE",
            )
            .with_for_update()
        )
        if active_hold:
            self._expire_hold_if_needed(active_hold)
            if active_hold.status == "ACTIVE":
                raise ReceptionAppointmentConflict(
                    "El aviso ya tiene un hold activo."
                )
        self._assert_slot_available(
            calendar,
            payload.slot_start,
            payload.slot_end,
            notice.expected_pallet_count,
            notice.expected_package_count,
            Decimal(notice.expected_gross_weight),
            notice.weight_unit_id,
        )
        hold = ReceptionAppointmentHoldModel(
            organization_id=organization_id,
            warehouse_id=notice.warehouse_id,
            calendar_id=calendar.id,
            arrival_notice_id=notice.id,
            slot_start=payload.slot_start,
            slot_end=payload.slot_end,
            expected_pallet_count=notice.expected_pallet_count,
            expected_package_count=notice.expected_package_count,
            expected_weight=notice.expected_gross_weight,
            weight_unit_id=notice.weight_unit_id,
            expires_at=utc_now() + timedelta(minutes=calendar.hold_duration_minutes),
            created_by=actor_user_id,
        )
        self.db.add(hold)
        self.db.flush()
        save_idempotent_response(
            self.db,
            organization_id,
            actor_user_id,
            "phase036.reception_hold.create",
            payload.idempotency_key,
            request_payload,
            {"hold_id": str(hold.id)},
        )
        write_audit(
            self.db,
            event_code="logistics.reception_appointment.hold_created",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            resource_type="RECEPTION_APPOINTMENT_HOLD",
            resource_id=hold.id,
            warehouse_id=hold.warehouse_id,
            new_data={
                "arrival_notice_id": hold.arrival_notice_id,
                "slot_start": hold.slot_start,
                "slot_end": hold.slot_end,
                "expires_at": hold.expires_at,
            },
        )
        return hold

    def cancel_hold(
        self,
        hold_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
    ) -> ReceptionAppointmentHoldModel:
        hold = self.get_hold(hold_id, organization_id, lock=True)
        if hold.status == "ACTIVE":
            hold.status = "CANCELLED"
            self.db.flush()
            write_audit(
                self.db,
                event_code="logistics.reception_appointment.hold_cancelled",
                actor_user_id=actor_user_id,
                organization_id=organization_id,
                resource_type="RECEPTION_APPOINTMENT_HOLD",
                resource_id=hold.id,
                warehouse_id=hold.warehouse_id,
                previous_data={"status": "ACTIVE"},
                new_data={"status": "CANCELLED"},
            )
        return hold

    def refresh_hold(
        self,
        hold_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
    ) -> ReceptionAppointmentHoldModel:
        hold = self.get_hold(hold_id, organization_id, lock=True)
        calendar = self.calendar_service.get(
            hold.calendar_id, organization_id, lock=True
        )
        if hold.status != "ACTIVE":
            raise ReceptionAppointmentHoldExpired("El hold ya no está activo.")
        if hold.refresh_count >= calendar.maximum_hold_refreshes:
            raise ReceptionAppointmentHoldExpired(
                "El hold alcanzó el máximo de renovaciones."
            )
        hold.refresh_count += 1
        hold.expires_at = utc_now() + timedelta(minutes=calendar.hold_duration_minutes)
        self.db.flush()
        write_audit(
            self.db,
            event_code="logistics.reception_appointment.hold_refreshed",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            resource_type="RECEPTION_APPOINTMENT_HOLD",
            resource_id=hold.id,
            warehouse_id=hold.warehouse_id,
            new_data={
                "expires_at": hold.expires_at,
                "refresh_count": hold.refresh_count,
            },
        )
        return hold

    def create_appointment(
        self,
        organization_id: UUID,
        actor_user_id: UUID,
        payload,
    ) -> ReceptionAppointmentModel:
        request_payload = payload.model_dump()
        cached = get_idempotent_response(
            self.db,
            organization_id,
            "phase036.reception_appointment.create",
            payload.idempotency_key,
            request_payload,
        )
        if cached:
            return self.get(UUID(cached["appointment_id"]), organization_id)
        hold = self.get_hold(payload.hold_id, organization_id, lock=True)
        notice = get_notice_for_org(
            self.db, payload.arrival_notice_id, organization_id, lock=True
        )
        if hold.status != "ACTIVE" or hold.expires_at <= utc_now():
            raise ReceptionAppointmentHoldExpired("El hold expiró.")
        if hold.arrival_notice_id != notice.id:
            raise ReceptionAppointmentConflict("El hold no corresponde al aviso.")
        if notice.appointment_id:
            existing = self.get(notice.appointment_id, organization_id)
            if existing.status not in {"CANCELLED", "RESCHEDULED"}:
                raise ReceptionAppointmentConflict("El aviso ya tiene una cita activa.")
        revision = self.notice_service.get_revision(
            notice.active_revision_id, organization_id
        )
        appointment = ReceptionAppointmentModel(
            organization_id=organization_id,
            branch_id=notice.branch_id,
            warehouse_id=notice.warehouse_id,
            calendar_id=hold.calendar_id,
            arrival_notice_id=notice.id,
            arrival_notice_revision_id=revision.id,
            status="PROPOSED",
            slot_start=hold.slot_start,
            slot_end=hold.slot_end,
            timezone=notice.expected_arrival_timezone,
            expected_pallet_count=notice.expected_pallet_count,
            expected_package_count=notice.expected_package_count,
            expected_gross_weight=notice.expected_gross_weight,
            weight_unit_id=notice.weight_unit_id,
            supplier_snapshot=revision.supplier_snapshot,
            carrier_snapshot=revision.carrier_snapshot,
            contact_snapshot=payload.contact_snapshot,
            special_requirements_snapshot=revision.special_requirements,
            confirmation_notes=payload.confirmation_notes,
        )
        self._copy_transport_snapshots(appointment, revision.id)
        self.db.add(appointment)
        self.db.flush()
        hold.status = "CONSUMED"
        notice.status = "SCHEDULED"
        notice.appointment_status = "PROPOSED"
        notice.appointment_id = appointment.id
        notice.row_version += 1
        self._history(
            appointment,
            actor_user_id,
            "APPOINTMENT_CREATED",
            None,
            appointment.status,
            new_slot=self._slot(appointment),
        )
        enqueue_event(
            self.db,
            organization_id=organization_id,
            aggregate_type="RECEPTION_APPOINTMENT",
            aggregate_id=appointment.id,
            event_type="ReceptionAppointmentProposed",
            payload={"appointment_id": appointment.id, "notice_id": notice.id},
            deduplication_key=f"appointment:{appointment.id}:proposed",
        )
        save_idempotent_response(
            self.db,
            organization_id,
            actor_user_id,
            "phase036.reception_appointment.create",
            payload.idempotency_key,
            request_payload,
            {"appointment_id": str(appointment.id)},
        )
        write_audit(
            self.db,
            event_code="logistics.reception_appointment.created",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            resource_type="RECEPTION_APPOINTMENT",
            resource_id=appointment.id,
            branch_id=appointment.branch_id,
            warehouse_id=appointment.warehouse_id,
            new_data={"status": appointment.status, **self._slot(appointment)},
        )
        return appointment

    def validate(
        self,
        appointment_id: UUID,
        organization_id: UUID,
    ) -> dict:
        appointment = self.get(appointment_id, organization_id)
        notice = get_notice_for_org(
            self.db, appointment.arrival_notice_id, organization_id
        )
        readiness = self.notice_service.transport_readiness(
            notice.id, organization_id
        )
        errors = []
        warnings = []
        if not readiness["ready"]:
            errors.extend(
                {"code": reason, "message": reason.replace("_", " ").title()}
                for reason in readiness["blocking_reasons"]
            )
        warnings.extend(
            {"code": warning, "message": warning.replace("_", " ").title()}
            for warning in readiness["warnings"]
        )
        calendar = self.calendar_service.get(
            appointment.calendar_id, organization_id
        )
        capacity_status = "AVAILABLE"
        try:
            self._assert_slot_available(
                calendar,
                appointment.slot_start,
                appointment.slot_end,
                appointment.expected_pallet_count,
                appointment.expected_package_count,
                Decimal(appointment.expected_gross_weight),
                appointment.weight_unit_id,
                exclude_appointment_id=appointment.id,
            )
        except (ReceptionSlotUnavailable, ReceptionSlotCapacityExceeded) as exc:
            capacity_status = "UNAVAILABLE"
            errors.append(exc.as_detail())
        errors.extend(self._transport_overlap_conflicts(appointment))
        return {
            "valid": not errors,
            "capacity_status": capacity_status,
            "transport_status": "READY" if readiness["ready"] else "INCOMPLETE",
            "errors": errors,
            "warnings": warnings,
        }

    def confirm(
        self,
        appointment_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        payload,
        *,
        allow_capacity_override: bool = False,
    ) -> ReceptionAppointmentModel:
        request_payload = {
            "appointment_id": appointment_id,
            **payload.model_dump(),
        }
        cached = get_idempotent_response(
            self.db,
            organization_id,
            "phase036.reception_appointment.confirm",
            payload.idempotency_key,
            request_payload,
        )
        if cached:
            return self.get(UUID(cached["appointment_id"]), organization_id)
        appointment = self.get(appointment_id, organization_id, lock=True)
        if appointment.status == "CONFIRMED":
            raise ReceptionAppointmentAlreadyConfirmed("La cita ya está confirmada.")
        if appointment.status not in {"PROPOSED", "PENDING_CONFIRMATION"}:
            raise ReceptionAppointmentConflict(
                f"No se puede confirmar una cita en estado {appointment.status}."
            )
        calendar = self.calendar_service.get(
            appointment.calendar_id, organization_id, lock=True
        )
        try:
            self._assert_slot_available(
                calendar,
                appointment.slot_start,
                appointment.slot_end,
                appointment.expected_pallet_count,
                appointment.expected_package_count,
                Decimal(appointment.expected_gross_weight),
                appointment.weight_unit_id,
                exclude_appointment_id=appointment.id,
                exclude_hold_id=payload.hold_id,
            )
        except ReceptionSlotCapacityExceeded:
            if not allow_capacity_override or not payload.capacity_override_reason:
                raise
        validation = self.validate(appointment.id, organization_id)
        if validation["transport_status"] != "READY":
            raise ArrivalNoticeTransportIncomplete(
                "La información de transporte aún no está lista.",
                details={"errors": validation["errors"]},
            )
        overlap_errors = [
            item
            for item in validation["errors"]
            if item.get("code") in {"VEHICLE_SLOT_OVERLAP", "DRIVER_SLOT_OVERLAP"}
        ]
        if overlap_errors:
            raise ReceptionAppointmentConflict(
                "El vehículo o conductor ya tiene una cita que se solapa.",
                details={"errors": overlap_errors},
            )
        previous = appointment.status
        appointment.status = "CONFIRMED"
        appointment.confirmation_notes = (
            payload.confirmation_notes or appointment.confirmation_notes
        )
        appointment.confirmed_at = utc_now()
        appointment.confirmed_by = actor_user_id
        appointment.row_version += 1
        notice = get_notice_for_org(
            self.db, appointment.arrival_notice_id, organization_id, lock=True
        )
        revision = self.notice_service.get_revision(
            appointment.arrival_notice_revision_id, organization_id, lock=True
        )
        revision.status = "CONFIRMED"
        revision.frozen_at = revision.frozen_at or utc_now()
        notice.status = "CONFIRMED"
        notice.appointment_status = "CONFIRMED"
        notice.confirmed_revision_id = revision.id
        notice.row_version += 1
        self._history(
            appointment,
            actor_user_id,
            "APPOINTMENT_CONFIRMED",
            previous,
            appointment.status,
            reason=payload.capacity_override_reason,
            metadata={"capacity_override": bool(payload.capacity_override_reason)},
        )
        enqueue_event(
            self.db,
            organization_id=organization_id,
            aggregate_type="RECEPTION_APPOINTMENT",
            aggregate_id=appointment.id,
            event_type="ReceptionAppointmentConfirmed",
            payload={
                "appointment_id": appointment.id,
                "arrival_notice_id": appointment.arrival_notice_id,
                "slot_start": appointment.slot_start,
                "slot_end": appointment.slot_end,
            },
            deduplication_key=f"appointment:{appointment.id}:confirmed",
        )
        save_idempotent_response(
            self.db,
            organization_id,
            actor_user_id,
            "phase036.reception_appointment.confirm",
            payload.idempotency_key,
            request_payload,
            {"appointment_id": str(appointment.id)},
        )
        write_audit(
            self.db,
            event_code="logistics.reception_appointment.confirmed",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            resource_type="RECEPTION_APPOINTMENT",
            resource_id=appointment.id,
            branch_id=appointment.branch_id,
            warehouse_id=appointment.warehouse_id,
            previous_data={"status": previous},
            new_data={"status": appointment.status},
            reason=payload.capacity_override_reason,
        )
        return appointment

    def request_reschedule(
        self,
        appointment_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        payload,
    ) -> ReceptionAppointmentModel:
        request_payload = {
            "appointment_id": appointment_id,
            **payload.model_dump(),
        }
        cached = get_idempotent_response(
            self.db,
            organization_id,
            "phase036.reception_appointment.request_reschedule",
            payload.idempotency_key,
            request_payload,
        )
        if cached:
            return self.get(UUID(cached["appointment_id"]), organization_id)
        appointment = self.get(appointment_id, organization_id, lock=True)
        if appointment.status != "CONFIRMED":
            raise ReceptionAppointmentRescheduleNotAllowed(
                "Solo una cita confirmada puede solicitar reprogramación."
            )
        previous = appointment.status
        appointment.status = "RESCHEDULE_REQUESTED"
        appointment.reschedule_reason = payload.reason
        appointment.row_version += 1
        self._history(
            appointment,
            actor_user_id,
            "RESCHEDULE_REQUESTED",
            previous,
            appointment.status,
            reason=payload.reason,
        )
        save_idempotent_response(
            self.db,
            organization_id,
            actor_user_id,
            "phase036.reception_appointment.request_reschedule",
            payload.idempotency_key,
            request_payload,
            {"appointment_id": str(appointment.id)},
        )
        return appointment

    def reschedule(
        self,
        appointment_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        payload,
    ) -> ReceptionAppointmentModel:
        request_payload = {
            "appointment_id": appointment_id,
            **payload.model_dump(),
        }
        cached = get_idempotent_response(
            self.db,
            organization_id,
            "phase036.reception_appointment.reschedule",
            payload.idempotency_key,
            request_payload,
        )
        if cached:
            return self.get(UUID(cached["appointment_id"]), organization_id)
        old = self.get(appointment_id, organization_id, lock=True)
        if old.status not in {"CONFIRMED", "RESCHEDULE_REQUESTED"}:
            raise ReceptionAppointmentRescheduleNotAllowed(
                "La cita no admite reprogramación."
            )
        calendar = self.calendar_service.get(
            old.calendar_id, organization_id, lock=True
        )
        if old.slot_start - utc_now() < timedelta(
            minutes=calendar.reschedule_cutoff_minutes
        ):
            raise ReceptionAppointmentRescheduleNotAllowed(
                "Se superó el límite temporal para reprogramar."
            )
        hold = self.get_hold(payload.hold_id, organization_id, lock=True)
        if (
            hold.status != "ACTIVE"
            or hold.arrival_notice_id != old.arrival_notice_id
            or hold.expires_at <= utc_now()
        ):
            raise ReceptionAppointmentHoldExpired(
                "El hold de reprogramación no es válido."
            )
        replacement = ReceptionAppointmentModel(
            organization_id=old.organization_id,
            branch_id=old.branch_id,
            warehouse_id=old.warehouse_id,
            calendar_id=hold.calendar_id,
            arrival_notice_id=old.arrival_notice_id,
            arrival_notice_revision_id=old.arrival_notice_revision_id,
            status="PROPOSED",
            slot_start=hold.slot_start,
            slot_end=hold.slot_end,
            timezone=old.timezone,
            expected_pallet_count=old.expected_pallet_count,
            expected_package_count=old.expected_package_count,
            expected_gross_weight=old.expected_gross_weight,
            weight_unit_id=old.weight_unit_id,
            vehicle_reference_snapshot=old.vehicle_reference_snapshot,
            driver_reference_snapshot=old.driver_reference_snapshot,
            supplier_snapshot=old.supplier_snapshot,
            carrier_snapshot=old.carrier_snapshot,
            contact_snapshot=old.contact_snapshot,
            special_requirements_snapshot=old.special_requirements_snapshot,
            rescheduled_from_appointment_id=old.id,
            reschedule_reason=payload.reason,
        )
        self.db.add(replacement)
        self.db.flush()
        old.status = "RESCHEDULED"
        old.row_version += 1
        hold.status = "CONSUMED"
        notice = get_notice_for_org(
            self.db, old.arrival_notice_id, organization_id, lock=True
        )
        notice.appointment_id = replacement.id
        notice.appointment_status = "PROPOSED"
        notice.status = "SCHEDULED"
        notice.row_version += 1
        self._history(
            old,
            actor_user_id,
            "APPOINTMENT_RESCHEDULED",
            "CONFIRMED",
            "RESCHEDULED",
            previous_slot=self._slot(old),
            new_slot=self._slot(replacement),
            reason=payload.reason,
            metadata={"replacement_appointment_id": str(replacement.id)},
        )
        self._history(
            replacement,
            actor_user_id,
            "APPOINTMENT_CREATED_FROM_RESCHEDULE",
            None,
            replacement.status,
            new_slot=self._slot(replacement),
            reason=payload.reason,
            metadata={"source_appointment_id": str(old.id)},
        )
        enqueue_event(
            self.db,
            organization_id=organization_id,
            aggregate_type="RECEPTION_APPOINTMENT",
            aggregate_id=old.id,
            event_type="ReceptionAppointmentRescheduled",
            payload={
                "previous_appointment_id": old.id,
                "replacement_appointment_id": replacement.id,
            },
            deduplication_key=f"appointment:{old.id}:rescheduled:{replacement.id}",
        )
        save_idempotent_response(
            self.db,
            organization_id,
            actor_user_id,
            "phase036.reception_appointment.reschedule",
            payload.idempotency_key,
            request_payload,
            {"appointment_id": str(replacement.id)},
        )
        return replacement

    def cancel(
        self,
        appointment_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        payload,
    ) -> ReceptionAppointmentModel:
        request_payload = {
            "appointment_id": appointment_id,
            **payload.model_dump(),
        }
        cached = get_idempotent_response(
            self.db,
            organization_id,
            "phase036.reception_appointment.cancel",
            payload.idempotency_key,
            request_payload,
        )
        if cached:
            return self.get(UUID(cached["appointment_id"]), organization_id)
        appointment = self.get(appointment_id, organization_id, lock=True)
        if appointment.status in {"CANCELLED", "RESCHEDULED"}:
            save_idempotent_response(
                self.db,
                organization_id,
                actor_user_id,
                "phase036.reception_appointment.cancel",
                payload.idempotency_key,
                request_payload,
                {"appointment_id": str(appointment.id)},
            )
            return appointment
        calendar = self.calendar_service.get(
            appointment.calendar_id, organization_id
        )
        if appointment.status == "CONFIRMED" and (
            appointment.slot_start - utc_now()
            < timedelta(minutes=calendar.cancellation_cutoff_minutes)
        ):
            raise ReceptionAppointmentCancellationBlocked(
                "Se superó el límite temporal para cancelar."
            )
        previous = appointment.status
        appointment.status = "CANCELLED"
        appointment.cancelled_at = utc_now()
        appointment.cancelled_by = actor_user_id
        appointment.cancellation_reason = payload.reason
        appointment.row_version += 1
        notice = get_notice_for_org(
            self.db, appointment.arrival_notice_id, organization_id, lock=True
        )
        if notice.appointment_id == appointment.id:
            notice.status = "READY_FOR_SCHEDULING"
            notice.appointment_status = "CANCELLED"
            notice.row_version += 1
        self._history(
            appointment,
            actor_user_id,
            "APPOINTMENT_CANCELLED",
            previous,
            "CANCELLED",
            reason=payload.reason,
        )
        enqueue_event(
            self.db,
            organization_id=organization_id,
            aggregate_type="RECEPTION_APPOINTMENT",
            aggregate_id=appointment.id,
            event_type="ReceptionAppointmentCancelled",
            payload={"appointment_id": appointment.id, "reason": payload.reason},
            deduplication_key=f"appointment:{appointment.id}:cancelled",
        )
        write_audit(
            self.db,
            event_code="logistics.reception_appointment.cancelled",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            resource_type="RECEPTION_APPOINTMENT",
            resource_id=appointment.id,
            branch_id=appointment.branch_id,
            warehouse_id=appointment.warehouse_id,
            previous_data={"status": previous},
            new_data={"status": appointment.status},
            reason=payload.reason,
        )
        save_idempotent_response(
            self.db,
            organization_id,
            actor_user_id,
            "phase036.reception_appointment.cancel",
            payload.idempotency_key,
            request_payload,
            {"appointment_id": str(appointment.id)},
        )
        return appointment

    def history(
        self, appointment_id: UUID, organization_id: UUID
    ) -> list[ReceptionAppointmentHistoryModel]:
        self.get(appointment_id, organization_id)
        return list(
            self.db.scalars(
                select(ReceptionAppointmentHistoryModel)
                .where(
                    ReceptionAppointmentHistoryModel.appointment_id
                    == appointment_id,
                    ReceptionAppointmentHistoryModel.organization_id
                    == organization_id,
                )
                .order_by(ReceptionAppointmentHistoryModel.created_at)
            )
        )

    def capabilities(self, appointment: ReceptionAppointmentModel) -> list[str]:
        values = ["read", "read_history", "gate_preparation"]
        if appointment.status in {"PROPOSED", "PENDING_CONFIRMATION"}:
            values.extend(["validate", "confirm", "cancel"])
        if appointment.status == "CONFIRMED":
            values.extend(
                [
                    "request_reschedule",
                    "reschedule",
                    "cancel",
                    "preview_cit",
                    "issue_cit",
                    "package",
                ]
            )
        if appointment.document_instance_id:
            values.extend(["read_document", "download_cit"])
        return list(dict.fromkeys(values))

    def gate_preparation(
        self, appointment_id: UUID, organization_id: UUID
    ) -> dict:
        appointment = self.get(appointment_id, organization_id)
        documents = list(
            self.db.scalars(
                select(ArrivalNoticeTransportDocumentModel).where(
                    ArrivalNoticeTransportDocumentModel.revision_id
                    == appointment.arrival_notice_revision_id,
                    ArrivalNoticeTransportDocumentModel.status == "ACTIVE",
                )
            )
        )
        vehicle = appointment.vehicle_reference_snapshot or {}
        driver = appointment.driver_reference_snapshot or {}
        warnings = []
        if not vehicle:
            warnings.append("VEHICLE_NOT_DECLARED")
        if not driver:
            warnings.append("DRIVER_NOT_DECLARED")
        return {
            "appointment_id": appointment.id,
            "appointment_code": appointment.appointment_code,
            "arrival_notice_id": appointment.arrival_notice_id,
            "warehouse_id": appointment.warehouse_id,
            "expected_slot": self._slot(appointment),
            "supplier": appointment.supplier_snapshot,
            "carrier": appointment.carrier_snapshot,
            "expected_plate": vehicle.get("plate"),
            "expected_vehicle_id": vehicle.get("vehicle_id"),
            "expected_driver_id": driver.get("driver_id"),
            "guide_references": [
                item.normalized_reference
                for item in documents
                if item.document_kind in {"REMITTANCE_GUIDE", "CARRIER_GUIDE"}
            ],
            "expected_seal_reference": None,
            "documents_summary": [
                {
                    "kind": item.document_kind,
                    "reference": item.normalized_reference,
                    "verification_status": item.verification_status,
                    "has_file": item.file_asset_id is not None,
                }
                for item in documents
            ],
            "special_requirements": appointment.special_requirements_snapshot,
            "verification_warnings": warnings,
            "appointment_status": appointment.status,
            "check_in_capabilities_future": [],
        }

    def create_package_job(
        self,
        appointment_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        payload,
    ) -> ReceptionAppointmentPackageJobModel:
        appointment = self.get(appointment_id, organization_id)
        request_payload = {
            "appointment_id": appointment_id,
            **payload.model_dump(),
        }
        existing = self.db.scalar(
            select(ReceptionAppointmentPackageJobModel).where(
                ReceptionAppointmentPackageJobModel.organization_id
                == organization_id,
                ReceptionAppointmentPackageJobModel.idempotency_key
                == payload.idempotency_key,
            )
        )
        digest = content_hash(request_payload)
        if existing:
            if existing.request_hash != digest:
                raise IdempotencyConflict(
                    "La clave de idempotencia ya fue usada con otra solicitud."
                )
            return existing
        job = ReceptionAppointmentPackageJobModel(
            organization_id=organization_id,
            appointment_id=appointment.id,
            idempotency_key=payload.idempotency_key,
            request_hash=digest,
            manifest={
                "appointment_id": str(appointment.id),
                "include_supplier_visible_files": payload.include_supplier_visible_files,
                "state": "QUEUED",
            },
            created_by=actor_user_id,
        )
        self.db.add(job)
        self.db.flush()
        enqueue_event(
            self.db,
            organization_id=organization_id,
            aggregate_type="RECEPTION_APPOINTMENT_PACKAGE",
            aggregate_id=job.id,
            event_type="ReceptionAppointmentPackageRequested",
            payload={"package_job_id": job.id, "appointment_id": appointment.id},
            deduplication_key=f"appointment-package:{job.id}",
        )
        return job

    def get_package_job(
        self, package_id: UUID, organization_id: UUID
    ) -> ReceptionAppointmentPackageJobModel:
        job = self.db.scalar(
            select(ReceptionAppointmentPackageJobModel).where(
                ReceptionAppointmentPackageJobModel.id == package_id,
                ReceptionAppointmentPackageJobModel.organization_id
                == organization_id,
            )
        )
        if job is None:
            raise ReceptionCalendarNotFound("El paquete de cita no existe.")
        return job

    def _assert_slot_available(
        self,
        calendar: WarehouseReceptionCalendarModel,
        slot_start,
        slot_end,
        pallets: int,
        packages: int,
        weight: Decimal,
        weight_unit_id: UUID,
        *,
        exclude_appointment_id: UUID | None = None,
        exclude_hold_id: UUID | None = None,
    ) -> None:
        now = utc_now()
        if calendar.status != "ACTIVE":
            raise ReceptionCalendarInactive("El calendario no está activo.")
        if slot_start >= slot_end or slot_start <= now:
            raise ReceptionSlotUnavailable("La franja no es válida o ya transcurrió.")
        if calendar.weight_unit_id and calendar.weight_unit_id != weight_unit_id:
            raise ReceptionSlotCapacityExceeded(
                "La unidad de peso no coincide con el calendario."
            )
        local_start = slot_start.astimezone(
            __import__("zoneinfo").ZoneInfo(calendar.timezone)
        )
        local_end = slot_end.astimezone(
            __import__("zoneinfo").ZoneInfo(calendar.timezone)
        )
        window = self.db.scalar(
            select(WarehouseReceptionOperatingWindowModel).where(
                WarehouseReceptionOperatingWindowModel.calendar_id == calendar.id,
                WarehouseReceptionOperatingWindowModel.status == "ACTIVE",
                WarehouseReceptionOperatingWindowModel.day_of_week
                == local_start.weekday(),
                WarehouseReceptionOperatingWindowModel.start_local_time
                <= local_start.time().replace(tzinfo=None),
                WarehouseReceptionOperatingWindowModel.end_local_time
                >= local_end.time().replace(tzinfo=None),
                WarehouseReceptionOperatingWindowModel.effective_from
                <= local_start.date(),
                (
                    WarehouseReceptionOperatingWindowModel.effective_to.is_(None)
                    | (
                        WarehouseReceptionOperatingWindowModel.effective_to
                        >= local_start.date()
                    )
                ),
            )
        )
        if window is None:
            raise ReceptionSlotUnavailable(
                "La franja está fuera del horario operativo."
            )
        blackout = self.db.scalar(
            select(WarehouseReceptionBlackoutModel.id).where(
                WarehouseReceptionBlackoutModel.calendar_id == calendar.id,
                WarehouseReceptionBlackoutModel.status == "ACTIVE",
                WarehouseReceptionBlackoutModel.starts_at < slot_end,
                WarehouseReceptionBlackoutModel.ends_at > slot_start,
            )
        )
        if blackout:
            raise ReceptionSlotUnavailable("La franja está bloqueada.")
        appointment_filters = [
            ReceptionAppointmentModel.calendar_id == calendar.id,
            ReceptionAppointmentModel.status.in_(_CAPACITY_STATUSES),
            ReceptionAppointmentModel.slot_start < slot_end,
            ReceptionAppointmentModel.slot_end > slot_start,
        ]
        if exclude_appointment_id:
            appointment_filters.append(
                ReceptionAppointmentModel.id != exclude_appointment_id
            )
        hold_filters = [
            ReceptionAppointmentHoldModel.calendar_id == calendar.id,
            ReceptionAppointmentHoldModel.status == "ACTIVE",
            ReceptionAppointmentHoldModel.expires_at > now,
            ReceptionAppointmentHoldModel.slot_start < slot_end,
            ReceptionAppointmentHoldModel.slot_end > slot_start,
        ]
        if exclude_hold_id:
            hold_filters.append(ReceptionAppointmentHoldModel.id != exclude_hold_id)
        appt = self.db.execute(
            select(
                func.count(ReceptionAppointmentModel.id),
                func.coalesce(
                    func.sum(ReceptionAppointmentModel.expected_pallet_count), 0
                ),
                func.coalesce(
                    func.sum(ReceptionAppointmentModel.expected_package_count), 0
                ),
                func.coalesce(
                    func.sum(ReceptionAppointmentModel.expected_gross_weight), 0
                ),
            ).where(*appointment_filters)
        ).one()
        holds = self.db.execute(
            select(
                func.count(ReceptionAppointmentHoldModel.id),
                func.coalesce(
                    func.sum(ReceptionAppointmentHoldModel.expected_pallet_count), 0
                ),
                func.coalesce(
                    func.sum(ReceptionAppointmentHoldModel.expected_package_count), 0
                ),
                func.coalesce(
                    func.sum(ReceptionAppointmentHoldModel.expected_weight), 0
                ),
            ).where(*hold_filters)
        ).one()
        max_count = (
            window.max_concurrent_appointments
            or calendar.default_max_concurrent_appointments
        )
        used_count = int(appt[0]) + int(holds[0])
        if used_count + 1 > max_count:
            raise ReceptionSlotCapacityExceeded(
                "La franja alcanzó el máximo de citas simultáneas."
            )
        max_pallets = (
            window.max_pallets
            if window.max_pallets is not None
            else calendar.default_max_pallets_per_slot
        )
        max_packages = (
            window.max_packages
            if window.max_packages is not None
            else calendar.default_max_packages_per_slot
        )
        max_weight = (
            Decimal(window.max_weight)
            if window.max_weight is not None
            else (
                Decimal(calendar.default_max_weight_per_slot)
                if calendar.default_max_weight_per_slot is not None
                else None
            )
        )
        if max_pallets is not None and int(appt[1]) + int(holds[1]) + pallets > max_pallets:
            raise ReceptionSlotCapacityExceeded("Capacidad de pallets excedida.")
        if max_packages is not None and int(appt[2]) + int(holds[2]) + packages > max_packages:
            raise ReceptionSlotCapacityExceeded("Capacidad de bultos excedida.")
        if (
            max_weight is not None
            and Decimal(appt[3]) + Decimal(holds[3]) + weight > max_weight
        ):
            raise ReceptionSlotCapacityExceeded("Capacidad de peso excedida.")

    def _copy_transport_snapshots(
        self, appointment: ReceptionAppointmentModel, revision_id: UUID
    ) -> None:
        vehicle = self.db.scalar(
            select(ArrivalNoticeVehicleReferenceModel).where(
                ArrivalNoticeVehicleReferenceModel.revision_id == revision_id
            )
        )
        driver = self.db.scalar(
            select(ArrivalNoticeDriverReferenceModel).where(
                ArrivalNoticeDriverReferenceModel.revision_id == revision_id
            )
        )
        appointment.vehicle_reference_snapshot = (
            {
                "vehicle_id": str(vehicle.vehicle_id) if vehicle.vehicle_id else None,
                "plate": vehicle.plate_snapshot,
                "normalized_plate": vehicle.normalized_plate,
                "verification_summary": vehicle.verification_summary,
                "verification_expiration": (
                    vehicle.verification_expiration.isoformat()
                    if vehicle.verification_expiration
                    else None
                ),
            }
            if vehicle
            else None
        )
        appointment.driver_reference_snapshot = (
            {
                "driver_id": str(driver.driver_id) if driver.driver_id else None,
                "full_name": driver.full_name_snapshot,
                "document_number_redacted": driver.document_number_redacted_snapshot,
                "license_number_redacted": driver.license_number_redacted_snapshot,
                "license_category": driver.license_category_snapshot,
                "license_expiration": (
                    driver.license_expiration_snapshot.isoformat()
                    if driver.license_expiration_snapshot
                    else None
                ),
            }
            if driver
            else None
        )

    @staticmethod
    def _normalize_plate(value: str | None) -> str | None:
        if not value:
            return None
        normalized = "".join(character for character in value.upper() if character.isalnum())
        return normalized or None

    def _transport_overlap_conflicts(
        self, appointment: ReceptionAppointmentModel
    ) -> list[dict]:
        """Detect overlapping confirmed use of the same declared vehicle or driver."""

        vehicle = appointment.vehicle_reference_snapshot or {}
        driver = appointment.driver_reference_snapshot or {}
        normalized_plate = self._normalize_plate(
            vehicle.get("normalized_plate") or vehicle.get("plate")
        )
        driver_id = driver.get("driver_id")
        if not normalized_plate and not driver_id:
            return []
        overlaps = list(
            self.db.scalars(
                select(ReceptionAppointmentModel).where(
                    ReceptionAppointmentModel.organization_id
                    == appointment.organization_id,
                    ReceptionAppointmentModel.id != appointment.id,
                    ReceptionAppointmentModel.status.in_(
                        {"PENDING_CONFIRMATION", "CONFIRMED", "RESCHEDULE_REQUESTED"}
                    ),
                    ReceptionAppointmentModel.slot_start < appointment.slot_end,
                    ReceptionAppointmentModel.slot_end > appointment.slot_start,
                )
            )
        )
        errors: list[dict] = []
        for other in overlaps:
            other_vehicle = other.vehicle_reference_snapshot or {}
            other_driver = other.driver_reference_snapshot or {}
            other_plate = self._normalize_plate(
                other_vehicle.get("normalized_plate") or other_vehicle.get("plate")
            )
            if normalized_plate and other_plate == normalized_plate:
                errors.append(
                    {
                        "code": "VEHICLE_SLOT_OVERLAP",
                        "message": "La placa ya está comprometida en una cita solapada.",
                        "conflicting_appointment_id": str(other.id),
                    }
                )
            if driver_id and other_driver.get("driver_id") == driver_id:
                errors.append(
                    {
                        "code": "DRIVER_SLOT_OVERLAP",
                        "message": "El conductor ya está comprometido en una cita solapada.",
                        "conflicting_appointment_id": str(other.id),
                    }
                )
        return errors

    def _history(
        self,
        appointment: ReceptionAppointmentModel,
        actor_user_id: UUID | None,
        event_type: str,
        previous_status: str | None,
        new_status: str | None,
        *,
        previous_slot: dict | None = None,
        new_slot: dict | None = None,
        reason: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.db.add(
            ReceptionAppointmentHistoryModel(
                appointment_id=appointment.id,
                organization_id=appointment.organization_id,
                event_type=event_type,
                previous_status=previous_status,
                new_status=new_status,
                previous_slot=json_safe(previous_slot),
                new_slot=json_safe(new_slot),
                reason=reason,
                actor_user_id=actor_user_id,
                metadata_data=json_safe(metadata or {}),
            )
        )
        self.db.flush()

    @staticmethod
    def _slot(appointment: ReceptionAppointmentModel) -> dict:
        return {
            "slot_start": appointment.slot_start,
            "slot_end": appointment.slot_end,
            "timezone": appointment.timezone,
        }


__all__ = ["ReceptionAppointmentService"]
