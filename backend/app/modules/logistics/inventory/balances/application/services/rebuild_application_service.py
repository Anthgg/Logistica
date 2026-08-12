"""
Rebuild Application Service with Atomic Swap (Phase 045).

Implements staging projection, replay, pre-swap validation, and atomic swap:
- G1 (active projection): is_active_projection=True, rebuild_job_id=None
- G2 (staging projection): is_active_projection=False, rebuild_job_id=<job_id>
- Atomic swap happens inside a single PostgreSQL transaction.
- If pre-swap validation fails, rollback_rebuild cleans up G2 and G1 remains active without interruption.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
    InventoryBalanceDeltaModel,
    InventoryBalanceRebuildJobModel,
    InventoryPositionBalanceModel,
)


class RebuildSwapFailedError(Exception):
    """Raised when atomic swap or pre-swap validation fails."""


class BalanceRebuildApplicationService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create_rebuild_job(
        self,
        *,
        organization_id: UUID,
        initiated_by_user_id: UUID,
        rebuild_mode: str = "FULL",
        target_warehouse_id: UUID | None = None,
        target_product_id: UUID | None = None,
        target_partition_key: str | None = None,
        step_up_verified: bool = False,
    ) -> InventoryBalanceRebuildJobModel:
        job = InventoryBalanceRebuildJobModel(
            id=uuid4(),
            organization_id=organization_id,
            rebuild_mode=rebuild_mode,
            target_warehouse_id=target_warehouse_id,
            target_product_id=target_product_id,
            target_partition_key=target_partition_key,
            status="PENDING",
            initiated_by_user_id=initiated_by_user_id,
            step_up_verified=step_up_verified,
            created_at=datetime.now(UTC),
        )
        self._db.add(job)
        self._db.flush()
        return job

    def prepare_staging_projection(
        self,
        job_id: UUID,
        positions_to_rebuild: Sequence[Mapping[str, object]],
    ) -> list[InventoryPositionBalanceModel]:
        """Creates G2 (staging) projection records with is_active_projection=False."""
        job = self._db.get(InventoryBalanceRebuildJobModel, job_id)
        if not job:
            raise RebuildSwapFailedError(f"Rebuild job {job_id} not found.")

        job.status = "RUNNING"
        job.started_at = datetime.now(UTC)
        staging_rows: list[InventoryPositionBalanceModel] = []

        for item in positions_to_rebuild:
            row = InventoryPositionBalanceModel(
                id=uuid4(),
                organization_id=job.organization_id,
                branch_id=item.get("branch_id", uuid4()),
                warehouse_id=item.get("warehouse_id"),
                warehouse_location_id=item.get("warehouse_location_id"),
                inventory_position_id=item["inventory_position_id"],
                product_id=item["product_id"],
                product_version_id=item.get("product_version_id"),
                base_unit_id=item["base_unit_id"],
                quantity=Decimal(str(item.get("initial_quantity", "0"))),
                dimension_key=item.get("dimension_key", "AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE"),
                last_applied_ledger_partition_key=item.get("partition_key", f"org:{job.organization_id}:default"),
                last_applied_ledger_sequence=0,
                rebuild_job_id=job_id,
                is_active_projection=False,
                data_quality_status="PROJECTION_STAGING",
            )
            staging_rows.append(row)
            self._db.add(row)

        self._db.flush()
        return staging_rows

    def replay_deltas_into_staging(
        self,
        job_id: UUID,
        deltas: Sequence[InventoryBalanceDeltaModel],
    ) -> int:
        """Applies deltas to G2 staging rows without touching active G1 rows."""
        job = self._db.get(InventoryBalanceRebuildJobModel, job_id)
        if not job or job.status != "RUNNING":
            raise RebuildSwapFailedError("Job is not in RUNNING state.")

        replayed_count = 0
        for delta in deltas:
            staging_row = self._db.scalars(
                select(InventoryPositionBalanceModel)
                .where(InventoryPositionBalanceModel.rebuild_job_id == job_id)
                .where(InventoryPositionBalanceModel.inventory_position_id == delta.position_id)
                .where(InventoryPositionBalanceModel.is_active_projection.is_(False))
            ).first()

            if staging_row:
                if delta.delta_type in ("INCREASE", "INBOUND", "POSITIVE"):
                    staging_row.quantity += delta.delta_quantity
                elif delta.delta_type in ("DECREASE", "OUTBOUND", "NEGATIVE"):
                    staging_row.quantity -= delta.delta_quantity
                staging_row.last_applied_ledger_sequence = max(
                    staging_row.last_applied_ledger_sequence, delta.ledger_sequence
                )
                replayed_count += 1

        job.movements_replayed += replayed_count
        self._db.flush()
        return replayed_count

    def validate_staging(self, job_id: UUID, allow_negative_stock: bool = False) -> bool:
        """Pre-swap validation on G2 staging rows."""
        job = self._db.get(InventoryBalanceRebuildJobModel, job_id)
        if not job:
            raise RebuildSwapFailedError("Job not found.")

        job.status = "VALIDATING"
        staging_rows = self._db.scalars(
            select(InventoryPositionBalanceModel)
            .where(InventoryPositionBalanceModel.rebuild_job_id == job_id)
            .where(InventoryPositionBalanceModel.is_active_projection.is_(False))
        ).all()

        if not staging_rows:
            job.status = "FAILED"
            raise RebuildSwapFailedError("PRE_SWAP_VALIDATION_FAILED: No staging rows created.")

        for row in staging_rows:
            if not allow_negative_stock and row.quantity < Decimal(0):
                job.status = "FAILED"
                raise RebuildSwapFailedError(
                    f"PRE_SWAP_VALIDATION_FAILED: Negative stock ({row.quantity}) in position {row.inventory_position_id}"
                )

        job.status = "READY_TO_SWAP"
        job.positions_processed = len(staging_rows)
        self._db.flush()
        return True

    def execute_atomic_swap(self, job_id: UUID) -> bool:
        """
        Executes atomic replacement in a SINGLE database transaction.
        
        1. Deactivates/removes old G1 active rows for the positions in G2.
        2. Activates G2 staging rows (is_active_projection = True, rebuild_job_id = None).
        3. Sets job status = COMPLETED.
        """
        job = self._db.get(InventoryBalanceRebuildJobModel, job_id)
        if not job or job.status != "READY_TO_SWAP":
            raise RebuildSwapFailedError(f"Job {job_id} is not READY_TO_SWAP.")

        job.status = "SWAPPING"

        # Get positions in staging
        staging_positions = self._db.scalars(
            select(InventoryPositionBalanceModel.inventory_position_id)
            .where(InventoryPositionBalanceModel.rebuild_job_id == job_id)
            .where(InventoryPositionBalanceModel.is_active_projection.is_(False))
        ).all()

        if not staging_positions:
            raise RebuildSwapFailedError("No staging rows to swap.")

        # Deactivate or delete old G1 active rows for these positions
        self._db.execute(
            delete(InventoryPositionBalanceModel)
            .where(InventoryPositionBalanceModel.inventory_position_id.in_(staging_positions))
            .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
        )

        # Activate G2 staging rows
        self._db.execute(
            update(InventoryPositionBalanceModel)
            .where(InventoryPositionBalanceModel.rebuild_job_id == job_id)
            .where(InventoryPositionBalanceModel.is_active_projection.is_(False))
            .values(
                is_active_projection=True,
                rebuild_job_id=None,
                data_quality_status="PROJECTION_CURRENT",
                updated_at=datetime.now(UTC),
            )
        )

        job.status = "COMPLETED"
        job.completed_at = datetime.now(UTC)
        self._db.flush()
        return True

    def rollback_rebuild(self, job_id: UUID, error_message: str | None = None) -> None:
        """Removes G2 staging rows and sets job status = FAILED."""
        job = self._db.get(InventoryBalanceRebuildJobModel, job_id)

        # Delete G2 staging rows
        self._db.execute(
            delete(InventoryPositionBalanceModel)
            .where(InventoryPositionBalanceModel.rebuild_job_id == job_id)
            .where(InventoryPositionBalanceModel.is_active_projection.is_(False))
        )

        if job:
            job.status = "FAILED"
            job.completed_at = datetime.now(UTC)

        self._db.flush()
