"""LogisticsPermissionScopeRule — allowed scope types per permission."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, utc_now


class LogisticsPermissionScopeRule(Base):
    __tablename__ = "logistics_permission_scope_rules"
    __table_args__ = (
        UniqueConstraint("permission_id", "allowed_scope_type", name="uq_perm_scope_type"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    permission_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("logistics_permissions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    allowed_scope_type: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    permission: Mapped["LogisticsPermission"] = relationship(back_populates="scope_rules")