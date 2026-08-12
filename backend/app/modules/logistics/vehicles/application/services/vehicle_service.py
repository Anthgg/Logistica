"""VehicleService — Core Vehicle CRUD, lifecycle, plate change, versioning, and status resolution (Phase 027)."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import and_, func, select, update
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.vehicles.domain.errors.exceptions import (
    VehicleBlockedError,
    VehicleCannotBeActivatedError,
    VehicleCodeConflictError,
    VehicleMakeNotFoundError,
    VehicleModelMakeMismatchError,
    VehicleModelNotFoundError,
    VehicleNotFoundError,
    VehiclePlateConflictError,
    VehiclePlateInvalidError,
    VehicleVinConflictError,
    VehicleVinInvalidError,
)
from app.modules.logistics.vehicles.domain.services.services import (
    VehicleCodeService,
    VehicleOperationalStatusResolver,
    VehiclePlateService,
    VehicleSnapshotProvider,
    VehicleVinService,
)
from app.modules.logistics.vehicles.domain.value_objects.enums import (
    BodyType,
    VehicleLifecycleStatus,
    VehicleOperationalStatus,
    VehicleType,
)
from app.modules.logistics.vehicles.infrastructure.persistence.models import (
    VehicleAliasModel,
    VehicleCarrierAssignmentModel,
    VehicleCapacityProfileModel,
    VehicleDimensionsModel,
    VehicleDocumentModel,
    VehicleMakeModel,
    VehicleModel,
    VehicleModelModel,
    VehicleOperationalRestrictionModel,
    VehicleOwnershipAssignmentModel,
    VehiclePlateAssignmentModel,
    VehicleVersionModel,
)


class VehicleService:
    def __init__(self, db: Session):
        self.db = db

    def generate_next_code(self, organization_id: UUID) -> str:
        count = self.db.scalar(
            select(func.count(VehicleModel.id)).where(VehicleModel.organization_id == organization_id)
        ) or 0
        return VehicleCodeService.format_code(count + 1)

    def create_vehicle(
        self,
        organization_id: UUID,
        display_plate: str,
        make_id: UUID,
        model_id: UUID,
        actor_id: UUID,
        vehicle_code: Optional[str] = None,
        vin: Optional[str] = None,
        chassis_number: Optional[str] = None,
        engine_number: Optional[str] = None,
        manufacturing_year: Optional[int] = None,
        vehicle_type: str = VehicleType.HEAVY_TRUCK.value,
        body_type: str = BodyType.CLOSED_BOX.value,
        notes: Optional[str] = None,
    ) -> VehicleModel:
        # Validate Plate
        if not VehiclePlateService.validate_format(display_plate):
            raise VehiclePlateInvalidError(display_plate)

        norm_plate = VehiclePlateService.normalize(display_plate)
        existing_plate = self.db.scalars(
            select(VehicleModel).where(
                and_(
                    VehicleModel.organization_id == organization_id,
                    VehicleModel.normalized_plate == norm_plate,
                    VehicleModel.lifecycle_status != VehicleLifecycleStatus.ARCHIVED.value,
                )
            )
        ).first()

        if existing_plate:
            raise VehiclePlateConflictError(display_plate)

        # Validate VIN if provided
        norm_vin = VehicleVinService.normalize(vin)
        if vin and not VehicleVinService.validate_format(vin):
            raise VehicleVinInvalidError(vin)

        if norm_vin:
            existing_vin = self.db.scalars(
                select(VehicleModel).where(
                    and_(
                        VehicleModel.organization_id == organization_id,
                        VehicleModel.normalized_vin == norm_vin,
                        VehicleModel.lifecycle_status != VehicleLifecycleStatus.ARCHIVED.value,
                    )
                )
            ).first()

            if existing_vin:
                raise VehicleVinConflictError(vin)

        # Validate Make & Model
        make = self.db.get(VehicleMakeModel, make_id)
        if not make:
            raise VehicleMakeNotFoundError(str(make_id))

        model = self.db.get(VehicleModelModel, model_id)
        if not model:
            raise VehicleModelNotFoundError(str(model_id))

        if model.make_id != make.id:
            raise VehicleModelMakeMismatchError(str(model_id), str(make_id))

        # Generate Code
        code = VehicleCodeService.normalize(vehicle_code) if vehicle_code else self.generate_next_code(organization_id)
        existing_code = self.db.scalars(
            select(VehicleModel).where(
                and_(VehicleModel.organization_id == organization_id, VehicleModel.normalized_vehicle_code == code)
            )
        ).first()

        if existing_code:
            raise VehicleCodeConflictError(code)

        vehicle = VehicleModel(
            id=uuid4(),
            organization_id=organization_id,
            vehicle_code=code,
            normalized_vehicle_code=code,
            display_plate=VehiclePlateService.format_display(display_plate),
            normalized_plate=norm_plate,
            vin=norm_vin,
            normalized_vin=norm_vin,
            chassis_number=chassis_number,
            engine_number=engine_number,
            make_id=make.id,
            model_id=model.id,
            manufacturing_year=manufacturing_year,
            vehicle_type=vehicle_type,
            body_type=body_type,
            lifecycle_status=VehicleLifecycleStatus.DRAFT.value,
            operational_status=VehicleOperationalStatus.UNAVAILABLE.value,
            notes=notes,
            created_by=actor_id,
        )
        self.db.add(vehicle)
        self.db.commit()

        # Create Initial Plate Assignment
        plate_assignment = VehiclePlateAssignmentModel(
            id=uuid4(),
            vehicle_id=vehicle.id,
            display_plate=vehicle.display_plate,
            normalized_plate=vehicle.normalized_plate,
            assignment_type="INITIAL",
            status="CURRENT",
            valid_from=utc_now(),
            reason="Registro inicial del vehículo",
            created_by=actor_id,
        )
        self.db.add(plate_assignment)
        self.db.commit()

        # Create Initial Version
        self._create_version_snapshot(vehicle, actor_id)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle.created",
                severity="medium",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="vehicle",
                resource_id=str(vehicle.id),
                resource_code=vehicle.vehicle_code,
                new_data={"code": vehicle.vehicle_code, "plate": vehicle.display_plate},
            ),
        )

        return vehicle

    def get_vehicle(self, vehicle_id: UUID, organization_id: UUID) -> VehicleModel:
        v = self.db.scalars(
            select(VehicleModel).where(
                and_(VehicleModel.id == vehicle_id, VehicleModel.organization_id == organization_id)
            )
        ).first()

        if not v:
            raise VehicleNotFoundError(str(vehicle_id))

        self.refresh_operational_status(v)
        return v

    def refresh_operational_status(self, vehicle: VehicleModel) -> VehicleModel:
        # Check active carrier
        carrier_ass = self.db.scalars(
            select(VehicleCarrierAssignmentModel).where(
                and_(
                    VehicleCarrierAssignmentModel.vehicle_id == vehicle.id,
                    VehicleCarrierAssignmentModel.status == "CURRENT",
                )
            )
        ).first()

        has_carrier = carrier_ass is not None

        # Check manual restriction/block
        restr = self.db.scalars(
            select(VehicleOperationalRestrictionModel).where(
                and_(
                    VehicleOperationalRestrictionModel.vehicle_id == vehicle.id,
                    VehicleOperationalRestrictionModel.status == "ACTIVE",
                )
            )
        ).first()

        is_blocked = restr is not None and restr.restriction_type == "MANUAL_BLOCK"
        is_maintenance = restr is not None and restr.restriction_type == "MAINTENANCE"

        # Check expired documents
        now = utc_now()
        expired_doc = self.db.scalars(
            select(VehicleDocumentModel).where(
                and_(
                    VehicleDocumentModel.vehicle_id == vehicle.id,
                    VehicleDocumentModel.status == "ACTIVE",
                    VehicleDocumentModel.expires_at.is_not(None),
                    VehicleDocumentModel.expires_at < now,
                )
            )
        ).first()

        has_expired = expired_doc is not None

        op_status, comp_status, _ = VehicleOperationalStatusResolver.resolve(
            lifecycle_status=vehicle.lifecycle_status,
            is_blocked=is_blocked,
            is_maintenance=is_maintenance,
            has_active_carrier=has_carrier,
            has_expired_required_docs=has_expired,
            has_missing_required_docs=False,
        )

        if vehicle.operational_status != op_status.value or vehicle.compliance_status != comp_status.value:
            vehicle.operational_status = op_status.value
            vehicle.compliance_status = comp_status.value
            self.db.commit()

        return vehicle

    def activate_vehicle(self, vehicle_id: UUID, organization_id: UUID, actor_id: UUID) -> VehicleModel:
        v = self.get_vehicle(vehicle_id, organization_id)
        if v.lifecycle_status not in [VehicleLifecycleStatus.DRAFT.value, VehicleLifecycleStatus.INACTIVE.value, VehicleLifecycleStatus.SUSPENDED.value]:
            raise VehicleCannotBeActivatedError(f"No se puede activar en estado '{v.lifecycle_status}'.")

        v.lifecycle_status = VehicleLifecycleStatus.ACTIVE.value
        self.refresh_operational_status(v)
        v.row_version += 1

        self._create_version_snapshot(v, actor_id)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle.activated",
                severity="high",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="vehicle",
                resource_id=str(v.id),
                resource_code=v.vehicle_code,
            ),
        )

        return v

    def block_vehicle(self, vehicle_id: UUID, organization_id: UUID, reason: str, actor_id: UUID) -> VehicleModel:
        v = self.get_vehicle(vehicle_id, organization_id)

        restr = VehicleOperationalRestrictionModel(
            id=uuid4(),
            vehicle_id=v.id,
            restriction_type="MANUAL_BLOCK",
            reason=reason,
            start_date=utc_now(),
            status="ACTIVE",
            created_by=actor_id,
        )
        self.db.add(restr)
        self.db.commit()

        self.refresh_operational_status(v)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle.blocked",
                severity="critical",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="vehicle",
                resource_id=str(v.id),
                resource_code=v.vehicle_code,
                reason_text=reason,
            ),
        )

        return v

    def unblock_vehicle(self, vehicle_id: UUID, organization_id: UUID, actor_id: UUID) -> VehicleModel:
        v = self.get_vehicle(vehicle_id, organization_id)

        self.db.execute(
            update(VehicleOperationalRestrictionModel)
            .where(
                and_(
                    VehicleOperationalRestrictionModel.vehicle_id == v.id,
                    VehicleOperationalRestrictionModel.restriction_type == "MANUAL_BLOCK",
                    VehicleOperationalRestrictionModel.status == "ACTIVE",
                )
            )
            .values(status="RESOLVED", resolved_by=actor_id, resolved_at=utc_now())
        )
        self.db.commit()

        self.refresh_operational_status(v)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle.unblocked",
                severity="critical",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="vehicle",
                resource_id=str(v.id),
                resource_code=v.vehicle_code,
            ),
        )

        return v

    def change_plate(
        self,
        vehicle_id: UUID,
        organization_id: UUID,
        new_display_plate: str,
        reason: str,
        actor_id: UUID,
    ) -> VehicleModel:
        v = self.get_vehicle(vehicle_id, organization_id)

        if not VehiclePlateService.validate_format(new_display_plate):
            raise VehiclePlateInvalidError(new_display_plate)

        new_norm = VehiclePlateService.normalize(new_display_plate)

        if new_norm == v.normalized_plate:
            return v

        # Check plate conflicts
        existing = self.db.scalars(
            select(VehicleModel).where(
                and_(
                    VehicleModel.organization_id == organization_id,
                    VehicleModel.normalized_plate == new_norm,
                    VehicleModel.id != v.id,
                    VehicleModel.lifecycle_status != VehicleLifecycleStatus.ARCHIVED.value,
                )
            )
        ).first()

        if existing:
            raise VehiclePlateConflictError(new_display_plate)

        old_display = v.display_plate
        old_norm = v.normalized_plate

        # Supersede current plate assignment
        self.db.execute(
            update(VehiclePlateAssignmentModel)
            .where(
                and_(
                    VehiclePlateAssignmentModel.vehicle_id == v.id,
                    VehiclePlateAssignmentModel.status == "CURRENT",
                )
            )
            .values(status="SUPERSEDED", valid_until=utc_now())
        )

        # New Plate Assignment
        new_assignment = VehiclePlateAssignmentModel(
            id=uuid4(),
            vehicle_id=v.id,
            display_plate=VehiclePlateService.format_display(new_display_plate),
            normalized_plate=new_norm,
            assignment_type="REPLACEMENT",
            status="CURRENT",
            valid_from=utc_now(),
            reason=reason,
            created_by=actor_id,
        )
        self.db.add(new_assignment)

        # Create Historical Alias
        alias = VehicleAliasModel(
            id=uuid4(),
            vehicle_id=v.id,
            alias_type="PLATE",
            previous_value=old_display,
            current_value=new_assignment.display_plate,
            reason=reason,
            valid_from=utc_now(),
            created_by=actor_id,
        )
        self.db.add(alias)

        v.display_plate = new_assignment.display_plate
        v.normalized_plate = new_norm
        v.row_version += 1
        self.db.commit()

        self._create_version_snapshot(v, actor_id)

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle.plate_changed",
                severity="high",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="vehicle",
                resource_id=str(v.id),
                resource_code=v.vehicle_code,
                previous_data={"plate": old_display},
                new_data={"plate": v.display_plate},
                reason_text=reason,
            ),
        )

        return v

    def _create_version_snapshot(self, vehicle: VehicleModel, actor_id: UUID) -> VehicleVersionModel:
        make = self.db.get(VehicleMakeModel, vehicle.make_id)
        model = self.db.get(VehicleModelModel, vehicle.model_id)

        payload = VehicleSnapshotProvider.build_snapshot_payload(
            vehicle_code=vehicle.vehicle_code,
            plate=vehicle.display_plate,
            vin=vehicle.vin,
            make_name=make.name if make else "",
            model_name=model.name if model else "",
            vehicle_type=vehicle.vehicle_type,
            body_type=vehicle.body_type,
            capacity_dict=None,
            dimensions_dict=None,
            owner_dict=None,
            carrier_dict=None,
        )

        chash = VehicleSnapshotProvider.calculate_content_hash(payload)
        version_str = f"1.0.{vehicle.row_version}"

        # Deprecate older version
        self.db.execute(
            update(VehicleVersionModel)
            .where(
                and_(
                    VehicleVersionModel.vehicle_id == vehicle.id,
                    VehicleVersionModel.status == "ACTIVE",
                )
            )
            .values(status="DEPRECATED", effective_to=utc_now())
        )

        ver = VehicleVersionModel(
            id=uuid4(),
            vehicle_id=vehicle.id,
            version=version_str,
            status="ACTIVE",
            vehicle_code=vehicle.vehicle_code,
            plate_snapshot=vehicle.display_plate,
            vin_snapshot=vehicle.vin,
            make_snapshot=make.name if make else "",
            model_snapshot=model.name if model else "",
            vehicle_type=vehicle.vehicle_type,
            body_type=vehicle.body_type,
            capacity_snapshot=payload["capacity"],
            dimensions_snapshot=payload["dimensions"],
            ownership_snapshot=payload["owner"],
            carrier_snapshot=payload["carrier"],
            content_hash=chash,
            effective_from=utc_now(),
            created_by=actor_id,
        )
        self.db.add(ver)
        self.db.commit()

        vehicle.active_version_id = ver.id
        self.db.commit()
        return ver
