"""Pydantic V2 Schemas for Phase 027 (Vehicles Module)."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.logistics.vehicles.domain.value_objects.enums import (
    BodyType,
    VehicleComplianceStatus,
    VehicleLifecycleStatus,
    VehicleOperationalStatus,
    VehicleType,
)


class VehicleMakeCreateDTO(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    country_code: Optional[str] = Field(None, max_length=3)


class VehicleMakeResponseDTO(BaseModel):
    id: UUID
    code: str
    name: str
    normalized_name: str
    country_code: Optional[str]
    status: str
    system_defined: bool

    class Config:
        from_attributes = True


class VehicleModelCreateDTO(BaseModel):
    make_id: UUID
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    vehicle_type: Optional[str] = None
    body_type: Optional[str] = None


class VehicleModelResponseDTO(BaseModel):
    id: UUID
    make_id: UUID
    code: str
    name: str
    normalized_name: str
    vehicle_type: Optional[str]
    body_type: Optional[str]
    status: str
    system_defined: bool

    class Config:
        from_attributes = True


class VehicleCreateDTO(BaseModel):
    display_plate: str = Field(..., max_length=20)
    make_id: UUID
    model_id: UUID
    vehicle_code: Optional[str] = Field(None, max_length=50)
    vin: Optional[str] = Field(None, max_length=30)
    chassis_number: Optional[str] = Field(None, max_length=50)
    engine_number: Optional[str] = Field(None, max_length=50)
    manufacturing_year: Optional[int] = None
    vehicle_type: str = VehicleType.HEAVY_TRUCK.value
    body_type: str = BodyType.CLOSED_BOX.value
    notes: Optional[str] = None


class VehicleResponseDTO(BaseModel):
    id: UUID
    organization_id: UUID
    vehicle_code: str
    display_plate: str
    normalized_plate: str
    masked_vin: Optional[str] = None
    make_id: UUID
    model_id: UUID
    manufacturing_year: Optional[int]
    vehicle_type: str
    body_type: str
    lifecycle_status: str
    operational_status: str
    compliance_status: str
    ownership_type: str
    active_capacity_profile_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    row_version: int

    class Config:
        from_attributes = True


class CapacityProfileCreateDTO(BaseModel):
    max_gross_weight: Optional[Decimal] = None
    max_gross_weight_unit_id: Optional[UUID] = None
    tare_weight: Optional[Decimal] = None
    tare_weight_unit_id: Optional[UUID] = None
    max_payload: Optional[Decimal] = None
    max_payload_unit_id: Optional[UUID] = None
    max_volume: Optional[Decimal] = None
    max_volume_unit_id: Optional[UUID] = None
    pallet_positions: Optional[int] = None
    axle_count: Optional[int] = None


class CapacityProfileResponseDTO(BaseModel):
    id: UUID
    vehicle_id: UUID
    version: int
    status: str
    maximum_gross_weight_value: Optional[Decimal]
    maximum_gross_weight_unit_id: Optional[UUID]
    tare_weight_value: Optional[Decimal]
    tare_weight_unit_id: Optional[UUID]
    maximum_payload_value: Optional[Decimal]
    maximum_payload_unit_id: Optional[UUID]
    maximum_volume_value: Optional[Decimal]
    maximum_volume_unit_id: Optional[UUID]
    pallet_position_count: Optional[int]
    effective_from: datetime

    class Config:
        from_attributes = True


class OwnerAssignmentCreateDTO(BaseModel):
    owner_type: str = Field(..., description="INTERNAL_ORGANIZATION or BUSINESS_PARTNER")
    owner_business_partner_id: Optional[UUID] = None
    ownership_type: str = "OWNED"
    contract_reference: Optional[str] = None


class CarrierAssignmentCreateDTO(BaseModel):
    carrier_business_partner_id: UUID
    assignment_type: str = "OWN_FLEET"
    authorization_reference: Optional[str] = None


class VehicleDocumentCreateDTO(BaseModel):
    document_type: str
    document_number: Optional[str] = None
    issuer: Optional[str] = None
    issued_at: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    file_reference_id: Optional[str] = None
    notes: Optional[str] = None


class VehicleDocumentResponseDTO(BaseModel):
    id: UUID
    vehicle_id: UUID
    document_type: str
    document_number: Optional[str]
    issuer: Optional[str]
    expires_at: Optional[datetime]
    verification_status: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PlateChangeRequestDTO(BaseModel):
    new_display_plate: str = Field(..., max_length=20)
    reason: str = Field(..., min_length=3)


class BlockVehicleRequestDTO(BaseModel):
    reason: str = Field(..., min_length=3)
