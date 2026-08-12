"""Reception-calendar configuration and deterministic availability service."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.arrival_notices.application.services.common import (
    content_hash,
    get_warehouse_for_org,
    utc_now,
    write_audit,
)
from app.modules.logistics.inbound.arrival_notices.domain.errors.exceptions import (
    ArrivalNoticeUnitInvalid,
    ReceptionCalendarBlackoutConflict,
    ReceptionCalendarInactive,
    ReceptionCalendarNotFound,
    ReceptionOperatingWindowInvalid,
)
from app.modules.logistics.inbound.reception_calendar.infrastructure.persistence.models import (
    ReceptionAppointmentHoldModel,
    ReceptionAppointmentModel,
    WarehouseReceptionBlackoutModel,
    WarehouseReceptionCalendarModel,
    WarehouseReceptionOperatingWindowModel,
)


_BUSY_APPOINTMENT_STATUSES = {
    "PROPOSED",
    "PENDING_CONFIRMATION",
    "CONFIRMED",
    "RESCHEDULE_REQUESTED",
}


class ReceptionCalendarService:
    def __init__(self, db: Session):
        self.db = db

    def get(
        self,
        calendar_id: UUID,
        organization_id: UUID,
        *,
        lock: bool = False,
    ) -> WarehouseReceptionCalendarModel:
        stmt = select(WarehouseReceptionCalendarModel).where(
            WarehouseReceptionCalendarModel.id == calendar_id,
            WarehouseReceptionCalendarModel.organization_id == organization_id,
        )
        if lock:
            stmt = stmt.with_for_update()
        calendar = self.db.scalar(stmt)
        if calendar is None:
            raise ReceptionCalendarNotFound("El calendario de recepción no existe.")
        return calendar

    def list(
        self,
        organization_id: UUID,
        *,
        warehouse_id: UUID | None = None,
        status: str | None = None,
    ) -> list[WarehouseReceptionCalendarModel]:
        stmt = select(WarehouseReceptionCalendarModel).where(
            WarehouseReceptionCalendarModel.organization_id == organization_id
        )
        if warehouse_id:
            stmt = stmt.where(WarehouseReceptionCalendarModel.warehouse_id == warehouse_id)
        if status:
            stmt = stmt.where(WarehouseReceptionCalendarModel.status == status.upper())
        return list(self.db.scalars(stmt.order_by(WarehouseReceptionCalendarModel.name)))

    def create(
        self,
        organization_id: UUID,
        actor_user_id: UUID,
        payload,
    ) -> WarehouseReceptionCalendarModel:
        warehouse = get_warehouse_for_org(
            self.db, payload.warehouse_id, organization_id
        )
        if payload.default_max_weight_per_slot is not None and payload.weight_unit_id is None:
            raise ArrivalNoticeUnitInvalid(
                "weight_unit_id es obligatorio cuando se configura capacidad de peso."
            )
        calendar = WarehouseReceptionCalendarModel(
            organization_id=organization_id,
            warehouse_id=warehouse.id,
            name=payload.name.strip(),
            timezone=payload.timezone,
            slot_duration_minutes=payload.slot_duration_minutes,
            booking_horizon_days=payload.booking_horizon_days,
            minimum_advance_minutes=payload.minimum_advance_minutes,
            maximum_advance_days=payload.maximum_advance_days,
            cancellation_cutoff_minutes=payload.cancellation_cutoff_minutes,
            reschedule_cutoff_minutes=payload.reschedule_cutoff_minutes,
            hold_duration_minutes=payload.hold_duration_minutes,
            maximum_hold_refreshes=payload.maximum_hold_refreshes,
            default_max_concurrent_appointments=payload.default_max_concurrent_appointments,
            default_max_pallets_per_slot=payload.default_max_pallets_per_slot,
            default_max_packages_per_slot=payload.default_max_packages_per_slot,
            default_max_weight_per_slot=payload.default_max_weight_per_slot,
            weight_unit_id=payload.weight_unit_id,
            created_by=actor_user_id,
        )
        self.db.add(calendar)
        self.db.flush()
        write_audit(
            self.db,
            event_code="logistics.reception_calendar.created",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            resource_type="WAREHOUSE_RECEPTION_CALENDAR",
            resource_id=calendar.id,
            warehouse_id=calendar.warehouse_id,
            new_data={"name": calendar.name, "status": calendar.status},
        )
        return calendar

    def update(
        self,
        calendar_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        payload,
    ) -> WarehouseReceptionCalendarModel:
        calendar = self.get(calendar_id, organization_id, lock=True)
        if calendar.status == "ARCHIVED":
            raise ReceptionCalendarInactive("Un calendario archivado no es editable.")
        if calendar.row_version != payload.row_version:
            raise ReceptionCalendarBlackoutConflict(
                "El calendario fue modificado por otra sesión.",
                details={"current_row_version": calendar.row_version},
            )
        before = {
            "name": calendar.name,
            "timezone": calendar.timezone,
            "row_version": calendar.row_version,
        }
        for field, value in payload.model_dump(exclude_unset=True).items():
            if field != "row_version":
                setattr(calendar, field, value)
        if (
            calendar.default_max_weight_per_slot is not None
            and calendar.weight_unit_id is None
        ):
            raise ArrivalNoticeUnitInvalid(
                "weight_unit_id es obligatorio cuando se configura capacidad de peso."
            )
        calendar.updated_by = actor_user_id
        calendar.row_version += 1
        self.db.flush()
        write_audit(
            self.db,
            event_code="logistics.reception_calendar.updated",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            resource_type="WAREHOUSE_RECEPTION_CALENDAR",
            resource_id=calendar.id,
            warehouse_id=calendar.warehouse_id,
            previous_data=before,
            new_data={
                "name": calendar.name,
                "timezone": calendar.timezone,
                "row_version": calendar.row_version,
            },
        )
        return calendar

    def transition(
        self,
        calendar_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        target_status: str,
    ) -> WarehouseReceptionCalendarModel:
        calendar = self.get(calendar_id, organization_id, lock=True)
        target_status = target_status.upper()
        allowed = {
            "DRAFT": {"ACTIVE", "ARCHIVED"},
            "ACTIVE": {"INACTIVE", "ARCHIVED"},
            "INACTIVE": {"ACTIVE", "ARCHIVED"},
            "ARCHIVED": set(),
        }
        if target_status not in allowed.get(calendar.status, set()):
            raise ReceptionCalendarInactive(
                f"No se permite {calendar.status} -> {target_status}."
            )
        if target_status == "ACTIVE":
            has_window = self.db.scalar(
                select(func.count())
                .select_from(WarehouseReceptionOperatingWindowModel)
                .where(
                    WarehouseReceptionOperatingWindowModel.calendar_id == calendar.id,
                    WarehouseReceptionOperatingWindowModel.status == "ACTIVE",
                )
            )
            if not has_window:
                raise ReceptionOperatingWindowInvalid(
                    "El calendario necesita al menos un horario operativo activo."
                )
            competing = self.db.scalar(
                select(WarehouseReceptionCalendarModel.id).where(
                    WarehouseReceptionCalendarModel.organization_id
                    == organization_id,
                    WarehouseReceptionCalendarModel.warehouse_id
                    == calendar.warehouse_id,
                    WarehouseReceptionCalendarModel.status == "ACTIVE",
                    WarehouseReceptionCalendarModel.id != calendar.id,
                )
            )
            if competing:
                raise ReceptionCalendarBlackoutConflict(
                    "El almacén ya tiene un calendario activo."
                )
        previous = calendar.status
        calendar.status = target_status
        calendar.updated_by = actor_user_id
        calendar.row_version += 1
        self.db.flush()
        write_audit(
            self.db,
            event_code=f"logistics.reception_calendar.{target_status.lower()}",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            resource_type="WAREHOUSE_RECEPTION_CALENDAR",
            resource_id=calendar.id,
            warehouse_id=calendar.warehouse_id,
            previous_data={"status": previous},
            new_data={"status": target_status},
        )
        return calendar

    def list_windows(
        self, calendar_id: UUID, organization_id: UUID
    ) -> list[WarehouseReceptionOperatingWindowModel]:
        self.get(calendar_id, organization_id)
        return list(
            self.db.scalars(
                select(WarehouseReceptionOperatingWindowModel)
                .where(
                    WarehouseReceptionOperatingWindowModel.calendar_id == calendar_id,
                    WarehouseReceptionOperatingWindowModel.status == "ACTIVE",
                )
                .order_by(
                    WarehouseReceptionOperatingWindowModel.day_of_week,
                    WarehouseReceptionOperatingWindowModel.start_local_time,
                )
            )
        )

    def add_window(
        self,
        calendar_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        payload,
    ) -> WarehouseReceptionOperatingWindowModel:
        calendar = self.get(calendar_id, organization_id, lock=True)
        if calendar.status == "ARCHIVED":
            raise ReceptionCalendarInactive("El calendario está archivado.")
        overlap_filters = [
            WarehouseReceptionOperatingWindowModel.calendar_id == calendar.id,
            WarehouseReceptionOperatingWindowModel.day_of_week == payload.day_of_week,
            WarehouseReceptionOperatingWindowModel.status == "ACTIVE",
            WarehouseReceptionOperatingWindowModel.start_local_time
            < payload.end_local_time,
            WarehouseReceptionOperatingWindowModel.end_local_time
            > payload.start_local_time,
            or_(
                WarehouseReceptionOperatingWindowModel.effective_to.is_(None),
                WarehouseReceptionOperatingWindowModel.effective_to
                >= payload.effective_from,
            ),
        ]
        if payload.effective_to is not None:
            overlap_filters.append(
                WarehouseReceptionOperatingWindowModel.effective_from
                <= payload.effective_to
            )
        overlap = self.db.scalar(
            select(WarehouseReceptionOperatingWindowModel.id).where(
                *overlap_filters
            )
        )
        if overlap:
            raise ReceptionOperatingWindowInvalid(
                "El horario se superpone con otro horario activo."
            )
        window = WarehouseReceptionOperatingWindowModel(
            calendar_id=calendar.id,
            **payload.model_dump(),
        )
        self.db.add(window)
        self.db.flush()
        write_audit(
            self.db,
            event_code="logistics.reception_calendar.window_created",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            resource_type="WAREHOUSE_RECEPTION_OPERATING_WINDOW",
            resource_id=window.id,
            warehouse_id=calendar.warehouse_id,
            new_data=payload.model_dump(),
        )
        return window

    def list_blackouts(
        self, calendar_id: UUID, organization_id: UUID
    ) -> list[WarehouseReceptionBlackoutModel]:
        self.get(calendar_id, organization_id)
        return list(
            self.db.scalars(
                select(WarehouseReceptionBlackoutModel)
                .where(
                    WarehouseReceptionBlackoutModel.calendar_id == calendar_id,
                    WarehouseReceptionBlackoutModel.status == "ACTIVE",
                )
                .order_by(WarehouseReceptionBlackoutModel.starts_at)
            )
        )

    def add_blackout(
        self,
        calendar_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        payload,
    ) -> WarehouseReceptionBlackoutModel:
        calendar = self.get(calendar_id, organization_id, lock=True)
        if calendar.status == "ARCHIVED":
            raise ReceptionCalendarInactive("El calendario está archivado.")
        duplicate = self.db.scalar(
            select(WarehouseReceptionBlackoutModel.id).where(
                WarehouseReceptionBlackoutModel.calendar_id == calendar.id,
                WarehouseReceptionBlackoutModel.status == "ACTIVE",
                WarehouseReceptionBlackoutModel.starts_at == payload.starts_at,
                WarehouseReceptionBlackoutModel.ends_at == payload.ends_at,
            )
        )
        if duplicate:
            raise ReceptionCalendarBlackoutConflict(
                "Ya existe un blackout para el mismo rango."
            )
        blackout = WarehouseReceptionBlackoutModel(
            calendar_id=calendar.id,
            created_by=actor_user_id,
            **payload.model_dump(),
        )
        self.db.add(blackout)
        self.db.flush()
        write_audit(
            self.db,
            event_code="logistics.reception_calendar.blackout_created",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            resource_type="WAREHOUSE_RECEPTION_BLACKOUT",
            resource_id=blackout.id,
            warehouse_id=calendar.warehouse_id,
            new_data=payload.model_dump(),
        )
        return blackout

    def availability(
        self,
        calendar_id: UUID,
        organization_id: UUID,
        payload,
    ) -> tuple[list[dict], str]:
        calendar = self.get(calendar_id, organization_id)
        if calendar.status != "ACTIVE":
            raise ReceptionCalendarInactive("El calendario no está activo.")
        if (
            calendar.default_max_weight_per_slot is not None
            and calendar.weight_unit_id != payload.weight_unit_id
        ):
            raise ArrivalNoticeUnitInvalid(
                "La unidad de peso consultada no coincide con la unidad del calendario."
            )
        now = utc_now()
        zone = ZoneInfo(calendar.timezone)
        windows = self.list_windows(calendar.id, organization_id)
        blackouts = self.list_blackouts(calendar.id, organization_id)
        slots: list[dict] = []
        day = payload.starts_on
        while day <= payload.ends_on:
            for window in windows:
                if window.day_of_week != day.weekday():
                    continue
                if day < window.effective_from:
                    continue
                if window.effective_to and day > window.effective_to:
                    continue
                slot_start = datetime.combine(day, window.start_local_time, zone)
                window_end = datetime.combine(day, window.end_local_time, zone)
                duration = timedelta(
                    minutes=payload.desired_duration_minutes
                    or calendar.slot_duration_minutes
                )
                while slot_start + duration <= window_end:
                    slot_end = slot_start + duration
                    slots.append(
                        self._availability_slot(
                            calendar,
                            window,
                            blackouts,
                            slot_start.astimezone(timezone.utc),
                            slot_end.astimezone(timezone.utc),
                            payload,
                            now,
                        )
                    )
                    slot_start += timedelta(minutes=calendar.slot_duration_minutes)
            day += timedelta(days=1)
        version_payload = {
            "calendar_id": calendar.id,
            "calendar_row_version": calendar.row_version,
            "request": payload.model_dump(),
            "slots": slots,
        }
        return slots, content_hash(version_payload)

    def _availability_slot(
        self,
        calendar,
        window,
        blackouts,
        slot_start,
        slot_end,
        payload,
        now,
    ) -> dict:
        warnings: list[str] = []
        blocked = any(
            blackout.starts_at < slot_end and blackout.ends_at > slot_start
            for blackout in blackouts
        )
        min_start = now + timedelta(minutes=calendar.minimum_advance_minutes)
        max_start = now + timedelta(days=calendar.maximum_advance_days)
        if slot_start < min_start:
            warnings.append("MINIMUM_ADVANCE_NOT_MET")
            blocked = True
        if slot_start > max_start:
            warnings.append("MAXIMUM_ADVANCE_EXCEEDED")
            blocked = True
        hold_stmt = select(
            func.count(ReceptionAppointmentHoldModel.id),
            func.coalesce(func.sum(ReceptionAppointmentHoldModel.expected_pallet_count), 0),
            func.coalesce(func.sum(ReceptionAppointmentHoldModel.expected_package_count), 0),
            func.coalesce(func.sum(ReceptionAppointmentHoldModel.expected_weight), 0),
        ).where(
            ReceptionAppointmentHoldModel.calendar_id == calendar.id,
            ReceptionAppointmentHoldModel.status == "ACTIVE",
            ReceptionAppointmentHoldModel.expires_at > now,
            ReceptionAppointmentHoldModel.slot_start < slot_end,
            ReceptionAppointmentHoldModel.slot_end > slot_start,
        )
        appointment_stmt = select(
            func.count(ReceptionAppointmentModel.id),
            func.coalesce(func.sum(ReceptionAppointmentModel.expected_pallet_count), 0),
            func.coalesce(func.sum(ReceptionAppointmentModel.expected_package_count), 0),
            func.coalesce(func.sum(ReceptionAppointmentModel.expected_gross_weight), 0),
        ).where(
            ReceptionAppointmentModel.calendar_id == calendar.id,
            ReceptionAppointmentModel.status.in_(_BUSY_APPOINTMENT_STATUSES),
            ReceptionAppointmentModel.slot_start < slot_end,
            ReceptionAppointmentModel.slot_end > slot_start,
        )
        hold_count, hold_pallets, hold_packages, hold_weight = self.db.execute(
            hold_stmt
        ).one()
        appt_count, appt_pallets, appt_packages, appt_weight = self.db.execute(
            appointment_stmt
        ).one()
        max_count = (
            window.max_concurrent_appointments
            or calendar.default_max_concurrent_appointments
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
        used_count = int(hold_count) + int(appt_count)
        used_pallets = int(hold_pallets) + int(appt_pallets)
        used_packages = int(hold_packages) + int(appt_packages)
        used_weight = Decimal(hold_weight) + Decimal(appt_weight)
        remaining_count = max(0, max_count - used_count)
        remaining_pallets = (
            None if max_pallets is None else max(0, max_pallets - used_pallets)
        )
        remaining_packages = (
            None if max_packages is None else max(0, max_packages - used_packages)
        )
        remaining_weight = (
            None if max_weight is None else max(Decimal("0"), max_weight - used_weight)
        )
        if remaining_count < 1:
            blocked = True
            warnings.append("CONCURRENT_CAPACITY_EXCEEDED")
        if remaining_pallets is not None and (
            payload.expected_pallet_count > remaining_pallets
        ):
            blocked = True
            warnings.append("PALLET_CAPACITY_EXCEEDED")
        if remaining_packages is not None and (
            payload.expected_package_count > remaining_packages
        ):
            blocked = True
            warnings.append("PACKAGE_CAPACITY_EXCEEDED")
        if remaining_weight is not None and payload.expected_weight > remaining_weight:
            blocked = True
            warnings.append("WEIGHT_CAPACITY_EXCEEDED")
        return {
            "slot_start": slot_start,
            "slot_end": slot_end,
            "timezone": calendar.timezone,
            "availability_status": "UNAVAILABLE" if blocked else "AVAILABLE",
            "remaining_appointments": remaining_count,
            "remaining_pallet_capacity": remaining_pallets,
            "remaining_package_capacity": remaining_packages,
            "remaining_weight_capacity": remaining_weight,
            "warnings": list(dict.fromkeys(warnings)),
            "hold_supported": not blocked,
        }


__all__ = ["ReceptionCalendarService"]
