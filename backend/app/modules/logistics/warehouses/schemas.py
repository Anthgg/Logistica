"""Pydantic v2 schemas for Phase 022 — Warehouses & Locations Hierarchy."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- WAREHOUSE SCHEMAS ---
class WarehouseCreate(BaseModel):
    branch_id: UUID
    code: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=2, max_length=150)
    description: str | None = None
    warehouse_type: str = "GENERAL"
    address: str | None = None
    address_id: UUID | None = None
    district: str | None = None
    province: str | None = None
    department: str | None = None
    capacity: Decimal | None = None
    manager_user_id: UUID | None = None
    operating_hours: dict[str, Any] | None = None
    temperature_controlled: bool = False
    hazardous_materials_allowed: bool = False
    cross_dock_enabled: bool = False
    receiving_enabled: bool = True
    dispatch_enabled: bool = True
    inventory_enabled: bool = True
    is_default: bool = False


class WarehouseUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    warehouse_type: str | None = None
    address: str | None = None
    address_id: UUID | None = None
    district: str | None = None
    province: str | None = None
    department: str | None = None
    capacity: Decimal | None = None
    manager_user_id: UUID | None = None
    operating_hours: dict[str, Any] | None = None
    temperature_controlled: bool | None = None
    hazardous_materials_allowed: bool | None = None
    cross_dock_enabled: bool | None = None
    receiving_enabled: bool | None = None
    dispatch_enabled: bool | None = None
    inventory_enabled: bool | None = None
    is_default: bool | None = None


class WarehouseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID | None
    branch_id: UUID | None
    code: str
    name: str
    description: str | None
    warehouse_type: str
    address: str | None
    address_id: UUID | None
    district: str | None
    province: str | None
    department: str | None
    capacity: Decimal | None
    status: str
    layout_status: str
    manager_user_id: UUID | None
    operating_hours: dict[str, Any] | None
    temperature_controlled: bool
    hazardous_materials_allowed: bool
    cross_dock_enabled: bool
    receiving_enabled: bool
    dispatch_enabled: bool
    inventory_enabled: bool
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- WAREHOUSE LOCATION SCHEMAS ---
class WarehouseLocationCreate(BaseModel):
    warehouse_id: UUID
    parent_location_id: UUID | None = None
    location_type: str
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    sequence_order: int = 1
    status: str = "ACTIVE"
    usage_type: str = "GENERAL_STORAGE"
    picking_priority: int | None = None
    putaway_priority: int | None = None
    is_pickable: bool = True
    is_receivable: bool = True
    is_dispatchable: bool = True
    is_countable: bool = True
    is_locked: bool = False
    lock_reason: str | None = None
    layout_x: Decimal | None = None
    layout_y: Decimal | None = None
    layout_width: Decimal | None = None
    layout_height: Decimal | None = None
    layout_rotation: Decimal | None = None
    floor_index: int = 1


class WarehouseLocationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sequence_order: int | None = None
    status: str | None = None
    usage_type: str | None = None
    picking_priority: int | None = None
    putaway_priority: int | None = None
    is_pickable: bool | None = None
    is_receivable: bool | None = None
    is_dispatchable: bool | None = None
    is_countable: bool | None = None
    is_locked: bool | None = None
    lock_reason: str | None = None
    layout_x: Decimal | None = None
    layout_y: Decimal | None = None
    layout_width: Decimal | None = None
    layout_height: Decimal | None = None
    layout_rotation: Decimal | None = None
    floor_index: int | None = None


class WarehouseLocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    branch_id: UUID
    warehouse_id: UUID
    parent_location_id: UUID | None
    location_type: str
    code: str
    full_code: str
    name: str
    description: str | None
    hierarchy_path: str
    depth: int
    sequence_order: int
    status: str
    usage_type: str
    picking_priority: int | None
    putaway_priority: int | None
    is_pickable: bool
    is_receivable: bool
    is_dispatchable: bool
    is_countable: bool
    is_locked: bool
    lock_reason: str | None
    layout_x: Decimal | None
    layout_y: Decimal | None
    layout_width: Decimal | None
    layout_height: Decimal | None
    layout_rotation: Decimal | None
    floor_index: int
    created_at: datetime
    updated_at: datetime


class WarehouseLocationMoveRequest(BaseModel):
    new_parent_location_id: UUID | None = None
    reason: str = Field(..., min_length=3)


class WarehouseLocationMovePreviewResponse(BaseModel):
    location_id: UUID
    current_parent_id: UUID | None
    new_parent_id: UUID | None
    current_full_code: str
    proposed_full_code: str
    descendants_affected_count: int
    warnings: list[str]
    is_move_allowed: bool


# --- BULK GENERATION SCHEMAS ---
class WarehouseLocationBulkPreviewRequest(BaseModel):
    warehouse_id: UUID
    parent_location_id: UUID | None = None
    zone_code: str | None = None
    aisle_count: int = Field(0, ge=0, le=50)
    aisle_start: int = 1
    aisle_end: int = 1
    rack_count: int = Field(0, ge=0, le=50)
    rack_start: int = 1
    rack_end: int = 1
    level_count: int = Field(0, ge=0, le=20)
    level_start: int = 1
    level_end: int = 1
    position_count: int = Field(0, ge=0, le=50)
    position_start: int = 1
    position_end: int = 1
    padding_length: int = 2


class WarehouseLocationBulkExecuteRequest(BaseModel):
    idempotency_key: str = Field(..., min_length=8)
    request_hash: str = Field(..., min_length=64, max_length=64)
    preview_request: WarehouseLocationBulkPreviewRequest


# --- CAPACITY & RESTRICTION SCHEMAS ---
class WarehouseLocationCapacityCreate(BaseModel):
    capacity_type: str
    maximum_value: Decimal
    unit_code: str
    warning_threshold: Decimal | None = None
    critical_threshold: Decimal | None = None


class WarehouseLocationCapacityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    location_id: UUID
    capacity_type: str
    maximum_value: Decimal
    unit_code: str
    warning_threshold: Decimal | None
    critical_threshold: Decimal | None
    status: str
    effective_from: datetime
    effective_to: datetime | None


class WarehouseLocationRestrictionCreate(BaseModel):
    restriction_type: str
    operator: str = "EQUALS"
    value_payload: dict[str, Any] | None = None
    severity: str = "MEDIUM"
    is_blocking: bool = True
    reason: str | None = None


class WarehouseLocationRestrictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    location_id: UUID
    restriction_type: str
    operator: str
    value_payload: dict[str, Any] | None
    severity: str
    is_blocking: bool
    reason: str | None
    status: str
    effective_from: datetime
    effective_to: datetime | None


# --- LAYOUT SCHEMAS ---
class WarehouseLayoutVersionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    canvas_width: Decimal = Decimal("1000.00")
    canvas_height: Decimal = Decimal("1000.00")
    floor_count: int = 1


class WarehouseLayoutNodeCreate(BaseModel):
    location_id: UUID | None = None
    floor_index: int = 1
    x: Decimal
    y: Decimal
    width: Decimal
    height: Decimal
    rotation_degrees: Decimal = Decimal("0.00")
    shape_type: str = "RECTANGLE"
    z_index: int = 1
    label_position: str = "CENTER"


class WarehouseLocationQRRotateRequest(BaseModel):
    reason: str = Field(..., min_length=3)
