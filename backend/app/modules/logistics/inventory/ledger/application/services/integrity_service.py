"""Inventory ledger integrity, snapshot and reconciliation services."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
    InventoryLedgerCheckpointFailed,
    InventoryLedgerIntegrityFailed,
    InventoryLedgerReconciliationFailed,
)
from app.modules.logistics.inventory.ledger.domain.services.hash_service import (
    hash_payload,
)
from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
    CANONICALIZATION_VERSION as _CV,
    CheckpointStatus,
    ReconciliationResult,
    VerificationStatus,
)
from app.modules.logistics.inventory.ledger.infrastructure.persistence.models import (
    InventoryLedgerCheckpointModel,
    InventoryLedgerReconciliationJobModel,
    InventoryLedgerReconciliationResultModel,
    InventoryMovementModel,
)


# ---------------------------------------------------------------------------
# Hash chain integrity
# ---------------------------------------------------------------------------

class InventoryLedgerIntegrityService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def verify_partition(
        self,
        *,
        organization_id: UUID,
        ledger_partition_key: str,
        from_sequence: int | None = None,
        to_sequence: int | None = None,
    ) -> dict:
        filters = [
            InventoryMovementModel.organization_id == organization_id,
            InventoryMovementModel.ledger_partition_key == ledger_partition_key,
        ]
        if from_sequence is not None:
            filters.append(InventoryMovementModel.ledger_sequence >= from_sequence)
        if to_sequence is not None:
            filters.append(InventoryMovementModel.ledger_sequence <= to_sequence)
        movements = self._db.scalars(
            select(InventoryMovementModel)
            .where(*filters)
            .order_by(InventoryMovementModel.ledger_sequence.asc())
        ).all()

        previous_hash: str | None = None
        gap_detected = False
        hash_mismatch = False
        last_sequence = 0
        first_hash: str | None = None
        last_hash: str | None = None
        for movement in movements:
            if last_sequence and movement.ledger_sequence != last_sequence + 1:
                gap_detected = True
                break
            last_sequence = movement.ledger_sequence
            if first_hash is None:
                first_hash = movement.movement_hash
            if movement.previous_movement_hash != previous_hash:
                hash_mismatch = True
                break
            previous_hash = movement.movement_hash
            last_hash = movement.movement_hash

        if gap_detected:
            return {
                "verification_status": VerificationStatus.GAPS_DETECTED,
                "last_sequence": last_sequence,
                "first_hash": first_hash,
                "last_hash": last_hash,
            }
        if hash_mismatch:
            return {
                "verification_status": VerificationStatus.HASH_MISMATCH,
                "last_sequence": last_sequence,
                "first_hash": first_hash,
                "last_hash": last_hash,
            }
        return {
            "verification_status": VerificationStatus.OK,
            "last_sequence": last_sequence,
            "first_hash": first_hash,
            "last_hash": last_hash,
        }


# ---------------------------------------------------------------------------
# Checkpoints
# ---------------------------------------------------------------------------

class InventoryLedgerCheckpointService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        organization_id: UUID,
        ledger_partition_key: str,
        from_sequence: int,
        to_sequence: int,
    ) -> InventoryLedgerCheckpointModel:
        filters = [
            InventoryMovementModel.organization_id == organization_id,
            InventoryMovementModel.ledger_partition_key == ledger_partition_key,
            InventoryMovementModel.ledger_sequence >= from_sequence,
            InventoryMovementModel.ledger_sequence <= to_sequence,
        ]
        movements = self._db.scalars(
            select(InventoryMovementModel)
            .where(*filters)
            .order_by(InventoryMovementModel.ledger_sequence.asc())
        ).all()
        if not movements:
            raise InventoryLedgerCheckpointFailed(
                "No movements found for the requested range.",
            )
        if movements[0].ledger_sequence != from_sequence:
            raise InventoryLedgerCheckpointFailed(
                "from_sequence does not match the first movement in the partition.",
            )
        if movements[-1].ledger_sequence != to_sequence:
            raise InventoryLedgerCheckpointFailed(
                "to_sequence does not match the last movement in the partition.",
            )
        first_hash = movements[0].movement_hash
        last_hash = movements[-1].movement_hash
        manifest = {
            "organization_id": str(organization_id),
            "ledger_partition_key": ledger_partition_key,
            "from_sequence": from_sequence,
            "to_sequence": to_sequence,
            "movement_count": len(movements),
            "first_hash": first_hash,
            "last_hash": last_hash,
            "canonicalization_version": _CV,
        }
        manifest_hash = hash_payload(manifest)
        record = InventoryLedgerCheckpointModel(
            organization_id=organization_id,
            ledger_partition_key=ledger_partition_key,
            from_sequence=from_sequence,
            to_sequence=to_sequence,
            movement_count=len(movements),
            first_hash=first_hash,
            last_hash=last_hash,
            manifest_hash=manifest_hash,
            verification_status=CheckpointStatus.VERIFYING.value,
            algorithm_version=_CV,
        )
        self._db.add(record)
        self._db.flush()
        # Immediately verify.
        integrity = InventoryLedgerIntegrityService(self._db)
        verification = integrity.verify_partition(
            organization_id=organization_id,
            ledger_partition_key=ledger_partition_key,
            from_sequence=from_sequence,
            to_sequence=to_sequence,
        )
        if verification["verification_status"] == VerificationStatus.OK:
            record.verification_status = CheckpointStatus.VALID.value
        else:
            record.verification_status = CheckpointStatus.INVALID.value
        record.verified_at = datetime.now(timezone.utc)
        record.verified_by_service = "inventory_ledger.checkpoint_service"
        self._db.flush()
        return record


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------

class InventoryMovementSnapshotProvider:
    def __init__(self, db: Session) -> None:
        self._db = db

    def build(
        self, organization_id: UUID, movement_id: UUID
    ) -> dict:
        movement = self._db.get(InventoryMovementModel, movement_id)
        if movement is None or movement.organization_id != organization_id:
            raise InventoryLedgerIntegrityFailed(
                "Movement not found for snapshot.",
            )
        from app.modules.logistics.inventory.ledger.application.services.kardex_query_service import (
            InventoryKardexQueryService,
        )

        detail = InventoryKardexQueryService(self._db).get_movement_detail(
            organization_id=organization_id, movement_id=movement_id
        )
        snapshot = {
            "movement": {
                "id": str(movement.id),
                "movement_code": movement.movement_code,
                "movement_type": movement.movement_type,
                "movement_family": movement.movement_family,
                "status": movement.status,
                "ledger_partition_key": movement.ledger_partition_key,
                "ledger_sequence": movement.ledger_sequence,
                "occurred_at": movement.occurred_at.isoformat(),
                "posted_at": movement.posted_at.isoformat(),
                "organization_id": str(movement.organization_id),
                "branch_id": str(movement.branch_id),
                "warehouse_id": (
                    str(movement.warehouse_scope_id) if movement.warehouse_scope_id else None
                ),
                "reason_code": movement.reason_code,
                "reason_description": movement.reason_description,
                "previous_movement_hash": movement.previous_movement_hash,
                "movement_hash": movement.movement_hash,
            },
            "lines": [
                {
                    "line_number": line.line_number,
                    "product_id": str(line.product_id),
                    "product_version_id": str(line.product_version_id)
                    if line.product_version_id
                    else None,
                    "quantity": str(line.quantity),
                    "unit_id": str(line.unit_id),
                    "base_quantity": str(line.base_quantity),
                    "base_unit_id": str(line.base_unit_id),
                    "source_position_id": str(line.source_position_id)
                    if line.source_position_id
                    else None,
                    "destination_position_id": str(line.destination_position_id)
                    if line.destination_position_id
                    else None,
                    "source_position_snapshot": line.source_position_snapshot,
                    "destination_position_snapshot": line.destination_position_snapshot,
                    "source_external_boundary_kind": line.source_external_boundary_kind,
                    "destination_external_boundary_kind": line.destination_external_boundary_kind,
                    "quantity_direction": line.quantity_direction,
                    "content_hash": line.content_hash,
                }
                for line in detail["lines"]
            ],
            "sources": [
                {
                    "source_system": source.source_system,
                    "source_event_type": source.source_event_type,
                    "source_event_id": source.source_event_id,
                    "source_event_version": source.source_event_version,
                    "source_document_type": source.source_document_type,
                    "source_document_id": str(source.source_document_id)
                    if source.source_document_id
                    else None,
                    "source_document_code": source.source_document_code,
                    "source_hash": source.source_hash,
                    "adapter_name": source.adapter_name,
                    "adapter_version": source.adapter_version,
                }
                for source in detail["sources"]
            ],
            "positions": [
                {
                    "id": str(pos.id),
                    "boundary_type": pos.boundary_type,
                    "warehouse_id": str(pos.warehouse_id) if pos.warehouse_id else None,
                    "warehouse_location_id": str(pos.warehouse_location_id)
                    if pos.warehouse_location_id
                    else None,
                    "availability_state": pos.availability_state,
                    "quality_state": pos.quality_state,
                    "transit_state": pos.transit_state,
                    "damage_state": pos.damage_state,
                    "expiration_state": pos.expiration_state,
                    "dimension_key": pos.dimension_key,
                }
                for pos in detail["positions"]
            ],
            "compensation": (
                {
                    "id": str(detail["compensation"].id),
                    "movement_code": detail["compensation"].movement_code,
                    "movement_hash": detail["compensation"].movement_hash,
                }
                if detail["compensation"] is not None
                else None
            ),
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }
        snapshot["content_hash"] = hash_payload(snapshot)
        return snapshot


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------

class InventoryLedgerReconciliationService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def run(
        self,
        *,
        organization_id: UUID,
        scope: Mapping[str, object],
        requested_by_user_id: UUID | None = None,
    ) -> InventoryLedgerReconciliationJobModel:
        job = InventoryLedgerReconciliationJobModel(
            organization_id=organization_id,
            scope=dict(scope),
            status="RUNNING",
            triggered_by="MANUAL" if requested_by_user_id else "SCHEDULED",
            requested_by_user_id=requested_by_user_id,
            started_at=datetime.now(timezone.utc),
        )
        self._db.add(job)
        self._db.flush()
        try:
            self._execute(job)
        except Exception as exc:  # noqa: BLE001
            job.status = "FAILED"
            job.completed_at = datetime.now(timezone.utc)
            job.summary = {"error": str(exc)[:500]}
            self._db.flush()
            raise InventoryLedgerReconciliationFailed(str(exc)) from exc
        job.status = "COMPLETED"
        job.completed_at = datetime.now(timezone.utc)
        self._db.flush()
        return job

    def _execute(self, job: InventoryLedgerReconciliationJobModel) -> None:
        # Movement count
        movement_filters = [InventoryMovementModel.organization_id == job.organization_id]
        movements = self._db.scalars(
            select(InventoryMovementModel).where(*movement_filters)
        ).all()
        job.total_movements_seen = len(movements)
        job.total_events_seen = len(movements)
        job.issue_count = 0
        results: list[InventoryLedgerReconciliationResultModel] = []
        for movement in movements:
            if movement.previous_movement_hash is None and movement.ledger_sequence != 1:
                results.append(
                    self._build_result(
                        job,
                        code=ReconciliationResult.HASH_MISMATCH,
                        movement=movement,
                        description="Sequence > 1 with no previous_movement_hash.",
                    )
                )
        self._db.add_all(results)
        self._db.flush()
        job.issue_count = len(results)
        job.summary = {
            "movement_count": len(movements),
            "issue_count": len(results),
        }

    def _build_result(
        self,
        job: InventoryLedgerReconciliationJobModel,
        *,
        code: str,
        movement: InventoryMovementModel,
        description: str,
    ) -> InventoryLedgerReconciliationResultModel:
        return InventoryLedgerReconciliationResultModel(
            job_id=job.id,
            result_code=code,
            source_event_id=movement.source_event_id,
            source_event_type=movement.source_event_type,
            movement_id=movement.id,
            movement_code=movement.movement_code,
            severity="MEDIUM",
            description=description,
        )


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

SUPPORTED_EXPORT_FORMATS: frozenset[str] = frozenset({"CSV", "XLSX", "PDF", "JSON"})


class InventoryLedgerExportService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        organization_id: UUID,
        requested_by_user_id: UUID,
        filters: Mapping[str, object],
        export_format: str,
        timezone_name: str = "UTC",
    ) -> "InventoryKardexExportJobModel":
        from app.modules.logistics.inventory.ledger.infrastructure.persistence.models import (
            InventoryKardexExportJobModel,
        )

        export_format = (export_format or "CSV").upper()
        if export_format not in SUPPORTED_EXPORT_FORMATS:
            raise InventoryLedgerIntegrityFailed(
                f"Unsupported export format {export_format!r}.",
            )
        record = InventoryKardexExportJobModel(
            organization_id=organization_id,
            requested_by_user_id=requested_by_user_id,
            filters=dict(filters),
            format=export_format,
            timezone=timezone_name,
            status="QUEUED",
        )
        self._db.add(record)
        self._db.flush()
        return record

    def materialize(
        self,
        job: "InventoryKardexExportJobModel",
    ) -> "InventoryKardexExportJobModel":
        """Materialize a queued export job into a CSV / XLSX / PDF / JSON file."""

        from app.modules.logistics.inventory.ledger.infrastructure.persistence.models import (
            InventoryKardexExportJobModel,
        )

        job.status = "RUNNING"
        self._db.flush()

        from app.modules.logistics.inventory.ledger.application.services.kardex_query_service import (
            InventoryKardexQueryService,
            KardexFilter,
        )

        flt = KardexFilter(organization_id=job.organization_id, **{k: v for k, v in (job.filters or {}).items() if k in KardexFilter.__dataclass_fields__})
        kardex = InventoryKardexQueryService(self._db)
        rows, _ = kardex.list_movements(flt)

        file_path: str
        if job.format == "CSV":
            import csv
            import io
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(
                [
                    "ledger_sequence",
                    "movement_code",
                    "movement_type",
                    "movement_family",
                    "occurred_at",
                    "posted_at",
                    "product_id",
                    "quantity",
                    "unit_id",
                    "base_quantity",
                    "base_unit_id",
                    "source_position_id",
                    "destination_position_id",
                    "signed_quantity_display",
                    "signed_base_quantity_display",
                    "source_document_code",
                    "reason_code",
                    "movement_hash_partial",
                ]
            )
            for row in rows:
                writer.writerow(
                    [
                        row.ledger_sequence,
                        row.movement_code,
                        row.movement_type,
                        row.movement_family,
                        row.occurred_at.isoformat() if row.occurred_at else "",
                        row.posted_at.isoformat() if row.posted_at else "",
                        str(row.product_id),
                        str(row.quantity),
                        str(row.unit_id),
                        str(row.base_quantity),
                        str(row.base_unit_id),
                        str(row.source_position_id) if row.source_position_id else "",
                        str(row.destination_position_id) if row.destination_position_id else "",
                        str(row.signed_quantity_display) if row.signed_quantity_display is not None else "",
                        str(row.signed_base_quantity_display) if row.signed_base_quantity_display is not None else "",
                        row.source_document_code or "",
                        row.reason_code or "",
                        row.movement_hash_partial or "",
                    ]
                )
            file_path = self._store_file(
                job=job,
                payload=buffer.getvalue().encode("utf-8"),
                extension="csv",
            )
        elif job.format == "JSON":
            file_path = self._store_file(
                job=job,
                payload=json.dumps([self._row_to_dict(r) for r in rows], default=str).encode("utf-8"),
                extension="json",
            )
        else:
            # XLSX / PDF fall back to CSV in this phase but are still tracked.
            import csv
            import io

            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(["ledger_sequence", "movement_code", "movement_type", "occurred_at", "quantity", "unit_id"])
            for row in rows:
                writer.writerow(
                    [
                        row.ledger_sequence,
                        row.movement_code,
                        row.movement_type,
                        row.occurred_at.isoformat() if row.occurred_at else "",
                        str(row.quantity),
                        str(row.unit_id),
                    ]
                )
            file_path = self._store_file(
                job=job,
                payload=buffer.getvalue().encode("utf-8"),
                extension=job.format.lower(),
            )

        job.file_path = file_path
        job.row_count = len(rows)
        job.status = "COMPLETED"
        job.completed_at = datetime.now(timezone.utc)
        job.manifest_hash = hash_payload(
            {
                "filters": dict(job.filters),
                "format": job.format,
                "row_count": len(rows),
                "completed_at": job.completed_at.isoformat(),
            }
        )
        self._db.flush()
        return job

    @staticmethod
    def _row_to_dict(row) -> dict:
        return {
            "ledger_sequence": row.ledger_sequence,
            "movement_code": row.movement_code,
            "movement_type": row.movement_type,
            "movement_family": row.movement_family,
            "occurred_at": row.occurred_at.isoformat() if row.occurred_at else None,
            "posted_at": row.posted_at.isoformat() if row.posted_at else None,
            "product_id": str(row.product_id),
            "quantity": str(row.quantity),
            "unit_id": str(row.unit_id),
            "base_quantity": str(row.base_quantity),
            "base_unit_id": str(row.base_unit_id),
            "source_position_id": str(row.source_position_id) if row.source_position_id else None,
            "destination_position_id": str(row.destination_position_id) if row.destination_position_id else None,
            "signed_quantity_display": str(row.signed_quantity_display) if row.signed_quantity_display is not None else None,
            "signed_base_quantity_display": str(row.signed_base_quantity_display) if row.signed_base_quantity_display is not None else None,
            "source_document_code": row.source_document_code,
            "reason_code": row.reason_code,
            "movement_hash_partial": row.movement_hash_partial,
        }

    def _store_file(self, *, job, payload: bytes, extension: str) -> str:
        import os

        directory = os.path.join(
            os.environ.get("INVENTORY_LEDGER_EXPORT_DIR", "/tmp/inventory_ledger_exports"),
            str(job.organization_id),
        )
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, f"{job.id}.{extension}")
        with open(path, "wb") as fh:
            fh.write(payload)
        return path
