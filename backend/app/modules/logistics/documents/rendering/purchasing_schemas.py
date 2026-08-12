"""Pydantic v2 schemas for Purchasing Document contexts (Phase 015)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class PurchasingItemSchema(BaseModel):
    line_number: int = 1
    sku: str | None = None
    description: str
    quantity: Decimal = Field(..., gt=0)
    unit: str = "UND"
    unit_price: Decimal = Field(Decimal("0.00"), ge=0)
    total: Decimal = Field(Decimal("0.00"), ge=0)


class SupplierSnapshotSchema(BaseModel):
    business_name: str
    ruc: str | None = None
    address: str | None = None
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None


class PurchasingReqContext(BaseModel):
    requesting_area: str = "Operaciones Logísticas"
    requester: str = "Usuario Comprador"
    request_date: str | None = None
    required_date: str | None = None
    priority: str = "MEDIA"
    justification: str = "Atención de requerimiento operativo"
    items: list[PurchasingItemSchema] = Field(default_factory=list)


class PurchasingScotContext(BaseModel):
    supplier: SupplierSnapshotSchema
    issue_date: str | None = None
    response_deadline: str
    currency: str = "PEN"
    delivery_address: str = "Almacén Principal Sede Lima"
    items: list[PurchasingItemSchema] = Field(default_factory=list)


class PurchasingCcoContext(BaseModel):
    related_request_reference: str = "REQ-2026-000001"
    evaluation_date: str | None = None
    evaluator: str = "Comprador Senior"
    currency: str = "PEN"
    suppliers: list[dict[str, Any]] = Field(default_factory=list)
    recommended_supplier_name: str
    recommendation_reason: str


class PurchasingOcContext(BaseModel):
    supplier: SupplierSnapshotSchema
    order_date: str | None = None
    currency: str = "PEN"
    payment_terms: str = "Crédito 30 días"
    delivery_date: str | None = None
    delivery_address: str = "Almacén Principal Sede Lima"
    items: list[PurchasingItemSchema] = Field(default_factory=list)
    subtotal: Decimal = Field(Decimal("0.00"), ge=0)
    tax: Decimal = Field(Decimal("0.00"), ge=0)
    total: Decimal = Field(Decimal("0.00"), ge=0)


class PurchasingApcContext(BaseModel):
    related_purchase_reference: str = "OC-2026-000001"
    approval_date: str | None = None
    decision: str = "APROBADO"
    amount: Decimal = Field(Decimal("0.00"), ge=0)
    currency: str = "PEN"
    approver: str = "Gerente de Finanzas"
    approval_level: str = "NIVEL_2_GERENCIAL"
    reason: str = "Aprobación presupuestal y operativa conforme al control interno"


class PurchasingCepContext(BaseModel):
    related_document_code: str = "OC-LIM-2026-000001"
    related_document_type: str = "ORDEN_COMPRA"
    supplier_name: str = "DISTRIBUIDORA INDUSTRIAL S.A.C."
    channel: str = "EMAIL_AUTOMATICO"
    recipients: str = "ventas@proveedor.com"
    sent_at: str | None = None
    send_status: str = "ENVIADO"
    responsible_user: str = "Sistema Compras"
    file_hash: str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    transaction_id: str = "MSG-20260726-987654"
