"""LogisticsRole model — system catalog of logistics roles."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, utc_now


class LogisticsRole(Base):
    __tablename__ = "logistics_roles"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    role_type: Mapped[str] = mapped_column(
        String(20), default="system", server_default=text("'system'"), nullable=False, index=True
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default="active", server_default=text("'active'"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    scope_rules: Mapped[list["LogisticsRoleScopeRule"]] = relationship(
        back_populates="role", cascade="all, delete-orphan", passive_deletes=True
    )
    assignments: Mapped[list["LogisticsRoleAssignment"]] = relationship(
        back_populates="role", passive_deletes=True
    )


from app.modules.logistics.rbac.models_scope_rule import LogisticsRoleScopeRule  # noqa: E402
from app.modules.logistics.rbac.models_assignment import LogisticsRoleAssignment  # noqa: E402