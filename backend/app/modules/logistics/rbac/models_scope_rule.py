"""LogisticsRoleScopeRule — allowed scope types per role."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, utc_now


class LogisticsRoleScopeRule(Base):
    __tablename__ = "logistics_role_scope_rules"
    __table_args__ = (
        UniqueConstraint("role_id", "allowed_scope_type", name="uq_role_scope_type"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("logistics_roles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    allowed_scope_type: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    role: Mapped["LogisticsRole"] = relationship(back_populates="scope_rules")