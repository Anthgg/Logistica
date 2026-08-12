"""Step-up challenge and proof models for Phase 009."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utc_now


class StepUpChallenge(Base):
    __tablename__ = "logistics_step_up_challenges"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    
    permission_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action_code: Mapped[str | None] = mapped_column(String(100))
    resource_type: Mapped[str | None] = mapped_column(String(100))
    resource_id: Mapped[str | None] = mapped_column(String(255))
    organization_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    branch_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    warehouse_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="pending", server_default=text("'pending'"), nullable=False, index=True)
    required_factors: Mapped[list] = mapped_column(JSONB, nullable=False)
    reason_codes: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'"))
    risk_level: Mapped[str | None] = mapped_column(String(20))
    risk_score: Mapped[float | None] = mapped_column()
    reason_text: Mapped[str | None] = mapped_column(String(500))

    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"), nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, server_default=text("3"), nullable=False)

    correlation_id: Mapped[str | None] = mapped_column(String(100), index=True)
    policy_version: Mapped[str] = mapped_column(String(20), default="1.0.0", server_default=text("'1.0.0'"), nullable=False)

    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class StepUpProof(Base):
    __tablename__ = "logistics_step_up_proofs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    challenge_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("logistics_step_up_challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    permission_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action_code: Mapped[str | None] = mapped_column(String(100))
    resource_type: Mapped[str | None] = mapped_column(String(100))
    resource_id: Mapped[str | None] = mapped_column(String(255))
    organization_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    branch_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    warehouse_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="active", server_default=text("'active'"), nullable=False, index=True)
    one_time: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    proof_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(20), default="1.0.0", server_default=text("'1.0.0'"), nullable=False)

    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)