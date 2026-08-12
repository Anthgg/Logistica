"""ApplyVehicleVerificationResult Application Service (Phase 028)."""

from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.vehicle_verifications.domain.errors.exceptions import (
    VehicleVerificationApplicationConflict,
    VehicleVerificationNotFound,
)
from app.modules.logistics.vehicle_verifications.domain.value_objects.enums import ConflictStatus
from app.modules.logistics.vehicle_verifications.infrastructure.persistence.models import (
    VehicleVerificationConflictModel,
    VehicleVerificationModel,
    VehicleVerificationResultModel,
)
from app.modules.logistics.vehicles.application.services.vehicle_service import VehicleService
from app.modules.logistics.vehicles.infrastructure.persistence.models import (
    VehicleMakeModel,
    VehicleModel,
    VehicleModelModel,
    VehicleVersionModel,
)


class ApplyVehicleVerificationService:
    def __init__(self, db: Session):
        self.db = db
        self.vehicle_service = VehicleService(db)

    def apply_verified_fields(
        self,
        verification_id: UUID,
        organization_id: UUID,
        selected_fields: List[str],  # e.g. ["make", "model", "manufacturing_year", "vin"]
        reason: str,
        actor_id: UUID,
    ) -> VehicleVersionModel:
        verif = self.db.scalars(
            select(VehicleVerificationModel).where(
                and_(VehicleVerificationModel.id == verification_id, VehicleVerificationModel.organization_id == organization_id)
            )
        ).first()

        if not verif:
            raise VehicleVerificationNotFound(str(verification_id))

        if "plate" in selected_fields:
            raise VehicleVerificationApplicationConflict(
                "La placa del vehículo no se puede modificar a través del aplicador de verificaciones. Utilice el flujo de cambio de placa de la Fase 027."
            )

        res = self.db.scalars(
            select(VehicleVerificationResultModel).where(VehicleVerificationResultModel.verification_id == verif.id)
        ).first()

        if not res:
            raise HTTPException(status_code=404, detail="Resultado de verificación no encontrado para aplicar.")

        vehicle = self.db.get(VehicleModel, verif.vehicle_id)

        # Apply selected fields
        modified = False

        if "manufacturing_year" in selected_fields and res.manufacturing_year:
            vehicle.manufacturing_year = res.manufacturing_year
            modified = True

        if "vin" in selected_fields and res.vin_masked:
            # Enmascarado de VIN respetando regla
            vehicle.vin = res.vin_masked
            vehicle.normalized_vin = res.vin_masked.replace("*", "").upper()
            modified = True

        if "chassis_number" in selected_fields and res.chassis_masked:
            vehicle.chassis_number = res.chassis_masked
            modified = True

        if "engine_number" in selected_fields and res.engine_number_masked:
            vehicle.engine_number = res.engine_number_masked
            modified = True

        if modified:
            vehicle.row_version += 1
            self.db.commit()

        # Create new version snapshot via VehicleService
        new_version = self.vehicle_service._create_version_snapshot(vehicle, actor_id)

        # Resolve related open conflicts if any
        conflicts = self.db.scalars(
            select(VehicleVerificationConflictModel).where(
                and_(
                    VehicleVerificationConflictModel.verification_id == verif.id,
                    VehicleVerificationConflictModel.status == ConflictStatus.OPEN.value,
                )
            )
        ).all()

        for c in conflicts:
            c.status = ConflictStatus.RESOLVED_APPLY_VERIFIED.value
            c.resolution = "APPLIED_VERIFIED_FIELDS"
            c.resolution_reason = reason
            c.reviewed_by = actor_id
            c.reviewed_at = utc_now()
            c.applied_vehicle_version_id = new_version.id

        self.db.commit()

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle_verification.data_applied",
                severity="high",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="vehicle",
                resource_id=str(vehicle.id),
                resource_code=vehicle.vehicle_code,
                new_data={"selected_fields": selected_fields, "new_version_id": str(new_version.id)},
                reason_text=reason,
            ),
        )

        return new_version
