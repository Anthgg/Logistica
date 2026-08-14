"""FastAPI routes for reception calendars, holds, appointments and CIT."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Body, Depends, Response, status
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
from app.modules.logistics.documents.application.lifecycle_service import (
    DocumentLifecycleService,
)
from app.modules.logistics.documents.models import DocumentArtifactModel
from app.modules.logistics.inbound.arrival_notices.domain.errors.exceptions import (
    ReceptionAppointmentConflict,
)
from app.modules.logistics.inbound.reception_calendar.application.services import (
    ReceptionAppointmentDocumentService,
    ReceptionAppointmentService,
    ReceptionCalendarService,
)
from app.modules.logistics.inbound.reception_calendar.presentation.schemas.schemas import (
    GateCheckInPreparationResponse,
    ReceptionAppointmentCancelRequest,
    ReceptionAppointmentConfirmRequest,
    ReceptionAppointmentCreate,
    ReceptionAppointmentHoldCreate,
    ReceptionAppointmentHoldResponse,
    ReceptionAppointmentPackageRequest,
    ReceptionAppointmentPackageResponse,
    ReceptionAppointmentRescheduleRequest,
    ReceptionAppointmentResponse,
    ReceptionAppointmentValidationResponse,
    ReceptionAvailabilityRequest,
    ReceptionAvailabilityResponse,
    ReceptionBlackoutCreate,
    ReceptionBlackoutResponse,
    ReceptionCalendarCreate,
    ReceptionCalendarResponse,
    ReceptionCalendarUpdate,
    ReceptionOperatingWindowCreate,
    ReceptionOperatingWindowResponse,
)
from app.modules.logistics.principal import LogisticsPrincipal
from app.services.audit_service import AuditService


router = APIRouter(tags=["Logistics - Reception Scheduling"])


@router.get(
    "/reception-calendars", response_model=list[ReceptionCalendarResponse]
)
def list_reception_calendars(
    warehouse_id: UUID | None = None,
    status_filter: str | None = None,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_calendars.read")
    ),
    db: Session = Depends(get_db),
):
    return ReceptionCalendarService(db).list(
        resolve_organization_id(principal),
        warehouse_id=warehouse_id,
        status=status_filter,
    )


@router.post(
    "/reception-calendars",
    response_model=ReceptionCalendarResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reception_calendar(
    payload: ReceptionCalendarCreate,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_calendars.manage")
    ),
    db: Session = Depends(get_db),
):
    calendar = ReceptionCalendarService(db).create(
        resolve_organization_id(principal), principal.user_id, payload
    )
    db.commit()
    db.refresh(calendar)
    return calendar


@router.get(
    "/reception-calendars/{calendar_id}",
    response_model=ReceptionCalendarResponse,
)
def get_reception_calendar(
    calendar_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_calendars.read")
    ),
    db: Session = Depends(get_db),
):
    return ReceptionCalendarService(db).get(
        calendar_id, resolve_organization_id(principal)
    )


@router.patch(
    "/reception-calendars/{calendar_id}",
    response_model=ReceptionCalendarResponse,
)
def update_reception_calendar(
    calendar_id: UUID,
    payload: ReceptionCalendarUpdate,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_calendars.manage")
    ),
    db: Session = Depends(get_db),
):
    calendar = ReceptionCalendarService(db).update(
        calendar_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload,
    )
    db.commit()
    db.refresh(calendar)
    return calendar


def _calendar_transition(
    db: Session,
    principal: LogisticsPrincipal,
    calendar_id: UUID,
    target_status: str,
):
    calendar = ReceptionCalendarService(db).transition(
        calendar_id,
        resolve_organization_id(principal),
        principal.user_id,
        target_status,
    )
    db.commit()
    db.refresh(calendar)
    return calendar


@router.post(
    "/reception-calendars/{calendar_id}/activate",
    response_model=ReceptionCalendarResponse,
)
def activate_reception_calendar(
    calendar_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_calendars.manage")
    ),
    db: Session = Depends(get_db),
):
    return _calendar_transition(db, principal, calendar_id, "ACTIVE")


@router.post(
    "/reception-calendars/{calendar_id}/deactivate",
    response_model=ReceptionCalendarResponse,
)
def deactivate_reception_calendar(
    calendar_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_calendars.manage")
    ),
    db: Session = Depends(get_db),
):
    return _calendar_transition(db, principal, calendar_id, "INACTIVE")


@router.post(
    "/reception-calendars/{calendar_id}/archive",
    response_model=ReceptionCalendarResponse,
)
def archive_reception_calendar(
    calendar_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_calendars.manage")
    ),
    db: Session = Depends(get_db),
):
    return _calendar_transition(db, principal, calendar_id, "ARCHIVED")


@router.get(
    "/reception-calendars/{calendar_id}/operating-windows",
    response_model=list[ReceptionOperatingWindowResponse],
)
def list_reception_windows(
    calendar_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_calendars.read")
    ),
    db: Session = Depends(get_db),
):
    return ReceptionCalendarService(db).list_windows(
        calendar_id, resolve_organization_id(principal)
    )


@router.post(
    "/reception-calendars/{calendar_id}/operating-windows",
    response_model=ReceptionOperatingWindowResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reception_window(
    calendar_id: UUID,
    payload: ReceptionOperatingWindowCreate,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_calendars.manage")
    ),
    db: Session = Depends(get_db),
):
    window = ReceptionCalendarService(db).add_window(
        calendar_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload,
    )
    db.commit()
    db.refresh(window)
    return window


@router.get(
    "/reception-calendars/{calendar_id}/blackouts",
    response_model=list[ReceptionBlackoutResponse],
)
def list_reception_blackouts(
    calendar_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_calendars.read")
    ),
    db: Session = Depends(get_db),
):
    return ReceptionCalendarService(db).list_blackouts(
        calendar_id, resolve_organization_id(principal)
    )


@router.post(
    "/reception-calendars/{calendar_id}/blackouts",
    response_model=ReceptionBlackoutResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reception_blackout(
    calendar_id: UUID,
    payload: ReceptionBlackoutCreate,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_calendars.manage_blackouts")
    ),
    db: Session = Depends(get_db),
):
    blackout = ReceptionCalendarService(db).add_blackout(
        calendar_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload,
    )
    db.commit()
    db.refresh(blackout)
    return blackout


@router.post(
    "/reception-calendars/{calendar_id}/availability",
    response_model=ReceptionAvailabilityResponse,
)
def get_reception_availability(
    calendar_id: UUID,
    payload: ReceptionAvailabilityRequest,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_calendars.read")
    ),
    db: Session = Depends(get_db),
):
    slots, version = ReceptionCalendarService(db).availability(
        calendar_id, resolve_organization_id(principal), payload
    )
    from app.modules.logistics.inbound.arrival_notices.application.services.common import (
        utc_now,
    )

    return {"slots": slots, "server_time": utc_now(), "availability_version": version}


@router.post(
    "/reception-appointment-holds",
    response_model=ReceptionAppointmentHoldResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reception_hold(
    payload: ReceptionAppointmentHoldCreate,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.create")
    ),
    db: Session = Depends(get_db),
):
    hold = ReceptionAppointmentService(db).create_hold(
        resolve_organization_id(principal), principal.user_id, payload
    )
    db.commit()
    db.refresh(hold)
    return hold


@router.get(
    "/reception-appointment-holds/{hold_id}",
    response_model=ReceptionAppointmentHoldResponse,
)
def get_reception_hold(
    hold_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.read")
    ),
    db: Session = Depends(get_db),
):
    return ReceptionAppointmentService(db).get_hold(
        hold_id, resolve_organization_id(principal)
    )


@router.post(
    "/reception-appointment-holds/{hold_id}/cancel",
    response_model=ReceptionAppointmentHoldResponse,
)
def cancel_reception_hold(
    hold_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.create")
    ),
    db: Session = Depends(get_db),
):
    hold = ReceptionAppointmentService(db).cancel_hold(
        hold_id, resolve_organization_id(principal), principal.user_id
    )
    db.commit()
    db.refresh(hold)
    return hold


@router.post(
    "/reception-appointment-holds/{hold_id}/refresh",
    response_model=ReceptionAppointmentHoldResponse,
)
def refresh_reception_hold(
    hold_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.create")
    ),
    db: Session = Depends(get_db),
):
    hold = ReceptionAppointmentService(db).refresh_hold(
        hold_id, resolve_organization_id(principal), principal.user_id
    )
    db.commit()
    db.refresh(hold)
    return hold


@router.get(
    "/reception-appointments", response_model=list[ReceptionAppointmentResponse]
)
def list_reception_appointments(
    warehouse_id: UUID | None = None,
    status_filter: str | None = None,
    arrival_notice_id: UUID | None = None,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.read")
    ),
    db: Session = Depends(get_db),
):
    return ReceptionAppointmentService(db).list(
        resolve_organization_id(principal),
        warehouse_id=warehouse_id,
        status=status_filter,
        arrival_notice_id=arrival_notice_id,
    )


@router.post(
    "/reception-appointments",
    response_model=ReceptionAppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reception_appointment(
    payload: ReceptionAppointmentCreate,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.create")
    ),
    db: Session = Depends(get_db),
):
    appointment = ReceptionAppointmentService(db).create_appointment(
        resolve_organization_id(principal), principal.user_id, payload
    )
    db.commit()
    db.refresh(appointment)
    return appointment


@router.get(
    "/reception-appointments/{appointment_id}",
    response_model=ReceptionAppointmentResponse,
)
def get_reception_appointment(
    appointment_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.read")
    ),
    db: Session = Depends(get_db),
):
    return ReceptionAppointmentService(db).get(
        appointment_id, resolve_organization_id(principal)
    )


@router.post(
    "/reception-appointments/{appointment_id}/validate",
    response_model=ReceptionAppointmentValidationResponse,
)
def validate_reception_appointment(
    appointment_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.read")
    ),
    db: Session = Depends(get_db),
):
    return ReceptionAppointmentService(db).validate(
        appointment_id, resolve_organization_id(principal)
    )


@router.post(
    "/reception-appointments/{appointment_id}/confirm",
    response_model=ReceptionAppointmentResponse,
)
def confirm_reception_appointment(
    appointment_id: UUID,
    payload: ReceptionAppointmentConfirmRequest,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.confirm")
    ),
    db: Session = Depends(get_db),
):
    if (
        payload.capacity_override_reason
        and not principal.has_permission(
            "logistics.reception_calendars.override_capacity"
        )
    ):
        raise ReceptionAppointmentConflict(
            "No tiene permiso para sobrepasar capacidad."
        )
    appointment = ReceptionAppointmentService(db).confirm(
        appointment_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload,
        allow_capacity_override=bool(payload.capacity_override_reason),
    )
    db.commit()
    db.refresh(appointment)
    return appointment


@router.post(
    "/reception-appointments/{appointment_id}/request-reschedule",
    response_model=ReceptionAppointmentResponse,
)
def request_reception_reschedule(
    appointment_id: UUID,
    payload: ReceptionAppointmentCancelRequest,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.reschedule")
    ),
    db: Session = Depends(get_db),
):
    appointment = ReceptionAppointmentService(db).request_reschedule(
        appointment_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload,
    )
    db.commit()
    db.refresh(appointment)
    return appointment


@router.post(
    "/reception-appointments/{appointment_id}/reschedule",
    response_model=ReceptionAppointmentResponse,
)
def reschedule_reception_appointment(
    appointment_id: UUID,
    payload: ReceptionAppointmentRescheduleRequest,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.reschedule")
    ),
    db: Session = Depends(get_db),
):
    appointment = ReceptionAppointmentService(db).reschedule(
        appointment_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload,
    )
    db.commit()
    db.refresh(appointment)
    return appointment


@router.post(
    "/reception-appointments/{appointment_id}/cancel",
    response_model=ReceptionAppointmentResponse,
)
def cancel_reception_appointment(
    appointment_id: UUID,
    payload: ReceptionAppointmentCancelRequest,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.cancel")
    ),
    db: Session = Depends(get_db),
):
    appointment = ReceptionAppointmentService(db).cancel(
        appointment_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload,
    )
    db.commit()
    db.refresh(appointment)
    return appointment


@router.get("/reception-appointments/{appointment_id}/history")
def get_reception_appointment_history(
    appointment_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.read_history")
    ),
    db: Session = Depends(get_db),
):
    rows = ReceptionAppointmentService(db).history(
        appointment_id, resolve_organization_id(principal)
    )
    return [
        {
            "id": item.id,
            "event_type": item.event_type,
            "previous_status": item.previous_status,
            "new_status": item.new_status,
            "previous_slot": item.previous_slot,
            "new_slot": item.new_slot,
            "reason": item.reason,
            "created_at": item.created_at,
        }
        for item in rows
    ]


@router.get("/reception-appointments/{appointment_id}/capabilities")
def get_reception_appointment_capabilities(
    appointment_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.read")
    ),
    db: Session = Depends(get_db),
):
    organization_id = resolve_organization_id(principal)
    service = ReceptionAppointmentService(db)
    appointment = service.get(appointment_id, organization_id)
    return {"capabilities": service.capabilities(appointment)}


@router.get(
    "/reception-appointments/{appointment_id}/gate-preparation",
    response_model=GateCheckInPreparationResponse,
)
def get_gate_preparation(
    appointment_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.read")
    ),
    db: Session = Depends(get_db),
):
    return ReceptionAppointmentService(db).gate_preparation(
        appointment_id, resolve_organization_id(principal)
    )


def _record_cit_document_event(
    db: Session,
    principal: LogisticsPrincipal,
    appointment_id: UUID,
    pdf: bytes,
    *,
    downloaded: bool,
) -> None:
    """Record viewing vs downloading the appointment CIT as distinct events.

    Call only after the PDF has been validated, so a failed render is never
    recorded as a delivered document.
    """
    AuditService().record(
        db=db,
        event_type=(
            "logistics.reception_appointment.document_downloaded"
            if downloaded
            else "logistics.document.preview_rendered"
        ),
        user_id=principal.user_id,
        session_id=principal.session_id,
        resource_type="reception_appointment_document",
        resource_id=str(appointment_id),
        event_metadata={
            "appointment_id": str(appointment_id),
            "size_bytes": len(pdf),
            "delivery": "attachment" if downloaded else "inline",
        },
    )
    db.commit()


@router.get("/reception-appointments/{appointment_id}/preview", responses=PDF_RESPONSE_SCHEMA)
def preview_reception_appointment_cit(
    appointment_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.preview")
    ),
    db: Session = Depends(get_db),
):
    pdf, filename = ReceptionAppointmentDocumentService(db).preview(
        appointment_id, resolve_organization_id(principal), principal.user_id
    )
    response = build_pdf_preview_response(pdf, filename)
    _record_cit_document_event(db, principal, appointment_id, pdf, downloaded=False)
    return response


@router.get("/reception-appointments/{appointment_id}/preview.pdf", responses=PDF_RESPONSE_SCHEMA)
def download_reception_appointment_cit(
    appointment_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.download")
    ),
    db: Session = Depends(get_db),
):
    """Same CIT render as the preview, delivered as an explicit download."""
    pdf, filename = ReceptionAppointmentDocumentService(db).preview(
        appointment_id, resolve_organization_id(principal), principal.user_id
    )
    response = build_pdf_download_response(pdf, filename)
    _record_cit_document_event(db, principal, appointment_id, pdf, downloaded=True)
    return response


@router.post("/reception-appointments/{appointment_id}/issue")
def issue_reception_appointment_cit(
    appointment_id: UUID,
    idempotency_key: str = Body(embed=True, min_length=8, max_length=128),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.reprint")
    ),
    db: Session = Depends(get_db),
):
    document = ReceptionAppointmentDocumentService(db).issue(
        appointment_id,
        resolve_organization_id(principal),
        principal.user_id,
        idempotency_key,
    )
    db.commit()
    return {
        "appointment_id": appointment_id,
        "document_id": document.id,
        "document_code": document.document_code,
        "status": document.status,
        "authoritative_artifact_id": document.authoritative_artifact_id,
    }


@router.get("/reception-appointments/{appointment_id}/document")
def get_reception_appointment_document(
    appointment_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.download")
    ),
    db: Session = Depends(get_db),
):
    document = ReceptionAppointmentDocumentService(db).get_document(
        appointment_id, resolve_organization_id(principal)
    )
    return {
        "id": document.id,
        "document_code": document.document_code,
        "status": document.status,
        "authoritative_artifact_id": document.authoritative_artifact_id,
        "issued_at": document.issued_at,
    }


@router.post(
    "/reception-appointments/{appointment_id}/package",
    response_model=ReceptionAppointmentPackageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_reception_appointment_package(
    appointment_id: UUID,
    payload: ReceptionAppointmentPackageRequest,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.download_package")
    ),
    db: Session = Depends(get_db),
):
    job = ReceptionAppointmentService(db).create_package_job(
        appointment_id,
        resolve_organization_id(principal),
        principal.user_id,
        payload,
    )
    db.commit()
    db.refresh(job)
    return job


@router.get(
    "/reception-appointment-packages/{package_id}",
    response_model=ReceptionAppointmentPackageResponse,
)
def get_reception_appointment_package(
    package_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.download_package")
    ),
    db: Session = Depends(get_db),
):
    return ReceptionAppointmentService(db).get_package_job(
        package_id, resolve_organization_id(principal)
    )


@router.get("/reception-appointment-packages/{package_id}/download")
def download_reception_appointment_package(
    package_id: UUID,
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.reception_appointments.download_package")
    ),
    db: Session = Depends(get_db),
):
    job = ReceptionAppointmentService(db).get_package_job(
        package_id, resolve_organization_id(principal)
    )
    if job.status != "COMPLETED" or not job.artifact_id:
        raise ReceptionAppointmentConflict("El paquete todavía no está disponible.")
    artifact = db.get(DocumentArtifactModel, job.artifact_id)
    if artifact is None:
        raise ReceptionAppointmentConflict("El artefacto del paquete no existe.")
    content = DocumentLifecycleService(db).storage.get(artifact.storage_key)
    return Response(
        content,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{artifact.filename}"',
            "X-Content-SHA256": artifact.file_hash,
        },
    )


__all__ = ["router"]
