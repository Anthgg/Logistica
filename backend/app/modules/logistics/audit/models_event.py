"""Unified logistics audit event model — immutable, hash-verified."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utc_now

JSON_TYPE = JSONB().with_variant(JSON(), "sqlite")


class LogisticsAuditEvent(Base):
    __tablename__ = "logistics_audit_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # --- Identity ---
    event_code: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    event_category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_version: Mapped[str] = mapped_column(String(20), default="1.0", server_default=text("'1.0'"), nullable=False)

    # --- Actor ---
    actor_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_type: Mapped[str] = mapped_column(String(30), default="user", server_default=text("'user'"), nullable=False)
    actor_display_name_snapshot: Mapped[str | None] = mapped_column(String(200))
    actor_role_codes_snapshot: Mapped[str | None] = mapped_column(Text)

    # --- Session & Device ---
    session_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    device_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    authentication_level: Mapped[str | None] = mapped_column(String(30))
    risk_score: Mapped[float | None] = mapped_column()
    step_up_required: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    step_up_result: Mapped[str | None] = mapped_column(String(30))

    # --- Organizational context ---
    organization_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    branch_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    warehouse_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)

    # --- Request context ---
    request_id: Mapped[str | None] = mapped_column(String(100), index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(100), index=True)
    method: Mapped[str | None] = mapped_column(String(10))
    endpoint: Mapped[str | None] = mapped_column(String(500))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    origin: Mapped[str | None] = mapped_column(String(500))

    # --- Timing ---
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # --- Resource ---
    resource_type: Mapped[str | None] = mapped_column(String(100), index=True)
    resource_id: Mapped[str | None] = mapped_column(String(255))
    resource_code: Mapped[str | None] = mapped_column(String(100))
    parent_resource_type: Mapped[str | None] = mapped_column(String(100))
    parent_resource_id: Mapped[str | None] = mapped_column(String(255))

    # --- Action ---
    action: Mapped[str | None] = mapped_column(String(50))
    result: Mapped[str] = mapped_column(String(20), default="success", server_default=text("'success'"), nullable=False, index=True)
    reason_code: Mapped[str | None] = mapped_column(String(50))
    reason_text: Mapped[str | None] = mapped_column(String(500))
    severity: Mapped[str] = mapped_column(String(20), default="info", server_default=text("'info'"), nullable=False, index=True)

    # --- Changes ---
    previous_data: Mapped[dict[str, Any] | None] = mapped_column(JSON_TYPE)
    new_data: Mapped[dict[str, Any] | None] = mapped_column(JSON_TYPE)
    changed_fields: Mapped[list[str] | None] = mapped_column(JSON_TYPE)

    # --- Metadata ---
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON_TYPE)
    source_module: Mapped[str | None] = mapped_column(String(50))
    source_service: Mapped[str | None] = mapped_column(String(100))

    # --- Integrity ---
    event_hash: Mapped[str | None] = mapped_column(String(128))
    hash_algorithm: Mapped[str] = mapped_column(String(20), default="sha256", server_default=text("'sha256'"), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), default="1.0", server_default=text("'1.0'"), nullable=False)

    # --- Timestamp ---
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)