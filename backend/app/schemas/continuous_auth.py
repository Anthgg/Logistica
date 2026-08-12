from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.schemas.inference import (
    LatencyBreakdownRead,
    PublicComponents,
)

RiskLevel = Literal["low", "medium", "high", "critical"]
AuthenticationLevel = Literal[
    "traditional",
    "continuously_verified",
    "verification_required",
    "restricted",
    "terminated",
]


class ContinuousAuthEvaluateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experimental_session_id: UUID
    facial_capture_id: UUID | None = None
    behavioral_window_id: str | None = Field(
        default=None, min_length=1, max_length=100
    )
    evaluation_timestamp: datetime

    @model_validator(mode="after")
    def validate_request(self) -> "ContinuousAuthEvaluateRequest":
        if self.evaluation_timestamp.tzinfo is None:
            raise ValueError("evaluation_timestamp debe incluir zona horaria")
        if not self.facial_capture_id and not self.behavioral_window_id:
            raise ValueError(
                "Se requiere una captura o una ventana conductual."
            )
        return self


class ContinuousAuthPublicEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    risk_score: float = Field(ge=0, le=1)
    risk_level: RiskLevel
    authentication_level: AuthenticationLevel
    recommended_action: str
    applied_action: str
    evaluated_at: datetime
    components: PublicComponents


class ContinuousAuthEvaluateResponse(BaseModel):
    success: bool = True
    evaluation: ContinuousAuthPublicEvaluation


class ContinuousAuthStatusResponse(BaseModel):
    success: bool = True
    enabled: bool
    continuous_auth_status: str
    risk_level: RiskLevel | None
    authentication_level: AuthenticationLevel
    last_evaluation_at: datetime | None
    recommended_action: str | None
    applied_action: str | None
    components_available: dict[str, bool]
    next_evaluation_after: datetime | None


class ContinuousAuthEvaluationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    session_id: UUID
    experimental_session_id: UUID | None
    participant_id: UUID | None
    facial_capture_id: UUID | None
    behavioral_window_id: str | None
    facial_available: bool
    pad_available: bool
    behavioral_available: bool
    facial_score: float | None
    pad_score: float | None
    behavioral_score: float | None
    facial_risk: float | None
    pad_risk: float | None
    behavioral_risk: float | None
    combined_risk: float
    risk_level: RiskLevel
    authentication_level: AuthenticationLevel
    recommended_action: str
    applied_action: str
    model_versions: dict[str, str]
    latency_ms: float
    latency_breakdown: dict[str, float]
    evaluated_at: datetime
    created_at: datetime


class ContinuousAuthEvaluationDetail(ContinuousAuthEvaluationRead):
    latency: LatencyBreakdownRead


class ReverifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: str = Field(min_length=1, max_length=128)


class ReverifyResponse(BaseModel):
    success: bool = True
    authentication_level: AuthenticationLevel
    continuous_auth_status: str
    reverified_at: datetime
