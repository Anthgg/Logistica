from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

IncidentType = Literal[
    "delay",
    "damaged_package",
    "missing_package",
    "incorrect_address",
    "failed_delivery",
    "vehicle_problem",
    "inventory_difference",
    "other",
]
IncidentSeverity = Literal["low", "medium", "high", "critical"]
IncidentStatus = Literal["open", "investigating", "resolved", "closed"]


class IncidentCreate(BaseModel):
    shipment_id: UUID | None = None
    incident_type: IncidentType
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=2, max_length=3000)
    severity: IncidentSeverity
    assigned_to: UUID | None = None


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, min_length=2, max_length=3000)
    severity: IncidentSeverity | None = None
    status: IncidentStatus | None = None
    assigned_to: UUID | None = None


class IncidentResolve(BaseModel):
    resolution: str = Field(min_length=3, max_length=3000)


class IncidentRead(IncidentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: IncidentStatus
    reported_by: UUID
    resolution: str | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime
