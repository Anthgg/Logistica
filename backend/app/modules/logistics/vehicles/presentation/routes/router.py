"""FastAPI Router definitions for Phase 027 (Master Vehicles Module)."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission, resolve_organization_id
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.vehicles.application.services.capacity_service import VehicleCapacityService
from app.modules.logistics.vehicles.application.services.document_service import VehicleDocumentService
from app.modules.logistics.vehicles.application.services.make_model_service import VehicleMakeModelService
from app.modules.logistics.vehicles.application.services.ownership_carrier_service import VehicleOwnershipCarrierService
from app.modules.logistics.vehicles.application.services.vehicle_service import VehicleService
from app.modules.logistics.vehicles.domain.services.services import VehicleVinService
from app.modules.logistics.vehicles.presentation.schemas.dto import (
    BlockVehicleRequestDTO,
    CapacityProfileCreateDTO,
    CapacityProfileResponseDTO,
    CarrierAssignmentCreateDTO,
    OwnerAssignmentCreateDTO,
    PlateChangeRequestDTO,
    VehicleCreateDTO,
    VehicleDocumentCreateDTO,
    VehicleDocumentResponseDTO,
    VehicleMakeCreateDTO,
    VehicleMakeResponseDTO,
    VehicleModelCreateDTO,
    VehicleModelResponseDTO,
    VehicleResponseDTO,
)

vehicles_router = APIRouter(prefix="/vehicles", tags=["Master Vehicles"])
makes_router = APIRouter(prefix="/vehicle-makes", tags=["Vehicle Makes & Models"])
models_router = APIRouter(prefix="/vehicle-models", tags=["Vehicle Makes & Models"])


# --- MAKES & MODELS ENDPOINTS ---

@makes_router.get("", response_model=List[VehicleMakeResponseDTO])
def get_makes(
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.vehicle_makes.read")),
):
    service = VehicleMakeModelService(db)
    return service.get_makes(resolve_organization_id(principal))


@makes_router.post("", response_model=VehicleMakeResponseDTO, status_code=status.HTTP_201_CREATED)
def create_make(
    data: VehicleMakeCreateDTO,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.vehicle_makes.manage")),
):
    service = VehicleMakeModelService(db)
    return service.create_make(
        organization_id=resolve_organization_id(principal),
        name=data.name,
        code=data.code,
        country_code=data.country_code,
        actor_id=principal.user_id,
    )


@makes_router.get("/{make_id}/models", response_model=List[VehicleModelResponseDTO])
def get_models_by_make(
    make_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.vehicle_models.read")),
):
    service = VehicleMakeModelService(db)
    return service.get_models_by_make(
        make_id=make_id,
        organization_id=resolve_organization_id(principal),
    )


@models_router.post("", response_model=VehicleModelResponseDTO, status_code=status.HTTP_201_CREATED)
def create_model(
    data: VehicleModelCreateDTO,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.vehicle_models.manage")),
):
    service = VehicleMakeModelService(db)
    return service.create_model(
        make_id=data.make_id,
        organization_id=resolve_organization_id(principal),
        name=data.name,
        code=data.code,
        vehicle_type=data.vehicle_type,
        body_type=data.body_type,
        actor_id=principal.user_id,
    )


# --- VEHICLES ENDPOINTS ---

@vehicles_router.post("", response_model=VehicleResponseDTO, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    data: VehicleCreateDTO,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.vehicles.create")),
):
    service = VehicleService(db)
    v = service.create_vehicle(
        organization_id=resolve_organization_id(principal),
        display_plate=data.display_plate,
        make_id=data.make_id,
        model_id=data.model_id,
        actor_id=principal.user_id,
        vehicle_code=data.vehicle_code,
        vin=data.vin,
        chassis_number=data.chassis_number,
        engine_number=data.engine_number,
        manufacturing_year=data.manufacturing_year,
        vehicle_type=data.vehicle_type,
        body_type=data.body_type,
        notes=data.notes,
    )
    res = VehicleResponseDTO.from_orm(v)
    res.masked_vin = VehicleVinService.mask_vin(v.vin)
    return res


@vehicles_router.get("/{vehicle_id}", response_model=VehicleResponseDTO)
def get_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.vehicles.read")),
):
    service = VehicleService(db)
    v = service.get_vehicle(vehicle_id, resolve_organization_id(principal))
    res = VehicleResponseDTO.from_orm(v)
    res.masked_vin = VehicleVinService.mask_vin(v.vin)
    return res


@vehicles_router.post("/{vehicle_id}/activate", response_model=VehicleResponseDTO)
def activate_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.vehicles.activate")),
):
    service = VehicleService(db)
    v = service.activate_vehicle(
        vehicle_id,
        resolve_organization_id(principal),
        principal.user_id,
    )
    res = VehicleResponseDTO.from_orm(v)
    res.masked_vin = VehicleVinService.mask_vin(v.vin)
    return res


@vehicles_router.post("/{vehicle_id}/block", response_model=VehicleResponseDTO)
def block_vehicle(
    vehicle_id: UUID,
    data: BlockVehicleRequestDTO,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.vehicles.block")),
):
    service = VehicleService(db)
    v = service.block_vehicle(
        vehicle_id,
        resolve_organization_id(principal),
        data.reason,
        principal.user_id,
    )
    res = VehicleResponseDTO.from_orm(v)
    res.masked_vin = VehicleVinService.mask_vin(v.vin)
    return res


@vehicles_router.post("/{vehicle_id}/unblock", response_model=VehicleResponseDTO)
def unblock_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.vehicles.block")),
):
    service = VehicleService(db)
    v = service.unblock_vehicle(
        vehicle_id,
        resolve_organization_id(principal),
        principal.user_id,
    )
    res = VehicleResponseDTO.from_orm(v)
    res.masked_vin = VehicleVinService.mask_vin(v.vin)
    return res


@vehicles_router.post("/{vehicle_id}/plate-change", response_model=VehicleResponseDTO)
def change_plate(
    vehicle_id: UUID,
    data: PlateChangeRequestDTO,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.vehicle_plates.change")),
):
    service = VehicleService(db)
    v = service.change_plate(
        vehicle_id=vehicle_id,
        organization_id=resolve_organization_id(principal),
        new_display_plate=data.new_display_plate,
        reason=data.reason,
        actor_id=principal.user_id,
    )
    res = VehicleResponseDTO.from_orm(v)
    res.masked_vin = VehicleVinService.mask_vin(v.vin)
    return res


@vehicles_router.post("/{vehicle_id}/capacity-profiles", response_model=CapacityProfileResponseDTO, status_code=status.HTTP_201_CREATED)
def create_capacity_profile(
    vehicle_id: UUID,
    data: CapacityProfileCreateDTO,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.vehicle_capacity.manage")),
):
    service = VehicleCapacityService(db)
    return service.create_capacity_profile(
        vehicle_id=vehicle_id,
        organization_id=resolve_organization_id(principal),
        actor_id=principal.user_id,
        max_gross_weight=data.max_gross_weight,
        max_gross_weight_unit_id=data.max_gross_weight_unit_id,
        tare_weight=data.tare_weight,
        tare_weight_unit_id=data.tare_weight_unit_id,
        max_payload=data.max_payload,
        max_payload_unit_id=data.max_payload_unit_id,
        max_volume=data.max_volume,
        max_volume_unit_id=data.max_volume_unit_id,
        pallet_positions=data.pallet_positions,
        axle_count=data.axle_count,
    )


@vehicles_router.post("/{vehicle_id}/owner-assignments", status_code=status.HTTP_201_CREATED)
def assign_owner(
    vehicle_id: UUID,
    data: OwnerAssignmentCreateDTO,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.vehicle_ownership.manage")),
):
    service = VehicleOwnershipCarrierService(db)
    return service.assign_owner(
        vehicle_id=vehicle_id,
        organization_id=resolve_organization_id(principal),
        owner_type=data.owner_type,
        actor_id=principal.user_id,
        owner_business_partner_id=data.owner_business_partner_id,
        ownership_type=data.ownership_type,
        contract_reference=data.contract_reference,
    )


@vehicles_router.post("/{vehicle_id}/carrier-assignments", status_code=status.HTTP_201_CREATED)
def assign_carrier(
    vehicle_id: UUID,
    data: CarrierAssignmentCreateDTO,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.vehicle_carrier_assignments.manage")
    ),
):
    service = VehicleOwnershipCarrierService(db)
    return service.assign_carrier(
        vehicle_id=vehicle_id,
        organization_id=resolve_organization_id(principal),
        carrier_business_partner_id=data.carrier_business_partner_id,
        actor_id=principal.user_id,
        assignment_type=data.assignment_type,
        authorization_reference=data.authorization_reference,
    )


@vehicles_router.post("/{vehicle_id}/documents", response_model=VehicleDocumentResponseDTO, status_code=status.HTTP_201_CREATED)
def add_document(
    vehicle_id: UUID,
    data: VehicleDocumentCreateDTO,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.vehicle_documents.create")),
):
    service = VehicleDocumentService(db)
    return service.add_document(
        vehicle_id=vehicle_id,
        organization_id=resolve_organization_id(principal),
        document_type=data.document_type,
        actor_id=principal.user_id,
        document_number=data.document_number,
        issuer=data.issuer,
        issued_at=data.issued_at,
        valid_from=data.valid_from,
        expires_at=data.expires_at,
        file_reference_id=data.file_reference_id,
        notes=data.notes,
    )


@vehicles_router.get("/{vehicle_id}/documents", response_model=List[VehicleDocumentResponseDTO])
def get_vehicle_documents(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.vehicle_documents.read")),
):
    service = VehicleDocumentService(db)
    return service.list_vehicle_documents(
        vehicle_id,
        resolve_organization_id(principal),
    )
