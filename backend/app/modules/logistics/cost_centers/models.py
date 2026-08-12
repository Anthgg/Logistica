"""ORM models for Cost Center master (Phase 031)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CostCenterModel(Base):
    """Master table for cost centers — no budget, no accounting."""

    __tablename__ = "cost_centers"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "normalized_code",
            name="uq_cost_centers_org_normalized_code",
        ),
        CheckConstraint(
            "parent_cost_center_id != id",
            name="ck_cost_center_no_self_parent",
        ),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    branch_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_branches.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    code = Column(String(50), nullable=False)
    normalized_code = Column(String(50), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    responsible_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    parent_cost_center_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("cost_centers.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    status = Column(String(20), nullable=False, default="DRAFT", index=True)
    valid_from = Column(Date, nullable=False, default=date.today)
    valid_until = Column(Date, nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=False)
    row_version = Column(Integer, nullable=False, default=1)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    parent = relationship(
        "CostCenterModel",
        remote_side=[id],
        backref="children",
        foreign_keys=[parent_cost_center_id],
    )
