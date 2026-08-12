"""CIT document adapter backed by the existing document lifecycle engine."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.logistics.documents.application.lifecycle_service import (
    DocumentLifecycleService,
)
from app.modules.logistics.documents.models import DocumentInstanceModel
from app.modules.logistics.documents.series.series_models import DocumentNumberModel
from app.modules.logistics.inbound.arrival_notices.application.services.common import (
    enqueue_event,
    write_audit,
)
from app.modules.logistics.inbound.arrival_notices.application.services.snapshot_provider import (
    ArrivalNoticeSnapshotProvider,
)
from app.modules.logistics.inbound.arrival_notices.domain.errors.exceptions import (
    ReceptionAppointmentDocumentIssueFailed,
)
from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
    ArrivalNoticeModel,
    ArrivalNoticeRevisionModel,
)
from app.modules.logistics.inbound.reception_calendar.application.services.appointment_service import (
    ReceptionAppointmentService,
)


class ReceptionAppointmentDocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.appointments = ReceptionAppointmentService(db)
        self.documents = DocumentLifecycleService(db)
        self.snapshots = ArrivalNoticeSnapshotProvider(db)

    def ensure_draft(
        self,
        appointment_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
    ) -> DocumentInstanceModel:
        appointment = self.appointments.get(
            appointment_id, organization_id, lock=True
        )
        if appointment.status != "CONFIRMED":
            raise ReceptionAppointmentDocumentIssueFailed(
                "La CIT solo puede prepararse para una cita confirmada."
            )
        if appointment.document_instance_id:
            document = self.db.get(
                DocumentInstanceModel, appointment.document_instance_id
            )
            if document and document.organization_id == organization_id:
                return document
        notice = self.db.get(ArrivalNoticeModel, appointment.arrival_notice_id)
        revision = self.db.get(
            ArrivalNoticeRevisionModel, appointment.arrival_notice_revision_id
        )
        if notice is None or revision is None:
            raise ReceptionAppointmentDocumentIssueFailed(
                "No se pudo reconstruir el snapshot de la cita."
            )
        snapshot = self.snapshots.build(notice, revision, appointment)
        document = self.documents.create_draft(
            organization_id=appointment.organization_id,
            branch_id=appointment.branch_id,
            warehouse_id=appointment.warehouse_id,
            doc_type_code="CIT",
            source_resource_type="RECEPTION_APPOINTMENT",
            source_resource_id=appointment.id,
            source_operation_id=None,
            title="Cita de recepción",
            structured_data=snapshot,
            sensitivity="INTERNAL",
            actor_id=actor_user_id,
        )
        appointment.document_instance_id = document.id
        self.db.flush()
        return document

    def preview(
        self,
        appointment_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
    ) -> tuple[bytes, str]:
        document = self.ensure_draft(
            appointment_id, organization_id, actor_user_id
        )
        return self.documents.preview_document(document.id, actor_user_id)

    def issue(
        self,
        appointment_id: UUID,
        organization_id: UUID,
        actor_user_id: UUID,
        idempotency_key: str,
    ) -> DocumentInstanceModel:
        appointment = self.appointments.get(
            appointment_id, organization_id, lock=True
        )
        document = self.ensure_draft(
            appointment_id, organization_id, actor_user_id
        )
        try:
            issued = self.documents.issue_document(
                document.id,
                idempotency_key=idempotency_key,
                actor_id=actor_user_id,
            )
        except Exception as exc:
            if getattr(exc, "code", None) == "DOCUMENT_ALREADY_ISSUED":
                existing = self.db.get(DocumentInstanceModel, document.id)
                if existing and existing.status == "ISSUED":
                    issued = existing
                else:
                    raise
            else:
                raise
        appointment.appointment_code = issued.document_code
        appointment.normalized_appointment_code = (
            issued.document_code.upper().replace(" ", "")
            if issued.document_code
            else None
        )
        number = (
            self.db.get(DocumentNumberModel, issued.document_number_id)
            if issued.document_number_id
            else None
        )
        appointment.document_series_id = number.series_id if number else None
        appointment.row_version += 1
        enqueue_event(
            self.db,
            organization_id=organization_id,
            aggregate_type="RECEPTION_APPOINTMENT",
            aggregate_id=appointment.id,
            event_type="ReceptionAppointmentCitIssued",
            payload={
                "appointment_id": appointment.id,
                "document_id": issued.id,
                "document_code": issued.document_code,
            },
            deduplication_key=f"appointment:{appointment.id}:cit:{issued.id}",
        )
        write_audit(
            self.db,
            event_code="logistics.reception_appointment.CIT_issued",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            resource_type="RECEPTION_APPOINTMENT",
            resource_id=appointment.id,
            branch_id=appointment.branch_id,
            warehouse_id=appointment.warehouse_id,
            new_data={
                "document_id": issued.id,
                "document_code": issued.document_code,
            },
        )
        self.db.flush()
        return issued

    def get_document(
        self, appointment_id: UUID, organization_id: UUID
    ) -> DocumentInstanceModel:
        appointment = self.appointments.get(appointment_id, organization_id)
        if not appointment.document_instance_id:
            raise ReceptionAppointmentDocumentIssueFailed(
                "La cita todavía no tiene una CIT."
            )
        document = self.db.get(
            DocumentInstanceModel, appointment.document_instance_id
        )
        if document is None or document.organization_id != organization_id:
            raise ReceptionAppointmentDocumentIssueFailed(
                "El documento CIT no existe."
            )
        return document


__all__ = ["ReceptionAppointmentDocumentService"]
