"""Step-up schemas for Phase 009."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StepUpChallengeCreateRequest(BaseModel):
    permission_code: str
    action_code: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    reason: str | None = Field(default=None, max_length=500)


class StepUpChallengeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    permission_code: str
    action_code: str | None
    resource_type: str | None
    resource_id: str | None
    status: str
    required_factors: list[str]
    risk_level: str | None
    issued_at: datetime
    expires_at: datetime
    attempts: int
    max_attempts: int


class StepUpFactorSubmitRequest(BaseModel):
    factor: str
    result: str = Field(pattern="^(passed|failed)$")
    risk_score: float | None = None


class StepUpCompleteRequest(BaseModel):
    pass


class StepUpProofResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    challenge_id: UUID
    permission_code: str
    action_code: str | None
    resource_type: str | None
    resource_id: str | None
    status: str
    one_time: bool
    issued_at: datetime
    expires_at: datetime


class StepUpRequiredError(BaseModel):
    success: bool = False
    error: dict


class PolicyResponse(BaseModel):
    policy_version: str
    sensitive_permissions: list[str]
    challenge_ttl_seconds: int
    proof_ttl_seconds: int
    max_attempts: int