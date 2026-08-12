"""Vehicle Capacity & Dimensions Service (Phase 027)."""

from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import and_, select, update
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.units.conversion_engine import UnitConversionEngine
from app.modules.logistics.vehicles.domain.errors.exceptions import (
    VehicleCapacityInvalidError,
    VehicleNotFoundError,
)
from app.modules.logistics.vehicles.infrastructure.persistence.models import (
    VehicleCapacityProfileModel,
    VehicleDimensionsModel,
    VehicleModel,
)


class VehicleCapacityService:
    def __init__(self, db: Session):
        self.db = db

    def create_capacity_profile(
        self,
        vehicle_id: UUID,
        organization_id: UUID,
        actor_id: UUID,
        max_gross_weight: Optional[Decimal] = None,
        max_gross_weight_unit_id: Optional[UUID] = None,
        tare_weight: Optional[Decimal] = None,
        tare_weight_unit_id: Optional[UUID] = None,
        max_payload: Optional[Decimal] = None,
        max_payload_unit_id: Optional[UUID] = None,
        max_volume: Optional[Decimal] = None,
        max_volume_unit_id: Optional[UUID] = None,
        pallet_positions: Optional[int] = None,
        axle_count: Optional[int] = None,
    ) -> VehicleCapacityProfileModel:
        vehicle = self.db.scalars(
            select(VehicleModel).where(
                and_(VehicleModel.id == vehicle_id, VehicleModel.organization_id == organization_id)
            )
        ).first()

        if not vehicle:
            raise VehicleNotFoundError(str(vehicle_id))

        # Validate Payload <= Gross Weight - Tare Weight if both are provided in same unit
        if max_gross_weight is not None and tare_weight is not None and max_payload is not None:
            if max_gross_weight_unit_id == tare_weight_unit_id == max_payload_unit_id:
                calc_payload = max_gross_weight - tare_weight
                if max_payload > calc_payload:
                    raise VehicleCapacityInvalidError(
                        f"La carga útil ({max_payload}) no puede ser mayor que Peso Bruto ({max_gross_weight}) - Tara ({tare_weight}) = {calc_payload}."
                    )

        # Supersede active profiles
        self.db.execute(
            update(VehicleCapacityProfileModel)
            .where(
                and_(
                    VehicleCapacityProfileModel.vehicle_id == vehicle_id,
                    VehicleCapacityProfileModel.status == "ACTIVE",
                )
            )
            .values(status="RETIRED", effective_to=utc_now())
        )

        profile = VehicleCapacityProfileModel(
            id=uuid4(),
            vehicle_id=vehicle_id,
            version=1,
            status="ACTIVE",
            maximum_gross_weight_value=max_gross_weight,
            maximum_gross_weight_unit_id=max_gross_weight_unit_id,
            tare_weight_value=tare_weight,
            tare_weight_unit_id=tare_weight_unit_id,
            maximum_payload_value=max_payload,
            maximum_payload_unit_id=max_payload_unit_id,
            maximum_volume_value=max_volume,
            maximum_volume_unit_id=max_volume_unit_id,
            pallet_position_count=pallet_positions,
            axle_count=axle_count,
            source_type="DECLARED",
            verified_status="NOT_VERIFIED",
            effective_from=utc_now(),
            created_by=actor_id,
        )
        self.db.add(profile)
        self.db.commit()

        vehicle.active_capacity_profile_id = profile.id
        self.db.commit()

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle.capacity_profile_created",
                severity="medium",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="vehicle_capacity_profile",
                resource_id=str(profile.id),
            ),
        )

        return profile

    def create_or_update_dimensions(
        self,
        vehicle_id: UUID,
        organization_id: UUID,
        dimension_unit_id: UUID,
        actor_id: UUID,
        ext_length: Optional[Decimal] = None,
        ext_width: Optional[Decimal] = None,
        ext_height: Optional[Decimal] = None,
        int_length: Optional[Decimal] = None,
        int_width: Optional[Decimal] = None,
        int_height: Optional[Decimal] = None,
        reported_volume: Optional[Decimal] = None,
    ) -> VehicleDimensionsModel:
        dims = self.db.scalars(
            select(VehicleDimensionsModel).where(VehicleDimensionsModel.vehicle_id == vehicle_id)
        ).first()

        calc_volume = None
        if int_length and int_width and int_height:
            calc_volume = int_length * int_width * int_height

        if not dims:
            dims = VehicleDimensionsModel(
                id=uuid4(),
                vehicle_id=vehicle_id,
                dimension_unit_id=dimension_unit_id,
                external_length_value=ext_length,
                external_width_value=ext_width,
                external_height_value=ext_height,
                internal_length_value=int_length,
                internal_width_value=int_width,
                internal_height_value=int_height,
                calculated_internal_volume=calc_volume,
                reported_internal_volume=reported_volume,
                source_type="DECLARED",
                verified_status="NOT_VERIFIED",
            )
            self.db.add(dims)
        else:
            dims.dimension_unit_id = dimension_unit_id
            dims.external_length_value = ext_length
            dims.external_width_value = ext_width
            dims.external_height_value = ext_height
            dims.internal_length_value = int_length
            dims.internal_width_value = int_width
            dims.internal_height_value = int_height
            dims.calculated_internal_volume = calc_volume
            dims.reported_internal_volume = reported_volume

        self.db.commit()
        return dims
