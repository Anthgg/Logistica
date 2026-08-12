from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utc_now


class BehavioralBatch(Base):
    __tablename__ = "behavioral_batches"
    __table_args__ = (
        UniqueConstraint(
            "experimental_session_id",
            "sequence_number",
            name="uq_behavior_session_sequence",
        ),
        CheckConstraint(
            "client_timezone_offset_minutes IS NULL OR "
            "client_timezone_offset_minutes BETWEEN -840 AND 840",
            name="ck_behavioral_batches_timezone_offset",
        ),
        CheckConstraint(
            "dropped_event_count >= 0", name="ck_behavioral_batches_dropped_events"
        ),
        CheckConstraint(
            "collector_error_count >= 0", name="ck_behavioral_batches_collector_errors"
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    experimental_session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("experimental_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    batch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer)
    event_count: Mapped[int] = mapped_column(Integer)
    keyboard_event_count: Mapped[int] = mapped_column(Integer)
    mouse_event_count: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    visibility_state: Mapped[str | None] = mapped_column(String(30))
    client_timezone_offset_minutes: Mapped[int | None] = mapped_column(Integer)
    dropped_event_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0")
    )
    collector_error_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0")
    )
    payload: Mapped[list[dict[str, object]]] = mapped_column(JSONB)
    checksum: Mapped[str] = mapped_column(String(64))
    processing_status: Mapped[str] = mapped_column(
        String(30), default="pending", server_default=text("'pending'")
    )
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
