from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class DatabaseHealth(BaseModel):
    status: Literal["connected", "disconnected"]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
    version: str
    environment: str
    database: DatabaseHealth
    timestamp: datetime
