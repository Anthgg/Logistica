"""Master dock, availability, queue, planning, assignment, and occupancy services."""

from datetime import datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.logistics.inbound.dock_operations.application.services.common import (
    DockMasterEventService,
    UnloadingOperationalEventService,
    actor_snapshot,
    canonical_json,
    normalize_code,
    server_now,
    sha256_payload,
)
from app.modules.logistics.inbound.dock_operations.domain.enums import (
    ACTIVE_ASSIGNMENT_STATUSES,
    ACTIVE_QUEUE_STATUSES,
    AssignmentMode,
    CompatibilityStatus,
    DockAssignmentStatus,
    DockMasterStatus,
    DockOperationDirection,
    DockOperationalEventType,
    DockOperationalStatus,
    OccupancyStatus,
    QueuePriority,
    QueueStatus,
)
from app.modules.logistics.inbound.dock_operations.domain.errors import (
    DockAssignmentNotFound,
    InboundDockQueueEntryNotFound,
    WarehouseDockNotFound,
    conflict,
    invalid,
)
from app.modules.logistics.inbound.dock_operations.domain.policies.state_machine import (
    ASSIGNMENT_TRANSITIONS,
    require_transition,
)
from app.modules.logistics.inbound.dock_operations.infrastructure.persistence.models import (
    DockAssignmentPlanModel,
    DockOccupancyIntervalModel,
    InboundDockAssignmentModel,
    InboundDockQueueEntryModel,
    WarehouseDockBlackoutModel,
    WarehouseDockCapabilityModel,
    WarehouseDockModel,
    WarehouseDockOperatingWindowModel,
)
from app.modules.logistics.inbound.gate_control.application.services import (
    DockAssignmentPreparationService,
)
from app.modules.logistics.inbound.gate_control.infrastructure.persistence.models import (
    GateCheckInModel,
)
from app.modules.logistics.principal import LogisticsPrincipal


_PRIORITY_WEIGHT = {
    QueuePriority.SAFETY_CRITICAL.value: 0,
    QueuePriority.URGENT.value: 1,
    QueuePriority.HIGH.value: 2,
    QueuePriority.NORMAL.value: 3,
    QueuePriority.LOW.value: 4,
}


def _as_json(value: object) -> object:
    """Round-trip values into the JSON-safe form used by PostgreSQL JSONB."""
    import json

    return json.loads(canonical_json(value))


class WarehouseDockService:
    def __init__(self, db: Session):
        self.db = db
        self.master_events = DockMasterEventService(db)

    def get(self, dock_id: UUID, organization_id: UUID, *, lock: bool = False) -> WarehouseDockModel:
        query = select(WarehouseDockModel).where(
            WarehouseDockModel.id == dock_id,
            WarehouseDockModel.organization_id == organization_id,
        )
        if lock:
            query = query.with_for_update()
        dock = self.db.scalar(query)
        if dock is None:
            raise WarehouseDockNotFound()
        return dock

    def list(
        self,
        organization_id: UUID,
        warehouse_id: UUID | None = None,
        status: str | None = None,
    ) -> list[WarehouseDockModel]:
        query = select(WarehouseDockModel).where(WarehouseDockModel.organization_id == organization_id)
        if warehouse_id is not None:
            query = query.where(WarehouseDockModel.warehouse_id == warehouse_id)
        if status is not None:
            query = query.where(WarehouseDockModel.status == status)
        return list(self.db.scalars(query.order_by(WarehouseDockModel.normalized_code)))

    def create(self, organization_id: UUID, principal: LogisticsPrincipal, body: object) -> WarehouseDockModel:
        data = body.model_dump()
        if str(data["operation_direction"]) == DockOperationDirection.OUTBOUND.value:
            raise invalid("WAREHOUSE_DOCK_DIRECTION_OUT_OF_SCOPE", "La Fase 038 solo admite muelles INBOUND o MIXED.")
        try:
            ZoneInfo(str(data["timezone"]))
        except ZoneInfoNotFoundError as exc:
            raise invalid("WAREHOUSE_DOCK_TIMEZONE_INVALID", "Zona horaria IANA inválida.") from exc
        normalized = normalize_code(data["code"])
        duplicate = self.db.scalar(
            select(WarehouseDockModel.id).where(
                WarehouseDockModel.warehouse_id == data["warehouse_id"],
                WarehouseDockModel.normalized_code == normalized,
            )
        )
        if duplicate:
            raise conflict("WAREHOUSE_DOCK_CODE_DUPLICATE", "Ya existe un muelle con ese código en el almacén.")
        dock = WarehouseDockModel(
            id=uuid4(),
            organization_id=organization_id,
            normalized_code=normalized,
            status=DockMasterStatus.DRAFT.value,
            created_by=principal.user_id,
            **data,
        )
        self.db.add(dock)
        self.db.flush()
        self.master_events.append(
            dock=dock, principal=principal, event_type="WAREHOUSE_DOCK_CREATED",
            audit_code="logistics.warehouse_dock.created", new_data={"status": dock.status, "code": dock.code},
        )
        return dock

    def update(
        self,
        dock_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        body: object,
    ) -> WarehouseDockModel:
        dock = self.get(dock_id, organization_id, lock=True)
        if dock.row_version != body.row_version:
            raise conflict("OPTIMISTIC_LOCK_CONFLICT", "El muelle fue modificado; recargue e intente nuevamente.")
        changes = body.model_dump(exclude_unset=True)
        changes.pop("row_version", None)
        new_capacity = changes.get("simultaneous_vehicle_capacity")
        if new_capacity is not None:
            active = int(
                self.db.scalar(
                    select(func.count()).select_from(InboundDockAssignmentModel).where(
                        InboundDockAssignmentModel.dock_id == dock.id,
                        InboundDockAssignmentModel.status.in_(ACTIVE_ASSIGNMENT_STATUSES),
                    )
                )
                or 0
            )
            if new_capacity < active:
                raise conflict("WAREHOUSE_DOCK_CAPACITY_EXCEEDED", "La nueva capacidad es menor que las asignaciones activas.")
        if changes.get("timezone"):
            try:
                ZoneInfo(changes["timezone"])
            except ZoneInfoNotFoundError as exc:
                raise invalid("WAREHOUSE_DOCK_TIMEZONE_INVALID", "Zona horaria IANA inválida.") from exc
        previous = {field: getattr(dock, field) for field in changes}
        for field, value in changes.items():
            setattr(dock, field, value)
        dock.updated_by = principal.user_id
        dock.row_version += 1
        self.db.flush()
        self.master_events.append(
            dock=dock, principal=principal, event_type="WAREHOUSE_DOCK_UPDATED",
            audit_code="logistics.warehouse_dock.updated", previous_data=_as_json(previous), new_data=_as_json(changes),
        )
        return dock

    def transition(
        self,
        dock_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        target: DockMasterStatus,
        reason: str | None = None,
    ) -> WarehouseDockModel:
        dock = self.get(dock_id, organization_id, lock=True)
        active = int(
            self.db.scalar(
                select(func.count()).select_from(InboundDockAssignmentModel).where(
                    InboundDockAssignmentModel.dock_id == dock.id,
                    InboundDockAssignmentModel.status.in_(ACTIVE_ASSIGNMENT_STATUSES),
                )
            )
            or 0
        )
        if target in {DockMasterStatus.INACTIVE, DockMasterStatus.ARCHIVED} and active:
            raise conflict("WAREHOUSE_DOCK_HAS_ACTIVE_ASSIGNMENTS", "No se puede inactivar o archivar un muelle asignado.")
        previous = dock.status
        dock.status = target.value
        dock.updated_by = principal.user_id
        dock.row_version += 1
        self.db.flush()
        self.master_events.append(
            dock=dock, principal=principal, event_type="WAREHOUSE_DOCK_STATUS_CHANGED",
            audit_code="logistics.warehouse_dock.status_changed", reason=reason,
            previous_data={"status": previous}, new_data={"status": dock.status},
        )
        return dock

    def add_capability(
        self,
        dock_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        body: object,
    ) -> WarehouseDockCapabilityModel:
        self.get(dock_id, organization_id)
        data = body.model_dump()
        capability = WarehouseDockCapabilityModel(
            id=uuid4(),
            dock_id=dock_id,
            capability_code=data["capability_code"].upper(),
            value_type=data["value_type"],
            value_data=_as_json(data["value_data"]),
            status="ACTIVE",
            effective_from=data["effective_from"] or server_now(),
            effective_to=data["effective_to"],
        )
        self.db.add(capability)
        self.db.flush()
        dock = self.get(dock_id, organization_id)
        self.master_events.append(
            dock=dock, principal=principal, event_type="WAREHOUSE_DOCK_CAPABILITY_ADDED",
            audit_code="logistics.warehouse_dock.capability_added", new_data={"capability_code": capability.capability_code},
        )
        return capability

    def add_window(
        self,
        dock_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        body: object,
    ) -> WarehouseDockOperatingWindowModel:
        self.get(dock_id, organization_id, lock=True)
        data = body.model_dump()
        overlap = self.db.scalar(
            select(WarehouseDockOperatingWindowModel.id).where(
                WarehouseDockOperatingWindowModel.dock_id == dock_id,
                WarehouseDockOperatingWindowModel.day_of_week == data["day_of_week"],
                WarehouseDockOperatingWindowModel.status == "ACTIVE",
                WarehouseDockOperatingWindowModel.start_local_time < data["end_local_time"],
                WarehouseDockOperatingWindowModel.end_local_time > data["start_local_time"],
                or_(WarehouseDockOperatingWindowModel.effective_to.is_(None), WarehouseDockOperatingWindowModel.effective_to >= data["effective_from"]),
                or_(data["effective_to"] is None, WarehouseDockOperatingWindowModel.effective_from <= data["effective_to"]),
            )
        )
        if overlap:
            raise conflict("WAREHOUSE_DOCK_SCHEDULE_CONFLICT", "La ventana se solapa con otra ventana activa.")
        window = WarehouseDockOperatingWindowModel(id=uuid4(), dock_id=dock_id, status="ACTIVE", **data)
        self.db.add(window)
        self.db.flush()
        dock = self.get(dock_id, organization_id)
        self.master_events.append(
            dock=dock, principal=principal, event_type="WAREHOUSE_DOCK_WINDOW_ADDED",
            audit_code="logistics.warehouse_dock.window_added", new_data={"day_of_week": window.day_of_week},
        )
        return window

    def add_blackout(
        self,
        dock_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        body: object,
    ) -> WarehouseDockBlackoutModel:
        self.get(dock_id, organization_id, lock=True)
        data = body.model_dump()
        blackout = WarehouseDockBlackoutModel(
            id=uuid4(), dock_id=dock_id, status="ACTIVE", created_by=principal.user_id, **data
        )
        self.db.add(blackout)
        impacted = list(
            self.db.scalars(
                select(InboundDockAssignmentModel).where(
                    InboundDockAssignmentModel.dock_id == dock_id,
                    InboundDockAssignmentModel.status.in_(ACTIVE_ASSIGNMENT_STATUSES),
                    or_(
                        InboundDockAssignmentModel.planned_start.is_(None),
                        InboundDockAssignmentModel.planned_end.is_(None),
                        and_(
                            InboundDockAssignmentModel.planned_start < data["ends_at"],
                            InboundDockAssignmentModel.planned_end > data["starts_at"],
                        ),
                    ),
                )
            )
        )
        for assignment in impacted:
            if assignment.status in {DockAssignmentStatus.ASSIGNED.value, DockAssignmentStatus.MOVING_TO_DOCK.value}:
                assignment.status = DockAssignmentStatus.REASSIGNMENT_REQUIRED.value
                assignment.row_version += 1
        self.db.flush()
        dock = self.get(dock_id, organization_id)
        self.master_events.append(
            dock=dock, principal=principal, event_type="WAREHOUSE_DOCK_BLACKOUT_CREATED",
            audit_code="logistics.warehouse_dock.blackout_created", reason=blackout.reason,
            new_data={"blackout_id": str(blackout.id), "starts_at": blackout.starts_at, "ends_at": blackout.ends_at},
        )
        return blackout


class WarehouseDockAvailabilityService:
    def __init__(self, db: Session):
        self.db = db

    def resolve(self, dock: WarehouseDockModel, at: datetime | None = None) -> dict[str, object]:
        now = at or server_now()
        reasons: list[str] = []
        active_count = int(
            self.db.scalar(
                select(func.count()).select_from(InboundDockAssignmentModel).where(
                    InboundDockAssignmentModel.dock_id == dock.id,
                    InboundDockAssignmentModel.status.in_(ACTIVE_ASSIGNMENT_STATUSES),
                )
            )
            or 0
        )
        blackout = bool(
            self.db.scalar(
                select(WarehouseDockBlackoutModel.id).where(
                    WarehouseDockBlackoutModel.dock_id == dock.id,
                    WarehouseDockBlackoutModel.status == "ACTIVE",
                    WarehouseDockBlackoutModel.starts_at <= now,
                    WarehouseDockBlackoutModel.ends_at > now,
                )
            )
        )
        windows = list(
            self.db.scalars(
                select(WarehouseDockOperatingWindowModel).where(
                    WarehouseDockOperatingWindowModel.dock_id == dock.id,
                    WarehouseDockOperatingWindowModel.status == "ACTIVE",
                )
            )
        )
        within_window: bool | None = None
        if windows:
            local = now.astimezone(ZoneInfo(dock.timezone))
            within_window = any(
                row.day_of_week == local.weekday()
                and row.effective_from <= local.date()
                and (row.effective_to is None or row.effective_to >= local.date())
                and row.start_local_time <= local.time().replace(tzinfo=None) < row.end_local_time
                for row in windows
            )
            if not within_window:
                reasons.append("OUTSIDE_OPERATING_WINDOW")
        else:
            reasons.append("OPERATING_WINDOW_NOT_CONFIGURED")

        if dock.status == DockMasterStatus.BLOCKED.value:
            status = DockOperationalStatus.BLOCKED.value
            reasons.append("MASTER_BLOCKED")
        elif dock.status == DockMasterStatus.MAINTENANCE.value:
            status = DockOperationalStatus.MAINTENANCE.value
            reasons.append("MASTER_MAINTENANCE")
        elif dock.status != DockMasterStatus.ACTIVE.value:
            status = DockOperationalStatus.INACTIVE.value
            reasons.append("MASTER_NOT_ACTIVE")
        elif blackout:
            status = DockOperationalStatus.BLOCKED.value
            reasons.append("ACTIVE_BLACKOUT")
        elif within_window is False:
            status = DockOperationalStatus.INACTIVE.value
        elif active_count >= dock.simultaneous_vehicle_capacity:
            status = DockOperationalStatus.OCCUPIED.value
            reasons.append("CAPACITY_EXHAUSTED")
        elif active_count:
            status = DockOperationalStatus.RESERVED.value
        elif within_window is None:
            status = DockOperationalStatus.UNKNOWN.value
        else:
            status = DockOperationalStatus.AVAILABLE.value
        return {
            "dock_id": dock.id,
            "operational_status": status,
            "active_assignments": active_count,
            "capacity": dock.simultaneous_vehicle_capacity,
            "blackout_active": blackout,
            "within_operating_window": within_window,
            "reasons": reasons,
            "server_time": now,
            "available": status in {DockOperationalStatus.AVAILABLE.value, DockOperationalStatus.RESERVED.value},
            "occupied_slots": active_count,
            "available_slots": max(dock.simultaneous_vehicle_capacity - active_count, 0),
        }


class InboundDockQueueService:
    def __init__(self, db: Session):
        self.db = db
        self.events = UnloadingOperationalEventService(db)

    def get(self, entry_id: UUID, organization_id: UUID, *, lock: bool = False) -> InboundDockQueueEntryModel:
        query = select(InboundDockQueueEntryModel).where(
            InboundDockQueueEntryModel.id == entry_id,
            InboundDockQueueEntryModel.organization_id == organization_id,
        )
        if lock:
            query = query.with_for_update()
        row = self.db.scalar(query)
        if row is None:
            raise InboundDockQueueEntryNotFound()
        return row

    def create_from_gate(
        self,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        gate_check_in_id: UUID,
        priority: str,
        priority_reason: str | None,
    ) -> InboundDockQueueEntryModel:
        preparation = DockAssignmentPreparationService(self.db).get_preparation(gate_check_in_id, organization_id)
        gate = self.db.scalar(
            select(GateCheckInModel).where(
                GateCheckInModel.id == gate_check_in_id,
                GateCheckInModel.organization_id == organization_id,
            ).with_for_update()
        )
        if gate is None or gate.entry_authorized_at is None:
            raise invalid("GATE_CLEARANCE_NOT_AUTHORIZED", "El control de puerta no tiene autorización de ingreso válida.")
        if not preparation.get("observed_plate"):
            raise invalid("GATE_OBSERVED_VEHICLE_REQUIRED", "La placa observada es obligatoria para la cola interna.")
        active = self.db.scalar(
            select(InboundDockQueueEntryModel).where(
                InboundDockQueueEntryModel.gate_check_in_id == gate_check_in_id,
                InboundDockQueueEntryModel.queue_status.in_(ACTIVE_QUEUE_STATUSES),
            ).with_for_update()
        )
        if active:
            raise conflict("INBOUND_DOCK_QUEUE_ENTRY_ALREADY_EXISTS", "Ya existe una entrada activa para este control de puerta.")
        entry = InboundDockQueueEntryModel(
            id=uuid4(),
            organization_id=organization_id,
            warehouse_id=gate.warehouse_id,
            gate_check_in_id=gate.id,
            appointment_id=gate.appointment_id,
            arrival_notice_id=gate.arrival_notice_id,
            vehicle_id=UUID(preparation["vehicle_id"]) if preparation.get("vehicle_id") else None,
            observed_plate_snapshot=preparation["observed_plate"],
            supplier_snapshot=preparation.get("supplier_summary"),
            carrier_snapshot=preparation.get("carrier_summary"),
            priority=priority,
            priority_reason=priority_reason,
            queue_status=QueueStatus.WAITING.value,
            gate_cleared_at=gate.entry_authorized_at,
            queued_at=server_now(),
        )
        self.db.add(entry)
        self.db.flush()
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=entry.warehouse_id,
            gate_check_in_id=entry.gate_check_in_id,
            event_type=DockOperationalEventType.QUEUED_FOR_DOCK.value,
            audit_code="logistics.inbound_dock_queue.created",
            payload={"queue_entry_id": str(entry.id), "priority": priority},
            new_status=entry.queue_status,
        )
        return entry

    def transition(
        self,
        entry_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        target: QueueStatus,
        reason: str | None = None,
    ) -> InboundDockQueueEntryModel:
        entry = self.get(entry_id, organization_id, lock=True)
        allowed = {
            QueueStatus.WAITING.value: {QueueStatus.READY.value, QueueStatus.ON_HOLD.value, QueueStatus.REMOVED.value, QueueStatus.CANCELLED.value},
            QueueStatus.READY.value: {QueueStatus.ON_HOLD.value, QueueStatus.REMOVED.value, QueueStatus.CANCELLED.value},
            QueueStatus.ON_HOLD.value: {QueueStatus.WAITING.value, QueueStatus.READY.value, QueueStatus.REMOVED.value, QueueStatus.CANCELLED.value},
        }
        if target.value not in allowed.get(entry.queue_status, set()):
            raise invalid("INBOUND_DOCK_QUEUE_STATUS_INVALID", "Transición inválida de la cola interna.")
        previous = entry.queue_status
        entry.queue_status = target.value
        entry.row_version += 1
        if target == QueueStatus.READY:
            entry.ready_for_assignment_at = server_now()
        elif target in {QueueStatus.REMOVED, QueueStatus.CANCELLED}:
            if not reason:
                raise invalid("QUEUE_REMOVAL_REASON_REQUIRED", "El motivo es obligatorio.")
            entry.removed_at = server_now()
            entry.removal_reason = reason
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=entry.warehouse_id,
            gate_check_in_id=entry.gate_check_in_id,
            event_type="QUEUE_STATUS_CHANGED",
            audit_code="logistics.inbound_dock_queue.ready" if target == QueueStatus.READY else "logistics.inbound_dock_queue.held",
            payload={"queue_entry_id": str(entry.id)},
            reason=reason,
            previous_status=previous,
            new_status=entry.queue_status,
        )
        self.db.flush()
        return entry

    def change_priority(
        self,
        entry_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        priority: str,
        reason: str,
        row_version: int,
    ) -> InboundDockQueueEntryModel:
        entry = self.get(entry_id, organization_id, lock=True)
        if entry.row_version != row_version:
            raise conflict("OPTIMISTIC_LOCK_CONFLICT", "La entrada de cola fue modificada.")
        previous = entry.priority
        entry.priority = priority
        entry.priority_reason = reason
        entry.row_version += 1
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=entry.warehouse_id,
            gate_check_in_id=entry.gate_check_in_id,
            event_type=DockOperationalEventType.PRIORITY_CHANGED.value,
            audit_code="logistics.inbound_dock_queue.priority_changed",
            payload={"queue_entry_id": str(entry.id), "previous_priority": previous, "priority": priority},
            reason=reason,
        )
        self.db.flush()
        return entry


class InboundDockQueueOrderingService:
    """Deterministic queue ordering. No random, AI, or invented distances."""

    @staticmethod
    def order(entries: list[InboundDockQueueEntryModel]) -> list[InboundDockQueueEntryModel]:
        return sorted(
            entries,
            key=lambda row: (
                _PRIORITY_WEIGHT.get(row.priority, 99),
                row.gate_cleared_at,
                row.queued_at,
                str(row.id),
            ),
        )


class WarehouseDockCompatibilityService:
    def __init__(self, db: Session):
        self.db = db
        self.availability = WarehouseDockAvailabilityService(db)

    def evaluate(
        self,
        dock: WarehouseDockModel,
        preparation: dict,
        required_capabilities: list[str],
        at: datetime | None = None,
    ) -> dict[str, object]:
        blocking: list[str] = []
        warnings: list[str] = []
        matched: list[str] = []
        missing: list[str] = []
        explanation: list[str] = []
        availability = self.availability.resolve(dock, at)
        if dock.operation_direction not in {DockOperationDirection.INBOUND.value, DockOperationDirection.MIXED.value}:
            blocking.append("DIRECTION_NOT_INBOUND")
        if not availability["available"]:
            blocking.extend(str(reason) for reason in availability["reasons"] if reason != "OPERATING_WINDOW_NOT_CONFIGURED")
        if "OPERATING_WINDOW_NOT_CONFIGURED" in availability["reasons"]:
            missing.append("OPERATING_WINDOW")

        capability_rows = list(
            self.db.scalars(
                select(WarehouseDockCapabilityModel).where(
                    WarehouseDockCapabilityModel.dock_id == dock.id,
                    WarehouseDockCapabilityModel.status == "ACTIVE",
                    or_(WarehouseDockCapabilityModel.effective_to.is_(None), WarehouseDockCapabilityModel.effective_to > server_now()),
                )
            )
        )
        capability_codes = {row.capability_code for row in capability_rows}
        for code in sorted(set(required_capabilities)):
            if code in capability_codes:
                matched.append(code)
            else:
                blocking.append(f"CAPABILITY_REQUIRED:{code}")

        expected_pallets = preparation.get("expected_pallet_count")
        if dock.maximum_expected_pallets is not None:
            if expected_pallets is None:
                missing.append("EXPECTED_PALLET_COUNT")
            elif int(expected_pallets) > dock.maximum_expected_pallets:
                blocking.append("MAX_EXPECTED_PALLETS_EXCEEDED")
            else:
                matched.append("MAX_EXPECTED_PALLETS")

        expected_weight = preparation.get("expected_weight")
        if dock.maximum_vehicle_weight is not None:
            if expected_weight is None:
                missing.append("EXPECTED_WEIGHT")
            else:
                try:
                    if float(expected_weight) > float(dock.maximum_vehicle_weight):
                        blocking.append("MAX_EXPECTED_WEIGHT_EXCEEDED")
                    else:
                        matched.append("MAX_EXPECTED_WEIGHT")
                except (TypeError, ValueError):
                    missing.append("EXPECTED_WEIGHT_VALID")

        requirements = preparation.get("special_requirements") or {}
        if isinstance(requirements, dict):
            flag_map = {
                "refrigeration": (dock.refrigeration_capable, "REFRIGERATION"),
                "temperature_control": (dock.temperature_control_capable, "TEMPERATURE_CONTROL"),
                "hazardous_declared": (dock.hazardous_declared_capable, "HAZARDOUS_DECLARED"),
                "oversized": (dock.oversized_capable, "OVERSIZED"),
                "high_value": (dock.high_value_capable, "HIGH_VALUE"),
                "dock_leveler_required": (dock.dock_leveler_available, "DOCK_LEVELER_REQUIRED"),
            }
            for key, (supported, code) in flag_map.items():
                if requirements.get(key):
                    (matched if supported else blocking).append(code if supported else f"CAPABILITY_REQUIRED:{code}")

        if blocking:
            status = CompatibilityStatus.INCOMPATIBLE.value
        elif missing:
            status = CompatibilityStatus.INFORMATION_INCOMPLETE.value
            warnings.append("INFORMATION_INCOMPLETE")
        elif warnings:
            status = CompatibilityStatus.COMPATIBLE_WITH_WARNINGS.value
        else:
            status = CompatibilityStatus.COMPATIBLE.value
        explanation.extend(f"MATCH:{code}" for code in matched)
        explanation.extend(f"BLOCK:{code}" for code in blocking)
        explanation.extend(f"MISSING:{code}" for code in missing)
        score = max(0, 100 + len(matched) * 5 - len(warnings) * 10 - len(missing) * 15 - len(blocking) * 100)
        return {
            "dock_id": dock.id,
            "compatibility_status": status,
            "blocking_reasons": blocking,
            "warnings": warnings,
            "matched_capabilities": sorted(set(matched)),
            "missing_information": sorted(set(missing)),
            "availability_status": availability["operational_status"],
            "recommendation_score": score,
            "explanation": explanation,
        }


class WarehouseDockRecommendationService:
    @staticmethod
    def rank(results: list[dict[str, object]]) -> list[dict[str, object]]:
        status_weight = {
            CompatibilityStatus.COMPATIBLE.value: 0,
            CompatibilityStatus.COMPATIBLE_WITH_WARNINGS.value: 1,
            CompatibilityStatus.INFORMATION_INCOMPLETE.value: 2,
            CompatibilityStatus.REQUIRES_MANUAL_REVIEW.value: 3,
            CompatibilityStatus.INCOMPATIBLE.value: 4,
        }
        return sorted(
            results,
            key=lambda item: (
                status_weight.get(str(item["compatibility_status"]), 99),
                -int(item["recommendation_score"]),
                str(item["dock_id"]),
            ),
        )


class DockAssignmentService:
    PLAN_TTL = timedelta(minutes=5)

    def __init__(self, db: Session):
        self.db = db
        self.events = UnloadingOperationalEventService(db)
        self.compatibility = WarehouseDockCompatibilityService(db)

    def _queue_for_gate(self, gate_check_in_id: UUID, organization_id: UUID, lock: bool = False) -> InboundDockQueueEntryModel:
        query = select(InboundDockQueueEntryModel).where(
            InboundDockQueueEntryModel.gate_check_in_id == gate_check_in_id,
            InboundDockQueueEntryModel.organization_id == organization_id,
            InboundDockQueueEntryModel.queue_status.in_({QueueStatus.READY.value, QueueStatus.ASSIGNED.value}),
        )
        if lock:
            query = query.with_for_update()
        row = self.db.scalar(query)
        if row is None:
            raise invalid("INBOUND_DOCK_QUEUE_NOT_READY", "El vehículo debe estar READY en la cola interna.")
        return row

    def _hash(
        self,
        queue: InboundDockQueueEntryModel,
        docks: list[WarehouseDockModel],
        request_data: dict,
    ) -> str:
        active_rows = list(
            self.db.execute(
                select(
                    InboundDockAssignmentModel.id,
                    InboundDockAssignmentModel.dock_id,
                    InboundDockAssignmentModel.capacity_slot,
                    InboundDockAssignmentModel.row_version,
                ).where(InboundDockAssignmentModel.status.in_(ACTIVE_ASSIGNMENT_STATUSES))
            )
        )
        return sha256_payload(
            {
                "schema_version": "1.0.0",
                "queue": {"id": queue.id, "row_version": queue.row_version, "status": queue.queue_status},
                "docks": [
                    {"id": dock.id, "row_version": dock.row_version, "status": dock.status, "capacity": dock.simultaneous_vehicle_capacity}
                    for dock in sorted(docks, key=lambda item: str(item.id))
                ],
                "active_assignments": [tuple(map(str, row)) for row in sorted(active_rows, key=lambda item: str(item.id))],
                "request": request_data,
            }
        )

    def create_plan(
        self,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        request_data: dict,
    ) -> tuple[DockAssignmentPlanModel, dict[str, object]]:
        if str(request_data["assignment_mode"]) == AssignmentMode.POLICY_AUTOMATIC.value:
            raise invalid("POLICY_AUTOMATIC_DISABLED", "La asignación automática está desactivada por defecto.")
        gate_check_in_id = request_data["gate_check_in_id"]
        queue = self._queue_for_gate(gate_check_in_id, organization_id)
        preparation = DockAssignmentPreparationService(self.db).get_preparation(gate_check_in_id, organization_id)
        docks_query = select(WarehouseDockModel).where(
            WarehouseDockModel.organization_id == organization_id,
            WarehouseDockModel.warehouse_id == queue.warehouse_id,
            WarehouseDockModel.operation_direction.in_({DockOperationDirection.INBOUND.value, DockOperationDirection.MIXED.value}),
            WarehouseDockModel.status == DockMasterStatus.ACTIVE.value,
        )
        if request_data.get("proposed_dock_id"):
            docks_query = docks_query.where(WarehouseDockModel.id == request_data["proposed_dock_id"])
        docks = list(self.db.scalars(docks_query))
        at = request_data.get("requested_interval", {}).get("starts_at") if request_data.get("requested_interval") else None
        results = [
            self.compatibility.evaluate(dock, preparation, request_data.get("required_capabilities", []), at)
            for dock in docks
        ]
        ranked = WarehouseDockRecommendationService.rank(results)
        eligible = [
            item for item in ranked
            if item["compatibility_status"] in {
                CompatibilityStatus.COMPATIBLE.value,
                CompatibilityStatus.COMPATIBLE_WITH_WARNINGS.value,
            }
        ]
        incompatible = [item for item in ranked if item not in eligible]
        assignment_hash = self._hash(queue, docks, request_data)
        now = server_now()
        plan = DockAssignmentPlanModel(
            id=uuid4(),
            organization_id=organization_id,
            gate_check_in_id=gate_check_in_id,
            queue_entry_id=queue.id,
            proposed_dock_id=request_data.get("proposed_dock_id"),
            requested_interval=_as_json(request_data.get("requested_interval")) if request_data.get("requested_interval") else None,
            estimated_duration_minutes=request_data.get("estimated_duration_minutes"),
            required_capabilities=request_data.get("required_capabilities", []),
            priority=str(request_data["priority"]),
            assignment_mode=str(request_data["assignment_mode"]),
            eligible_docks=_as_json(eligible),
            recommendation=_as_json(eligible[0]) if eligible else None,
            conflicts=[],
            warnings=["NO_ELIGIBLE_DOCK"] if not eligible else [],
            assignment_hash=assignment_hash,
            status="ACTIVE",
            created_by=principal.user_id,
            expires_at=now + self.PLAN_TTL,
        )
        self.db.add(plan)
        self.db.flush()
        ordered = InboundDockQueueOrderingService.order(
            list(
                self.db.scalars(
                    select(InboundDockQueueEntryModel).where(
                        InboundDockQueueEntryModel.warehouse_id == queue.warehouse_id,
                        InboundDockQueueEntryModel.queue_status.in_({QueueStatus.WAITING.value, QueueStatus.READY.value}),
                    )
                )
            )
        )
        position = next((index + 1 for index, row in enumerate(ordered) if row.id == queue.id), None)
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=queue.warehouse_id,
            gate_check_in_id=queue.gate_check_in_id,
            event_type=DockOperationalEventType.ASSIGNMENT_PLANNED.value,
            audit_code="logistics.inbound_dock_assignment.planned",
            payload={"plan_id": str(plan.id), "assignment_hash": assignment_hash},
        )
        return plan, {
            "plan_id": plan.id,
            "gate_check_in_id": gate_check_in_id,
            "eligible_docks": eligible,
            "recommendation": eligible[0] if eligible else None,
            "incompatibilities": incompatible,
            "conflicts": [],
            "warnings": plan.warnings,
            "assignment_hash": assignment_hash,
            "active_queue_position": position,
            "expires_at": plan.expires_at,
            "server_time": now,
        }

    def get(self, assignment_id: UUID, organization_id: UUID, *, lock: bool = False) -> InboundDockAssignmentModel:
        query = select(InboundDockAssignmentModel).where(
            InboundDockAssignmentModel.id == assignment_id,
            InboundDockAssignmentModel.organization_id == organization_id,
        )
        if lock:
            query = query.with_for_update()
        assignment = self.db.scalar(query)
        if assignment is None:
            raise DockAssignmentNotFound()
        return assignment

    def execute_plan(
        self,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        assignment_hash: str,
        selected_dock_id: UUID | None,
        reason: str,
    ) -> InboundDockAssignmentModel:
        plan = self.db.scalar(
            select(DockAssignmentPlanModel).where(
                DockAssignmentPlanModel.organization_id == organization_id,
                DockAssignmentPlanModel.assignment_hash == assignment_hash,
            ).with_for_update()
        )
        if plan is None or plan.status != "ACTIVE":
            raise invalid("DOCK_ASSIGNMENT_PLAN_EXPIRED", "El plan no existe o ya fue ejecutado.")
        if plan.expires_at <= server_now():
            plan.status = "EXPIRED"
            raise conflict("DOCK_ASSIGNMENT_PLAN_EXPIRED", "El plan expiró; genere uno nuevo.")
        queue = self._queue_for_gate(plan.gate_check_in_id, organization_id, lock=True)
        eligible_ids = {UUID(str(item["dock_id"])) for item in plan.eligible_docks}
        dock_id = selected_dock_id or (UUID(str(plan.recommendation["dock_id"])) if plan.recommendation else None)
        if dock_id is None or dock_id not in eligible_ids:
            raise invalid("WAREHOUSE_DOCK_INCOMPATIBLE", "El muelle no fue elegible en el plan.")
        dock = WarehouseDockService(self.db).get(dock_id, organization_id, lock=True)
        request_data = {
            "gate_check_in_id": plan.gate_check_in_id,
            "proposed_dock_id": plan.proposed_dock_id,
            "estimated_duration_minutes": plan.estimated_duration_minutes,
            "assignment_mode": plan.assignment_mode,
            "priority": plan.priority,
            "requested_interval": plan.requested_interval,
            "required_capabilities": plan.required_capabilities,
        }
        all_docks = list(
            self.db.scalars(
                select(WarehouseDockModel).where(
                    WarehouseDockModel.organization_id == organization_id,
                    WarehouseDockModel.warehouse_id == queue.warehouse_id,
                    WarehouseDockModel.operation_direction.in_({"INBOUND", "MIXED"}),
                    WarehouseDockModel.status == "ACTIVE",
                    *([WarehouseDockModel.id == plan.proposed_dock_id] if plan.proposed_dock_id else []),
                )
            )
        )
        if self._hash(queue, all_docks, request_data) != assignment_hash:
            raise conflict("DOCK_ASSIGNMENT_HASH_MISMATCH", "La disponibilidad cambió; genere un plan nuevo.")
        replaced_assignment = self.db.scalar(
            select(InboundDockAssignmentModel).where(
                InboundDockAssignmentModel.gate_check_in_id == plan.gate_check_in_id,
                InboundDockAssignmentModel.organization_id == organization_id,
                InboundDockAssignmentModel.status == DockAssignmentStatus.REASSIGNMENT_REQUIRED.value,
            ).with_for_update()
        )
        if replaced_assignment is not None:
            replaced_assignment.status = DockAssignmentStatus.SUPERSEDED.value
            replaced_assignment.row_version += 1
            previous_occupancy = self.db.scalar(
                select(DockOccupancyIntervalModel).where(
                    DockOccupancyIntervalModel.dock_assignment_id == replaced_assignment.id,
                    DockOccupancyIntervalModel.status == OccupancyStatus.ACTIVE.value,
                ).with_for_update()
            )
            if previous_occupancy is not None:
                previous_occupancy.status = OccupancyStatus.CANCELLED.value
                previous_occupancy.occupied_until = server_now()
            self.db.flush()
        preparation = DockAssignmentPreparationService(self.db).get_preparation(plan.gate_check_in_id, organization_id)
        compatibility = self.compatibility.evaluate(
            dock,
            preparation,
            list(plan.required_capabilities or []),
            datetime.fromisoformat(plan.requested_interval["starts_at"]) if plan.requested_interval else None,
        )
        if compatibility["compatibility_status"] not in {
            CompatibilityStatus.COMPATIBLE.value,
            CompatibilityStatus.COMPATIBLE_WITH_WARNINGS.value,
        }:
            raise conflict("WAREHOUSE_DOCK_UNAVAILABLE", "El muelle dejó de estar disponible o compatible.")
        active = list(
            self.db.scalars(
                select(InboundDockAssignmentModel).where(
                    InboundDockAssignmentModel.dock_id == dock.id,
                    InboundDockAssignmentModel.status.in_(ACTIVE_ASSIGNMENT_STATUSES),
                ).with_for_update()
            )
        )
        occupied_slots = {row.capacity_slot for row in active}
        free_slot = next((slot for slot in range(1, dock.simultaneous_vehicle_capacity + 1) if slot not in occupied_slots), None)
        if free_slot is None:
            raise conflict("WAREHOUSE_DOCK_CAPACITY_EXCEEDED", "No queda capacidad en el muelle.")
        planned_start = planned_end = None
        if plan.requested_interval:
            planned_start = datetime.fromisoformat(plan.requested_interval["starts_at"])
            planned_end = datetime.fromisoformat(plan.requested_interval["ends_at"])
            overlap = self.db.scalar(
                select(InboundDockAssignmentModel.id).where(
                    InboundDockAssignmentModel.dock_id == dock.id,
                    InboundDockAssignmentModel.capacity_slot == free_slot,
                    InboundDockAssignmentModel.status.in_(ACTIVE_ASSIGNMENT_STATUSES),
                    InboundDockAssignmentModel.planned_start < planned_end,
                    InboundDockAssignmentModel.planned_end > planned_start,
                )
            )
            if overlap:
                raise conflict("DOCK_ASSIGNMENT_OVERLAP_CONFLICT", "El intervalo se solapa con una asignación activa.")
        now = server_now()
        assignment = InboundDockAssignmentModel(
            id=uuid4(),
            organization_id=organization_id,
            branch_id=dock.branch_id,
            warehouse_id=dock.warehouse_id,
            dock_id=dock.id,
            queue_entry_id=queue.id,
            gate_check_in_id=queue.gate_check_in_id,
            appointment_id=queue.appointment_id,
            arrival_notice_id=queue.arrival_notice_id,
            vehicle_id=queue.vehicle_id,
            observed_plate_snapshot=queue.observed_plate_snapshot,
            status=DockAssignmentStatus.ASSIGNED.value,
            assignment_mode=plan.assignment_mode,
            assignment_reason=reason,
            compatibility_snapshot=_as_json(compatibility),
            assignment_hash=assignment_hash,
            planned_start=planned_start,
            planned_end=planned_end,
            capacity_slot=free_slot,
            assigned_at=now,
            assigned_by_user_id=principal.user_id,
            assigned_by_snapshot=actor_snapshot(principal),
        )
        self.db.add(assignment)
        queue.queue_status = QueueStatus.ASSIGNED.value
        queue.assigned_at = now
        queue.row_version += 1
        plan.status = "EXECUTED"
        plan.executed_at = now
        try:
            self.db.flush()
        except IntegrityError as exc:
            raise conflict("DOCK_ASSIGNMENT_CONFLICT", "Otra transacción confirmó una asignación incompatible.") from exc
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=assignment.warehouse_id,
            gate_check_in_id=assignment.gate_check_in_id,
            dock_id=assignment.dock_id,
            assignment_id=assignment.id,
            event_type=DockOperationalEventType.DOCK_ASSIGNED.value,
            audit_code="logistics.inbound_dock_assignment.created",
            payload={"capacity_slot": free_slot, "assignment_mode": assignment.assignment_mode},
            reason=reason,
            new_status=assignment.status,
        )
        return assignment

    def start_movement(self, assignment_id: UUID, organization_id: UUID, principal: LogisticsPrincipal) -> InboundDockAssignmentModel:
        assignment = self.get(assignment_id, organization_id, lock=True)
        require_transition(assignment.status, DockAssignmentStatus.MOVING_TO_DOCK.value, ASSIGNMENT_TRANSITIONS, "dock_assignment")
        dock = WarehouseDockService(self.db).get(assignment.dock_id, organization_id, lock=True)
        availability = WarehouseDockAvailabilityService(self.db).resolve(dock)
        if (
            dock.status != DockMasterStatus.ACTIVE.value
            or availability["blackout_active"]
            or availability["within_operating_window"] is False
        ):
            raise conflict("WAREHOUSE_DOCK_UNAVAILABLE", "El muelle no está operativo para iniciar el movimiento.")
        DockAssignmentPreparationService(self.db).get_preparation(assignment.gate_check_in_id, organization_id)
        previous = assignment.status
        assignment.status = DockAssignmentStatus.MOVING_TO_DOCK.value
        assignment.movement_started_at = server_now()
        assignment.row_version += 1
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=assignment.warehouse_id,
            gate_check_in_id=assignment.gate_check_in_id,
            dock_id=assignment.dock_id,
            assignment_id=assignment.id,
            event_type=DockOperationalEventType.MOVEMENT_TO_DOCK_STARTED.value,
            audit_code="logistics.inbound_dock_assignment.movement_started",
            previous_status=previous,
            new_status=assignment.status,
        )
        self.db.flush()
        return assignment

    def confirm_arrival(self, assignment_id: UUID, organization_id: UUID, principal: LogisticsPrincipal) -> InboundDockAssignmentModel:
        assignment = self.get(assignment_id, organization_id, lock=True)
        require_transition(assignment.status, DockAssignmentStatus.AT_DOCK.value, ASSIGNMENT_TRANSITIONS, "dock_assignment")
        WarehouseDockService(self.db).get(assignment.dock_id, organization_id, lock=True)
        existing = self.db.scalar(
            select(DockOccupancyIntervalModel).where(
                DockOccupancyIntervalModel.dock_assignment_id == assignment.id,
                DockOccupancyIntervalModel.status == OccupancyStatus.ACTIVE.value,
            ).with_for_update()
        )
        if existing:
            raise conflict("DOCK_OCCUPANCY_ALREADY_ACTIVE", "La asignación ya ocupa el muelle.")
        now = server_now()
        previous = assignment.status
        assignment.status = DockAssignmentStatus.AT_DOCK.value
        assignment.dock_arrived_at = now
        assignment.row_version += 1
        self.db.add(
            DockOccupancyIntervalModel(
                id=uuid4(),
                dock_id=assignment.dock_id,
                dock_assignment_id=assignment.id,
                vehicle_id=assignment.vehicle_id,
                gate_check_in_id=assignment.gate_check_in_id,
                capacity_slot=assignment.capacity_slot,
                occupied_from=now,
                status=OccupancyStatus.ACTIVE.value,
                source="DOCK_ARRIVAL",
            )
        )
        try:
            self.db.flush()
        except IntegrityError as exc:
            raise conflict("DOCK_OCCUPANCY_CONFLICT", "El espacio del muelle ya está ocupado.") from exc
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=assignment.warehouse_id,
            gate_check_in_id=assignment.gate_check_in_id,
            dock_id=assignment.dock_id,
            assignment_id=assignment.id,
            event_type=DockOperationalEventType.ARRIVED_AT_DOCK.value,
            audit_code="logistics.inbound_dock_assignment.arrived_at_dock",
            previous_status=previous,
            new_status=assignment.status,
        )
        return assignment

    def mark_ready(self, assignment_id: UUID, organization_id: UUID, principal: LogisticsPrincipal) -> InboundDockAssignmentModel:
        assignment = self.get(assignment_id, organization_id, lock=True)
        require_transition(assignment.status, DockAssignmentStatus.READY_FOR_UNLOADING.value, ASSIGNMENT_TRANSITIONS, "dock_assignment")
        previous = assignment.status
        assignment.status = DockAssignmentStatus.READY_FOR_UNLOADING.value
        assignment.row_version += 1
        self.db.flush()
        return assignment

    def cancel(self, assignment_id: UUID, organization_id: UUID, principal: LogisticsPrincipal, reason: str) -> InboundDockAssignmentModel:
        assignment = self.get(assignment_id, organization_id, lock=True)
        if assignment.status in {
            DockAssignmentStatus.UNLOADING_IN_PROGRESS.value,
            DockAssignmentStatus.UNLOADING_PAUSED.value,
            DockAssignmentStatus.UNLOADING_COMPLETED.value,
            DockAssignmentStatus.DOCK_RELEASED.value,
        }:
            raise invalid("DOCK_ASSIGNMENT_CANCELLATION_NOT_ALLOWED", "No se puede cancelar en el estado actual.")
        previous = assignment.status
        assignment.status = DockAssignmentStatus.CANCELLED.value
        assignment.cancellation_reason = reason
        assignment.row_version += 1
        queue = self.db.get(InboundDockQueueEntryModel, assignment.queue_entry_id)
        if queue:
            queue.queue_status = QueueStatus.CANCELLED.value
            queue.removed_at = server_now()
            queue.removal_reason = reason
            queue.row_version += 1
        occupancy = self.db.scalar(
            select(DockOccupancyIntervalModel).where(
                DockOccupancyIntervalModel.dock_assignment_id == assignment.id,
                DockOccupancyIntervalModel.status == OccupancyStatus.ACTIVE.value,
            ).with_for_update()
        )
        if occupancy:
            occupancy.status = OccupancyStatus.CANCELLED.value
            occupancy.occupied_until = server_now()
        self.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=assignment.warehouse_id,
            gate_check_in_id=assignment.gate_check_in_id,
            dock_id=assignment.dock_id,
            assignment_id=assignment.id,
            event_type="DOCK_ASSIGNMENT_CANCELLED",
            audit_code="logistics.inbound_dock_assignment.cancelled",
            reason=reason,
            previous_status=previous,
            new_status=assignment.status,
        )
        self.db.flush()
        return assignment

    def request_reassignment(self, assignment_id: UUID, organization_id: UUID, principal: LogisticsPrincipal, reason: str) -> InboundDockAssignmentModel:
        assignment = self.get(assignment_id, organization_id, lock=True)
        if assignment.status not in {DockAssignmentStatus.ASSIGNED.value, DockAssignmentStatus.MOVING_TO_DOCK.value, DockAssignmentStatus.AT_DOCK.value}:
            raise invalid("DOCK_REASSIGNMENT_NOT_ALLOWED", "La reasignación ordinaria solo se permite antes de iniciar descarga.")
        assignment.status = DockAssignmentStatus.REASSIGNMENT_REQUIRED.value
        assignment.cancellation_reason = reason
        assignment.row_version += 1
        queue = self.db.get(InboundDockQueueEntryModel, assignment.queue_entry_id)
        if queue:
            queue.queue_status = QueueStatus.READY.value
            queue.row_version += 1
        self.db.flush()
        return assignment


class DockAssignmentValidator:
    @staticmethod
    def ensure_server_owned_fields(payload_fields: set[str]) -> None:
        prohibited = {
            "assigned_at", "assigned_by", "assigned_by_user_id", "movement_started_at",
            "dock_arrived_at", "released_at", "released_by", "status",
        }
        if payload_fields & prohibited:
            raise invalid("AUTHORITATIVE_FIELD_REJECTED", "El cliente envió campos autoritativos.")


class DockOccupancyService:
    def __init__(self, db: Session):
        self.db = db

    def close(self, assignment: InboundDockAssignmentModel, at: datetime) -> DockOccupancyIntervalModel:
        occupancy = self.db.scalar(
            select(DockOccupancyIntervalModel).where(
                DockOccupancyIntervalModel.dock_assignment_id == assignment.id,
                DockOccupancyIntervalModel.status == OccupancyStatus.ACTIVE.value,
            ).with_for_update()
        )
        if occupancy is None:
            raise invalid("UNLOADING_DOCK_RELEASE_BLOCKED", "No existe ocupación activa para liberar.")
        if at < occupancy.occupied_from:
            raise invalid("UNLOADING_TIME_SEQUENCE_INVALID", "La liberación no puede preceder a la ocupación.")
        occupancy.occupied_until = at
        occupancy.status = OccupancyStatus.CLOSED.value
        self.db.flush()
        return occupancy


class DockReassignmentService:
    def __init__(self, db: Session):
        self.db = db
        self.assignments = DockAssignmentService(db)

    def reassign(
        self,
        old_assignment_id: UUID,
        organization_id: UUID,
        principal: LogisticsPrincipal,
        new_dock_id: UUID,
        assignment_hash: str,
        reason: str,
        row_version: int,
    ) -> InboundDockAssignmentModel:
        old = self.assignments.get(old_assignment_id, organization_id, lock=True)
        if old.row_version != row_version:
            raise conflict("OPTIMISTIC_LOCK_CONFLICT", "La asignación cambió durante la reasignación.")
        if old.status != DockAssignmentStatus.REASSIGNMENT_REQUIRED.value:
            raise invalid("DOCK_REASSIGNMENT_NOT_ALLOWED", "Primero debe solicitarse la reasignación.")
        new = self.assignments.execute_plan(
            organization_id,
            principal,
            assignment_hash,
            new_dock_id,
            reason,
        )
        new.reassigned_from_assignment_id = old.id
        old.superseded_by_assignment_id = new.id
        self.assignments.events.append(
            principal=principal,
            organization_id=organization_id,
            warehouse_id=new.warehouse_id,
            gate_check_in_id=new.gate_check_in_id,
            dock_id=new.dock_id,
            assignment_id=new.id,
            event_type=DockOperationalEventType.DOCK_REASSIGNED.value,
            audit_code="logistics.inbound_dock_assignment.reassigned",
            payload={"previous_assignment_id": str(old.id), "previous_dock_id": str(old.dock_id)},
            reason=reason,
        )
        self.db.flush()
        return new
