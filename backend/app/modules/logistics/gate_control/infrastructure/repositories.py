"""SQLAlchemy 2.0 Persistence Repositories for Gate Control Core Domain (Phase 037)."""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.logistics.gate_control.domain.enums import GateRecordStatus
from app.modules.logistics.gate_control.domain.models import (
    GateControlHistoryModel,
    GateControlRecordModel,
    WarehouseGateModel,
    compute_gate_content_hash,
)


class GateControlConcurrencyError(Exception):
    """Raised when an optimistic concurrency check fails on row_version mismatch."""

    pass


class WarehouseGateRepository:
    """Persistence repository for warehouse gates."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(
        self, gate_id: UUID, organization_id: UUID | None = None
    ) -> WarehouseGateModel | None:
        stmt = select(WarehouseGateModel).where(WarehouseGateModel.id == gate_id)
        if organization_id:
            stmt = stmt.where(WarehouseGateModel.organization_id == organization_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def get_by_code(
        self, organization_id: UUID, code: str
    ) -> WarehouseGateModel | None:
        stmt = select(WarehouseGateModel).where(
            WarehouseGateModel.organization_id == organization_id,
            WarehouseGateModel.code == code.strip().upper(),
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def list_by_warehouse(
        self,
        warehouse_id: UUID,
        organization_id: UUID | None = None,
        is_active: bool | None = True,
    ) -> Sequence[WarehouseGateModel]:
        stmt = select(WarehouseGateModel).where(WarehouseGateModel.warehouse_id == warehouse_id)
        if organization_id:
            stmt = stmt.where(WarehouseGateModel.organization_id == organization_id)
        if is_active is not None:
            stmt = stmt.where(WarehouseGateModel.is_active == is_active)
        stmt = stmt.order_by(WarehouseGateModel.code.asc())
        return self._db.execute(stmt).scalars().all()

    def list_by_organization(
        self, organization_id: UUID, is_active: bool | None = None
    ) -> Sequence[WarehouseGateModel]:
        stmt = select(WarehouseGateModel).where(WarehouseGateModel.organization_id == organization_id)
        if is_active is not None:
            stmt = stmt.where(WarehouseGateModel.is_active == is_active)
        stmt = stmt.order_by(WarehouseGateModel.code.asc())
        return self._db.execute(stmt).scalars().all()

    def create(self, gate: WarehouseGateModel) -> WarehouseGateModel:
        if not gate.content_hash:
            gate.content_hash = compute_gate_content_hash({
                "organization_id": str(gate.organization_id),
                "code": gate.code,
                "name": gate.name,
                "warehouse_id": str(gate.warehouse_id),
                "gate_type": gate.gate_type,
                "status": gate.status,
            })
        self._db.add(gate)
        self._db.flush()
        return gate

    def update(
        self, gate: WarehouseGateModel, expected_version: int | None = None
    ) -> WarehouseGateModel:
        if expected_version is not None:
            if gate.row_version != expected_version:
                raise GateControlConcurrencyError(
                    f"Concurrency mismatch for gate {gate.id}: expected version {expected_version}, got {gate.row_version}"
                )
            gate.row_version = expected_version + 1

        gate.content_hash = compute_gate_content_hash({
            "organization_id": str(gate.organization_id),
            "code": gate.code,
            "name": gate.name,
            "warehouse_id": str(gate.warehouse_id),
            "gate_type": gate.gate_type,
            "status": gate.status,
            "row_version": gate.row_version,
        })
        self._db.flush()
        return gate


class GateControlRecordRepository:
    """Persistence repository for gate control records and history transitions."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(
        self,
        record_id: UUID,
        organization_id: UUID | None = None,
        include_history: bool = True,
    ) -> GateControlRecordModel | None:
        stmt = select(GateControlRecordModel).where(GateControlRecordModel.id == record_id)
        if organization_id:
            stmt = stmt.where(GateControlRecordModel.organization_id == organization_id)
        if include_history:
            stmt = stmt.options(
                selectinload(GateControlRecordModel.history_entries),
                selectinload(GateControlRecordModel.gate),
            )
        return self._db.execute(stmt).scalar_one_or_none()

    def get_by_code(
        self, organization_id: UUID, record_code: str
    ) -> GateControlRecordModel | None:
        stmt = (
            select(GateControlRecordModel)
            .where(
                GateControlRecordModel.organization_id == organization_id,
                GateControlRecordModel.record_code == record_code.strip().upper(),
            )
            .options(
                selectinload(GateControlRecordModel.history_entries),
                selectinload(GateControlRecordModel.gate),
            )
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def list_by_gate(
        self,
        gate_id: UUID,
        status: GateRecordStatus | str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[GateControlRecordModel]:
        stmt = select(GateControlRecordModel).where(GateControlRecordModel.gate_id == gate_id)
        if status:
            stmt = stmt.where(GateControlRecordModel.status == str(status))
        stmt = stmt.order_by(GateControlRecordModel.arrival_at.desc()).limit(limit).offset(offset)
        return self._db.execute(stmt).scalars().all()

    def list_by_appointment(
        self, appointment_id: UUID
    ) -> Sequence[GateControlRecordModel]:
        stmt = (
            select(GateControlRecordModel)
            .where(GateControlRecordModel.reception_appointment_id == appointment_id)
            .order_by(GateControlRecordModel.created_at.desc())
        )
        return self._db.execute(stmt).scalars().all()

    def list_by_plate(
        self, organization_id: UUID, plate: str
    ) -> Sequence[GateControlRecordModel]:
        normalized_plate = plate.strip().upper().replace("-", "").replace(" ", "")
        stmt = (
            select(GateControlRecordModel)
            .where(
                GateControlRecordModel.organization_id == organization_id,
                GateControlRecordModel.plate_observed == normalized_plate,
            )
            .order_by(GateControlRecordModel.arrival_at.desc())
        )
        return self._db.execute(stmt).scalars().all()

    def create(self, record: GateControlRecordModel) -> GateControlRecordModel:
        if record.plate_observed:
            record.plate_observed = record.plate_observed.strip().upper().replace("-", "").replace(" ", "")
        if not record.content_hash:
            record.content_hash = compute_gate_content_hash({
                "organization_id": str(record.organization_id),
                "record_code": record.record_code,
                "gate_id": str(record.gate_id),
                "event_type": record.event_type,
                "arrival_at": record.arrival_at.isoformat() if record.arrival_at else None,
                "access_decision": record.access_decision,
                "plate_observed": record.plate_observed,
                "status": record.status,
            })
        self._db.add(record)
        self._db.flush()
        return record

    def update(
        self, record: GateControlRecordModel, expected_version: int | None = None
    ) -> GateControlRecordModel:
        if record.plate_observed:
            record.plate_observed = record.plate_observed.strip().upper().replace("-", "").replace(" ", "")
        if expected_version is not None:
            if record.row_version != expected_version:
                raise GateControlConcurrencyError(
                    f"Concurrency mismatch for record {record.id}: expected version {expected_version}, got {record.row_version}"
                )
            record.row_version = expected_version + 1

        record.content_hash = compute_gate_content_hash({
            "organization_id": str(record.organization_id),
            "record_code": record.record_code,
            "gate_id": str(record.gate_id),
            "event_type": record.event_type,
            "arrival_at": record.arrival_at.isoformat() if record.arrival_at else None,
            "check_in_at": record.check_in_at.isoformat() if record.check_in_at else None,
            "check_out_at": record.check_out_at.isoformat() if record.check_out_at else None,
            "access_decision": record.access_decision,
            "plate_observed": record.plate_observed,
            "seal_status": record.seal_status,
            "status": record.status,
            "row_version": record.row_version,
        })
        self._db.flush()
        return record

    def add_history(
        self, history_entry: GateControlHistoryModel
    ) -> GateControlHistoryModel:
        self._db.add(history_entry)
        self._db.flush()
        return history_entry

    def get_history_by_record(
        self, record_id: UUID
    ) -> Sequence[GateControlHistoryModel]:
        stmt = (
            select(GateControlHistoryModel)
            .where(GateControlHistoryModel.record_id == record_id)
            .order_by(GateControlHistoryModel.created_at.asc())
        )
        return self._db.execute(stmt).scalars().all()
