"""Pydantic v2 schemas for Phase 024 UOM Engine."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Dimension Schemas ---

class MeasurementDimensionResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    canonical_unit_id: Optional[UUID] = None
    supports_fractional_quantities: bool
    default_precision: int
    status: str
    system_defined: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Unit Schemas ---

class UnitCreateRequest(BaseModel):
    dimension_id: UUID
    code: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=100)
    symbol: str = Field(..., min_length=1, max_length=20)
    unit_kind: str = Field("DERIVED", pattern="^(BASE|DERIVED|PACKAGING|CUSTOM)$")
    plural_name: Optional[str] = None
    decimal_precision: int = Field(4, ge=0, le=18)
    integer_only: bool = False


class UnitResponse(BaseModel):
    id: UUID
    organization_id: Optional[UUID] = None
    dimension_id: UUID
    code: str
    normalized_code: str
    name: str
    plural_name: Optional[str] = None
    symbol: str
    unit_scope: str
    unit_kind: str
    decimal_precision: int
    integer_only: bool
    is_canonical: bool
    status: str
    system_defined: bool
    row_version: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Conversion Rule Schemas ---

class UnitConversionRuleCreateRequest(BaseModel):
    source_unit_id: UUID
    target_unit_id: UUID
    multiplier: str = Field(..., description="Multiplier as string decimal")
    product_id: Optional[UUID] = None
    allows_inverse: bool = True
    rounding_policy: str = Field("HALF_UP", pattern="^(NONE|EXACT_REQUIRED|HALF_UP|HALF_EVEN|FLOOR|CEILING|DOWN|UP)$")


class UnitConversionRuleResponse(BaseModel):
    id: UUID
    organization_id: Optional[UUID] = None
    product_id: Optional[UUID] = None
    source_unit_id: UUID
    target_unit_id: UUID
    conversion_scope: str
    multiplier: str
    allows_inverse: bool
    precision: int
    rounding_policy: str
    status: str
    version: str
    content_hash: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Product Unit Configuration Schemas ---

class ProductUnitConfigurationRequest(BaseModel):
    base_unit_id: UUID
    purchase_unit_id: Optional[UUID] = None
    reception_unit_id: Optional[UUID] = None
    storage_unit_id: Optional[UUID] = None
    picking_unit_id: Optional[UUID] = None
    dispatch_unit_id: Optional[UUID] = None


class ProductUnitConfigurationResponse(BaseModel):
    id: UUID
    product_id: UUID
    base_unit_id: UUID
    purchase_unit_id: Optional[UUID] = None
    reception_unit_id: Optional[UUID] = None
    storage_unit_id: Optional[UUID] = None
    picking_unit_id: Optional[UUID] = None
    dispatch_unit_id: Optional[UUID] = None
    status: str
    version: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Packaging Definition Schemas ---

class ProductPackagingDefinitionRequest(BaseModel):
    packaging_unit_id: UUID
    contained_unit_id: UUID
    contained_quantity: str = Field(..., description="Contained quantity as Decimal string")
    level_order: int = Field(..., ge=1, le=10)
    package_type: str = Field("BOX", max_length=30)
    gross_weight: Optional[str] = None


class ProductPackagingDefinitionResponse(BaseModel):
    id: UUID
    product_id: UUID
    packaging_unit_id: UUID
    contained_unit_id: UUID
    contained_quantity: str
    level_order: int
    package_type: str
    gross_weight: Optional[str] = None
    status: str
    version: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Evaluation & Decomposition Schemas ---

class UnitConversionEvaluateRequest(BaseModel):
    quantity: str = Field(..., description="Quantity to convert as string")
    source_unit_code: str
    target_unit_code: str
    product_id: Optional[UUID] = None
    purpose: str = Field("SIMULATION", max_length=30)
    rounding_policy: str = Field("HALF_UP", pattern="^(NONE|EXACT_REQUIRED|HALF_UP|HALF_EVEN|FLOOR|CEILING|DOWN|UP)$")


class UnitConversionEvaluateResponse(BaseModel):
    input_quantity: str
    input_unit: str
    exact_result: str
    rounded_result: str
    target_unit: str
    effective_factor: str
    conversion_path: List[str]
    rounding_applied: bool
    residual: str
    engine_version: str


class UnitDecomposeRequest(BaseModel):
    quantity: str = Field(..., description="Base quantity to decompose as string")
    source_unit_code: str = "UND"
    strategy: str = "LARGEST_FIRST"


class PackagingComponentResponse(BaseModel):
    unit_code: str
    unit_name: str
    quantity: str
    equivalent_base_quantity: str


class UnitDecomposeResponse(BaseModel):
    input_quantity: str
    input_unit: str
    normalized_base_quantity: str
    base_unit_code: str
    components: List[PackagingComponentResponse]
    residual: str
    strategy: str
    decomposed_at: str


class UnitCompareRequest(BaseModel):
    left_quantity: str
    left_unit_code: str
    right_quantity: str
    right_unit_code: str
    product_id: Optional[UUID] = None


class UnitCompareResponse(BaseModel):
    left: Dict[str, str]
    right: Dict[str, str]
    comparison: str
    right_converted_to_left: str
    difference: str
    equivalent: bool
    conversion_path: List[str]
