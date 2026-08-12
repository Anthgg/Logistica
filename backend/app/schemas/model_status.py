from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ModelComponentStatusRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    available: bool
    loaded: bool
    checksum_valid: bool
    version: str | None
    reason_code: str | None


class ModelStatusRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    global_status: str
    facial: ModelComponentStatusRead
    pad: ModelComponentStatusRead
    behavioral_available: int
    behavioral_loaded: int
    behavioral_versions: list[str]
    device: str
    loaded_at: datetime | None
    registry_checksum_valid: bool
    fusion_loaded: bool
    normalization_loaded: bool
    errors: list[str]


class ModelStatusResponse(BaseModel):
    success: bool = True
    models: ModelStatusRead
