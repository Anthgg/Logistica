"""Explicit state machines; status is never accepted through generic PATCH."""

from __future__ import annotations

from app.modules.logistics.inbound.arrival_notices.domain.enums import ArrivalNoticeStatus
from app.modules.logistics.inbound.arrival_notices.domain.errors.exceptions import (
    ArrivalNoticeStatusInvalid,
)
from app.modules.logistics.inbound.reception_calendar.domain.enums import (
    ReceptionAppointmentStatus,
)


ARRIVAL_NOTICE_TRANSITIONS: dict[str, frozenset[str]] = {
    "DRAFT": frozenset({"SUBMITTED", "CANCELLED"}),
    "SUBMITTED": frozenset({"UNDER_REVIEW", "REQUIRES_CHANGES", "READY_FOR_SCHEDULING", "CANCELLED"}),
    "UNDER_REVIEW": frozenset({"REQUIRES_CHANGES", "READY_FOR_SCHEDULING", "CANCELLED"}),
    "REQUIRES_CHANGES": frozenset({"SUBMITTED", "CANCELLED"}),
    "READY_FOR_SCHEDULING": frozenset({"SCHEDULED", "CANCELLED"}),
    "SCHEDULED": frozenset({"CONFIRMED", "RESCHEDULE_REQUESTED", "CANCELLED"}),
    "CONFIRMED": frozenset({"RESCHEDULE_REQUESTED", "CANCELLED", "WINDOW_ELAPSED"}),
    "RESCHEDULE_REQUESTED": frozenset({"SCHEDULED", "CONFIRMED", "CANCELLED"}),
    "WINDOW_ELAPSED": frozenset({"ARCHIVED"}),
    "CANCELLED": frozenset({"ARCHIVED"}),
}

APPOINTMENT_TRANSITIONS: dict[str, frozenset[str]] = {
    "PROPOSED": frozenset({"HELD", "PENDING_CONFIRMATION", "CANCELLED"}),
    "HELD": frozenset({"PENDING_CONFIRMATION", "CANCELLED"}),
    "PENDING_CONFIRMATION": frozenset({"CONFIRMED", "RESCHEDULE_REQUESTED", "CANCELLED"}),
    "CONFIRMED": frozenset({"RESCHEDULE_REQUESTED", "CANCELLED", "WINDOW_ELAPSED"}),
    "RESCHEDULE_REQUESTED": frozenset({"RESCHEDULED", "CONFIRMED", "CANCELLED"}),
    "RESCHEDULED": frozenset({"SUPERSEDED"}),
}


def ensure_arrival_notice_transition(current: str, target: str) -> ArrivalNoticeStatus:
    if target not in ARRIVAL_NOTICE_TRANSITIONS.get(current, frozenset()):
        raise ArrivalNoticeStatusInvalid(
            f"No se permite cambiar el aviso de {current} a {target}.",
            details={"current_status": current, "target_status": target},
        )
    return ArrivalNoticeStatus(target)


def ensure_appointment_transition(current: str, target: str) -> ReceptionAppointmentStatus:
    if target not in APPOINTMENT_TRANSITIONS.get(current, frozenset()):
        raise ArrivalNoticeStatusInvalid(
            f"No se permite cambiar la cita de {current} a {target}.",
            details={"current_status": current, "target_status": target},
        )
    return ReceptionAppointmentStatus(target)
