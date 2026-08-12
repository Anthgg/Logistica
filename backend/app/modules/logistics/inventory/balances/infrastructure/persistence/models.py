"""Phase 045 — Inventory balance ORM models (materialized projection).

Contains the 11 authorized tables for inventory position balances:
1. inventory_position_balances
2. inventory_balance_deltas
3. inventory_balance_projection_cursors
4. inventory_balance_formula_definitions
5. inventory_balance_formula_versions
6. inventory_balance_checkpoints
7. inventory_balance_rebuild_jobs
8. inventory_balance_rebuild_differences
9. inventory_balance_reconciliation_jobs
10. inventory_balance_reconciliation_differences
11. inventory_balance_export_jobs
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def _uuid() -> UUID:
    return uuid4()


def _utcnow() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# 1. Materialized Position Balance
# ---------------------------------------------------------------------------


class InventoryPositionBalanceModel(Base):
    """Saldo atómico materializado por InventoryPosition (Fase 045)."""
    __tablename__ = "inventory_position_balances"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    branch_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    warehouse_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    warehouse_location_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    inventory_position_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    rebuild_job_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("inventory_balance_rebuild_jobs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_active_projection: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    product_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    product_version_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    base_unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False, default=Decimal("0.000000000000000000"), index=True)

    availability_state: Mapped[str] = mapped_column(String(50), nullable=False, default="UNKNOWN", index=True)
    quality_state: Mapped[str] = mapped_column(String(50), nullable=False, default="UNKNOWN", index=True)
    transit_state: Mapped[str] = mapped_column(String(50), nullable=False, default="NOT_IN_TRANSIT", index=True)
    damage_state: Mapped[str] = mapped_column(String(50), nullable=False, default="NORMAL", index=True)
    expiration_state: Mapped[str] = mapped_column(String(50), nullable=False, default="NOT_APPLICABLE", index=True)

    ownership_type: Mapped[str] = mapped_column(String(50), nullable=False, default="OWNED")
    owner_business_partner_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    tracking_reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tracking_reference_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    handling_unit_reference_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    dimension_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    last_applied_ledger_partition_key: Mapped[str] = mapped_column(String(120), nullable=False)
    last_applied_ledger_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_applied_movement_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    last_applied_movement_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    balance_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    data_quality_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PROJECTION_CURRENT")
    reconciliation_status: Mapped[str] = mapped_column(String(50), nullable=False, default="RECONCILED", index=True)

    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


# ---------------------------------------------------------------------------
# 2. Materialized Balance Delta
# ---------------------------------------------------------------------------


class InventoryBalanceDeltaModel(Base):
    """Delta de saldo materializado derivado de una línea de movimiento MOV (Fase 045)."""
    __tablename__ = "inventory_balance_deltas"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    ledger_partition_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    ledger_sequence: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    movement_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    movement_line_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    position_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    product_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    warehouse_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    location_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    delta_type: Mapped[str] = mapped_column(String(50), nullable=False)
    delta_quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    base_unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    movement_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    materialization_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)

    applied_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING", index=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    balance_before: Mapped[Decimal | None] = mapped_column(Numeric(38, 18), nullable=True)
    balance_after: Mapped[Decimal | None] = mapped_column(Numeric(38, 18), nullable=True)
    consumer_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ---------------------------------------------------------------------------
# 3. Projection Cursor
# ---------------------------------------------------------------------------


class InventoryBalanceProjectionCursorModel(Base):
    """Cursor de secuencia y lag por partición de inventario (Fase 045)."""
    __tablename__ = "inventory_balance_projection_cursors"
    __table_args__ = (
        UniqueConstraint("organization_id", "ledger_partition_key", name="uq_cursor_org_partition"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    ledger_partition_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)

    last_applied_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_applied_movement_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    last_applied_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="CURRENT", index=True)
    lag_movement_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lag_seconds: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, default=Decimal("0.000"))

    last_success_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(50), nullable=True)

    consumer_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


# ---------------------------------------------------------------------------
# 4. Formula Definition & Versions
# ---------------------------------------------------------------------------


class InventoryBalanceFormulaDefinitionModel(Base):
    """Definición declarativa de fórmulas de cálculo de saldos (Fase 045)."""
    __tablename__ = "inventory_balance_formula_definitions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    metric_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    dimension_family: Mapped[str] = mapped_column(String(50), nullable=False)
    aggregation_type: Mapped[str] = mapped_column(String(50), nullable=False, default="SUM")
    mutually_exclusive_group: Mapped[str | None] = mapped_column(String(50), nullable=True)
    overlap_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    active_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class InventoryBalanceFormulaVersionModel(Base):
    """Versión declarativa de fórmula de saldos (Fase 045)."""
    __tablename__ = "inventory_balance_formula_versions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    formula_definition_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("inventory_balance_formula_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    expression_rules: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ---------------------------------------------------------------------------
# 5. Checkpoints, Rebuild & Reconciliation Jobs
# ---------------------------------------------------------------------------


class InventoryBalanceCheckpointModel(Base):
    """Snapshot de saldo para aceleración de reconstrucción (Fase 045)."""
    __tablename__ = "inventory_balance_checkpoints"
    __table_args__ = (
        UniqueConstraint("ledger_partition_key", "checkpoint_sequence", name="uq_balance_checkpoint_partition_seq"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    ledger_partition_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)

    checkpoint_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    checkpoint_movement_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    checkpoint_movement_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    balance_manifest_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    position_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_product_count: Mapped[int] = mapped_column(Integer, nullable=False)
    formula_version_set: Mapped[str] = mapped_column(String(100), nullable=False, default="1.0.0")
    projection_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="VALID")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class InventoryBalanceRebuildJobModel(Base):
    """Trabajo de reconstrucción total o parcial de saldos (Fase 045)."""
    __tablename__ = "inventory_balance_rebuild_jobs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    rebuild_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    target_warehouse_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    target_product_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    target_position_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    target_partition_key: Mapped[str | None] = mapped_column(String(120), nullable=True)

    as_of_sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING", index=True)

    positions_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    movements_replayed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    differences_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    initiated_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    step_up_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class InventoryBalanceRebuildDifferenceModel(Base):
    """Diferencias detectadas durante un trabajo de rebuild (Fase 045)."""
    __tablename__ = "inventory_balance_rebuild_differences"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    rebuild_job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("inventory_balance_rebuild_jobs.id"), nullable=False
    )

    position_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    product_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    warehouse_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    current_projected_quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    replayed_ledger_quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    difference_quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class InventoryBalanceReconciliationJobModel(Base):
    """Trabajo de auditoría y reconciliación de saldos (Fase 045)."""
    __tablename__ = "inventory_balance_reconciliation_jobs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    warehouse_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING", index=True)
    total_positions_audited: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_differences_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    initiated_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class InventoryBalanceReconciliationDifferenceModel(Base):
    """Detalle de inconsistencia detectada en reconciliación de saldo (Fase 045)."""
    __tablename__ = "inventory_balance_reconciliation_differences"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    reconciliation_job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("inventory_balance_reconciliation_jobs.id"), nullable=False
    )
    difference_type: Mapped[str] = mapped_column(String(50), nullable=False)

    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    warehouse_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    product_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    position_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    projected_quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    replay_quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    difference_quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    expected_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    resolution_status: Mapped[str] = mapped_column(String(50), nullable=False, default="OPEN", index=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class InventoryBalanceExportJobModel(Base):
    """Trabajo de exportación asíncrona de saldos de inventario (Fase 045)."""
    __tablename__ = "inventory_balance_export_jobs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=_uuid)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    filter_params: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
