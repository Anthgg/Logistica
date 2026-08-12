from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, utc_now

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.device import Device
    from app.models.user import User


class UserSession(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint(
            "continuous_auth_status IN "
            "('pending', 'active', 'degraded', "
            "'verification_required', 'restricted', 'terminated')",
            name="ck_sessions_continuous_auth_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    device_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL")
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    refresh_token_hash: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True
    )
    previous_refresh_token_hash: Mapped[str | None] = mapped_column(
        String(255), index=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    refresh_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=Decimal("0"), server_default=text("0")
    )
    authentication_level: Mapped[str] = mapped_column(
        String(50), default="traditional", server_default=text("'traditional'")
    )
    last_continuous_verification_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    last_risk_action: Mapped[str | None] = mapped_column(String(60))
    continuous_auth_status: Mapped[str] = mapped_column(
        String(30), default="pending", server_default=text("'pending'")
    )
    created_by_login: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true")
    )

    user: Mapped["User"] = relationship(back_populates="sessions")
    device: Mapped["Device | None"] = relationship(back_populates="sessions")
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="session", passive_deletes=True
    )
