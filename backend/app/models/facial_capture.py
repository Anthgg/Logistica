from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utc_now


class FacialCapture(Base):
    __tablename__ = "facial_captures"
    __table_args__ = (
        UniqueConstraint(
            "experimental_session_id",
            "sequence_number",
            name="uq_facial_capture_session_sequence",
        ),
        CheckConstraint(
            "client_timezone_offset_minutes IS NULL OR "
            "client_timezone_offset_minutes BETWEEN -840 AND 840",
            name="ck_facial_captures_timezone_offset",
        ),
        CheckConstraint(
            "capture_source IN ('webcam', 'controlled_upload')",
            name="ck_facial_captures_source",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    experimental_session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("experimental_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(Integer)
    storage_path: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(50))
    file_size: Mapped[int] = mapped_column(Integer)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    visibility_state: Mapped[str | None] = mapped_column(String(30))
    client_timezone_offset_minutes: Mapped[int | None] = mapped_column(Integer)
    capture_source: Mapped[str] = mapped_column(
        String(30), default="webcam", server_default=text("'webcam'")
    )
    camera_facing_mode: Mapped[str | None] = mapped_column(String(20))
    processing_status: Mapped[str] = mapped_column(
        String(30), default="pending", server_default=text("'pending'")
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    checksum: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
