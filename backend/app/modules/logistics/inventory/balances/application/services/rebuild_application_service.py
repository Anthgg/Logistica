"""
Rebuild Application Service with Atomic Swap (Phase 045).

Implements canonical ledger rebuild from Phase 044 Event Ledger (or valid checkpoints),
staging projection (G2), hash/sequence integrity verification, pre-swap validation,
and tenant-safe atomic swap:
- G1 (active projection): is_active_projection=True, rebuild_job_id=None
- G2 (staging projection): is_active_projection=False, rebuild_job_id=<job_id>
- Canonical Source: Phase 044 Ledger (InventoryMovementModel + InventoryMovementLineModel) / Checkpoint.
  Initial quantity conceptual = Decimal("0"). G1.quantity is NEVER copied as source of truth.
- Tenant Safety: All DELETE, UPDATE, and staging operations include explicit organization_id filters.
- Pre-swap integrity check: Fails if hash mismatch or sequence gap detected in Phase 044 ledger.
- Atomic swap happens inside a single PostgreSQL transaction.
- If pre-swap validation or integrity fails, rollback_rebuild cleans up G2 and G1 remains active without interruption.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
    InventoryBalanceCheckpointModel,
    InventoryBalanceDeltaModel,
    InventoryBalanceRebuildJobModel,
    InventoryPositionBalanceModel,
)
from app.modules.logistics.inventory.ledger.application.services.integrity_service import (
    InventoryLedgerIntegrityService,
)
from app.modules.logistics.inventory.ledger.domain.value_objects.enums import VerificationStatus
from app.modules.logistics.inventory.ledger.infrastructure.persistence.models import (
    InventoryLedgerPartitionModel,
    InventoryMovementLineModel,
    InventoryMovementModel,
    InventoryPositionModel,
)


class RebuildSwapFailedError(Exception):
    """Raised when atomic swap, ledger integrity or pre-swap validation fails."""


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
        """Creates G2 (staging) projection records with is_active_projection=False.
        
        Initial quantity defaults to Decimal("0") unless explicit valid checkpoint quantity is provided.
        G1.quantity MUST NOT be used as canonical initial quantity.
        """
        job = self._db.get(InventoryBalanceRebuildJobModel, job_id)
        if not job:
            raise RebuildSwapFailedError(f"Rebuild job {job_id} not found.")

        job.status = "RUNNING"
        job.started_at = datetime.now(UTC)
        staging_rows: list[InventoryPositionBalanceModel] = []

        for item in positions_to_rebuild:
            # Force organization_id from job to prevent multi-tenant contamination
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
                availability_state=str(item.get("availability_state", "AVAILABLE")),
                quality_state=str(item.get("quality_state", "APPROVED")),
                transit_state=str(item.get("transit_state", "NOT_IN_TRANSIT")),
                damage_state=str(item.get("damage_state", "NORMAL")),
                expiration_state=str(item.get("expiration_state", "NOT_APPLICABLE")),
                dimension_key=str(item.get("dimension_key", "AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE")),
                last_applied_ledger_partition_key=str(item.get("partition_key", f"org:{job.organization_id}:default")),
                last_applied_ledger_sequence=int(str(item.get("checkpoint_sequence", 0))),
                rebuild_job_id=job_id,
                is_active_projection=False,
                data_quality_status="PROJECTION_STAGING",
            )
            staging_rows.append(row)
            self._db.add(row)

        self._db.flush()
        return staging_rows

    def verify_ledger_integrity(self, job_id: UUID) -> None:
        """Validates Phase 044 Ledger partition sequence and hash chain continuity before replay.
        
        Raises RebuildSwapFailedError if GAPS_DETECTED or HASH_MISMATCH are found.
        """
        job = self._db.get(InventoryBalanceRebuildJobModel, job_id)
        if not job:
            raise RebuildSwapFailedError("Job not found.")

        integrity_service = InventoryLedgerIntegrityService(self._db)

        # Get target partitions for this organization
        partitions_query = select(InventoryLedgerPartitionModel.partition_key).where(
            InventoryLedgerPartitionModel.organization_id == job.organization_id
        )
        if job.target_partition_key:
            partitions_query = partitions_query.where(
                InventoryLedgerPartitionModel.partition_key == job.target_partition_key
            )
        partition_keys = list(self._db.scalars(partitions_query))

        if not partition_keys:
            # Fallback to distinct movement partition keys if partitions table not populated
            mov_part_query = (
                select(InventoryMovementModel.ledger_partition_key)
                .where(InventoryMovementModel.organization_id == job.organization_id)
                .distinct()
            )
            if job.target_partition_key:
                mov_part_query = mov_part_query.where(
                    InventoryMovementModel.ledger_partition_key == job.target_partition_key
                )
            partition_keys = list(self._db.scalars(mov_part_query))

        for p_key in partition_keys:
            res = integrity_service.verify_partition(
                organization_id=job.organization_id,
                ledger_partition_key=p_key,
            )
            status = res.get("verification_status")
            if status in (VerificationStatus.HASH_MISMATCH, VerificationStatus.GAPS_DETECTED):
                self.rollback_rebuild(job_id, f"LEDGER_INTEGRITY_FAILED: {status}")
                raise RebuildSwapFailedError(f"LEDGER_INTEGRITY_FAILED: {status}")

    def execute_rebuild_from_ledger(
        self,
        job_id: UUID,
        allow_negative_stock: bool = False,
    ) -> InventoryBalanceRebuildJobModel:
        """Executes full canonical rebuild from Phase 044 Ledger movements (or valid Checkpoints).
        
        1. Verifies Phase 044 Ledger hash chain & sequence integrity.
        2. Resolves target positions and initializes G2 staging rows with initial_quantity = Decimal("0").
        3. Replays Phase 044 movement lines in strict ledger_sequence ASC order.
        4. Validates G2 staging rows.
        5. Performs tenant-safe atomic swap (deactivating G1 and activating G2).
        """
        job = self._db.get(InventoryBalanceRebuildJobModel, job_id)
        if not job:
            raise RebuildSwapFailedError(f"Job {job_id} not found.")

        try:
            # Step 1: Ledger Integrity Check
            self.verify_ledger_integrity(job_id)

            # Step 2: Checkpoint Resolution (Optional)
            checkpoint_start_seq = 0
            checkpoint = None
            if job.target_partition_key:
                checkpoint = self._db.scalars(
                    select(InventoryBalanceCheckpointModel)
                    .where(InventoryBalanceCheckpointModel.organization_id == job.organization_id)
                    .where(InventoryBalanceCheckpointModel.ledger_partition_key == job.target_partition_key)
                    .where(InventoryBalanceCheckpointModel.status == "VALID")
                    .order_by(InventoryBalanceCheckpointModel.checkpoint_sequence.desc())
                ).first()
                if checkpoint:
                    checkpoint_start_seq = checkpoint.checkpoint_sequence

            # Step 3: Resolve Inventory Positions from Phase 044 Position Model / Movements
            pos_query = select(InventoryPositionModel).where(
                InventoryPositionModel.organization_id == job.organization_id
            )
            if job.target_warehouse_id:
                pos_query = pos_query.where(InventoryPositionModel.warehouse_id == job.target_warehouse_id)
            if job.target_product_id:
                pos_query = pos_query.where(InventoryPositionModel.product_id == job.target_product_id)

            positions = list(self._db.scalars(pos_query))
            
            # Map position definitions
            positions_to_rebuild: list[dict[str, Any]] = []
            for p in positions:
                positions_to_rebuild.append(
                    {
                        "inventory_position_id": p.id,
                        "branch_id": p.branch_id,
                        "warehouse_id": p.warehouse_id,
                        "warehouse_location_id": p.warehouse_location_id,
                        "product_id": p.product_id,
                        "product_version_id": p.product_version_id,
                        "base_unit_id": p.product_id, # Fallback base unit reference
                        "initial_quantity": Decimal(0), # Canonical start quantity = 0!
                        "availability_state": p.availability_state,
                        "quality_state": p.quality_state,
                        "transit_state": p.transit_state,
                        "damage_state": p.damage_state,
                        "expiration_state": p.expiration_state,
                        "dimension_key": p.dimension_key,
                        "partition_key": f"org:{job.organization_id}:default",
                        "checkpoint_sequence": checkpoint_start_seq,
                    }
                )

            # If no positions in F044 Position Model nor G1, mark job as COMPLETED with 0 positions
            if not positions_to_rebuild:
                job.status = "COMPLETED"
                job.completed_at = datetime.now(UTC)
                self._db.flush()
                return job

            # Step 4: Prepare G2 Staging Rows
            self.prepare_staging_projection(job_id, positions_to_rebuild)

            # Step 5: Replay Phase 044 Movement Lines into G2 Staging Rows
            mov_query = (
                select(InventoryMovementModel)
                .where(InventoryMovementModel.organization_id == job.organization_id)
                .where(InventoryMovementModel.status == "POSTED")
                .order_by(
                    InventoryMovementModel.ledger_partition_key.asc(),
                    InventoryMovementModel.ledger_sequence.asc(),
                )
            )
            if checkpoint_start_seq > 0:
                mov_query = mov_query.where(InventoryMovementModel.ledger_sequence > checkpoint_start_seq)
            if job.target_partition_key:
                mov_query = mov_query.where(
                    InventoryMovementModel.ledger_partition_key == job.target_partition_key
                )

            movements = list(self._db.scalars(mov_query))
            replayed_count = 0

            # Build staging map for fast lookup: position_id -> staging_row
            staging_map = {
                row.inventory_position_id: row
                for row in self._db.scalars(
                    select(InventoryPositionBalanceModel)
                    .where(InventoryPositionBalanceModel.rebuild_job_id == job_id)
                    .where(InventoryPositionBalanceModel.organization_id == job.organization_id)
                    .where(InventoryPositionBalanceModel.is_active_projection.is_(False))
                )
            }

            for mov in movements:
                lines = self._db.scalars(
                    select(InventoryMovementLineModel)
                    .where(InventoryMovementLineModel.inventory_movement_id == mov.id)
                    .order_by(InventoryMovementLineModel.line_number.asc())
                ).all()

                for line in lines:
                    # Destination position receives stock (inbound)
                    if line.destination_position_id and line.destination_position_id in staging_map:
                        stg = staging_map[line.destination_position_id]
                        stg.quantity += line.base_quantity
                        stg.last_applied_ledger_sequence = max(
                            stg.last_applied_ledger_sequence, mov.ledger_sequence
                        )
                        stg.last_applied_movement_id = mov.id
                        stg.last_applied_movement_hash = mov.movement_hash
                        replayed_count += 1

                    # Source position loses stock (outbound)
                    if line.source_position_id and line.source_position_id in staging_map:
                        stg = staging_map[line.source_position_id]
                        stg.quantity -= line.base_quantity
                        stg.last_applied_ledger_sequence = max(
                            stg.last_applied_ledger_sequence, mov.ledger_sequence
                        )
                        stg.last_applied_movement_id = mov.id
                        stg.last_applied_movement_hash = mov.movement_hash
                        replayed_count += 1

            # Also replay Phase 045 InventoryBalanceDeltaModel if present
            deltas = list(
                self._db.scalars(
                    select(InventoryBalanceDeltaModel)
                    .where(InventoryBalanceDeltaModel.organization_id == job.organization_id)
                    .order_by(InventoryBalanceDeltaModel.ledger_sequence.asc())
                )
            )
            if deltas:
                for delta in deltas:
                    if delta.position_id in staging_map:
                        stg = staging_map[delta.position_id]
                        if delta.delta_type in ("INCREASE", "INBOUND", "POSITIVE"):
                            stg.quantity += delta.delta_quantity
                        elif delta.delta_type in ("DECREASE", "OUTBOUND", "NEGATIVE"):
                            stg.quantity -= delta.delta_quantity
                        stg.last_applied_ledger_sequence = max(
                            stg.last_applied_ledger_sequence, delta.ledger_sequence
                        )
                        replayed_count += 1

            job.movements_replayed = replayed_count

            # Step 6: Pre-Swap Validation
            self.validate_staging(job_id, allow_negative_stock=allow_negative_stock)

            # Step 7: Tenant-Safe Atomic Swap
            self.execute_atomic_swap(job_id)

            return job

        except Exception as exc:
            self.rollback_rebuild(job_id, str(exc))
            raise

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
            if delta.organization_id != job.organization_id:
                raise RebuildSwapFailedError("CROSS_TENANT_LEDGER_MISMATCH: Delta organization_id does not match job.")

            staging_row = self._db.scalars(
                select(InventoryPositionBalanceModel)
                .where(InventoryPositionBalanceModel.rebuild_job_id == job_id)
                .where(InventoryPositionBalanceModel.organization_id == job.organization_id)
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
        staging_rows = list(
            self._db.scalars(
                select(InventoryPositionBalanceModel)
                .where(InventoryPositionBalanceModel.rebuild_job_id == job_id)
                .where(InventoryPositionBalanceModel.organization_id == job.organization_id)
                .where(InventoryPositionBalanceModel.is_active_projection.is_(False))
            )
        )

        if not staging_rows:
            job.status = "FAILED"
            raise RebuildSwapFailedError("PRE_SWAP_VALIDATION_FAILED: No staging rows created.")

        for row in staging_rows:
            if row.organization_id != job.organization_id:
                job.status = "FAILED"
                raise RebuildSwapFailedError(
                    f"CROSS_TENANT_LEDGER_MISMATCH: Staging row org {row.organization_id} != job org {job.organization_id}"
                )

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
        Executes tenant-safe atomic replacement in a SINGLE database transaction.
        
        1. Deactivates/removes old G1 active rows ONLY for job.organization_id and positions in G2.
        2. Activates G2 staging rows ONLY for job.organization_id (is_active_projection = True, rebuild_job_id = None).
        3. Sets job status = COMPLETED.
        """
        job = self._db.get(InventoryBalanceRebuildJobModel, job_id)
        if not job or job.status != "READY_TO_SWAP":
            raise RebuildSwapFailedError(f"Job {job_id} is not READY_TO_SWAP.")

        job.status = "SWAPPING"

        # Get positions in staging for THIS organization
        staging_positions = list(
            self._db.scalars(
                select(InventoryPositionBalanceModel.inventory_position_id)
                .where(InventoryPositionBalanceModel.rebuild_job_id == job_id)
                .where(InventoryPositionBalanceModel.organization_id == job.organization_id)
                .where(InventoryPositionBalanceModel.is_active_projection.is_(False))
            )
        )

        if not staging_positions:
            raise RebuildSwapFailedError("No staging rows to swap.")

        # Deactivate or delete old G1 active rows STRICTLY for job.organization_id
        self._db.execute(
            delete(InventoryPositionBalanceModel)
            .where(InventoryPositionBalanceModel.organization_id == job.organization_id)
            .where(InventoryPositionBalanceModel.inventory_position_id.in_(staging_positions))
            .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
        )

        # Activate G2 staging rows STRICTLY for job.organization_id
        self._db.execute(
            update(InventoryPositionBalanceModel)
            .where(InventoryPositionBalanceModel.rebuild_job_id == job_id)
            .where(InventoryPositionBalanceModel.organization_id == job.organization_id)
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
        """Removes G2 staging rows for job.organization_id and sets job status = FAILED."""
        job = self._db.get(InventoryBalanceRebuildJobModel, job_id)

        if job:
            # Delete G2 staging rows strictly filtered by organization_id
            self._db.execute(
                delete(InventoryPositionBalanceModel)
                .where(InventoryPositionBalanceModel.rebuild_job_id == job_id)
                .where(InventoryPositionBalanceModel.organization_id == job.organization_id)
                .where(InventoryPositionBalanceModel.is_active_projection.is_(False))
            )
            job.status = "FAILED"
            job.completed_at = datetime.now(UTC)

        self._db.flush()
