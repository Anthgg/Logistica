from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utc_now


class ContinuousAuthEvaluation(Base):
    __tablename__ = "continuous_auth_evaluations"
    __table_args__ = (
        CheckConstraint(
            "combined_risk >= 0 AND combined_risk <= 1",
            name="ck_continuous_auth_evaluations_combined_risk",
        ),
        CheckConstraint(
            "facial_risk IS NULL OR "
            "(facial_risk >= 0 AND facial_risk <= 1)",
            name="ck_continuous_auth_evaluations_facial_risk",
        ),
        CheckConstraint(
            "pad_risk IS NULL OR (pad_risk >= 0 AND pad_risk <= 1)",
            name="ck_continuous_auth_evaluations_pad_risk",
        ),
        CheckConstraint(
            "behavioral_risk IS NULL OR "
            "(behavioral_risk >= 0 AND behavioral_risk <= 1)",
            name="ck_continuous_auth_evaluations_behavioral_risk",
        ),
        CheckConstraint(
            "latency_ms >= 0",
            name="ck_continuous_auth_evaluations_latency",
        ),
        CheckConstraint(
            "risk_level IN ('low', 'medium', 'high', 'critical')",
            name="ck_continuous_auth_evaluations_risk_level",
        ),
        CheckConstraint(
            "authentication_level IN "
            "('traditional', 'continuously_verified', "
            "'verification_required', 'restricted', 'terminated')",
            name="ck_continuous_auth_evaluations_authentication_level",
        ),
        Index(
            "ix_continuous_auth_evaluations_session_evaluated",
            "session_id",
            "evaluated_at",
        ),
        Index(
            "ix_continuous_auth_evaluations_user_evaluated",
            "user_id",
            "evaluated_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
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
    experimental_session_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("experimental_sessions.id", ondelete="SET NULL"),
        index=True,
    )
    participant_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("research_participants.id", ondelete="SET NULL"),
        index=True,
    )
    facial_capture_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("facial_captures.id", ondelete="SET NULL"),
        index=True,
    )
    behavioral_window_id: Mapped[str | None] = mapped_column(String(100))
    facial_available: Mapped[bool] = mapped_column(Boolean)
    pad_available: Mapped[bool] = mapped_column(Boolean)
    behavioral_available: Mapped[bool] = mapped_column(Boolean)
    facial_score: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    pad_score: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    behavioral_score: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    facial_risk: Mapped[Decimal | None] = mapped_column(Numeric(6, 5))
    pad_risk: Mapped[Decimal | None] = mapped_column(Numeric(6, 5))
    behavioral_risk: Mapped[Decimal | None] = mapped_column(Numeric(6, 5))
    combined_risk: Mapped[Decimal] = mapped_column(Numeric(6, 5))
    risk_level: Mapped[str] = mapped_column(String(20), index=True)
    authentication_level: Mapped[str] = mapped_column(String(50), index=True)
    recommended_action: Mapped[str] = mapped_column(String(60))
    applied_action: Mapped[str] = mapped_column(String(60))
    model_versions: Mapped[dict[str, str]] = mapped_column(JSONB)
    latency_ms: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    latency_breakdown: Mapped[dict[str, float]] = mapped_column(JSONB)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
