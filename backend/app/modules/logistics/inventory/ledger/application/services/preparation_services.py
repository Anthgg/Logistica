"""Inventory balance and traceability preparation services.

These services DO NOT persist a balance table. They produce immutable
read-only views of the ledger that Phase 045 (balances) and
Phase 046 (traceability) will consume as their *only* source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.ledger.infrastructure.persistence.models import (
    InventoryMovementLineModel,
    InventoryMovementModel,
    InventoryPositionModel,
)


@dataclass
class BalancePreparationEntry:
    movement_id: UUID
    movement_line_id: UUID
    ledger_sequence: int
    organization_id: UUID
    warehouse_id: UUID | None
    position_id: UUID | None
    product_id: UUID
    product_version_id: UUID | None
    unit_id: UUID
    base_unit_id: UUID
    entry_base_quantity: Decimal
    exit_base_quantity: Decimal
    signed_delta_for_position: Decimal
    availability_state: str
    quality_state: str
    transit_state: str
    damage_state: str
    expiration_state: str
    occurred_at: Any
    posted_at: Any
    movement_hash: str
    source_hash: str
    compensation_status: str
    balance_materialization_key: str


def _balance_key(
    *,
    organization_id: UUID,
    warehouse_id: UUID | None,
    position_id: UUID | None,
    product_id: UUID,
    base_unit_id: UUID,
    movement_id: UUID,
    line_id: UUID,
) -> str:
    return f"{organization_id}:{warehouse_id}:{position_id}:{product_id}:{base_unit_id}:{movement_id}:{line_id}"


class InventoryBalancePreparationService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def for_movement(
        self, organization_id: UUID, movement_id: UUID
    ) -> list[BalancePreparationEntry]:
        movement = self._db.get(InventoryMovementModel, movement_id)
        if movement is None or movement.organization_id != organization_id:
            return []
        lines = self._db.scalars(
            select(InventoryMovementLineModel).where(
                InventoryMovementLineModel.inventory_movement_id == movement_id
            )
        ).all()
        return self._to_entries(movement, lines)

    def for_ledger(
        self,
        organization_id: UUID,
        *,
        warehouse_id: UUID | None = None,
        product_id: UUID | None = None,
        sequence_from: int | None = None,
        sequence_to: int | None = None,
    ) -> list[BalancePreparationEntry]:
        movement_filters = [InventoryMovementModel.organization_id == organization_id]
        if warehouse_id is not None:
            movement_filters.append(InventoryMovementModel.warehouse_scope_id == warehouse_id)
        if sequence_from is not None:
            movement_filters.append(InventoryMovementModel.ledger_sequence >= sequence_from)
        if sequence_to is not None:
            movement_filters.append(InventoryMovementModel.ledger_sequence <= sequence_to)
        movements = self._db.scalars(
            select(InventoryMovementModel)
            .where(*movement_filters)
            .order_by(InventoryMovementModel.ledger_sequence.asc())
        ).all()
        if not movements:
            return []
        movement_ids = [m.id for m in movements]
        line_filters = [InventoryMovementLineModel.inventory_movement_id.in_(movement_ids)]
        if product_id is not None:
            line_filters.append(InventoryMovementLineModel.product_id == product_id)
        lines = self._db.scalars(
            select(InventoryMovementLineModel)
            .where(*line_filters)
            .order_by(
                InventoryMovementLineModel.inventory_movement_id.asc(),
                InventoryMovementLineModel.line_number.asc(),
            )
        ).all()
        grouped: dict[UUID, list[InventoryMovementLineModel]] = {}
        for line in lines:
            grouped.setdefault(line.inventory_movement_id, []).append(line)
        result: list[BalancePreparationEntry] = []
        for movement in movements:
            result.extend(
                self._to_entries(movement, grouped.get(movement.id, []))
            )
        return result

    def _to_entries(
        self,
        movement: InventoryMovementModel,
        lines: list[InventoryMovementLineModel],
    ) -> list[BalancePreparationEntry]:
        result: list[BalancePreparationEntry] = []
        positions_cache: dict[UUID, InventoryPositionModel] = {}
        for line in lines:
            position_id = line.source_position_id or line.destination_position_id
            position = None
            if position_id is not None:
                position = positions_cache.get(position_id)
                if position is None:
                    position = self._db.get(InventoryPositionModel, position_id)
                    if position is not None:
                        positions_cache[position_id] = position
            entry = BalancePreparationEntry(
                movement_id=movement.id,
                movement_line_id=line.id,
                ledger_sequence=movement.ledger_sequence,
                organization_id=movement.organization_id,
                warehouse_id=movement.warehouse_scope_id,
                position_id=position_id,
                product_id=line.product_id,
                product_version_id=line.product_version_id,
                unit_id=line.unit_id,
                base_unit_id=line.base_unit_id,
                entry_base_quantity=(
                    Decimal(line.base_quantity)
                    if line.destination_position_id is not None
                    else Decimal("0")
                ),
                exit_base_quantity=(
                    Decimal(line.base_quantity)
                    if line.source_position_id is not None
                    else Decimal("0")
                ),
                signed_delta_for_position=Decimal("0"),
                availability_state=position.availability_state if position else "UNKNOWN",
                quality_state=position.quality_state if position else "UNKNOWN",
                transit_state=position.transit_state if position else "NOT_IN_TRANSIT",
                damage_state=position.damage_state if position else "NORMAL",
                expiration_state=position.expiration_state if position else "NOT_APPLICABLE",
                occurred_at=movement.occurred_at,
                posted_at=movement.posted_at,
                movement_hash=movement.movement_hash,
                source_hash=movement.source_event_id,
                compensation_status=(
                    "COMPENSATED"
                    if movement.compensated_by_movement_id
                    else "ACTIVE"
                ),
                balance_materialization_key=_balance_key(
                    organization_id=movement.organization_id,
                    warehouse_id=movement.warehouse_scope_id,
                    position_id=position_id,
                    product_id=line.product_id,
                    base_unit_id=line.base_unit_id,
                    movement_id=movement.id,
                    line_id=line.id,
                ),
            )
            result.append(entry)
        return result


# ---------------------------------------------------------------------------
# Traceability preparation
# ---------------------------------------------------------------------------


@dataclass
class TraceabilityPreparationEntry:
    movement_id: UUID
    movement_line_id: UUID
    product_id: UUID
    product_version_id: UUID | None
    source_position: dict | None
    destination_position: dict | None
    traceability_reference_type: str | None
    observed_lot_references: list
    observed_serial_references: list
    expiration_observations: list
    packaging_snapshot: dict | None
    handling_unit_reference_hash: str | None
    quantity: Decimal
    unit: UUID
    movement_hash: str


class InventoryTraceabilityPreparationService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def for_movement(
        self, organization_id: UUID, movement_id: UUID
    ) -> list[TraceabilityPreparationEntry]:
        movement = self._db.get(InventoryMovementModel, movement_id)
        if movement is None or movement.organization_id != organization_id:
            return []
        lines = self._db.scalars(
            select(InventoryMovementLineModel).where(
                InventoryMovementLineModel.inventory_movement_id == movement_id
            )
        ).all()
        return [self._to_entry(movement, line) for line in lines]

    def for_ledger(
        self,
        organization_id: UUID,
        *,
        warehouse_id: UUID | None = None,
        product_id: UUID | None = None,
    ) -> list[TraceabilityPreparationEntry]:
        movement_filters = [InventoryMovementModel.organization_id == organization_id]
        if warehouse_id is not None:
            movement_filters.append(InventoryMovementModel.warehouse_scope_id == warehouse_id)
        movements = self._db.scalars(
            select(InventoryMovementModel).where(*movement_filters)
        ).all()
        if not movements:
            return []
        movement_ids = [m.id for m in movements]
        line_filters = [InventoryMovementLineModel.inventory_movement_id.in_(movement_ids)]
        if product_id is not None:
            line_filters.append(InventoryMovementLineModel.product_id == product_id)
        lines = self._db.scalars(
            select(InventoryMovementLineModel).where(*line_filters)
        ).all()
        by_movement: dict[UUID, InventoryMovementModel] = {m.id: m for m in movements}
        return [self._to_entry(by_movement[line.inventory_movement_id], line) for line in lines]

    @staticmethod
    def _to_entry(
        movement: InventoryMovementModel,
        line: InventoryMovementLineModel,
    ) -> TraceabilityPreparationEntry:
        return TraceabilityPreparationEntry(
            movement_id=movement.id,
            movement_line_id=line.id,
            product_id=line.product_id,
            product_version_id=line.product_version_id,
            source_position=line.source_position_snapshot,
            destination_position=line.destination_position_snapshot,
            traceability_reference_type=line.traceability_reference_snapshot.get("type")
            if isinstance(line.traceability_reference_snapshot, Mapping)
            else None,
            observed_lot_references=[],
            observed_serial_references=[],
            expiration_observations=[],
            packaging_snapshot=line.metadata_snapshot,
            handling_unit_reference_hash=None,
            quantity=Decimal(line.quantity),
            unit=line.unit_id,
            movement_hash=movement.movement_hash,
        )
