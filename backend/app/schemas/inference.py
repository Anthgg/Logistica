from pydantic import BaseModel, ConfigDict


class PublicComponentStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    available: bool
    status: str


class PublicComponents(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facial: PublicComponentStatus
    pad: PublicComponentStatus
    behavioral: PublicComponentStatus


class LatencyBreakdownRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image_decode_ms: float | None = None
    facial_ms: float | None = None
    pad_ms: float | None = None
    behavioral_load_ms: float | None = None
    behavioral_ms: float | None = None
    normalization_ms: float | None = None
    fusion_ms: float | None = None
    database_ms: float | None = None
    total_ms: float
