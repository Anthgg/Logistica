from datetime import datetime
from uuid import UUID, uuid4

from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utc_now


class ExperimentalSession(Base):
    __tablename__ = "experimental_sessions"
    __table_args__ = (
        CheckConstraint(
            "identity_label IN ('genuine', 'impostor')",
            name="ck_experimental_sessions_identity_label",
        ),
        CheckConstraint(
            "sample_role IN ('enrollment', 'verification', 'change_operator')",
            name="ck_experimental_sessions_sample_role",
        ),
        CheckConstraint(
            "annotation_status IN ('pending', 'confirmed')",
            name="ck_experimental_sessions_annotation_status",
        ),
        CheckConstraint(
            "presentation_label IS NULL OR presentation_label IN ('bona_fide', 'attack')",
            name="ck_experimental_sessions_presentation_label",
        ),
        CheckConstraint(
            "attack_type IS NULL OR attack_type IN "
            "('none', 'printed_photo', 'screen_photo', 'replayed_video')",
            name="ck_experimental_sessions_attack_type",
        ),
        CheckConstraint(
            "client_timezone_offset_minutes IS NULL OR "
            "client_timezone_offset_minutes BETWEEN -840 AND 840",
            name="ck_experimental_sessions_timezone_offset",
        ),
        CheckConstraint(
            "(presentation_label IS NULL AND attack_type IS NULL) OR "
            "(presentation_label = 'bona_fide' AND attack_type = 'none') OR "
            "(presentation_label = 'attack' AND attack_type IN "
            "('printed_photo', 'screen_photo', 'replayed_video'))",
            name="ck_experimental_sessions_pad_consistency",
        ),
        CheckConstraint(
            "(sample_role = 'change_operator' AND operator_change_at IS NOT NULL) OR "
            "(sample_role <> 'change_operator' AND operator_change_at IS NULL)",
            name="ck_experimental_sessions_operator_change_consistency",
        ),
        CheckConstraint(
            "annotation_status = 'pending' OR "
            "(annotated_by IS NOT NULL AND annotated_at IS NOT NULL)",
            name="ck_experimental_sessions_annotation_confirmation",
        ),
        CheckConstraint(
            "annotation_notes IS NULL OR char_length(annotation_notes) <= 500",
            name="ck_experimental_sessions_annotation_notes_length",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    participant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("research_participants.id", ondelete="RESTRICT"),
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    scenario: Mapped[str] = mapped_column(String(60), index=True)
    status: Mapped[str] = mapped_column(
        String(20), default="created", server_default=text("'created'"), index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expected_duration_minutes: Mapped[int] = mapped_column(Integer)
    protocol_version: Mapped[str] = mapped_column(
        String(50),
        default="pilot-protocol-v0.1.0",
        server_default=text("'pilot-protocol-v0.1.0'"),
    )
    collector_version: Mapped[str] = mapped_column(
        String(50), default="web-v0.1.0", server_default=text("'web-v0.1.0'")
    )
    identity_label: Mapped[str] = mapped_column(
        String(20), default="genuine", server_default=text("'genuine'")
    )
    sample_role: Mapped[str] = mapped_column(
        String(30), default="verification", server_default=text("'verification'")
    )
    operator_change_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    presentation_label: Mapped[str | None] = mapped_column(String(20))
    attack_type: Mapped[str | None] = mapped_column(String(30))
    source_device: Mapped[str | None] = mapped_column(String(100))
    pad_source_id: Mapped[str | None] = mapped_column(String(100))
    annotation_status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default=text("'pending'"), index=True
    )
    annotated_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    annotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    annotation_notes: Mapped[str | None] = mapped_column(Text)
    capture_interval_seconds: Mapped[int] = mapped_column(
        Integer, default=5, server_default=text("5")
    )
    batch_interval_seconds: Mapped[int] = mapped_column(
        Integer, default=3, server_default=text("3")
    )
    max_batch_events: Mapped[int] = mapped_column(
        Integer, default=100, server_default=text("100")
    )
    max_image_size_bytes: Mapped[int] = mapped_column(
        Integer, default=1_048_576, server_default=text("1048576")
    )
    facial_capture_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    keyboard_event_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    mouse_event_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    batch_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    error_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    client_timezone: Mapped[str | None] = mapped_column(String(80))
    client_timezone_offset_minutes: Mapped[int | None] = mapped_column(Integer)
    client_language: Mapped[str | None] = mapped_column(String(20))
    screen_width: Mapped[int] = mapped_column(Integer)
    screen_height: Mapped[int] = mapped_column(Integer)
    screen_pixel_ratio: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    browser: Mapped[str | None] = mapped_column(String(100))
    operating_system: Mapped[str | None] = mapped_column(String(100))
    device_type: Mapped[str | None] = mapped_column(String(50))
    invalid_reason: Mapped[str | None] = mapped_column(Text)
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
