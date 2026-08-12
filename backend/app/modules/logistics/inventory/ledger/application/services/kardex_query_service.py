"""Inventory kardex query service.

Provides a read-only technical view of the append-only book that:

* supports the filters mandated by Phase 044
* computes a signed quantity only for the *position* the user is asking
  about (entry positive, exit negative, state change context-aware)
* never recomputes balances; it only replays the lines
* supports an *opt-in* running quantity when the caller provides an
  unambiguous dimension (org, warehouse, product, position-or-states,
  base unit, sequence range)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Iterable, Mapping
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
    InventoryKardexScopeAmbiguous,
    InventoryKardexUnitMismatch,
)
from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
    RunningDataQuality,
)
from app.modules.logistics.inventory.ledger.infrastructure.persistence.models import (
    InventoryMovementLineModel,
    InventoryMovementModel,
    InventoryMovementSourceReferenceModel,
    InventoryPositionModel,
)


@dataclass
class KardexFilter:
    organization_id: UUID
    search: str | None = None
    movement_code: str | None = None
    ledger_sequence_from: int | None = None
    ledger_sequence_to: int | None = None
    movement_family: str | None = None
    movement_type: str | None = None
    status: str | None = None
    branch_id: UUID | None = None
    warehouse_id: UUID | None = None
    location_id: UUID | None = None
    product_id: UUID | None = None
    product_version_id: UUID | None = None
    sku: str | None = None
    source_system: str | None = None
    source_event_type: str | None = None
    source_event_id: str | None = None
    source_document_type: str | None = None
    source_document_code: str | None = None
    availability_state_from: str | None = None
    availability_state_to: str | None = None
    quality_state_from: str | None = None
    quality_state_to: str | None = None
    transit_state_from: str | None = None
    transit_state_to: str | None = None
    damage_state_from: str | None = None
    damage_state_to: str | None = None
    expiration_state_from: str | None = None
    expiration_state_to: str | None = None
    compensated: bool | None = None
    integrity_status: str | None = None
    occurred_from: datetime | None = None
    occurred_to: datetime | None = None
    posted_from: datetime | None = None
    posted_to: datetime | None = None
    posted_by: UUID | None = None
    correlation_id: str | None = None
    page: int = 1
    page_size: int = 50
    sort_by: str = "ledger_sequence"
    sort_direction: str = "DESC"


@dataclass
class KardexRow:
    movement_id: UUID
    movement_code: str
    ledger_sequence: int
    movement_type: str
    movement_family: str
    status: str
    occurred_at: datetime
    posted_at: datetime
    warehouse_id: UUID | None
    product_id: UUID
    product_version_id: UUID | None
    quantity: Decimal
    base_quantity: Decimal
    unit_id: UUID
    base_unit_id: UUID
    source_position_id: UUID | None
    destination_position_id: UUID | None
    source_position_snapshot: dict | None
    destination_position_snapshot: dict | None
    source_document_code: str | None
    reason_code: str | None
    source_event_id: str
    movement_hash_partial: str
    compensation_status: str | None
    line_number: int | None = None
    signed_quantity_display: Decimal | None = None
    signed_base_quantity_display: Decimal | None = None
    quantity_direction: str | None = None
    capabilities: list[str] = field(default_factory=list)


def _as_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    return UUID(str(value))


class InventoryKardexQueryService:
    def __init__(self, db: Session) -> None:
        self._db = db

    # ---------------------------------------------------------------- list
    def list_movements(self, flt: KardexFilter) -> tuple[list[KardexRow], int]:
        movement_filters = self._movement_filters(flt)
        base_stmt = select(InventoryMovementModel).where(*movement_filters)
        count_stmt = select(func.count()).select_from(InventoryMovementModel).where(*movement_filters)
        total = self._db.scalar(count_stmt) or 0

        sort_col = self._sort_column(flt.sort_by)
        sort_clause = sort_col.asc() if flt.sort_direction.upper() == "ASC" else sort_col.desc()
        page = max(flt.page, 1)
        size = max(min(flt.page_size, 500), 1)
        rows = self._db.scalars(
            base_stmt.order_by(sort_clause).offset((page - 1) * size).limit(size)
        ).all()

        results: list[KardexRow] = []
        for movement in rows:
            line_filters = self._line_filters(flt)
            line_filters.append(InventoryMovementLineModel.inventory_movement_id == movement.id)
            first_line = self._db.scalars(
                select(InventoryMovementLineModel).where(*line_filters).order_by(
                    InventoryMovementLineModel.line_number.asc()
                ).limit(1)
            ).first()
            if first_line is None:
                continue
            results.append(
                self._to_kardex_row(movement, first_line, flt)
            )
        return results, total

    def get_movement_detail(
        self, organization_id: UUID, movement_id: UUID
    ) -> Mapping[str, Any]:
        movement = self._db.get(InventoryMovementModel, movement_id)
        if movement is None or movement.organization_id != organization_id:
            raise InventoryKardexScopeAmbiguous(
                "Movement not found for the current organization.",
            )
        lines = self._db.scalars(
            select(InventoryMovementLineModel)
            .where(InventoryMovementLineModel.inventory_movement_id == movement_id)
            .order_by(InventoryMovementLineModel.line_number.asc())
        ).all()
        sources = self._db.scalars(
            select(InventoryMovementSourceReferenceModel)
            .where(InventoryMovementSourceReferenceModel.movement_id == movement_id)
        ).all()
        positions: dict[UUID, InventoryPositionModel] = {}
        for line in lines:
            for pos_id in (line.source_position_id, line.destination_position_id):
                if pos_id is None:
                    continue
                if pos_id in positions:
                    continue
                pos = self._db.get(InventoryPositionModel, pos_id)
                if pos is not None:
                    positions[pos_id] = pos
        compensation = None
        if movement.compensation_for_movement_id is not None:
            compensation = self._db.get(InventoryMovementModel, movement.compensation_for_movement_id)
        return {
            "movement": movement,
            "lines": lines,
            "sources": sources,
            "positions": list(positions.values()),
            "compensation": compensation,
        }

    # --------------------------------------------------- running quantity
    def compute_technical_running_quantity(
        self,
        *,
        organization_id: UUID,
        warehouse_id: UUID,
        product_id: UUID,
        base_unit_id: UUID,
        position_id: UUID | None = None,
        availability_states: Iterable[str] | None = None,
        quality_states: Iterable[str] | None = None,
        transit_states: Iterable[str] | None = None,
        damage_states: Iterable[str] | None = None,
        expiration_states: Iterable[str] | None = None,
        sequence_from: int | None = None,
        sequence_to: int | None = None,
        opening_quantity_reference: Decimal = Decimal("0"),
    ) -> list[dict]:
        if position_id is None and not (
            availability_states
            or quality_states
            or transit_states
            or damage_states
            or expiration_states
        ):
            raise InventoryKardexScopeAmbiguous(
                "Either position_id or a state set must be provided to compute running quantity.",
            )

        line_filters = [
            InventoryMovementLineModel.product_id == product_id,
            InventoryMovementLineModel.base_unit_id == base_unit_id,
        ]

        if position_id is not None:
            line_filters.append(
                or_(
                    InventoryMovementLineModel.source_position_id == position_id,
                    InventoryMovementLineModel.destination_position_id == position_id,
                )
            )

        movement_filters = [
            InventoryMovementModel.organization_id == organization_id,
            InventoryMovementModel.warehouse_scope_id == warehouse_id,
        ]
        if sequence_from is not None:
            movement_filters.append(InventoryMovementModel.ledger_sequence >= sequence_from)
        if sequence_to is not None:
            movement_filters.append(InventoryMovementModel.ledger_sequence <= sequence_to)

        position_filters: list[Any] = []
        if availability_states:
            position_filters.append(
                InventoryPositionModel.availability_state.in_(list(availability_states))
            )
        if quality_states:
            position_filters.append(
                InventoryPositionModel.quality_state.in_(list(quality_states))
            )
        if transit_states:
            position_filters.append(
                InventoryPositionModel.transit_state.in_(list(transit_states))
            )
        if damage_states:
            position_filters.append(
                InventoryPositionModel.damage_state.in_(list(damage_states))
            )
        if expiration_states:
            position_filters.append(
                InventoryPositionModel.expiration_state.in_(list(expiration_states))
            )

        results: list[dict] = []
        running = Decimal(opening_quantity_reference)
        data_quality = RunningDataQuality.COMPLETE

        stmt = (
            select(InventoryMovementLineModel, InventoryMovementModel)
            .join(
                InventoryMovementModel,
                InventoryMovementModel.id == InventoryMovementLineModel.inventory_movement_id,
            )
            .where(*movement_filters)
            .order_by(InventoryMovementModel.ledger_sequence.asc(), InventoryMovementLineModel.line_number.asc())
        )

        for line, movement in self._db.execute(stmt).all():
            if not self._line_matches_filters(line, line_filters):
                continue
            if line.base_unit_id != base_unit_id:
                data_quality = RunningDataQuality.UNIT_MISMATCH
                continue
            if position_id is not None:
                if line.source_position_id == position_id:
                    signed = -Decimal(line.base_quantity)
                elif line.destination_position_id == position_id:
                    signed = Decimal(line.base_quantity)
                else:
                    continue
            else:
                # Without position_id, the line is ambiguous: we report the
                # direction only.
                signed = Decimal("0")
                data_quality = RunningDataQuality.AMBIGUOUS_SCOPE
            running += signed
            results.append(
                {
                    "ledger_sequence": movement.ledger_sequence,
                    "movement_id": str(movement.id),
                    "movement_code": movement.movement_code,
                    "line_number": line.line_number,
                    "signed_delta": str(signed),
                    "running_quantity_reference": str(running),
                    "data_quality_status": data_quality.value,
                    "calculation_scope": "TECHNICAL_REPLAY",
                }
            )
        if data_quality == RunningDataQuality.COMPLETE and not results:
            data_quality = RunningDataQuality.NOT_APPLICABLE
        return results

    def _line_matches_filters(
        self, line: InventoryMovementLineModel, line_filters: list[Any]
    ) -> bool:
        for clause in line_filters:
            if not self._evaluate_clause(line, clause):
                return False
        return True

    @staticmethod
    def _evaluate_clause(line: InventoryMovementLineModel, clause: Any) -> bool:
        """Lightweight clause evaluator used to keep running-quantity replay in Python.

        Only the predicates we explicitly build (eq / is_(None) / in_ / ge / le)
        are supported. The full query already filters the joined movement,
        so this function mostly checks per-line structural properties.
        """

        try:
            python_value = line
        except Exception:  # noqa: BLE001
            return True
        # Best-effort: try to interpret clause as ``<col> <op> <literal>``
        if hasattr(clause, "left") and hasattr(clause, "right"):
            attr = getattr(clause.left, "key", None) or getattr(clause.left, "name", None)
            op = getattr(clause, "operator", None)
            value = clause.right.value if hasattr(clause.right, "value") else clause.right
            current = getattr(python_value, attr, None) if attr else None
            if op is None:
                return True
            op_name = getattr(op, "name", None) or getattr(op, "__name__", "")
            try:
                if op_name in {"eq", "is"}:
                    if value is None:
                        return current is None
                    return current == value
                if op_name == "ge":
                    return current is not None and current >= value
                if op_name == "le":
                    return current is not None and current <= value
                if op_name == "ne":
                    return current != value
                if op_name == "in_op":
                    return current in (value or [])
            except Exception:  # noqa: BLE001
                return True
        return True

    # ---------------------------------------------------------------- helpers
    def _movement_filters(self, flt: KardexFilter) -> list[Any]:
        filters: list[Any] = [InventoryMovementModel.organization_id == flt.organization_id]
        if flt.search:
            pattern = f"%{flt.search}%"
            filters.append(
                or_(
                    InventoryMovementModel.movement_code.ilike(pattern),
                    InventoryMovementModel.normalized_movement_code.ilike(pattern),
                )
            )
        if flt.movement_code:
            filters.append(InventoryMovementModel.normalized_movement_code == flt.movement_code)
        if flt.ledger_sequence_from is not None:
            filters.append(InventoryMovementModel.ledger_sequence >= flt.ledger_sequence_from)
        if flt.ledger_sequence_to is not None:
            filters.append(InventoryMovementModel.ledger_sequence <= flt.ledger_sequence_to)
        if flt.movement_family:
            filters.append(InventoryMovementModel.movement_family == flt.movement_family)
        if flt.movement_type:
            filters.append(InventoryMovementModel.movement_type == flt.movement_type)
        if flt.status:
            filters.append(InventoryMovementModel.status == flt.status)
        if flt.branch_id:
            filters.append(InventoryMovementModel.branch_id == flt.branch_id)
        if flt.warehouse_id:
            filters.append(InventoryMovementModel.warehouse_scope_id == flt.warehouse_id)
        if flt.source_event_id:
            filters.append(InventoryMovementModel.source_event_id == flt.source_event_id)
        if flt.source_event_type:
            filters.append(InventoryMovementModel.source_event_type == flt.source_event_type)
        if flt.source_system:
            filters.append(InventoryMovementModel.source_system == flt.source_system)
        if flt.source_document_code:
            filters.append(InventoryMovementModel.source_document_code == flt.source_document_code)
        if flt.source_document_type:
            filters.append(InventoryMovementModel.source_document_type == flt.source_document_type)
        if flt.posted_by:
            filters.append(InventoryMovementModel.posted_by_user_id == flt.posted_by)
        if flt.occurred_from:
            filters.append(InventoryMovementModel.occurred_at >= flt.occurred_from)
        if flt.occurred_to:
            filters.append(InventoryMovementModel.occurred_at <= flt.occurred_to)
        if flt.posted_from:
            filters.append(InventoryMovementModel.posted_at >= flt.posted_from)
        if flt.posted_to:
            filters.append(InventoryMovementModel.posted_at <= flt.posted_to)
        if flt.correlation_id:
            filters.append(InventoryMovementModel.source_event_id == flt.correlation_id)
        if flt.compensated is True:
            filters.append(InventoryMovementModel.compensated_by_movement_id.is_not(None))
        elif flt.compensated is False:
            filters.append(InventoryMovementModel.compensated_by_movement_id.is_(None))
        return filters

    def _line_filters(self, flt: KardexFilter) -> list[Any]:
        filters: list[Any] = []
        if flt.product_id:
            filters.append(InventoryMovementLineModel.product_id == flt.product_id)
        if flt.product_version_id:
            filters.append(
                InventoryMovementLineModel.product_version_id == flt.product_version_id
            )
        if flt.availability_state_from or flt.availability_state_to:
            for pos_filter in self._position_state_filters(flt):
                filters.append(pos_filter)
        if flt.location_id:
            filters.append(
                or_(
                    self._position_id_by_location(flt.location_id, "source"),
                    self._position_id_by_location(flt.location_id, "destination"),
                )
            )
        return filters

    def _position_state_filters(self, flt: KardexFilter) -> list[Any]:
        # Resolve position ids matching the state combination and use them
        # to filter the line.
        filters_pos: list[Any] = [InventoryPositionModel.organization_id == flt.organization_id]
        if flt.availability_state_from:
            filters_pos.append(
                InventoryPositionModel.availability_state >= flt.availability_state_from
            )
        if flt.availability_state_to:
            filters_pos.append(
                InventoryPositionModel.availability_state <= flt.availability_state_to
            )
        if flt.quality_state_from:
            filters_pos.append(
                InventoryPositionModel.quality_state >= flt.quality_state_from
            )
        if flt.quality_state_to:
            filters_pos.append(
                InventoryPositionModel.quality_state <= flt.quality_state_to
            )
        if flt.transit_state_from:
            filters_pos.append(
                InventoryPositionModel.transit_state >= flt.transit_state_from
            )
        if flt.transit_state_to:
            filters_pos.append(
                InventoryPositionModel.transit_state <= flt.transit_state_to
            )
        if flt.damage_state_from:
            filters_pos.append(
                InventoryPositionModel.damage_state >= flt.damage_state_from
            )
        if flt.damage_state_to:
            filters_pos.append(
                InventoryPositionModel.damage_state <= flt.damage_state_to
            )
        if flt.expiration_state_from:
            filters_pos.append(
                InventoryPositionModel.expiration_state >= flt.expiration_state_from
            )
        if flt.expiration_state_to:
            filters_pos.append(
                InventoryPositionModel.expiration_state <= flt.expiration_state_to
            )
        position_ids = [
            row[0]
            for row in self._db.execute(
                select(InventoryPositionModel.id).where(*filters_pos)
            ).all()
        ]
        if not position_ids:
            filters.append(InventoryMovementLineModel.id.is_(None))
            return filters
        filters.append(
            or_(
                InventoryMovementLineModel.source_position_id.in_(position_ids),
                InventoryMovementLineModel.destination_position_id.in_(position_ids),
            )
        )
        return filters

    def _position_id_by_location(self, location_id: UUID, side: str) -> Any:
        column = (
            InventoryMovementLineModel.source_position_id
            if side == "source"
            else InventoryMovementLineModel.destination_position_id
        )
        return column.in_(
            select(InventoryPositionModel.id).where(
                InventoryPositionModel.warehouse_location_id == location_id
            )
        )

    def _sort_column(self, sort_by: str):
        sort_by = (sort_by or "ledger_sequence").lower()
        return {
            "ledger_sequence": InventoryMovementModel.ledger_sequence,
            "occurred_at": InventoryMovementModel.occurred_at,
            "posted_at": InventoryMovementModel.posted_at,
            "movement_code": InventoryMovementModel.normalized_movement_code,
        }.get(sort_by, InventoryMovementModel.ledger_sequence)

    def _to_kardex_row(
        self,
        movement: InventoryMovementModel,
        line: InventoryMovementLineModel,
        flt: KardexFilter,
    ) -> KardexRow:
        signed: Decimal | None = None
        signed_base: Decimal | None = None
        if flt.warehouse_id and movement.warehouse_scope_id == flt.warehouse_id:
            if flt.location_id is not None:
                source = self._db.get(InventoryPositionModel, line.source_position_id) if line.source_position_id else None
                destination = self._db.get(InventoryPositionModel, line.destination_position_id) if line.destination_position_id else None
                if source and source.warehouse_location_id == flt.location_id:
                    signed = -Decimal(line.quantity)
                    signed_base = -Decimal(line.base_quantity)
                elif destination and destination.warehouse_location_id == flt.location_id:
                    signed = Decimal(line.quantity)
                    signed_base = Decimal(line.base_quantity)
            else:
                if line.destination_position_id is not None:
                    signed = Decimal(line.quantity)
                    signed_base = Decimal(line.base_quantity)
                elif line.source_position_id is not None:
                    signed = -Decimal(line.quantity)
                    signed_base = -Decimal(line.base_quantity)

        return KardexRow(
            movement_id=movement.id,
            movement_code=movement.movement_code,
            ledger_sequence=movement.ledger_sequence,
            movement_type=movement.movement_type,
            movement_family=movement.movement_family,
            status=movement.status,
            occurred_at=movement.occurred_at,
            posted_at=movement.posted_at,
            warehouse_id=movement.warehouse_scope_id,
            product_id=line.product_id,
            product_version_id=line.product_version_id,
            quantity=Decimal(line.quantity),
            base_quantity=Decimal(line.base_quantity),
            unit_id=line.unit_id,
            base_unit_id=line.base_unit_id,
            source_position_id=line.source_position_id,
            destination_position_id=line.destination_position_id,
            source_position_snapshot=line.source_position_snapshot,
            destination_position_snapshot=line.destination_position_snapshot,
            source_document_code=movement.source_document_code,
            reason_code=movement.reason_code,
            source_event_id=movement.source_event_id,
            movement_hash_partial=movement.movement_hash[:16] if movement.movement_hash else "",
            compensation_status=(
                "COMPENSATED" if movement.compensated_by_movement_id else "ACTIVE"
            ),
            line_number=line.line_number,
            signed_quantity_display=signed,
            signed_base_quantity_display=signed_base,
            quantity_direction=line.quantity_direction,
            capabilities=[
                "logistics.inventory_ledger.read",
                "logistics.inventory_kardex.read",
            ],
        )
