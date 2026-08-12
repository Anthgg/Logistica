"""LogisticsPermission model — system catalog of granular permissions."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, utc_now


class LogisticsPermission(Base):
    __tablename__ = "logistics_permissions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    resource: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(
        String(20), default="low", server_default=text("'low'"), nullable=False, index=True
    )
    is_sensitive: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    requires_reason: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    requires_step_up: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
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

    scope_rules: Mapped[list["LogisticsPermissionScopeRule"]] = relationship(
        back_populates="permission", cascade="all, delete-orphan", passive_deletes=True
    )
    role_permissions: Mapped[list["LogisticsRolePermission"]] = relationship(
        back_populates="permission", passive_deletes=True
    )


from app.modules.logistics.rbac.models_role_permission import LogisticsRolePermission  # noqa: E402
from app.modules.logistics.rbac.models_permission_scope import LogisticsPermissionScopeRule  # noqa: E402