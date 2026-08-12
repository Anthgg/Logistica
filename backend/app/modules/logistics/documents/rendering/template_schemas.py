"""Pydantic schemas for Document Templates and Rendering API endpoints (Phase 014)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentTemplateResponse(BaseModel):
    id: UUID
    template_key: str
    document_family_code: str
    document_type_code: str | None = None
    name: str
    description: str | None = None
    status: str
    is_system: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentTemplateVersionResponse(BaseModel):
    id: UUID
    template_id: UUID
    version: str
    engine: str
    engine_version: str
    html_path: str
    schema_version: str
    content_hash: str
    status: str
    effective_from: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentPreviewRenderRequest(BaseModel):
    document_type_code: str = Field("GENERIC", json_schema_extra={"example": "OC"})
    document_title: str = Field("VISTA PREVIA DE DOCUMENTO", json_schema_extra={"example": "ORDEN DE COMPRA"})
    document_code: str | None = Field(None, json_schema_extra={"example": "OC-LIM-2026-000001"})
    document_status: str = Field("PREVIEW", json_schema_extra={"example": "PREVIEW"})
    organization_name: str = Field("PROYECTO T1 LOGÍSTICA S.A.C.", json_schema_extra={"example": "PROYECTO T1 LOGÍSTICA S.A.C."})
    branch_name: str = Field("SEDE LIMA PRINCIPAL", json_schema_extra={"example": "SEDE LIMA PRINCIPAL"})
    document_data: dict[str, Any] = Field(default_factory=dict)
    watermark_text: str | None = Field("VISTA PREVIA", json_schema_extra={"example": "VISTA PREVIA"})
    qr_data: str | None = Field(None, json_schema_extra={"example": "https://logistics.t1.com/verify/DOC123"})
    signature_data: dict[str, Any] | None = Field(None)


class DocumentRendererStatusResponse(BaseModel):
    renderer_available: bool = True
    renderer_name: str
    active_engine: str = "Jinja2+WeasyPrint/Fallback"
    base_template_available: bool = True
    active_template_key: str = "base.document"
    active_template_version: str = "1.0.0"
    qr_generator_available: bool = True
