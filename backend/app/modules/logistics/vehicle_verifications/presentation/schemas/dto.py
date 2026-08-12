"""Pydantic V2 Schemas & DTOs for Phase 028 — Vehicle Verifications."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class VehicleVerificationSourceRequestDTO(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    authority: str = Field(..., max_length=100)
    source_type: str = "OTHER"
    base_domain: Optional[str] = None
    provider_code: Optional[str] = None
    verification_domains: List[str] = Field(default_factory=list)
    automation_mode: str = "MANUAL_ASSISTED"
    authorization_status: str = "NOT_EVALUATED"
    authorization_reference: Optional[str] = None
    priority: int = 100


class VehicleVerificationSourceResponseDTO(BaseModel):
    id: UUID
    code: str
    name: str
    authority: str
    source_type: str
    base_domain: Optional[str] = None
    provider_code: Optional[str] = None
    verification_domains: List[str]
    enabled: bool
    automation_mode: str
    authorization_status: str
    authorization_reference: Optional[str] = None
    priority: int
    status: str

    model_config = {"from_attributes": True}


class CreateVehicleVerificationRequestDTO(BaseModel):
    verification_domain: str
    source_code: str
    purpose: str = "LOGISTICS_COMPLIANCE"
    file_reference_id: Optional[str] = None


class VehicleVerificationResponseDTO(BaseModel):
    id: UUID
    organization_id: UUID
    vehicle_id: UUID
    normalized_plate: str
    verification_domain: str
    verification_method: str
    source_id: UUID
    provider_code: Optional[str] = None
    status: str
    result_status: str
    confidence_level: str
    source_data_at: Optional[datetime] = None
    requested_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    evidence_status: str
    conflict_status: str

    model_config = {"from_attributes": True}


class CreateAssistedVerificationRequestDTO(BaseModel):
    verification_domain: str
    source_id: UUID
    verification_reason: str
    observed_plate: str
    source_reference: Optional[str] = None
    observed_owner: Optional[str] = None
    observed_make: Optional[str] = None
    observed_model: Optional[str] = None
    observed_year: Optional[int] = None
    observed_status: Optional[str] = None
    observed_expiration: Optional[datetime] = None
    observations: Optional[str] = None
    evidence_reference_id: Optional[str] = None
    result_status: str = "VALID"


class AssistedVerificationResponseDTO(BaseModel):
    id: UUID
    organization_id: UUID
    vehicle_id: UUID
    verification_domain: str
    source_id: UUID
    verification_reason: str
    observed_plate: str
    observed_owner: Optional[str] = None
    observed_make: Optional[str] = None
    observed_model: Optional[str] = None
    observed_year: Optional[int] = None
    observed_status: Optional[str] = None
    observed_expiration: Optional[datetime] = None
    approval_status: str
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplyVerificationFieldsRequestDTO(BaseModel):
    selected_fields: List[str]  # e.g., ["make", "model", "manufacturing_year", "vin"]
    reason: str


class VehicleVerificationComplianceResponseDTO(BaseModel):
    vehicle_id: UUID
    vehicle_code: str
    display_plate: str
    compliance_status: str
    required_domains: List[str]
    completed_domains: List[str]
    missing_domains: List[str]
    expired_domains: List[str]
    stale_domains: List[str]
    has_open_conflicts: bool
    blocking_reasons: List[str]
    warnings: List[str]
    evaluated_at: str
