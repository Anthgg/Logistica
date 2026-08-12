"""LogisticsRoleAssignment — user-role-scope assignment with temporal validity."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, utc_now


class LogisticsRoleAssignment(Base):
    __tablename__ = "logistics_role_assignments"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "role_id", "scope_type",
            "organization_id", "branch_id", "warehouse_id",
            "status",
            name="uq_assignment_active_unique",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("logistics_roles.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    organization_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=True, index=True,
    )
    branch_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("logistics_branches.id", ondelete="RESTRICT"),
        nullable=True, index=True,
    )
    warehouse_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=True, index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), default="active", server_default=text("'active'"),
        nullable=False, index=True,
    )
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assigned_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    revoked_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revocation_reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    role: Mapped["LogisticsRole"] = relationship(back_populates="assignments")