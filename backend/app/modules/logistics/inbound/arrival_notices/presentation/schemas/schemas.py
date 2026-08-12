"""Pydantic v2 contracts for arrival notices.

Decimal inputs are intentionally JSON strings.  IEEE float values, NaN and
Infinity are rejected before domain services are invoked.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

from app.modules.logistics.inbound.arrival_notices.domain.enums import (
    ArrivalNoticeSourceType,
    DocumentVerificationStatus,
    ReferenceSourceType,
    SpecialRequirement,
    SubmissionChannel,
    TransportDocumentKind,
    TransportMode,
)


def _decimal_string(value: object) -> Decimal:
    if not isinstance(value, str):
        raise ValueError("Las cantidades y pesos deben enviarse como strings decimales.")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Decimal inválido.") from exc
    if not parsed.is_finite():
        raise ValueError("NaN e Infinity no están permitidos.")
    return parsed


DecimalString = Annotated[Decimal, BeforeValidator(_decimal_string)]


class ApiModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        json_encoders={Decimal: lambda value: format(value, "f")},
    )


class ArrivalNoticeCreate(ApiModel):
    branch_id: UUID
    warehouse_id: UUID
    supplier_business_partner_id: UUID
    carrier_business_partner_id: UUID | None = None
    submission_channel: SubmissionChannel = SubmissionChannel.INTERNAL
    external_reference: str | None = Field(default=None, max_length=160)
    source_type: ArrivalNoticeSourceType = ArrivalNoticeSourceType.PURCHASE_ORDER
    purchase_order_ids: list[UUID] = Field(min_length=1, max_length=100)
    expected_arrival_date: date
    expected_arrival_timezone: str = Field(min_length=1, max_length=64)
    expected_pallet_count: int = Field(default=0, ge=0)
    expected_package_count: int = Field(default=0, ge=0)
    expected_loose_item_count: int | None = Field(default=None, ge=0)
    expected_gross_weight: DecimalString = Field(ge=Decimal("0"))
    weight_unit_id: UUID
    transport_mode: TransportMode = TransportMode.TO_BE_CONFIRMED
    special_requirements: list[SpecialRequirement] = Field(default_factory=list, max_length=20)
    comments: str | None = Field(default=None, max_length=4000)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("expected_arrival_timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Zona horaria IANA inválida.") from exc
        return value


class ArrivalNoticeUpdate(ApiModel):
    row_version: int = Field(ge=1)
    carrier_business_partner_id: UUID | None = None
    expected_arrival_date: date | None = None
    expected_arrival_timezone: str | None = Field(default=None, max_length=64)
    expected_pallet_count: int | None = Field(default=None, ge=0)
    expected_package_count: int | None = Field(default=None, ge=0)
    expected_loose_item_count: int | None = Field(default=None, ge=0)
    expected_gross_weight: DecimalString | None = Field(default=None, ge=Decimal("0"))
    weight_unit_id: UUID | None = None
    transport_mode: TransportMode | None = None
    special_requirements: list[SpecialRequirement] | None = Field(default=None, max_length=20)
    comments: str | None = Field(default=None, max_length=4000)


class ArrivalNoticeSubmitRequest(ApiModel):
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class ArrivalNoticeRequestChangesRequest(ApiModel):
    reason: str = Field(min_length=10, max_length=2000)


class ArrivalNoticeCancelRequest(ApiModel):
    reason: str = Field(min_length=10, max_length=2000)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class ArrivalNoticeRevisionCreate(ApiModel):
    change_summary: str = Field(min_length=3, max_length=2000)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class ArrivalNoticeExpectedLineCreate(ApiModel):
    purchase_order_reference_id: UUID
    purchase_order_line_id: UUID
    purchase_order_schedule_line_id: UUID | None = None
    expected_quantity: DecimalString = Field(gt=Decimal("0"))
    expected_unit_id: UUID
    expected_package_count: int | None = Field(default=None, ge=0)
    expected_pallet_count: int | None = Field(default=None, ge=0)
    supplier_lot_reference: str | None = Field(default=None, max_length=120)
    supplier_expiration_reference: date | None = None
    notes: str | None = Field(default=None, max_length=2000)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class ArrivalNoticeExpectedLineUpdate(ApiModel):
    expected_quantity: DecimalString | None = Field(default=None, gt=Decimal("0"))
    expected_unit_id: UUID | None = None
    expected_package_count: int | None = Field(default=None, ge=0)
    expected_pallet_count: int | None = Field(default=None, ge=0)
    supplier_lot_reference: str | None = Field(default=None, max_length=120)
    supplier_expiration_reference: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class ArrivalNoticeVehicleReferenceRequest(ApiModel):
    vehicle_id: UUID | None = None
    plate: str = Field(min_length=3, max_length=20)
    source_type: ReferenceSourceType = ReferenceSourceType.VEHICLE_MASTER
    exception_reason: str | None = Field(default=None, min_length=10, max_length=2000)


class ArrivalNoticeDriverReferenceRequest(ApiModel):
    driver_id: UUID | None = None
    full_name: str | None = Field(default=None, max_length=300)
    source_type: ReferenceSourceType = ReferenceSourceType.DRIVER_MASTER
    exception_reason: str | None = Field(default=None, min_length=10, max_length=2000)


class ArrivalNoticeTransportDocumentCreate(ApiModel):
    document_kind: TransportDocumentKind
    issuer_business_partner_id: UUID | None = None
    issuer_tax_identifier: str | None = Field(default=None, max_length=40)
    series: str | None = Field(default=None, max_length=40)
    number: str = Field(min_length=1, max_length=80)
    issue_date: date | None = None
    document_date: date | None = None
    transport_reference: str | None = Field(default=None, max_length=160)
    file_asset_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=2000)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("series", "number", "transport_reference")
    @classmethod
    def reject_markup(cls, value: str | None) -> str | None:
        if value is not None and ("<" in value or ">" in value):
            raise ValueError("No se permite HTML en referencias documentales.")
        return value


class ArrivalNoticeTransportDocumentUpdate(ApiModel):
    series: str | None = Field(default=None, max_length=40)
    number: str | None = Field(default=None, min_length=1, max_length=80)
    issue_date: date | None = None
    document_date: date | None = None
    transport_reference: str | None = Field(default=None, max_length=160)
    notes: str | None = Field(default=None, max_length=2000)


class TransportDocumentAssociateFileRequest(ApiModel):
    file_asset_id: UUID


class ArrivalNoticeResponse(ApiModel):
    id: UUID
    organization_id: UUID
    branch_id: UUID
    warehouse_id: UUID
    supplier_business_partner_id: UUID
    carrier_business_partner_id: UUID | None
    submission_channel: str
    external_reference: str | None
    status: str
    appointment_status: str
    source_type: str
    current_revision_number: int
    active_revision_id: UUID | None
    confirmed_revision_id: UUID | None
    appointment_id: UUID | None
    expected_arrival_date: date
    expected_arrival_timezone: str
    total_purchase_orders: int
    total_lines: int
    expected_pallet_count: int
    expected_package_count: int
    expected_loose_item_count: int | None
    expected_gross_weight: Decimal
    weight_unit_id: UUID
    transport_mode: str
    special_handling_summary: list
    comments: str | None
    created_at: datetime
    updated_at: datetime
    row_version: int


class ArrivalNoticeSummary(ArrivalNoticeResponse):
    purchase_order_codes: list[str] = Field(default_factory=list)
    warnings_count: int = 0
    document_count: int = 0
    capabilities: list[str] = Field(default_factory=list)


class ArrivalNoticeDetail(ArrivalNoticeResponse):
    supplier_snapshot: dict
    carrier_snapshot: dict | None
    revisions: list[dict] = Field(default_factory=list)


class ArrivalNoticeListResponse(ApiModel):
    items: list[ArrivalNoticeSummary]
    page: int
    page_size: int
    total: int


class ArrivalNoticeValidationResponse(ApiModel):
    valid: bool
    errors: list[dict] = Field(default_factory=list)
    warnings: list[dict] = Field(default_factory=list)


class ArrivalNoticeRevisionResponse(ApiModel):
    id: UUID
    arrival_notice_id: UUID
    revision_number: int
    status: str
    content_hash: str | None
    change_summary: str | None
    created_at: datetime
    submitted_at: datetime | None
    frozen_at: datetime | None


class ArrivalNoticeExpectedLineResponse(ApiModel):
    id: UUID
    arrival_notice_revision_id: UUID
    purchase_order_reference_id: UUID
    purchase_order_line_id: UUID
    line_number: int
    product_id: UUID | None
    sku_snapshot: str | None
    product_name_snapshot: str
    expected_quantity: Decimal
    expected_unit_id: UUID
    expected_base_quantity: Decimal
    base_unit_id: UUID
    expected_package_count: int | None
    expected_pallet_count: int | None
    status: str


class ArrivalNoticeTransportReadinessResponse(ApiModel):
    ready: bool
    vehicle_status: str
    driver_status: str
    document_status: str
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ArrivalNoticeTransportDocumentResponse(ApiModel):
    id: UUID
    revision_id: UUID
    document_kind: str
    series: str | None
    number: str
    normalized_reference: str
    verification_status: str
    verification_source: str | None
    file_asset_id: UUID | None
    status: str


class FormatVerificationResponse(ApiModel):
    document_id: UUID
    verification_status: DocumentVerificationStatus
    external_verification_performed: Literal[False] = False


class CapabilityResponse(ApiModel):
    capabilities: list[str]
