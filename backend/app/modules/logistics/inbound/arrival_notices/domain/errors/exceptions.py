"""Sanitized domain errors for Phase 036."""

from __future__ import annotations

from app.core.exceptions import ApplicationError


class InboundDomainError(ApplicationError):
    code = "INBOUND_DOMAIN_ERROR"
    http_status = 409

    def __init__(self, message: str | None = None, *, details: dict | None = None):
        self.message = message or self.code.replace("_", " ").title()
        self.details = details or {}
        super().__init__(self.code, self.message, self.http_status)

    def as_detail(self) -> dict:
        detail = {"code": self.code, "message": self.message}
        if self.details:
            detail["details"] = self.details
        return detail


def _error(name: str, code: str, http_status: int = 409):
    return type(name, (InboundDomainError,), {"code": code, "http_status": http_status})


ArrivalNoticeNotFound = _error("ArrivalNoticeNotFound", "ARRIVAL_NOTICE_NOT_FOUND", 404)
ArrivalNoticeStatusInvalid = _error("ArrivalNoticeStatusInvalid", "ARRIVAL_NOTICE_STATUS_INVALID")
ArrivalNoticeNotEditable = _error("ArrivalNoticeNotEditable", "ARRIVAL_NOTICE_NOT_EDITABLE")
ArrivalNoticeRevisionConflict = _error("ArrivalNoticeRevisionConflict", "ARRIVAL_NOTICE_REVISION_CONFLICT")
ArrivalNoticePurchaseOrderInvalid = _error("ArrivalNoticePurchaseOrderInvalid", "ARRIVAL_NOTICE_PURCHASE_ORDER_INVALID", 422)
ArrivalNoticeSupplierMismatch = _error("ArrivalNoticeSupplierMismatch", "ARRIVAL_NOTICE_SUPPLIER_MISMATCH", 422)
ArrivalNoticeQuantityExceeded = _error("ArrivalNoticeQuantityExceeded", "ARRIVAL_NOTICE_QUANTITY_EXCEEDED", 422)
ArrivalNoticeUnitInvalid = _error("ArrivalNoticeUnitInvalid", "ARRIVAL_NOTICE_UNIT_INVALID", 422)
ArrivalNoticeTransportIncomplete = _error("ArrivalNoticeTransportIncomplete", "ARRIVAL_NOTICE_TRANSPORT_INCOMPLETE", 422)
ArrivalNoticeVehicleInvalid = _error("ArrivalNoticeVehicleInvalid", "ARRIVAL_NOTICE_VEHICLE_INVALID", 422)
ArrivalNoticeVehicleVerificationExpired = _error("ArrivalNoticeVehicleVerificationExpired", "ARRIVAL_NOTICE_VEHICLE_VERIFICATION_EXPIRED", 422)
ArrivalNoticeDriverInvalid = _error("ArrivalNoticeDriverInvalid", "ARRIVAL_NOTICE_DRIVER_INVALID", 422)
ArrivalNoticeDriverLicenseExpired = _error("ArrivalNoticeDriverLicenseExpired", "ARRIVAL_NOTICE_DRIVER_LICENSE_EXPIRED", 422)
ArrivalNoticeGuideRequired = _error("ArrivalNoticeGuideRequired", "ARRIVAL_NOTICE_GUIDE_REQUIRED", 422)
ArrivalNoticeTransportDocumentInvalid = _error("ArrivalNoticeTransportDocumentInvalid", "ARRIVAL_NOTICE_TRANSPORT_DOCUMENT_INVALID", 422)
ReceptionCalendarNotFound = _error("ReceptionCalendarNotFound", "RECEPTION_CALENDAR_NOT_FOUND", 404)
ReceptionCalendarInactive = _error("ReceptionCalendarInactive", "RECEPTION_CALENDAR_INACTIVE")
ReceptionOperatingWindowInvalid = _error("ReceptionOperatingWindowInvalid", "RECEPTION_OPERATING_WINDOW_INVALID", 422)
ReceptionCalendarBlackoutConflict = _error("ReceptionCalendarBlackoutConflict", "RECEPTION_CALENDAR_BLACKOUT_CONFLICT")
ReceptionSlotUnavailable = _error("ReceptionSlotUnavailable", "RECEPTION_SLOT_UNAVAILABLE")
ReceptionSlotCapacityExceeded = _error("ReceptionSlotCapacityExceeded", "RECEPTION_SLOT_CAPACITY_EXCEEDED")
ReceptionAppointmentHoldExpired = _error("ReceptionAppointmentHoldExpired", "RECEPTION_APPOINTMENT_HOLD_EXPIRED")
ReceptionAppointmentConflict = _error("ReceptionAppointmentConflict", "RECEPTION_APPOINTMENT_CONFLICT")
ReceptionAppointmentAlreadyConfirmed = _error("ReceptionAppointmentAlreadyConfirmed", "RECEPTION_APPOINTMENT_ALREADY_CONFIRMED")
ReceptionAppointmentRescheduleNotAllowed = _error("ReceptionAppointmentRescheduleNotAllowed", "RECEPTION_APPOINTMENT_RESCHEDULE_NOT_ALLOWED")
ReceptionAppointmentCancellationBlocked = _error("ReceptionAppointmentCancellationBlocked", "RECEPTION_APPOINTMENT_CANCELLATION_BLOCKED")
ReceptionAppointmentDocumentIssueFailed = _error("ReceptionAppointmentDocumentIssueFailed", "RECEPTION_APPOINTMENT_DOCUMENT_ISSUE_FAILED", 500)
IdempotencyConflict = _error("IdempotencyConflict", "IDEMPOTENCY_CONFLICT")
