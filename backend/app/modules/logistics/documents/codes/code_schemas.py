"""Pydantic schemas for Document Code Standard API endpoints (Phase 012)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentCodeStandardResponse(BaseModel):
    id: UUID
    code: str
    version: str
    name: str
    description: str | None = None
    pattern: str
    separator: str
    document_type_min_length: int
    document_type_max_length: int
    site_code_min_length: int
    site_code_max_length: int
    year_length: int
    sequence_length: int
    sequence_start: int
    sequence_max: int
    status: str
    effective_from: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentCodePartsRequest(BaseModel):
    document_type_code: str = Field(..., json_schema_extra={"example": "OC"})
    site_code: str = Field(..., json_schema_extra={"example": "LIM"})
    year: int = Field(..., json_schema_extra={"example": 2026})
    sequence: int = Field(..., json_schema_extra={"example": 1})


class DocumentCodePartsResponse(BaseModel):
    document_type_code: str
    site_code: str
    year: int
    sequence: int
    formatted_code: str
    standard_version: str = "1.0.0"


class DocumentCodeValidationRequest(BaseModel):
    code: str = Field(..., json_schema_extra={"example": "OC-LIM-2026-000001"})


class DocumentCodeValidationResponse(BaseModel):
    valid: bool
    code: str
    normalized_code: str | None = None
    standard_version: str = "1.0.0"
    errors: list[str]
    parts: dict[str, Any] | None = None


class DocumentCodeParseResponse(BaseModel):
    code: str
    document_type_code: str
    site_code: str
    year: int
    sequence: int
    standard_version: str = "1.0.0"


class DocumentCodePreviewRequest(BaseModel):
    document_type_code: str = Field(..., json_schema_extra={"example": "OC"})
    branch_id: UUID | None = None
    site_code: str | None = Field(None, json_schema_extra={"example": "LIM"})
    year: int | None = Field(None, json_schema_extra={"example": 2026})
    example_sequence: int = Field(1, ge=1, le=999999)


class DocumentCodePreviewResponse(BaseModel):
    code_preview: str
    standard_version: str = "1.0.0"
    document_type_code: str
    site_code: str
    year: int
    sequence_example: int
    is_reserved: bool = False
    warning: str = "Este código es solo una vista previa y NO reserva el correlativo."


class DocumentSiteCodeResponse(BaseModel):
    id: UUID
    organization_id: UUID
    branch_id: UUID
    code: str
    status: str
    is_primary: bool
    effective_from: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentSiteCodeCreateRequest(BaseModel):
    branch_id: UUID
    code: str = Field(..., min_length=2, max_length=10, json_schema_extra={"example": "LIM"})


class DocumentSiteCodeRetireRequest(BaseModel):
    reason: str = Field(..., min_length=5, json_schema_extra={"example": "Reestructuración de sedes operativas"})


class DocumentCodeExampleItem(BaseModel):
    family_code: str
    document_type_code: str
    document_name: str
    canonical_example: str


class DocumentCodeExamplesResponse(BaseModel):
    standard_version: str = "1.0.0"
    pattern: str = "TIPO-SEDE-AÑO-CORRELATIVO"
    examples: list[DocumentCodeExampleItem]
