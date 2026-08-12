"""Pydantic v2 schemas for Phase 023 — Product Catalog."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Category Schemas ---
class ProductCategoryCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    parent_category_id: Optional[UUID] = None


class ProductCategoryResponse(BaseModel):
    id: UUID
    organization_id: UUID
    parent_category_id: Optional[UUID] = None
    code: str
    name: str
    description: Optional[str] = None
    hierarchy_path: str
    depth: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductCategoryTreeNode(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    hierarchy_path: str
    depth: int
    status: str
    children: List["ProductCategoryTreeNode"] = []


# --- Brand Schemas ---
class ProductBrandCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    manufacturer_name: Optional[str] = None
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)


class ProductBrandResponse(BaseModel):
    id: UUID
    organization_id: UUID
    code: str
    name: str
    normalized_name: str
    description: Optional[str] = None
    manufacturer_name: Optional[str] = None
    country_code: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Identifier Schemas ---
class ProductIdentifierCreate(BaseModel):
    identifier_type: str = Field(..., description="INTERNAL_BARCODE, GTIN_8, GTIN_12, GTIN_13, GTIN_14, EAN_13, UPC_A, etc.")
    value: str = Field(..., min_length=1, max_length=100)
    is_primary: bool = False
    symbology: Optional[str] = "CODE128"
    issuer: Optional[str] = None


class ProductIdentifierResponse(BaseModel):
    id: UUID
    organization_id: UUID
    product_id: UUID
    identifier_type: str
    value: str
    normalized_value: str
    symbology: Optional[str] = None
    issuer: Optional[str] = None
    is_primary: bool
    status: str
    verified_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Physical Profile Schemas ---
class ProductPhysicalProfileUpdate(BaseModel):
    net_weight_value: Optional[Decimal] = None
    net_weight_unit: Optional[str] = "KG"
    gross_weight_value: Optional[Decimal] = None
    gross_weight_unit: Optional[str] = "KG"
    length_value: Optional[Decimal] = None
    width_value: Optional[Decimal] = None
    height_value: Optional[Decimal] = None
    dimension_unit: Optional[str] = "CM"
    reported_volume_value: Optional[Decimal] = None
    volume_unit: Optional[str] = "M3"
    measurement_source: str = "MANUAL"


class ProductPhysicalProfileResponse(BaseModel):
    id: UUID
    product_id: UUID
    net_weight_value: Optional[Decimal] = None
    net_weight_unit: Optional[str] = None
    gross_weight_value: Optional[Decimal] = None
    gross_weight_unit: Optional[str] = None
    length_value: Optional[Decimal] = None
    width_value: Optional[Decimal] = None
    height_value: Optional[Decimal] = None
    dimension_unit: Optional[str] = None
    volume_value: Optional[Decimal] = None
    volume_unit: Optional[str] = None
    measurement_source: str
    status: str

    model_config = ConfigDict(from_attributes=True)


# --- Tracking Policy Schemas ---
class ProductTrackingPolicyUpdate(BaseModel):
    tracking_type: str = "NONE"
    lot_control: bool = False
    serial_control: bool = False
    expiration_control: str = "NONE"
    manufacturing_date_control: bool = False
    best_before_control: bool = False
    minimum_shelf_life_days: Optional[int] = None
    total_shelf_life_days: Optional[int] = None


class ProductTrackingPolicyResponse(BaseModel):
    id: UUID
    product_id: UUID
    tracking_type: str
    lot_control: bool
    serial_control: bool
    expiration_control: str
    manufacturing_date_control: bool
    best_before_control: bool
    minimum_shelf_life_days: Optional[int] = None
    total_shelf_life_days: Optional[int] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


# --- Storage Condition Schemas ---
class ProductStorageConditionCreate(BaseModel):
    condition_type: str = Field(..., description="TEMPERATURE, HUMIDITY, COLD_CHAIN, FROZEN, HAZARDOUS, FRAGILE, etc.")
    minimum_value: Optional[Decimal] = None
    maximum_value: Optional[Decimal] = None
    unit_code: Optional[str] = None
    severity: str = "HARD_BLOCK"
    handling_instruction: Optional[str] = None


class ProductStorageConditionResponse(BaseModel):
    id: UUID
    product_id: UUID
    condition_type: str
    minimum_value: Optional[Decimal] = None
    maximum_value: Optional[Decimal] = None
    unit_code: Optional[str] = None
    severity: str
    handling_instruction: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


# --- Product Base Schemas ---
class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    category_id: UUID
    brand_id: Optional[UUID] = None
    product_type: str = "PHYSICAL_GOOD"
    base_unit_code: str = "UND"
    short_name: Optional[str] = None
    description: Optional[str] = None


class ProductSKUChangeRequest(BaseModel):
    new_sku: str = Field(..., min_length=2, max_length=50)
    reason: str = Field(..., min_length=5)


class ProductStatusChangeRequest(BaseModel):
    target_status: str
    reason: Optional[str] = None


class ProductVersionResponse(BaseModel):
    id: UUID
    product_id: UUID
    version: str
    status: str
    sku_snapshot: str
    name: str
    content_hash: str
    effective_from: datetime
    effective_to: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(BaseModel):
    id: UUID
    organization_id: UUID
    sku: str
    normalized_sku: str
    name: str
    short_name: Optional[str] = None
    description: Optional[str] = None
    category_id: UUID
    brand_id: Optional[UUID] = None
    product_type: str
    base_unit_code: str
    status: str
    lifecycle_status: str
    row_version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductDetailResponse(ProductResponse):
    category: Optional[ProductCategoryResponse] = None
    brand: Optional[ProductBrandResponse] = None
    identifiers: List[ProductIdentifierResponse] = []
    physical_profile: Optional[ProductPhysicalProfileResponse] = None
    tracking_policy: Optional[ProductTrackingPolicyResponse] = None
    storage_conditions: List[ProductStorageConditionResponse] = []


class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int


class ProductLocationCompatibilityRequest(BaseModel):
    warehouse_location_id: UUID
    quantity: Optional[Decimal] = None
    unit_code: Optional[str] = None


class ProductLocationCompatibilityResponse(BaseModel):
    status: str
    blocking_reasons: List[str]
    warnings: List[str]
    evaluated_at: str
    evaluator_version: str
