"""Phase 043 — Application services for putaway orchestration."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from ...domain.enums import (
    PutawayOrderStatus,
    PutawayOrderSourceType,
    PutawayTaskStatus,
    PutawayRecommendationRunStatus,
    PutawayCandidateStatus,
    ReservationStatus,
    ExecutionSessionStatus,
    ScanValidationStatus,
    PlacementConfirmationStatus,
    ScannerType,
    ScanType,
    ScanResolutionStatus,
    OverrideReasonCode,
    ExceptionType,
    ExceptionSeverity,
    ExceptionStatus,
    PauseReason,
    OperationalPlacementStatus,
    PutawayTaskDestinationStatus,
    PutawayOrderRevisionStatus,
    AssignmentStatus,
)
from ...domain.errors import (
    PutawayOrderNotFound,
    PutawayOrderStatusInvalid,
    PutawayTaskNotFound,
    PutawayTaskStatusInvalid,
    PutawayTaskAlreadyAssigned,
    PutawayTaskScanRequired,
    PutawayProductMismatch,
    PutawayQuantityInvalid,
    PutawayQuantityExceeded,
    PutawayLocationBlocked,
    PutawayIntegrityFailed,
)
from ...domain.services.recommendation_service import RecommendationService
from ...domain.services.eligibility_service import EligibilityService
from ...domain.services.capacity_service import CapacityService
from ...infrastructure.persistence.repositories import (
    PutawayOrderRepository,
    PutawayOrderRevisionRepository,
    PutawayTaskRepository,
    PutawayTaskDestinationRepository,
    PutawayTaskAssignmentRepository,
    PutawayLocationReservationRepository,
    PutawayExecutionSessionRepository,
    PutawayScanEventRepository,
    PutawayPlacementConfirmationRepository,
    PutawayLocationOverrideRepository,
    PutawayTaskExceptionRepository,
    PutawayTaskPauseRepository,
    OperationalInventoryPlacementRepository,
    PutawayLocationPlacementProjectionRepository,
    compute_content_hash,
)
from ...infrastructure.persistence.models import (
    PutawayOrderModel,
    PutawayOrderRevisionModel,
    PutawayTaskModel,
    PutawayTaskDestinationModel,
    PutawayTaskAssignmentModel,
    PutawayLocationReservationModel,
    PutawayExecutionSessionModel,
    PutawayScanEventModel,
    PutawayPlacementConfirmationModel,
    PutawayLocationOverrideModel,
    PutawayTaskExceptionModel,
    PutawayTaskPauseModel,
    OperationalInventoryPlacementModel,
)


class PutawayApplicationService:
    """High-level orchestration for putaway workflows."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._recommendation = RecommendationService(db)
        self._eligibility = EligibilityService(db)
        self._capacity = CapacityService(db)

        self._order_repo = PutawayOrderRepository(db)
        self._revision_repo = PutawayOrderRevisionRepository(db)
        self._task_repo = PutawayTaskRepository(db)
        self._dest_repo = PutawayTaskDestinationRepository(db)
        self._assignment_repo = PutawayTaskAssignmentRepository(db)
        self._reservation_repo = PutawayLocationReservationRepository(db)
        self._session_repo = PutawayExecutionSessionRepository(db)
        self._scan_repo = PutawayScanEventRepository(db)
        self._confirmation_repo = PutawayPlacementConfirmationRepository(db)
        self._override_repo = PutawayLocationOverrideRepository(db)
        self._exception_repo = PutawayTaskExceptionRepository(db)
        self._pause_repo = PutawayTaskPauseRepository(db)
        self._placement_repo = OperationalInventoryPlacementRepository(db)
        self._projection_repo = PutawayLocationPlacementProjectionRepository(db)

    # =========================================================================
    # Orders
    # =========================================================================
    def create_order(
        self,
        *,
        organization_id: UUID,
        branch_id: UUID,
        warehouse_id: UUID,
        source_type: str = PutawayOrderSourceType.QUALITY_RELEASE.value,
        priority: int = 0,
        created_by: UUID,
    ) -> PutawayOrderModel:
        order_count = self._order_repo.list(
            organization_id, warehouse_id=warehouse_id, page_size=1
        )[1]
        order_code = f"PO-{warehouse_id.hex[:8].upper()}-{order_count + 1:06d}"

        order = PutawayOrderModel(
            id=uuid4(),
            organization_id=organization_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            order_code=order_code,
            normalized_order_code=order_code.upper(),
            status=PutawayOrderStatus.DRAFT.value,
            source_type=source_type,
            priority=priority,
            created_by=created_by,
        )
        return self._order_repo.create(order)

    def issue_order(self, order_id: UUID, *, issued_by: UUID) -> PutawayOrderModel:
        order = self._order_repo.get(order_id)
        if not order:
            raise PutawayOrderNotFound(str(order_id))
        if order.status != PutawayOrderStatus.DRAFT.value:
            raise PutawayOrderStatusInvalid(
                f"Cannot issue order in status {order.status}"
            )

        tasks = self._task_repo.list(order.organization_id, putaway_order_id=order_id, page_size=1000)[0]
        if not tasks:
            raise PutawayIntegrityFailed("Order has no tasks")

        order.status = PutawayOrderStatus.ISSUED.value
        order.issued_at = datetime.now(timezone.utc)
        order.issued_by = issued_by
        order.task_count = len(tasks)
        order.current_revision_number = 1

        revision = PutawayOrderRevisionModel(
            id=uuid4(),
            putaway_order_id=order.id,
            revision_number=1,
            status=PutawayOrderRevisionStatus.FROZEN.value,
            created_by=issued_by,
            frozen_at=datetime.now(timezone.utc),
        )
        self._revision_repo.create(revision)
        order.active_revision_id = revision.id

        return self._order_repo.update(order)

    def cancel_order(
        self, order_id: UUID, *, cancelled_by: UUID, reason: str
    ) -> PutawayOrderModel:
        order = self._order_repo.get(order_id)
        if not order:
            raise PutawayOrderNotFound(str(order_id))
        if order.status in (PutawayOrderStatus.COMPLETED.value, PutawayOrderStatus.CANCELLED.value):
            raise PutawayOrderStatusInvalid(f"Cannot cancel order in status {order.status}")

        order.status = PutawayOrderStatus.CANCELLED.value
        order.cancelled_at = datetime.now(timezone.utc)
        order.cancellation_reason = reason
        return self._order_repo.update(order)

    def complete_order(self, order_id: UUID) -> PutawayOrderModel:
        order = self._order_repo.get(order_id)
        if not order:
            raise PutawayOrderNotFound(str(order_id))

        completed = self._task_repo.count_completed_by_order(order_id)
        exceptions = self._task_repo.count_exception_by_order(order_id)

        if exceptions > 0:
            order.status = PutawayOrderStatus.EXCEPTION.value
        elif completed == order.task_count:
            order.status = PutawayOrderStatus.COMPLETED.value
            order.completed_at = datetime.now(timezone.utc)
        else:
            order.status = PutawayOrderStatus.IN_PROGRESS.value

        return self._order_repo.update(order)

    def list_orders(
        self, organization_id: UUID, **kwargs
    ) -> tuple[list[PutawayOrderModel], int]:
        return self._order_repo.list(organization_id, **kwargs)

    def get_order(self, order_id: UUID, organization_id: UUID | None = None) -> PutawayOrderModel | None:
        return self._order_repo.get(order_id, organization_id)

    # =========================================================================
    # Tasks
    # =========================================================================
    def create_task(
        self,
        *,
        organization_id: UUID,
        warehouse_id: UUID,
        putaway_order_id: UUID,
        source_allocation_id: UUID,
        required_quantity: Decimal,
        required_unit_id: UUID,
        required_base_quantity: Decimal,
        expected_product_id: UUID,
        priority: int = 0,
        scan_policy: str = "PRODUCT_THEN_LOCATION",
    ) -> PutawayTaskModel:
        task_number = self._task_repo.next_task_number(putaway_order_id)

        task = PutawayTaskModel(
            id=uuid4(),
            organization_id=organization_id,
            warehouse_id=warehouse_id,
            putaway_order_id=putaway_order_id,
            task_number=task_number,
            source_allocation_id=source_allocation_id,
            status=PutawayTaskStatus.CREATED.value,
            priority=priority,
            required_quantity=required_quantity,
            required_unit_id=required_unit_id,
            required_base_quantity=required_base_quantity,
            remaining_quantity=required_quantity,
            remaining_base_quantity=required_base_quantity,
            scan_policy=scan_policy,
            expected_product_id=expected_product_id,
        )
        return self._task_repo.create(task)

    def assign_task(
        self,
        task_id: UUID,
        *,
        user_id: UUID,
        assigned_by: UUID,
    ) -> PutawayTaskModel:
        task = self._task_repo.get(task_id)
        if not task:
            raise PutawayTaskNotFound(str(task_id))
        if task.status not in (PutawayTaskStatus.CREATED.value, PutawayTaskStatus.READY.value):
            raise PutawayTaskStatusInvalid(f"Cannot assign task in status {task.status}")
        if task.assignment_status != "UNASSIGNED":
            raise PutawayTaskAlreadyAssigned(str(task_id))

        assignment = PutawayTaskAssignmentModel(
            id=uuid4(),
            task_id=task_id,
            assignment_type="USER",
            user_id=user_id,
            status=AssignmentStatus.ASSIGNED.value,
            assigned_by=assigned_by,
        )
        self._assignment_repo.create(assignment)

        task.assignment_status = "ASSIGNED"
        task.assigned_user_id = user_id
        task.assigned_at = datetime.now(timezone.utc)
        return self._task_repo.update(task)

    def start_task(self, task_id: UUID, *, user_id: UUID) -> PutawayTaskModel:
        task = self._task_repo.get(task_id)
        if not task:
            raise PutawayTaskNotFound(str(task_id))
        if task.status != PutawayTaskStatus.CREATED.value:
            raise PutawayTaskStatusInvalid(f"Cannot start task in status {task.status}")
        if task.assigned_user_id != user_id:
            raise PutawayTaskStatusInvalid("Task not assigned to this user")

        task.status = PutawayTaskStatus.IN_PROGRESS.value
        task.started_at = datetime.now(timezone.utc)
        return self._task_repo.update(task)

    def complete_task(self, task_id: UUID) -> PutawayTaskModel:
        task = self._task_repo.get(task_id)
        if not task:
            raise PutawayTaskNotFound(str(task_id))
        if task.status != PutawayTaskStatus.IN_PROGRESS.value:
            raise PutawayTaskStatusInvalid(f"Cannot complete task in status {task.status}")

        confirmations = self._confirmation_repo.list_by_task(task_id)
        total_placed = sum(c.base_quantity for c in confirmations if c.confirmation_status == "CONFIRMED")

        if total_placed < task.required_base_quantity:
            raise PutawayQuantityInvalid(
                f"Placed quantity {total_placed} less than required {task.required_base_quantity}"
            )

        task.status = PutawayTaskStatus.COMPLETED.value
        task.completed_at = datetime.now(timezone.utc)
        task.placed_base_quantity = total_placed
        task.remaining_base_quantity = Decimal("0")
        task.remaining_quantity = Decimal("0")
        return self._task_repo.update(task)

    def pause_task(
        self,
        task_id: UUID,
        *,
        user_id: UUID,
        reason: str,
        description: str | None = None,
    ) -> PutawayTaskPauseModel:
        task = self._task_repo.get(task_id)
        if not task:
            raise PutawayTaskNotFound(str(task_id))
        if task.status != PutawayTaskStatus.IN_PROGRESS.value:
            raise PutawayTaskStatusInvalid(f"Cannot pause task in status {task.status}")

        task.status = PutawayTaskStatus.PAUSED.value
        task.paused_at = datetime.now(timezone.utc)
        self._task_repo.update(task)

        pause = PutawayTaskPauseModel(
            id=uuid4(),
            task_id=task_id,
            pause_reason=reason,
            description=description,
            paused_by=user_id,
        )
        return self._pause_repo.create(pause)

    def resume_task(self, task_id: UUID) -> PutawayTaskModel:
        task = self._task_repo.get(task_id)
        if not task:
            raise PutawayTaskNotFound(str(task_id))
        if task.status != PutawayTaskStatus.PAUSED.value:
            raise PutawayTaskStatusInvalid(f"Cannot resume task in status {task.status}")

        active_pause = self._pause_repo.get_active_for_task(task_id)
        if active_pause:
            self._pause_repo.resume(active_pause.id)

        task.status = PutawayTaskStatus.IN_PROGRESS.value
        task.paused_at = None
        return self._task_repo.update(task)

    def get_task(self, task_id: UUID, organization_id: UUID | None = None) -> PutawayTaskModel | None:
        return self._task_repo.get(task_id, organization_id)

    def list_tasks(
        self, organization_id: UUID, **kwargs
    ) -> tuple[list[PutawayTaskModel], int]:
        return self._task_repo.list(organization_id, **kwargs)

    # =========================================================================
    # Reservations
    # =========================================================================
    def create_reservation(
        self,
        *,
        organization_id: UUID,
        warehouse_id: UUID,
        location_id: UUID,
        task_id: UUID,
        source_allocation_id: UUID,
        capacity_profile_id: UUID,
        reserved_value: Decimal,
        unit_id: UUID,
        reserved_base_quantity: Decimal,
        expires_in_minutes: int = 30,
    ) -> PutawayLocationReservationModel:
        now = datetime.now(timezone.utc)
        reservation = PutawayLocationReservationModel(
            id=uuid4(),
            organization_id=organization_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            task_id=task_id,
            source_allocation_id=source_allocation_id,
            capacity_profile_id=capacity_profile_id,
            reserved_value=reserved_value,
            unit_id=unit_id,
            reserved_base_quantity=reserved_base_quantity,
            status=ReservationStatus.ACTIVE.value,
            reserved_at=now,
            expires_at=now.replace(minute=now.minute + expires_in_minutes),
        )
        reservation = self._reservation_repo.create(reservation)

        self._capacity.update_projection(
            organization_id, warehouse_id, location_id, capacity_profile_id,
            active_reserved_delta=reserved_value,
        )

        return reservation

    def release_reservation(self, reservation_id: UUID) -> PutawayLocationReservationModel:
        reservation = self._reservation_repo.get(reservation_id)
        if not reservation:
            raise ValueError(f"Reservation {reservation_id} not found")

        self._capacity.update_projection(
            reservation.organization_id, reservation.warehouse_id,
            reservation.location_id, reservation.capacity_profile_id,
            active_reserved_delta=-reservation.reserved_value,
        )

        reservation.status = ReservationStatus.RELEASED.value
        reservation.released_at = datetime.now(timezone.utc)
        self._reservation_repo.update_status(
            reservation_id,
            status=ReservationStatus.RELEASED.value,
            released_at=datetime.now(timezone.utc),
        )
        return reservation

    def consume_reservation(self, reservation_id: UUID) -> PutawayLocationReservationModel:
        reservation = self._reservation_repo.get(reservation_id)
        if not reservation:
            raise ValueError(f"Reservation {reservation_id} not found")

        self._capacity.update_projection(
            reservation.organization_id, reservation.warehouse_id,
            reservation.location_id, reservation.capacity_profile_id,
            operational_occupied_delta=reservation.reserved_value,
            active_reserved_delta=-reservation.reserved_value,
        )

        reservation.status = ReservationStatus.CONSUMED.value
        reservation.consumed_at = datetime.now(timezone.utc)
        self._reservation_repo.update_status(
            reservation_id,
            status=ReservationStatus.CONSUMED.value,
            consumed_at=datetime.now(timezone.utc),
        )
        return reservation

    def release_expired_reservations(self) -> int:
        return self._reservation_repo.release_expired()

    # =========================================================================
    # Execution Sessions
    # =========================================================================
    def create_execution_session(
        self,
        *,
        task_id: UUID,
        operator_user_id: UUID,
        scanner_type: str = ScannerType.HANDHELD_TERMINAL.value,
        device_reference_hash: str | None = None,
        client_session_reference: str | None = None,
    ) -> PutawayExecutionSessionModel:
        task = self._task_repo.get(task_id)
        if not task:
            raise PutawayTaskNotFound(str(task_id))
        if task.status not in (PutawayTaskStatus.IN_PROGRESS.value, PutawayTaskStatus.CREATED.value):
            raise PutawayTaskStatusInvalid(f"Cannot create session for task in status {task.status}")

        session = PutawayExecutionSessionModel(
            id=uuid4(),
            task_id=task_id,
            operator_user_id=operator_user_id,
            scanner_type=scanner_type,
            device_reference_hash=device_reference_hash,
            status=ExecutionSessionStatus.ACTIVE.value,
            client_session_reference=client_session_reference,
        )
        return self._session_repo.create(session)

    def complete_execution_session(self, session_id: UUID) -> PutawayExecutionSessionModel:
        session = self._session_repo.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.status = ExecutionSessionStatus.COMPLETED.value
        session.completed_at = datetime.now(timezone.utc)
        self._session_repo.update_status(
            session_id,
            status=ExecutionSessionStatus.COMPLETED.value,
            completed_at=datetime.now(timezone.utc),
        )
        return session

    # =========================================================================
    # Scans
    # =========================================================================
    def record_scan(
        self,
        *,
        session_id: UUID,
        task_id: UUID,
        organization_id: UUID,
        warehouse_id: UUID,
        client_scan_id: str,
        scan_type: str,
        normalized_code: str,
        code_hash: str,
        symbology: str | None = None,
        raw_code_encrypted: str | None = None,
        operator_user_id: UUID,
    ) -> PutawayScanEventModel:
        existing = self._scan_repo.get_by_client_scan_id(session_id, client_scan_id)
        if existing:
            return existing

        server_sequence = self._scan_repo.next_server_sequence(session_id)

        event = PutawayScanEventModel(
            id=uuid4(),
            organization_id=organization_id,
            warehouse_id=warehouse_id,
            task_id=task_id,
            execution_session_id=session_id,
            client_scan_id=client_scan_id,
            server_sequence=server_sequence,
            scan_type=scan_type,
            normalized_code=normalized_code,
            code_hash=code_hash,
            symbology=symbology,
            raw_code_encrypted=raw_code_encrypted,
            resolution_status=ScanResolutionStatus.RECORDED.value,
            operator_user_id=operator_user_id,
            status=ScanResolutionStatus.RECORDED.value,
        )
        return self._scan_repo.create(event)

    def validate_product_scan(
        self, session_id: UUID, event_id: UUID, *, expected_product_id: UUID
    ) -> PutawayScanEventModel:
        event = self._scan_repo.get(event_id)
        if not event:
            raise ValueError(f"Scan event {event_id} not found")

        task = self._task_repo.get(event.task_id)
        if task and task.expected_product_id == expected_product_id:
            event.resolution_status = ScanResolutionStatus.MATCHED.value
            event.resolved_product_id = expected_product_id
            event.validation_status = "VALID"
        else:
            event.resolution_status = ScanResolutionStatus.MISMATCH.value
            event.validation_status = "INVALID"

        event.status = ScanResolutionStatus.VALID.value
        self._db.flush()
        return event

    def validate_location_scan(
        self, session_id: UUID, event_id: UUID, *, expected_location_id: UUID | None = None
    ) -> PutawayScanEventModel:
        event = self._scan_repo.get(event_id)
        if not event:
            raise ValueError(f"Scan event {event_id} not found")

        if expected_location_id and event.resolved_location_id == expected_location_id:
            event.resolution_status = ScanResolutionStatus.MATCHED.value
            event.validation_status = "VALID"
        elif expected_location_id is None:
            event.resolution_status = ScanResolutionStatus.MATCHED.value
            event.validation_status = "VALID"
        else:
            event.resolution_status = ScanResolutionStatus.MISMATCH.value
            event.validation_status = "INVALID"

        event.status = ScanResolutionStatus.VALID.value
        self._db.flush()
        return event

    def require_scans_for_task(self, session_id: UUID, scan_policy: str) -> bool:
        if scan_policy == "PRODUCT_THEN_LOCATION":
            return self._scan_repo.has_product_scan(session_id)
        elif scan_policy == "LOCATION_THEN_PRODUCT":
            return self._scan_repo.has_location_scan(session_id)
        return True

    # =========================================================================
    # Placement Confirmations
    # =========================================================================
    def confirm_placement(
        self,
        *,
        task_id: UUID,
        source_allocation_id: UUID,
        location_id: UUID,
        quantity: Decimal,
        unit_id: UUID,
        base_quantity: Decimal,
        confirmed_by: UUID,
        product_scan_event_id: UUID | None = None,
        location_scan_event_id: UUID | None = None,
        reservation_id: UUID | None = None,
        observation: str | None = None,
    ) -> PutawayPlacementConfirmationModel:
        task = self._task_repo.get(task_id)
        if not task:
            raise PutawayTaskNotFound(str(task_id))

        existing_placed = self._confirmation_repo.sum_placed_for_allocation(source_allocation_id)
        if existing_placed + base_quantity > task.required_base_quantity:
            raise PutawayQuantityExceeded(
                f"Placement would exceed required quantity. "
                f"Already placed: {existing_placed}, "
                f"Trying to place: {base_quantity}, "
                f"Required: {task.required_base_quantity}"
            )

        content_hash = compute_content_hash({
            "task_id": str(task_id),
            "location_id": str(location_id),
            "quantity": str(quantity),
            "unit_id": str(unit_id),
            "base_quantity": str(base_quantity),
            "confirmed_by": str(confirmed_by),
        })

        existing_by_hash = self._confirmation_repo.get_by_hash(content_hash)
        if existing_by_hash:
            return existing_by_hash

        confirmation = PutawayPlacementConfirmationModel(
            id=uuid4(),
            organization_id=task.organization_id,
            warehouse_id=task.warehouse_id,
            task_id=task_id,
            source_allocation_id=source_allocation_id,
            location_id=location_id,
            quantity=quantity,
            unit_id=unit_id,
            base_quantity=base_quantity,
            product_scan_event_id=product_scan_event_id,
            location_scan_event_id=location_scan_event_id,
            reservation_id=reservation_id,
            confirmation_status=PlacementConfirmationStatus.CONFIRMED.value,
            confirmed_by=confirmed_by,
            observation=observation,
            content_hash=content_hash,
        )
        return self._confirmation_repo.create(confirmation)

    def finalize_placement(self, confirmation_id: UUID) -> OperationalInventoryPlacementModel:
        confirmation = self._confirmation_repo.get(confirmation_id)
        if not confirmation:
            raise ValueError(f"Confirmation {confirmation_id} not found")

        task = self._task_repo.get(confirmation.task_id)
        if not task:
            raise PutawayTaskNotFound(str(confirmation.task_id))

        operational = OperationalInventoryPlacementModel(
            id=uuid4(),
            organization_id=confirmation.organization_id,
            warehouse_id=confirmation.warehouse_id,
            location_id=confirmation.location_id,
            source_allocation_id=confirmation.source_allocation_id,
            putaway_order_id=task.putaway_order_id,
            putaway_task_id=task.id,
            placement_confirmation_id=confirmation.id,
            product_id=task.expected_product_id,
            product_version_id=task.product_version_id,
            quantity=confirmation.quantity,
            unit_id=confirmation.unit_id,
            base_quantity=confirmation.base_quantity,
            quality_release_hash=task.quality_release_hash,
            status=OperationalPlacementStatus.PLACED_PENDING_MOVEMENT_LEDGER.value,
            placed_by=confirmation.confirmed_by,
        )
        operational.content_hash = compute_content_hash({
            "id": str(operational.id),
            "location_id": str(operational.location_id),
            "product_id": str(operational.product_id),
            "quantity": str(operational.quantity),
        })

        placement = self._placement_repo.create(operational)

        self._projection_repo.update_quantity(
            confirmation.organization_id, confirmation.warehouse_id,
            confirmation.location_id, task.expected_product_id,
            quantity_delta=confirmation.quantity,
            base_quantity_delta=confirmation.base_quantity,
        )

        return placement

    # =========================================================================
    # Overrides
    # =========================================================================
    def request_location_override(
        self,
        *,
        task_id: UUID,
        recommended_location_id: UUID,
        selected_location_id: UUID,
        recommendation_run_id: UUID,
        recommended_score: Decimal,
        selected_score: Decimal,
        reason_code: str,
        reason: str,
        requested_by: UUID,
    ) -> PutawayLocationOverrideModel:
        override = PutawayLocationOverrideModel(
            id=uuid4(),
            task_id=task_id,
            recommended_location_id=recommended_location_id,
            selected_location_id=selected_location_id,
            recommendation_run_id=recommendation_run_id,
            recommended_score=recommended_score,
            selected_score=selected_score,
            reason_code=reason_code,
            reason=reason,
            requested_by=requested_by,
        )
        return self._override_repo.create(override)

    def approve_override(
        self,
        override_id: UUID,
        *,
        approved_by: UUID,
        step_up_summary: dict | None = None,
    ) -> None:
        self._override_repo.approve(override_id, approved_by, step_up_summary)

    # =========================================================================
    # Exceptions
    # =========================================================================
    def report_exception(
        self,
        *,
        task_id: UUID,
        exception_type: str,
        severity: str = ExceptionSeverity.MEDIUM.value,
        description: str,
        detected_by: UUID,
        product_scan_event_id: UUID | None = None,
        location_scan_event_id: UUID | None = None,
        location_id: UUID | None = None,
        quantity: Decimal | None = None,
        unit_id: UUID | None = None,
        evidence_file_ids: list[str] | None = None,
    ) -> PutawayTaskExceptionModel:
        task = self._task_repo.get(task_id)
        if not task:
            raise PutawayTaskNotFound(str(task_id))

        exception = PutawayTaskExceptionModel(
            id=uuid4(),
            task_id=task_id,
            exception_type=exception_type,
            severity=severity,
            product_scan_event_id=product_scan_event_id,
            location_scan_event_id=location_scan_event_id,
            location_id=location_id,
            quantity=quantity,
            unit_id=unit_id,
            description=description,
            evidence_file_ids=evidence_file_ids or [],
            status=ExceptionStatus.OPEN.value,
            detected_by=detected_by,
        )
        exc = self._exception_repo.create(exception)

        task.exception_count += 1
        task.status = PutawayTaskStatus.EXCEPTION.value
        self._task_repo.update(task)

        return exc

    def resolve_exception(
        self,
        exception_id: UUID,
        *,
        resolved_by: UUID,
        resolution: str,
    ) -> PutawayTaskExceptionModel:
        exc = self._exception_repo.get(exception_id)
        if not exc:
            raise ValueError(f"Exception {exception_id} not found")

        self._exception_repo.update_status(
            exception_id,
            status=ExceptionStatus.RESOLVED.value,
            resolved_by=resolved_by,
            resolution=resolution,
        )

        open_count = self._exception_repo.count_open_by_task(exc.task_id)
        if open_count == 0:
            task = self._task_repo.get(exc.task_id)
            if task and task.status == PutawayTaskStatus.EXCEPTION.value:
                task.status = PutawayTaskStatus.IN_PROGRESS.value
                self._task_repo.update(task)

        return self._exception_repo.get(exception_id)

    # =========================================================================
    # Recommendations
    # =========================================================================
    def request_recommendation(
        self,
        *,
        organization_id: UUID,
        warehouse_id: UUID,
        source_allocation_id: UUID,
        requested_quantity: Decimal,
        requested_unit_id: UUID,
        requested_base_quantity: Decimal,
        source_location_id: UUID,
        product_id: UUID,
        product_category_id: UUID | None,
        created_by: UUID,
    ):
        return self._recommendation.execute_recommendation(
            organization_id=organization_id,
            warehouse_id=warehouse_id,
            source_allocation_id=source_allocation_id,
            requested_quantity=requested_quantity,
            requested_unit_id=requested_unit_id,
            requested_base_quantity=requested_base_quantity,
            source_location_id=source_location_id,
            product_id=product_id,
            product_category_id=product_category_id,
            created_by=created_by,
        )

    def get_recommendation(self, run_id: UUID):
        return self._recommendation.get_recommendation(run_id)

    def list_recommendation_candidates(self, run_id: UUID):
        return self._recommendation.list_candidates(run_id)

    def get_best_recommendation(self, run_id: UUID):
        return self._recommendation.get_best_candidate(run_id)

    # =========================================================================
    # Projections
    # =========================================================================
    def get_location_projection(self, location_id: UUID):
        return self._projection_repo.list_by_location(location_id)

    def get_product_projections(self, organization_id: UUID, product_id: UUID):
        return self._projection_repo.list_by_product(organization_id, product_id)
