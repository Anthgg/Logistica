from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

ResearchScenario = Literal[
    "register_shipment",
    "search_shipment",
    "update_shipment_status",
    "assign_route",
    "register_inventory_movement",
    "report_incident",
    "review_dashboard",
    "mixed_operations",
]
ResearchSessionStatus = Literal["created", "active", "completed", "cancelled", "invalid"]
IdentityLabel = Literal["genuine", "impostor"]
SampleRole = Literal["enrollment", "verification", "change_operator"]
PresentationLabel = Literal["bona_fide", "attack"]
AttackType = Literal["none", "printed_photo", "screen_photo", "replayed_video"]


class ParticipantCreate(BaseModel):
    linked_user_id: UUID | None = None


class ParticipantUpdate(BaseModel):
    linked_user_id: UUID | None = None
    is_active: bool | None = None


class ParticipantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    linked_user_id: UUID | None
    participant_code: str
    is_active: bool
    enrollment_date: datetime
    withdrawal_date: datetime | None
    created_at: datetime
    updated_at: datetime


class SelfEnrollmentResponse(BaseModel):
    success: bool = True
    participant: ParticipantRead
    created: bool


class ConsentCreate(BaseModel):
    participant_id: UUID
    consent_version: str = Field(min_length=1, max_length=50)
    accepted: bool


class ConsentWithdraw(BaseModel):
    participant_id: UUID


class ConsentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    participant_id: UUID
    consent_version: str
    accepted: bool
    accepted_at: datetime
    withdrawn_at: datetime | None


class ExperimentalSessionStart(BaseModel):
    participant_id: UUID
    scenario: ResearchScenario
    expected_duration_minutes: int = Field(ge=1, le=240)
    client_timezone: str | None = Field(default=None, max_length=80)
    client_timezone_offset_minutes: int | None = Field(default=None, ge=-840, le=840)
    client_language: str | None = Field(default=None, max_length=20)
    screen_width: int = Field(ge=240, le=16384)
    screen_height: int = Field(ge=240, le=16384)
    screen_pixel_ratio: Decimal | None = Field(default=None, ge=0.5, le=10)
    browser: str | None = Field(default=None, max_length=100)
    operating_system: str | None = Field(default=None, max_length=100)
    device_type: str | None = Field(default=None, max_length=50)
    collector_version: str | None = Field(default=None, max_length=50)


class CollectorConfiguration(BaseModel):
    id: UUID
    scenario: ResearchScenario
    status: ResearchSessionStatus
    started_at: datetime
    capture_interval_seconds: int
    batch_interval_seconds: int
    max_batch_events: int
    max_image_size_bytes: int


class SessionStartResponse(BaseModel):
    success: bool = True
    session: CollectorConfiguration


class BehavioralBatchCreate(BaseModel):
    batch_id: UUID
    sequence_number: int = Field(gt=0)
    started_at: datetime
    ended_at: datetime
    events: list[dict[str, object]]
    visibility_state: str | None = Field(default=None, max_length=30)
    client_timezone_offset_minutes: int | None = Field(default=None, ge=-840, le=840)
    dropped_event_count: int = Field(default=0, ge=0, le=100000)
    collector_error_count: int = Field(default=0, ge=0, le=10000)

    @model_validator(mode="after")
    def validate_range(self) -> "BehavioralBatchCreate":
        if self.ended_at < self.started_at:
            raise ValueError("ended_at no puede ser anterior a started_at")
        return self


class BehavioralBatchResponse(BaseModel):
    success: bool = True
    id: UUID
    batch_id: UUID
    sequence_number: int
    event_count: int
    keyboard_event_count: int
    mouse_event_count: int
    idempotent_replay: bool


class FacialCaptureResponse(BaseModel):
    success: bool = True
    id: UUID
    sequence_number: int
    file_size: int
    width: int
    height: int
    captured_at: datetime
    processing_status: str
    idempotent_replay: bool


class ExperimentalSessionFinish(BaseModel):
    client_ended_at: datetime
    client_error_count: int = Field(default=0, ge=0, le=10000)

    @model_validator(mode="after")
    def validate_timezone(self) -> "ExperimentalSessionFinish":
        if self.client_ended_at.tzinfo is None:
            raise ValueError("client_ended_at debe incluir zona horaria")
        return self


class ExperimentalSessionCancel(BaseModel):
    reason: str = Field(min_length=2, max_length=500)


class ExperimentalSessionAnnotationUpdate(BaseModel):
    identity_label: IdentityLabel
    sample_role: SampleRole
    operator_change_at: datetime | None = None
    presentation_label: PresentationLabel | None = None
    attack_type: AttackType | None = None
    source_device: str | None = Field(default=None, max_length=100)
    pad_source_id: str | None = Field(default=None, max_length=100)
    annotation_notes: str | None = Field(default=None, max_length=500)
    confirmed: bool = True

    @model_validator(mode="after")
    def validate_annotation(self) -> "ExperimentalSessionAnnotationUpdate":
        if self.operator_change_at is not None and self.operator_change_at.tzinfo is None:
            raise ValueError("operator_change_at debe incluir zona horaria")
        if self.sample_role == "change_operator" and self.operator_change_at is None:
            raise ValueError("change_operator requiere operator_change_at")
        if self.sample_role != "change_operator" and self.operator_change_at is not None:
            raise ValueError("operator_change_at solo corresponde a change_operator")
        if self.presentation_label is None:
            if self.attack_type is not None or self.source_device or self.pad_source_id:
                raise ValueError("Los metadatos PAD requieren presentation_label")
        elif self.presentation_label == "bona_fide" and self.attack_type != "none":
            raise ValueError("bona_fide requiere attack_type=none")
        elif self.presentation_label == "attack" and self.attack_type not in {
            "printed_photo",
            "screen_photo",
            "replayed_video",
        }:
            raise ValueError("attack requiere un tipo de ataque controlado")
        return self


class ExperimentalSessionRead(BaseModel):
    id: UUID
    participant_id: UUID
    scenario: ResearchScenario
    status: ResearchSessionStatus
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int
    facial_capture_count: int
    keyboard_event_count: int
    mouse_event_count: int
    batch_count: int
    error_count: int
    protocol_version: str
    collector_version: str
    identity_label: IdentityLabel
    sample_role: SampleRole
    operator_change_at: datetime | None
    presentation_label: PresentationLabel | None
    attack_type: AttackType | None
    source_device: str | None
    pad_source_id: str | None
    annotation_status: Literal["pending", "confirmed"]


class SessionMutationResponse(BaseModel):
    success: bool = True
    session: ExperimentalSessionRead
