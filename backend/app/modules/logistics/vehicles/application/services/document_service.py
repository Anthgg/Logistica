"""Vehicle Document & Compliance Service (Phase 027)."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.vehicles.domain.errors.exceptions import VehicleNotFoundError
from app.modules.logistics.vehicles.infrastructure.persistence.models import (
    VehicleDocumentModel,
    VehicleDocumentRequirementModel,
    VehicleModel,
)


class VehicleDocumentService:
    def __init__(self, db: Session):
        self.db = db

    def add_document(
        self,
        vehicle_id: UUID,
        organization_id: UUID,
        document_type: str,
        actor_id: UUID,
        document_number: Optional[str] = None,
        issuer: Optional[str] = None,
        issued_at: Optional[datetime] = None,
        valid_from: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        file_reference_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> VehicleDocumentModel:
        vehicle = self.db.scalars(
            select(VehicleModel).where(
                and_(VehicleModel.id == vehicle_id, VehicleModel.organization_id == organization_id)
            )
        ).first()

        if not vehicle:
            raise VehicleNotFoundError(str(vehicle_id))

        doc = VehicleDocumentModel(
            id=uuid4(),
            vehicle_id=vehicle_id,
            document_type=document_type,
            document_number=document_number,
            issuer=issuer,
            issued_at=issued_at,
            valid_from=valid_from,
            expires_at=expires_at,
            verification_status="NOT_VERIFIED",  # No external SUNARP/MTC check in Phase 027
            status="ACTIVE",
            file_reference_id=file_reference_id,
            source_type="DECLARED",
            notes=notes,
            created_by=actor_id,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle.document_created",
                severity="medium",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="vehicle_document",
                resource_id=str(doc.id),
            ),
        )

        return doc

    def review_document_metadata(
        self,
        document_id: UUID,
        organization_id: UUID,
        actor_id: UUID,
        notes: Optional[str] = None,
    ) -> VehicleDocumentModel:
        doc = self.db.get(VehicleDocumentModel, document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Documento vehicular no encontrado.")

        doc.verification_status = "METADATA_REVIEWED"
        doc.reviewed_by = actor_id
        doc.reviewed_at = utc_now()
        if notes:
            doc.notes = (doc.notes or "") + f"\n[Revisado metadata por usuario]: {notes}"
        self.db.commit()

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle.document_reviewed",
                severity="medium",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="vehicle_document",
                resource_id=str(doc.id),
            ),
        )

        return doc

    def list_vehicle_documents(self, vehicle_id: UUID, organization_id: UUID) -> List[VehicleDocumentModel]:
        vehicle = self.db.scalar(
            select(VehicleModel).where(
                and_(
                    VehicleModel.id == vehicle_id,
                    VehicleModel.organization_id == organization_id,
                )
            )
        )
        if not vehicle:
            raise VehicleNotFoundError(str(vehicle_id))

        return list(
            self.db.scalars(
                select(VehicleDocumentModel).where(
                    and_(VehicleDocumentModel.vehicle_id == vehicle_id, VehicleDocumentModel.status == "ACTIVE")
                )
            ).all()
        )
