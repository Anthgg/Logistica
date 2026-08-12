"""Organization model — represents the legal entity owning logistics operations."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, utc_now


class Organization(Base):
    __tablename__ = "logistics_organizations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="active", server_default=text("'active'"), nullable=False, index=True
    )
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="America/Lima", server_default=text("'America/Lima'"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    updated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))

    branches: Mapped[list["Branch"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan", passive_deletes=True
    )


# Forward reference to Branch (defined in same file for cohesion)
from app.models.branch import Branch  # noqa: E402, F401