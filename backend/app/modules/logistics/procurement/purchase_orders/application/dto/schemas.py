"""Purchase Order Pydantic v2 DTO schemas.

All monetary and quantity fields are formatted as Decimal/str in JSON
to prevent float precision loss on JavaScript clients.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Base Schema Config
# ---------------------------------------------------------------------------
class StrictBaseModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )


# ---------------------------------------------------------------------------
# Line Schemas
# ---------------------------------------------------------------------------
class PurchaseOrderLineCreate(StrictBaseModel):
    line_number: int = Field(..., ge=1)
    product_id: Optional[UUID] = None
    product_name_snapshot: str = Field(..., min_length=1, max_length=500)
    product_description_snapshot: Optional[str] = None
    specifications_snapshot: Optional[dict[str, Any]] = None
    supplier_product_reference: Optional[str] = None
    ordered_quantity: Decimal = Field(..., gt=0)
    ordered_unit_id: Optional[UUID] = None
    ordered_unit_code: str = Field(..., min_length=1, max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    currency_code: str = Field(..., min_length=3, max_length=3)
    discount_type: Optional[str] = "NONE"       # PERCENTAGE | FIXED_AMOUNT | NONE
    discount_value: Optional[Decimal] = Field(default=None, ge=0)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0, le=100)
    freight_amount: Decimal = Field(default=Decimal("0"), ge=0)
    other_charges_amount: Decimal = Field(default=Decimal("0"), ge=0)
    required_date: Optional[datetime] = None
    destination_warehouse_id: Optional[UUID] = None
    notes: Optional[str] = None

    @field_validator("ordered_quantity", "unit_price", "discount_value", "tax_rate", "freight_amount", "other_charges_amount", mode="before")
    @classmethod
    def reject_floats(cls, v: Any) -> Any:
        if isinstance(v, float):
            raise TypeError("float values are not allowed for monetary or quantity fields. Send a string or Decimal.")
        return v


class PurchaseOrderLineResponse(StrictBaseModel):
    id: UUID
    line_number: int
    product_id: Optional[UUID] = None
    product_name_snapshot: str
    product_description_snapshot: Optional[str] = None
    supplier_product_reference: Optional[str] = None
    ordered_quantity: Decimal
    ordered_unit_code: str
    unit_price: Decimal
    currency_code: str
    discount_amount: Decimal
    tax_amount: Decimal
    freight_amount: Decimal
    other_charges_amount: Decimal
    line_subtotal: Decimal
    line_total: Decimal
    status: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Revision Schemas
# ---------------------------------------------------------------------------
class PurchaseOrderRevisionResponse(StrictBaseModel):
    id: UUID
    revision_number: int
    status: str
    currency_code: str
    supplier_snapshot: Optional[dict[str, Any]] = None
    monetary_summary: Optional[dict[str, Any]] = None
    content_hash: Optional[str] = None
    lines: List[PurchaseOrderLineResponse] = Field(default_factory=list)
    created_at: datetime
    approved_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Generation Plan Schemas (CCO -> PO)
# ---------------------------------------------------------------------------
class PurchaseOrderGenerationPlanRequest(StrictBaseModel):
    evaluation_decision_id: UUID


class GenerationPlanLineResponse(StrictBaseModel):
    evaluation_decision_line_id: UUID
    product_name_snapshot: str
    ordered_quantity: Decimal
    ordered_unit_code: str
    unit_price: Decimal
    currency_code: str
    source_line_total: Decimal


class GenerationPlanEntryResponse(StrictBaseModel):
    entry_index: int
    supplier_business_partner_id: UUID
    supplier_name_snapshot: str
    currency_code: str
    estimated_subtotal: Decimal
    estimated_grand_total: Decimal
    lines: List[GenerationPlanLineResponse] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class PurchaseOrderGenerationPlanResponse(StrictBaseModel):
    evaluation_decision_id: UUID
    evaluation_decision_status: str
    is_executable: bool
    total_orders_to_create: int
    entries: List[GenerationPlanEntryResponse] = Field(default_factory=list)
    blocking_issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class PurchaseOrderGenerateFromDecisionRequest(StrictBaseModel):
    evaluation_decision_id: UUID
    site_code: str = Field("LIM", min_length=2, max_length=10)
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Action Schemas (Submit, Approve, Reject, Return, Cancel)
# ---------------------------------------------------------------------------
class PurchaseOrderSubmitRequest(StrictBaseModel):
    notes: Optional[str] = None


class PurchaseOrderApproveRequest(StrictBaseModel):
    reason: Optional[str] = None
    allow_self_approval_override: bool = False


class PurchaseOrderRejectRequest(StrictBaseModel):
    reason: str = Field(..., min_length=20, max_length=2000, description="Rejection reason (at least 20 chars)")


class PurchaseOrderReturnRequest(StrictBaseModel):
    reason: str = Field(..., min_length=20, max_length=2000, description="Return for changes reason (at least 20 chars)")


class PurchaseOrderCancelRequest(StrictBaseModel):
    cancellation_reason: str = Field(..., min_length=10, max_length=2000)


# ---------------------------------------------------------------------------
# Main Summary & Detail Response Schemas
# ---------------------------------------------------------------------------
class PurchaseOrderSummaryResponse(StrictBaseModel):
    id: UUID
    organization_id: UUID
    branch_id: UUID
    purchase_order_code: Optional[str] = None
    supplier_business_partner_id: UUID
    supplier_name: Optional[str] = None
    currency_code: str
    status: str
    approval_status: str
    issuance_status: str
    dispatch_status: str
    acknowledgement_status: str
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    freight_total: Decimal
    grand_total: Decimal
    created_at: datetime
    updated_at: datetime


class PurchaseOrderDetailResponse(PurchaseOrderSummaryResponse):
    source_decision_id: UUID
    buyer_user_id: UUID
    current_revision_number: int
    supplier_snapshot: Optional[dict[str, Any]] = None
    supplier_address_snapshot: Optional[dict[str, Any]] = None
    supplier_contact_snapshot: Optional[dict[str, Any]] = None
    buyer_snapshot: Optional[dict[str, Any]] = None
    notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    issued_at: Optional[datetime] = None
    dispatched_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    revisions: List[PurchaseOrderRevisionResponse] = Field(default_factory=list)
