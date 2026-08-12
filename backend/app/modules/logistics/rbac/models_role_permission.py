"""LogisticsRolePermission — maps permissions to roles."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, utc_now


class LogisticsRolePermission(Base):
    __tablename__ = "logistics_role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("logistics_roles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    permission_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("logistics_permissions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    effect: Mapped[str] = mapped_column(String(10), default="allow", server_default="'allow'", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))

    role: Mapped["LogisticsRole"] = relationship()  # noqa: F821
    permission: Mapped["LogisticsPermission"] = relationship(back_populates="role_permissions")