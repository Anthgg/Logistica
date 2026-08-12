"""LogisticsRoleConflictRule — separation of duties rules."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utc_now


class LogisticsRoleConflictRule(Base):
    __tablename__ = "logistics_role_conflict_rules"
    __table_args__ = (
        UniqueConstraint("role_a_id", "role_b_id", name="uq_role_conflict_pair"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    role_a_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("logistics_roles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    role_b_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("logistics_roles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    conflict_type: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="'active'")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)