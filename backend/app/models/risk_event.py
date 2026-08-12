from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utc_now


class RiskEvent(Base):
    __tablename__ = "risk_events"
    __table_args__ = (
        CheckConstraint(
            "previous_risk_level IS NULL OR previous_risk_level IN "
            "('low', 'medium', 'high', 'critical')",
            name="ck_risk_events_previous_level",
        ),
        CheckConstraint(
            "new_risk_level IN ('low', 'medium', 'high', 'critical')",
            name="ck_risk_events_new_level",
        ),
        Index("ix_risk_events_session_created", "session_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    continuous_auth_evaluation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "continuous_auth_evaluations.id",
            ondelete="CASCADE",
        ),
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        index=True,
    )
    previous_risk_level: Mapped[str | None] = mapped_column(String(20))
    new_risk_level: Mapped[str] = mapped_column(String(20))
    recommended_action: Mapped[str] = mapped_column(String(60))
    applied_action: Mapped[str] = mapped_column(String(60))
    reason_code: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
