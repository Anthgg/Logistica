"""AssistedVehicleVerification Application Service (Phase 028)."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.vehicle_verifications.domain.errors.exceptions import (
    AssistedVehicleVerificationAlreadyApproved,
    AssistedVehicleVerificationInvalid,
    AssistedVehicleVerificationSeparationOfDutiesError,
)
from app.modules.logistics.vehicle_verifications.domain.value_objects.enums import (
    AssistedApprovalStatus,
    ConfidenceLevel,
    VerificationDomain,
    VerificationMethod,
    VerificationResultStatus,
    VerificationStatus,
)
from app.modules.logistics.vehicle_verifications.infrastructure.persistence.models import (
    AssistedVehicleVerificationModel,
    VehicleVerificationEvidenceModel,
    VehicleVerificationFieldProvenanceModel,
    VehicleVerificationModel,
    VehicleVerificationResultModel,
    VehicleVerificationSourceModel,
)
from app.modules.logistics.vehicles.infrastructure.persistence.models import (
    VehicleModel,
    VehiclePlateAssignmentModel,
)


class AssistedVehicleVerificationService:
    def __init__(self, db: Session):
        self.db = db

    def create_assisted_verification(
        self,
        organization_id: UUID,
        vehicle_id: UUID,
        domain: str,
        source_id: UUID,
        verification_reason: str,
        observed_plate: str,
        actor_id: UUID,
        source_reference: Optional[str] = None,
        observed_owner: Optional[str] = None,
        observed_make: Optional[str] = None,
        observed_model: Optional[str] = None,
        observed_year: Optional[int] = None,
        observed_status: Optional[str] = None,
        observed_expiration: Optional[datetime] = None,
        observations: Optional[str] = None,
        evidence_reference_id: Optional[str] = None,
        result_status: str = VerificationResultStatus.VALID.value,
    ) -> AssistedVehicleVerificationModel:
        # Validate Vehicle
        vehicle = self.db.scalars(
            select(VehicleModel).where(
                and_(VehicleModel.id == vehicle_id, VehicleModel.organization_id == organization_id)
            )
        ).first()

        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehículo no encontrado.")

        # Validate Source
        source = self.db.get(VehicleVerificationSourceModel, source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Fuente de verificación no encontrada.")

        plate_ass = self.db.scalars(
            select(VehiclePlateAssignmentModel).where(
                and_(
                    VehiclePlateAssignmentModel.vehicle_id == vehicle.id,
                    VehiclePlateAssignmentModel.status == "CURRENT",
                )
            )
        ).first()

        assisted = AssistedVehicleVerificationModel(
            id=uuid4(),
            organization_id=organization_id,
            vehicle_id=vehicle.id,
            plate_assignment_id=plate_ass.id if plate_ass else None,
            verification_domain=domain,
            source_id=source.id,
            verification_reason=verification_reason,
            source_reference=source_reference,
            reviewed_at=utc_now(),
            reviewed_by=actor_id,
            observed_plate=observed_plate,
            observed_owner=observed_owner,
            observed_make=observed_make,
            observed_model=observed_model,
            observed_year=observed_year,
            observed_status=observed_status,
            observed_expiration=observed_expiration,
            observations=observations,
            evidence_reference_id=evidence_reference_id,
            result_status=result_status,
            confidence_level=ConfidenceLevel.MEDIUM.value,  # Manual review defaults to MEDIUM
            approval_status=AssistedApprovalStatus.SUBMITTED.value,
        )
        self.db.add(assisted)
        self.db.commit()

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle_verification.assisted_created",
                severity="medium",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="assisted_vehicle_verification",
                resource_id=str(assisted.id),
                resource_code=observed_plate,
                new_data={"domain": domain, "reason": verification_reason},
            ),
        )

        return assisted

    def approve_assisted_verification(
        self,
        assisted_id: UUID,
        organization_id: UUID,
        approver_id: UUID,
        enforce_separation_of_duties: bool = True,
    ) -> VehicleVerificationModel:
        assisted = self.db.scalars(
            select(AssistedVehicleVerificationModel).where(
                and_(
                    AssistedVehicleVerificationModel.id == assisted_id,
                    AssistedVehicleVerificationModel.organization_id == organization_id,
                )
            )
        ).first()

        if not assisted:
            raise HTTPException(status_code=404, detail="Verificación asistida no encontrada.")

        if assisted.approval_status == AssistedApprovalStatus.APPROVED.value:
            raise AssistedVehicleVerificationAlreadyApproved(str(assisted_id))

        if enforce_separation_of_duties and assisted.reviewed_by == approver_id:
            raise AssistedVehicleVerificationSeparationOfDutiesError(str(approver_id))

        assisted.approval_status = AssistedApprovalStatus.APPROVED.value
        assisted.approved_by = approver_id
        assisted.approved_at = utc_now()
        self.db.commit()

        # Create Completed VehicleVerification
        verif = VehicleVerificationModel(
            id=uuid4(),
            organization_id=organization_id,
            vehicle_id=assisted.vehicle_id,
            plate_assignment_id=assisted.plate_assignment_id,
            normalized_plate=assisted.observed_plate.replace("-", "").strip().upper(),
            verification_domain=assisted.verification_domain,
            verification_method=VerificationMethod.MANUAL_ASSISTED.value,
            source_id=assisted.source_id,
            status=VerificationStatus.COMPLETED.value,
            result_status=assisted.result_status,
            confidence_level=assisted.confidence_level,
            source_data_at=assisted.reviewed_at,
            requested_at=assisted.created_at,
            completed_at=utc_now(),
            expires_at=assisted.observed_expiration,
            verified_by_user_id=assisted.reviewed_by,
            approved_by_user_id=approver_id,
            evidence_status="HAS_EVIDENCE" if assisted.evidence_reference_id else "NO_EVIDENCE",
        )
        self.db.add(verif)
        self.db.commit()

        # Create Result Record
        res = VehicleVerificationResultModel(
            id=uuid4(),
            verification_id=verif.id,
            queried_plate=assisted.observed_plate,
            registered_owner_name=assisted.observed_owner,
            make=assisted.observed_make,
            model=assisted.observed_model,
            manufacturing_year=assisted.observed_year,
            registration_status=assisted.observed_status,
            normalized_payload={
                "assisted_id": str(assisted.id),
                "observations": assisted.observations,
                "reviewed_by": str(assisted.reviewed_by),
                "approved_by": str(approver_id),
            },
        )
        self.db.add(res)

        # Create Evidence Record if reference provided
        if assisted.evidence_reference_id:
            ev = VehicleVerificationEvidenceModel(
                id=uuid4(),
                verification_id=verif.id,
                evidence_type="MANUAL_REVIEW_NOTE",
                file_reference_id=assisted.evidence_reference_id,
                captured_at=assisted.reviewed_at,
                captured_by=assisted.reviewed_by,
                status="ACTIVE",
            )
            self.db.add(ev)

        self.db.commit()

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle_verification.assisted_approved",
                severity="high",
                actor_user_id=approver_id,
                organization_id=organization_id,
                resource_type="assisted_vehicle_verification",
                resource_id=str(assisted.id),
                resource_code=assisted.observed_plate,
                new_data={"verification_id": str(verif.id)},
            ),
        )

        return verif

    def reject_assisted_verification(
        self,
        assisted_id: UUID,
        organization_id: UUID,
        rejector_id: UUID,
        rejection_reason: str,
    ) -> AssistedVehicleVerificationModel:
        assisted = self.db.scalars(
            select(AssistedVehicleVerificationModel).where(
                and_(
                    AssistedVehicleVerificationModel.id == assisted_id,
                    AssistedVehicleVerificationModel.organization_id == organization_id,
                )
            )
        ).first()

        if not assisted:
            raise HTTPException(status_code=404, detail="Verificación asistida no encontrada.")

        assisted.approval_status = AssistedApprovalStatus.REJECTED.value
        assisted.rejected_by = rejector_id
        assisted.rejected_at = utc_now()
        assisted.rejection_reason = rejection_reason
        self.db.commit()

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle_verification.assisted_rejected",
                severity="medium",
                actor_user_id=rejector_id,
                organization_id=organization_id,
                resource_type="assisted_vehicle_verification",
                resource_id=str(assisted.id),
                reason_text=rejection_reason,
            ),
        )

        return assisted
