from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utc_now


class ResearchParticipant(Base):
    __tablename__ = "research_participants"
    __table_args__ = (
        Index(
            "uq_research_participants_active_linked_user",
            "linked_user_id",
            unique=True,
            postgresql_where=text(
                "linked_user_id IS NOT NULL AND is_active = true"
            ),
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    linked_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    participant_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    enrollment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    withdrawal_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
