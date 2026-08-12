"""Pydantic v2 schemas for Phase 025 — Business Partners Master Data."""

from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BusinessPartnerCreateSchema(BaseModel):
    legal_name: str = Field(..., min_length=2, max_length=200)
    trade_name: Optional[str] = Field(None, max_length=200)
    person_type: str = Field("LEGAL_ENTITY", pattern="^(LEGAL_ENTITY|NATURAL_PERSON)$")
    country_code: str = Field("PE", min_length=2, max_length=3)
    tax_id_type: Optional[str] = Field(None, description="e.g. RUC, DNI, CE")
    tax_id_value: Optional[str] = Field(None, description="Tax ID string")
    roles: Optional[List[str]] = Field(default_factory=list, description="e.g. ['SUPPLIER', 'CUSTOMER', 'CARRIER']")


class BusinessPartnerRoleCreateSchema(BaseModel):
    role_type: str = Field(..., pattern="^(SUPPLIER|CUSTOMER|CARRIER|MANUFACTURER|SHIPPER)$")


class BusinessPartnerAddressCreateSchema(BaseModel):
    address_line_1: str = Field(..., min_length=3, max_length=200)
    address_type: str = Field("FISCAL", max_length=30)
    district: Optional[str] = None
    province: Optional[str] = None
    department: Optional[str] = None
    is_primary: bool = True


class BusinessPartnerContactCreateSchema(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    contact_type: str = Field("GENERAL", max_length=30)
    email: Optional[str] = None
    phone: Optional[str] = None
    is_primary: bool = True


class EvaluationCriterionInputSchema(BaseModel):
    code: str
    name: str
    weight: Decimal = Field(..., ge=0, le=100)
    score: Decimal = Field(..., ge=0, le=100)
    observations: Optional[str] = None


class BusinessPartnerEvaluationCreateSchema(BaseModel):
    role_type: str = Field(..., pattern="^(SUPPLIER|CUSTOMER|CARRIER)$")
    criteria: List[EvaluationCriterionInputSchema]
    summary: Optional[str] = None


class BusinessPartnerResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    partner_code: str
    legal_name: str
    trade_name: Optional[str] = None
    person_type: str
    country_code: str
    status: str
    lifecycle_status: str
    risk_status: str
    compliance_status: str
    row_version: int
    created_at: datetime
    updated_at: datetime


class DuplicateCheckRequestSchema(BaseModel):
    tax_id_value: Optional[str] = None
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
