"""Pydantic V2 Schemas for Phase 026 (RUC Module)."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RucLookupQuerySchema(BaseModel):
    include_annexes: bool = False
    allow_provider: bool = False


class RucLookupResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    query_ruc: str
    normalized_ruc: str
    found: bool
    legal_name: Optional[str] = None
    taxpayer_status: str
    taxpayer_status_raw: Optional[str] = None
    domicile_condition: str
    domicile_condition_raw: Optional[str] = None
    ubigeo_code: Optional[str] = None
    annex_addresses: List[Dict[str, Any]] = Field(default_factory=list)
    source: str
    source_name: str
    dataset_version_id: Optional[str] = None
    source_published_at: Optional[str] = None
    fetched_at: str
    lookup_at: str
    data_age_days: Optional[int] = None
    staleness_level: str
    is_stale: bool
    confidence_level: str
    verification_status: str
    field_provenance: Dict[str, Any]
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    provider_used: Optional[str] = None
    cache_status: str
    correlation_id: Optional[str] = None


class RucImportJobRequestSchema(BaseModel):
    dataset_type: str = Field("RUC_GENERAL", description="RUC_GENERAL or RUC_ANNEX_ADDRESS")
    custom_url: Optional[str] = None


class RucImportJobResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: UUID = Field(..., alias="id")
    dataset_type: str
    trigger_type: str
    status: str
    current_stage: str
    downloaded_bytes: int
    processed_rows: int
    accepted_rows: int
    rejected_rows: int
    created_at: datetime


class RucAssistedVerificationCreateSchema(BaseModel):
    ruc: str = Field(..., min_length=11, max_length=11)
    verification_reason: str = Field(..., min_length=5)
    source_reference: str
    business_partner_id: Optional[UUID] = None
    observed_legal_name: Optional[str] = None
    observed_status: Optional[str] = None
    observed_condition: Optional[str] = None
    observed_ubigeo: Optional[str] = None
    observations: Optional[str] = None


class ApplyRucDataToPartnerSchema(BaseModel):
    verification_id: UUID
    apply_legal_name: bool = False
    apply_annex_as_candidate: bool = False
    selected_annex_address: Optional[str] = None
    reason: Optional[str] = None
