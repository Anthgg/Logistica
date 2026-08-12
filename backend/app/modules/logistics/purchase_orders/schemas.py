"""API schemas for purchase orders."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PurchaseOrderLineCreate(BaseModel):
    product_id: UUID
    description: str | None = Field(default=None, max_length=300)
    unit_code: str | None = Field(default=None, min_length=1, max_length=20)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(default=Decimal("18"), ge=0, le=100)


class PurchaseOrderCreate(BaseModel):
    supplier_id: UUID
    currency_code: str = Field(default="PEN", min_length=3, max_length=3)
    expected_delivery_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)
    lines: list[PurchaseOrderLineCreate] = Field(min_length=1, max_length=500)

    @field_validator("currency_code")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class PurchaseOrderUpdate(BaseModel):
    expected_delivery_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class PurchaseOrderCancel(BaseModel):
    reason: str = Field(min_length=15, max_length=1000)


class PurchaseOrderLineResponse(BaseModel):
    id: UUID
    line_number: int
    product_id: UUID
    description: str
    unit_code: str
    quantity: Decimal
    unit_price: Decimal
    tax_rate: Decimal
    subtotal_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderResponse(BaseModel):
    id: UUID
    organization_id: UUID
    supplier_id: UUID
    supplier_name: str
    order_number: str
    currency_code: str
    subtotal_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: Literal["DRAFT", "APPROVED", "ISSUED", "CONFIRMED", "PARTIALLY_RECEIVED", "CLOSED", "ANNULLED"]
    expected_delivery_date: date | None
    notes: str | None
    row_version: int
    approved_by: UUID | None
    approved_at: datetime | None
    issued_by: UUID | None
    issued_at: datetime | None
    annulled_by: UUID | None
    annulled_at: datetime | None
    annulment_reason: str | None
    created_at: datetime
    updated_at: datetime
    lines: list[PurchaseOrderLineResponse]

    model_config = ConfigDict(from_attributes=True)
