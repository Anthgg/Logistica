"""Pydantic schemas for Document Series, Talonarios, and Numbering API endpoints (Phase 013)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentSeriesCreateRequest(BaseModel):
    branch_id: UUID
    document_type_code: str = Field(..., json_schema_extra={"example": "OC"})
    document_year: int = Field(..., json_schema_extra={"example": 2026})
    sequence_start: int = Field(1, ge=1)
    sequence_max: int = Field(999999, ge=1, le=999999)
    reason: str | None = Field(None, json_schema_extra={"example": "Apertura de serie compras LIM 2026"})
    idempotency_key: str | None = Field(None, json_schema_extra={"example": "SER-CREATE-2026-001"})


class DocumentSeriesResponse(BaseModel):
    id: UUID
    organization_id: UUID
    branch_id: UUID
    document_site_code_id: UUID
    document_type_id: UUID
    document_year: int
    code_standard_version: str
    sequence_scope: str
    prefix: str
    sequence_start: int
    next_sequence: int
    sequence_max: int
    status: str
    opened_at: datetime | None = None
    closed_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentSeriesStatusChangeRequest(BaseModel):
    reason: str = Field(..., min_length=5, json_schema_extra={"example": "Operación de mantenimiento ordinario"})


class DocumentTalonarioCreateRequest(BaseModel):
    quantity: int = Field(..., ge=1, le=1000, json_schema_extra={"example": 100})
    purpose: str = Field(..., min_length=5, json_schema_extra={"example": "Talonario impreso de contingencia comisionistas"})
    idempotency_key: str | None = Field(None, json_schema_extra={"example": "TAL-RESERVE-2026-001"})


class DocumentTalonarioResponse(BaseModel):
    id: UUID
    organization_id: UUID
    series_id: UUID
    talonario_code: str
    range_start: int
    range_end: int
    total_numbers: int
    reserved_numbers: int
    assigned_numbers: int
    issued_numbers: int
    cancelled_numbers: int
    voided_numbers: int
    available_numbers: int
    status: str
    purpose: str | None = None
    reserved_at: datetime
    manifest_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentTalonarioCancelRequest(BaseModel):
    reason: str = Field(..., min_length=5, json_schema_extra={"example": "Talonario extraviado o deteriorado"})


class DocumentNumberResponse(BaseModel):
    id: UUID
    organization_id: UUID
    series_id: UUID
    talonario_id: UUID | None = None
    sequence_number: int
    full_document_code: str
    status: str
    reservation_type: str
    reservation_purpose: str | None = None
    reserved_at: datetime
    assigned_resource_type: str | None = None
    assigned_resource_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class DocumentTalonarioManifestResponse(BaseModel):
    manifest_version: str = "1.0.0"
    talonario_id: UUID
    talonario_code: str
    organization_id: UUID
    prefix: str
    range_start: int
    range_end: int
    total_numbers: int
    status: str
    reserved_at: datetime
    numbers: list[DocumentNumberResponse]
    rendering_status: str = "PENDING_RENDERER_PHASE_014"
