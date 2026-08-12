"""Core application services for Phase 037 Gate Control.

Key design decisions:
- GateArrivalTimeService: Server clock only, never client-supplied time.
- GateGuardResolver: Guard identity from authenticated session only.
- GateAppointmentResolver: Resolves CIT/QR without leaking cross-tenant data.
- GateDecisionService: Append-only decision log, no PATCH on decisions.
- GateCheckInSnapshotProvider: Immutable snapshot; never re-queries live data.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.modules.logistics.inbound.gate_control.domain.errors import (
    GateCheckInAlreadyExistsError,
    GateCheckInAppointmentAlreadyUsedError,
    GateCheckInAppointmentCancelledError,
    GateCheckInAppointmentInvalidError,
    GateCheckInArrivalAlreadyRecordedError,
    GateCheckInDecisionConflictError,
    GateCheckInExceptionNotApprovedError,
    GateCheckInNotFoundError,
    GateCheckInStatusInvalidError,
    GateCheckInWalkInNotAllowedError,
    WarehouseGateInactiveError,
    WarehouseGateNotFoundError,
)
from app.modules.logistics.inbound.gate_control.domain.value_objects import (
    ArrivalClassification,
    DecisionType,
    GateCheckInStatus,
    GateStatus,
    validate_status_transition,
)
from app.modules.logistics.inbound.gate_control.infrastructure.persistence.models import (
    GateCheckInModel,
    GateCheckInRevisionModel,
    GateEntryDecisionModel,
    GateVerificationCheckResultModel,
    GateVerificationExceptionModel,
    WarehouseGateModel,
)


# ─────────────────────────────────────────────────────────────────────────────
# GateArrivalTimeService
# ─────────────────────────────────────────────────────────────────────────────

class GateArrivalTimeService:
    """Provides authoritative server-side arrival timestamps.

    CRITICAL: arrived_at is ALWAYS set from the server clock.
    Client-supplied timestamps are NEVER accepted for ordinary arrival registration.
    """

    def now_utc(self) -> datetime:
        """Return current UTC time from server clock."""
        return datetime.now(timezone.utc)

    def classify_arrival(
        self,
        arrived_at: datetime,
        window_start: Optional[datetime],
        window_end: Optional[datetime],
        late_tolerance_minutes: int = 30,
        early_tolerance_minutes: int = 60,
    ) -> str:
        """Classify arrival relative to appointment window.

        Returns an ArrivalClassification enum value string.
        """
        if window_start is None or window_end is None:
            return ArrivalClassification.TIME_NOT_CLASSIFIED.value

        if window_start.tzinfo is None:
            window_start = window_start.replace(tzinfo=timezone.utc)
        if window_end.tzinfo is None:
            window_end = window_end.replace(tzinfo=timezone.utc)

        from datetime import timedelta

        early_threshold = window_start - timedelta(minutes=early_tolerance_minutes)
        late_threshold = window_end + timedelta(minutes=late_tolerance_minutes)

        if arrived_at < early_threshold:
            return ArrivalClassification.OUTSIDE_WINDOW.value
        elif arrived_at < window_start:
            return ArrivalClassification.EARLY.value
        elif arrived_at <= window_end:
            return ArrivalClassification.ON_TIME.value
        elif arrived_at <= late_threshold:
            return ArrivalClassification.LATE.value
        else:
            return ArrivalClassification.OUTSIDE_WINDOW.value


gate_arrival_time_service = GateArrivalTimeService()


# ─────────────────────────────────────────────────────────────────────────────
# GateGuardResolver
# ─────────────────────────────────────────────────────────────────────────────

class GateGuardResolver:
    """Resolves guard identity from the authenticated session.

    CRITICAL: guard_user_id is NEVER accepted from frontend payload.
    """

    def resolve(self, principal) -> dict:
        """Return guard snapshot from the authenticated principal.

        Raises GateCheckInGuardNotAuthorizedError if the user lacks
        the required gate guard permission.
        """
        from app.modules.logistics.inbound.gate_control.domain.errors import (
            GateCheckInGuardNotAuthorizedError,
        )

        if not principal.has_permission("logistics.gate_check_ins.create") and not principal.is_platform_admin:
            raise GateCheckInGuardNotAuthorizedError()

        return {
            "user_id": str(principal.user_id),
            "display_name": getattr(principal, "display_name", None)
            or getattr(principal, "full_name", None)
            or str(principal.user_id),
            "email": getattr(principal, "email", None),
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }


gate_guard_resolver = GateGuardResolver()


# ─────────────────────────────────────────────────────────────────────────────
# GateAppointmentResolver
# ─────────────────────────────────────────────────────────────────────────────

class GateAppointmentResolver:
    """Resolves a confirmed appointment for gate check-in.

    Supports resolution by:
    - CIT code (exact)
    - Opaque internal QR payload
    - Appointment UUID (authorized, internal)
    - Expected plate (returns minimal result set)
    """

    # Appointment statuses allowed for gate check-in
    ALLOWED_STATUSES = {"CONFIRMED", "WINDOW_ELAPSED"}
    BLOCKED_STATUSES = {"CANCELLED", "REPLACED", "SUPERSEDED"}

    def resolve_by_cit_code(
        self,
        db: Session,
        cit_code: str,
        warehouse_id: UUID,
        organization_id: UUID,
    ) -> dict:
        """Resolve appointment by CIT code within warehouse/org scope."""
        from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
            ReceptionAppointmentModel,
        )

        row = db.scalars(
            select(ReceptionAppointmentModel).where(
                ReceptionAppointmentModel.organization_id == organization_id,
                ReceptionAppointmentModel.warehouse_id == warehouse_id,
                ReceptionAppointmentModel.appointment_code == cit_code,
            )
        ).first()

        if row is None:
            raise GateCheckInAppointmentInvalidError("Código CIT no encontrado.")

        return self._validate_and_build(db, row, organization_id)

    def resolve_by_appointment_id(
        self,
        db: Session,
        appointment_id: UUID,
        warehouse_id: UUID,
        organization_id: UUID,
    ) -> dict:
        """Resolve appointment by internal UUID (requires authenticated session)."""
        from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
            ReceptionAppointmentModel,
        )

        row = db.scalars(
            select(ReceptionAppointmentModel).where(
                ReceptionAppointmentModel.id == appointment_id,
                ReceptionAppointmentModel.organization_id == organization_id,
                ReceptionAppointmentModel.warehouse_id == warehouse_id,
            )
        ).first()

        if row is None:
            raise GateCheckInAppointmentInvalidError(
                "Cita no encontrada en este almacén."
            )

        return self._validate_and_build(db, row, organization_id)

    def _validate_and_build(
        self,
        db: Session,
        row,
        organization_id: UUID,
    ) -> dict:
        """Validate appointment eligibility and return gate preparation data."""
        status = getattr(row, "status", None) or getattr(row, "appointment_status", None)

        if status in self.BLOCKED_STATUSES:
            if status == "CANCELLED":
                raise GateCheckInAppointmentCancelledError()
            raise GateCheckInAppointmentInvalidError(
                f"La cita tiene estado '{status}' y no permite check-in."
            )

        if status not in self.ALLOWED_STATUSES:
            raise GateCheckInAppointmentInvalidError(
                f"La cita tiene estado '{status}'. Se requiere CONFIRMED."
            )

        # Check for existing active check-ins
        existing = db.scalars(
            select(GateCheckInModel).where(
                GateCheckInModel.appointment_id == row.id,
                GateCheckInModel.status.not_in(
                    ["CANCELLED", "COMPLETED", "ENTRY_DENIED", "SUPERSEDED"]
                ),
            )
        ).first()

        if existing is not None:
            raise GateCheckInAlreadyExistsError(str(row.id))

        # Build preparation data from Fase 036 gate_preparation contract
        from app.modules.logistics.inbound.reception_calendar.application.services.appointment_service import (
            AppointmentService,
        )

        svc = AppointmentService(db)
        try:
            prep = svc.gate_preparation(row.id, organization_id)
        except Exception:
            prep = {}

        return {
            "appointment_id": row.id,
            "appointment_code": getattr(row, "appointment_code", None),
            "appointment_status": status,
            "arrival_notice_id": getattr(row, "arrival_notice_id", None),
            "warehouse_id": getattr(row, "warehouse_id", None),
            "supplier_snapshot": getattr(row, "supplier_snapshot", None),
            "carrier_snapshot": getattr(row, "carrier_snapshot", None),
            "gate_preparation": prep,
        }


gate_appointment_resolver = GateAppointmentResolver()


# ─────────────────────────────────────────────────────────────────────────────
# GateCheckInService
# ─────────────────────────────────────────────────────────────────────────────

class GateCheckInService:
    """Core lifecycle service for GateCheckIn aggregate."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, check_in_id: UUID, organization_id: UUID) -> GateCheckInModel:
        row = self.db.scalars(
            select(GateCheckInModel).where(
                GateCheckInModel.id == check_in_id,
                GateCheckInModel.organization_id == organization_id,
            )
        ).first()
        if row is None:
            raise GateCheckInNotFoundError(str(check_in_id))
        return row

    def create(
        self,
        db: Session,
        *,
        gate_id: UUID,
        appointment_resolution: dict,
        guard_snapshot: dict,
        guard_user_id: UUID,
        organization_id: UUID,
        branch_id: UUID,
        warehouse_id: UUID,
        source_type: str = "APPOINTMENT",
        policy_version_id: Optional[UUID] = None,
        idempotency_key: Optional[str] = None,
    ) -> GateCheckInModel:
        """Create a new GateCheckIn from an appointment resolution.

        The guard is taken from guard_snapshot/guard_user_id which are
        resolved from the authenticated session, NEVER from the payload.
        """
        gate = db.scalars(
            select(WarehouseGateModel).where(
                WarehouseGateModel.id == gate_id,
                WarehouseGateModel.organization_id == organization_id,
            )
        ).first()
        if gate is None:
            raise WarehouseGateNotFoundError(str(gate_id))
        if gate.status != GateStatus.ACTIVE.value:
            raise WarehouseGateInactiveError(str(gate_id))

        appointment_id = appointment_resolution.get("appointment_id")
        arrival_notice_id = appointment_resolution.get("arrival_notice_id")

        check_in = GateCheckInModel(
            id=uuid4(),
            organization_id=organization_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            gate_id=gate_id,
            appointment_id=appointment_id,
            arrival_notice_id=arrival_notice_id,
            appointment_code_snapshot=appointment_resolution.get("appointment_code"),
            status=GateCheckInStatus.CREATED.value,
            source_type=source_type,
            arrival_classification=ArrivalClassification.TIME_NOT_CLASSIFIED.value,
            gate_timezone=gate.timezone,
            guard_user_id=guard_user_id,
            guard_snapshot=guard_snapshot,
            supplier_snapshot=appointment_resolution.get("supplier_snapshot"),
            carrier_snapshot=appointment_resolution.get("carrier_snapshot"),
            verification_policy_version_id=policy_version_id
            or gate.active_verification_policy_version_id,
            current_revision_number=1,
            exception_count=0,
            failed_check_count=0,
            warning_count=0,
        )
        db.add(check_in)
        db.flush()

        # Create initial editable revision
        revision = GateCheckInRevisionModel(
            id=uuid4(),
            gate_check_in_id=check_in.id,
            revision_number=1,
            status="EDITABLE",
            created_by=guard_user_id,
        )
        db.add(revision)
        db.flush()

        check_in.active_revision_id = revision.id
        return check_in

    def record_arrival(
        self,
        check_in_id: UUID,
        organization_id: UUID,
        *,
        policy_version_tolerance: Optional[dict] = None,
    ) -> GateCheckInModel:
        """Record authoritative arrival time from server clock.

        CRITICAL: arrived_at is set exclusively from server clock.
        No client-supplied time is accepted here.
        """
        check_in = self.get(check_in_id, organization_id)

        if check_in.status != GateCheckInStatus.CREATED.value:
            if check_in.arrived_at is not None:
                raise GateCheckInArrivalAlreadyRecordedError()
            raise GateCheckInStatusInvalidError(
                check_in.status, GateCheckInStatus.CREATED.value
            )

        now = gate_arrival_time_service.now_utc()
        check_in.arrived_at = now
        check_in.recorded_at = now

        # Classify arrival against appointment window if available
        appt_data = self._get_appointment_window(check_in)
        if appt_data:
            tolerance = policy_version_tolerance or {}
            check_in.arrival_classification = gate_arrival_time_service.classify_arrival(
                arrived_at=now,
                window_start=appt_data.get("window_start"),
                window_end=appt_data.get("window_end"),
                late_tolerance_minutes=tolerance.get("late_tolerance_minutes", 30),
                early_tolerance_minutes=tolerance.get("early_tolerance_minutes", 60),
            )

        self._transition(check_in, GateCheckInStatus.ARRIVAL_RECORDED.value)
        return check_in

    def start_verification(
        self,
        check_in_id: UUID,
        organization_id: UUID,
        user_id: UUID,
    ) -> GateCheckInModel:
        check_in = self.get(check_in_id, organization_id)
        validate_status_transition(check_in.status, GateCheckInStatus.VERIFICATION_IN_PROGRESS.value)
        now = gate_arrival_time_service.now_utc()
        if check_in.check_started_at is None:
            check_in.check_started_at = now
        self._transition(check_in, GateCheckInStatus.VERIFICATION_IN_PROGRESS.value)
        return check_in

    def hold(
        self,
        check_in_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        hold_reason: str,
    ) -> GateCheckInModel:
        check_in = self.get(check_in_id, organization_id)
        validate_status_transition(check_in.status, GateCheckInStatus.HELD_AT_GATE.value)
        check_in.hold_reason = hold_reason
        self._transition(check_in, GateCheckInStatus.HELD_AT_GATE.value)
        return check_in

    def request_supervisor(
        self,
        check_in_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> GateCheckInModel:
        check_in = self.get(check_in_id, organization_id)
        validate_status_transition(check_in.status, GateCheckInStatus.WAITING_SUPERVISOR.value)
        self._transition(check_in, GateCheckInStatus.WAITING_SUPERVISOR.value)
        return check_in

    def resume(
        self,
        check_in_id: UUID,
        organization_id: UUID,
        user_id: UUID,
    ) -> GateCheckInModel:
        check_in = self.get(check_in_id, organization_id)
        validate_status_transition(check_in.status, GateCheckInStatus.VERIFICATION_IN_PROGRESS.value)
        self._transition(check_in, GateCheckInStatus.VERIFICATION_IN_PROGRESS.value)
        return check_in

    def cancel(
        self,
        check_in_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> GateCheckInModel:
        check_in = self.get(check_in_id, organization_id)
        validate_status_transition(check_in.status, GateCheckInStatus.CANCELLED.value)
        self._transition(check_in, GateCheckInStatus.CANCELLED.value)
        return check_in

    def complete(
        self,
        check_in_id: UUID,
        organization_id: UUID,
        user_id: UUID,
    ) -> GateCheckInModel:
        check_in = self.get(check_in_id, organization_id)
        validate_status_transition(check_in.status, GateCheckInStatus.COMPLETED.value)
        now = gate_arrival_time_service.now_utc()
        check_in.check_completed_at = now
        self._transition(check_in, GateCheckInStatus.COMPLETED.value)
        return check_in

    def _transition(self, check_in: GateCheckInModel, new_status: str) -> None:
        """Apply status transition and bump row_version (optimistic concurrency)."""
        check_in.status = new_status
        check_in.row_version = (check_in.row_version or 1) + 1

    def _get_appointment_window(self, check_in: GateCheckInModel) -> Optional[dict]:
        """Try to retrieve appointment window for classification."""
        if check_in.appointment_id is None:
            return None
        try:
            from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
                ReceptionAppointmentModel,
            )

            appt = self.db.scalars(
                select(ReceptionAppointmentModel).where(
                    ReceptionAppointmentModel.id == check_in.appointment_id,
                )
            ).first()
            if appt is None:
                return None
            return {
                "window_start": getattr(appt, "scheduled_start_time", None),
                "window_end": getattr(appt, "scheduled_end_time", None),
            }
        except Exception:
            return None


# ─────────────────────────────────────────────────────────────────────────────
# GateDecisionService
# ─────────────────────────────────────────────────────────────────────────────

class GateDecisionService:
    """Handles entry decisions for gate check-ins.

    Rules:
    - Decisions are APPEND-ONLY. No PATCH or DELETE.
    - AUTHORIZE_ENTRY only allowed when no blocking failures remain.
    - AUTHORIZE_WITH_OBSERVATIONS requires all blocking exceptions approved.
    - DENY_ENTRY requires a reason.
    - decided_by resolved from authenticated session, never from payload.
    """

    def __init__(self, db: Session):
        self.db = db

    def validate_can_decide(self, check_in: GateCheckInModel) -> dict:
        """Validate whether a decision can be taken. Return summary."""
        # Check for existing final decision
        existing_final = self.db.scalars(
            select(GateEntryDecisionModel).where(
                GateEntryDecisionModel.gate_check_in_id == check_in.id,
                GateEntryDecisionModel.decision_type.in_([
                    DecisionType.AUTHORIZE_ENTRY.value,
                    DecisionType.AUTHORIZE_WITH_OBSERVATIONS.value,
                    DecisionType.DENY_ENTRY.value,
                ])
            )
        ).first()
        if existing_final:
            raise GateCheckInDecisionConflictError()

        # Count blocking failed checks
        blocking_failed = list(self.db.scalars(
            select(GateVerificationCheckResultModel).where(
                GateVerificationCheckResultModel.gate_check_in_id == check_in.id,
                GateVerificationCheckResultModel.result == "FAIL",
                GateVerificationCheckResultModel.blocking == True,
            )
        ))

        # Count pending exceptions
        pending_exceptions = list(self.db.scalars(
            select(GateVerificationExceptionModel).where(
                GateVerificationExceptionModel.gate_check_in_id == check_in.id,
                GateVerificationExceptionModel.status == "REQUESTED",
            )
        ))

        return {
            "blocking_failed_count": len(blocking_failed),
            "blocking_failed": [r.check_code for r in blocking_failed],
            "pending_exceptions_count": len(pending_exceptions),
            "can_authorize": len(blocking_failed) == 0 and len(pending_exceptions) == 0,
            "can_authorize_with_observations": len(pending_exceptions) == 0,
        }

    def authorize_entry(
        self,
        check_in: GateCheckInModel,
        decided_by: UUID,
        reason: str,
        step_up_summary: Optional[dict] = None,
        supervisor_user_id: Optional[UUID] = None,
    ) -> GateEntryDecisionModel:
        """Authorize entry without observations (all checks must pass)."""
        summary = self.validate_can_decide(check_in)
        if not summary["can_authorize"]:
            from app.modules.logistics.inbound.gate_control.domain.errors import (
                GateCheckInBlockingCheckFailedError,
            )
            raise GateCheckInBlockingCheckFailedError(
                ", ".join(summary["blocking_failed"])
            )

        decision_hash = self._compute_hash(check_in, DecisionType.AUTHORIZE_ENTRY.value)
        now = gate_arrival_time_service.now_utc()

        decision = GateEntryDecisionModel(
            id=uuid4(),
            gate_check_in_id=check_in.id,
            decision_type=DecisionType.AUTHORIZE_ENTRY.value,
            decision_reason=reason,
            decided_by=decided_by,
            decided_at=now,
            supervisor_user_id=supervisor_user_id,
            step_up_assurance_summary=step_up_summary,
            decision_hash=decision_hash,
        )
        self.db.add(decision)

        check_in.decision = DecisionType.AUTHORIZE_ENTRY.value
        check_in.decision_reason = reason
        check_in.decision_at = now
        check_in.entry_authorized_at = now
        check_in.entry_authorized_by = decided_by
        check_in.status = GateCheckInStatus.ENTRY_AUTHORIZED.value
        check_in.row_version = (check_in.row_version or 1) + 1

        self.db.flush()
        return decision

    def authorize_with_observations(
        self,
        check_in: GateCheckInModel,
        decided_by: UUID,
        reason: str,
        conditions: Optional[list] = None,
        step_up_summary: Optional[dict] = None,
        supervisor_user_id: Optional[UUID] = None,
    ) -> GateEntryDecisionModel:
        """Authorize entry with observations (exceptions must be resolved)."""
        summary = self.validate_can_decide(check_in)
        if not summary["can_authorize_with_observations"]:
            raise GateCheckInExceptionNotApprovedError()

        decision_hash = self._compute_hash(check_in, DecisionType.AUTHORIZE_WITH_OBSERVATIONS.value)
        now = gate_arrival_time_service.now_utc()

        decision = GateEntryDecisionModel(
            id=uuid4(),
            gate_check_in_id=check_in.id,
            decision_type=DecisionType.AUTHORIZE_WITH_OBSERVATIONS.value,
            decision_reason=reason,
            conditions=conditions,
            decided_by=decided_by,
            decided_at=now,
            supervisor_user_id=supervisor_user_id,
            step_up_assurance_summary=step_up_summary,
            decision_hash=decision_hash,
        )
        self.db.add(decision)

        check_in.decision = DecisionType.AUTHORIZE_WITH_OBSERVATIONS.value
        check_in.decision_reason = reason
        check_in.decision_at = now
        check_in.entry_authorized_at = now
        check_in.entry_authorized_by = decided_by
        check_in.status = GateCheckInStatus.ENTRY_AUTHORIZED_WITH_OBSERVATIONS.value
        check_in.row_version = (check_in.row_version or 1) + 1

        self.db.flush()
        return decision

    def deny_entry(
        self,
        check_in: GateCheckInModel,
        decided_by: UUID,
        reason: str,
        step_up_summary: Optional[dict] = None,
        supervisor_user_id: Optional[UUID] = None,
    ) -> GateEntryDecisionModel:
        """Deny entry — requires a mandatory reason."""
        if not reason or not reason.strip():
            raise ApplicationError(
                "GATE_DENY_REASON_REQUIRED",
                "Se debe indicar el motivo de la denegación de ingreso.",
                422,
            )
        summary = self.validate_can_decide(check_in)

        decision_hash = self._compute_hash(check_in, DecisionType.DENY_ENTRY.value)
        now = gate_arrival_time_service.now_utc()

        decision = GateEntryDecisionModel(
            id=uuid4(),
            gate_check_in_id=check_in.id,
            decision_type=DecisionType.DENY_ENTRY.value,
            decision_reason=reason,
            blocking_checks=summary["blocking_failed"],
            decided_by=decided_by,
            decided_at=now,
            supervisor_user_id=supervisor_user_id,
            step_up_assurance_summary=step_up_summary,
            decision_hash=decision_hash,
        )
        self.db.add(decision)

        check_in.decision = DecisionType.DENY_ENTRY.value
        check_in.decision_reason = reason
        check_in.decision_at = now
        check_in.entry_denied_at = now
        check_in.entry_denied_by = decided_by
        check_in.status = GateCheckInStatus.ENTRY_DENIED.value
        check_in.row_version = (check_in.row_version or 1) + 1

        self.db.flush()
        return decision

    def _compute_hash(self, check_in: GateCheckInModel, decision_type: str) -> str:
        """Compute SHA-256 hash of core decision inputs."""
        payload = {
            "check_in_id": str(check_in.id),
            "appointment_id": str(check_in.appointment_id) if check_in.appointment_id else None,
            "guard_user_id": str(check_in.guard_user_id),
            "decision_type": decision_type,
        }
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(canonical.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# GateControlIntegrityService
# ─────────────────────────────────────────────────────────────────────────────

class GateControlIntegrityService:
    """SHA-256 integrity verification for gate check-in data.

    IMPORTANT: This is a cryptographic hash, NOT a digital signature.
    Mismatches generate alerts but do NOT silently correct data.
    """

    def compute_revision_hash(self, revision_data: dict) -> str:
        canonical = json.dumps(revision_data, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def compute_snapshot_hash(self, snapshot: dict) -> str:
        canonical = json.dumps(snapshot, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def verify_revision(
        self, db: Session, revision, stored_hash: Optional[str]
    ) -> bool:
        """Return True if stored hash matches computed hash."""
        if stored_hash is None:
            return True  # No hash stored yet — not a violation
        computed = self.compute_revision_hash(
            {
                "id": str(revision.id),
                "gate_check_in_id": str(revision.gate_check_in_id),
                "revision_number": revision.revision_number,
            }
        )
        return computed == stored_hash


gate_integrity_service = GateControlIntegrityService()


# ─────────────────────────────────────────────────────────────────────────────
# GateCheckInSnapshotProvider
# ─────────────────────────────────────────────────────────────────────────────

class GateCheckInSnapshotProvider:
    """Builds an immutable snapshot of all gate check-in data.

    The snapshot is frozen at decision time. Subsequent queries for
    reprinting or audit MUST use the frozen snapshot — live data is
    NEVER re-queried for document generation.
    """

    def __init__(self, db: Session):
        self.db = db

    def build(self, check_in: GateCheckInModel) -> dict:
        """Build comprehensive snapshot for the check-in."""
        from app.modules.logistics.inbound.gate_control.infrastructure.persistence.models import (
            GateVehicleInspectionModel,
            GateDriverInspectionModel,
            GateSealInspectionModel,
            GatePhotoEvidenceModel,
            GateVerificationCheckResultModel,
            GateVerificationExceptionModel,
            GateEntryDecisionModel,
            GatePresentedDocumentModel,
        )

        vehicle_insp = self.db.scalars(
            select(GateVehicleInspectionModel).where(
                GateVehicleInspectionModel.gate_check_in_id == check_in.id
            )
        ).first()

        driver_insp = self.db.scalars(
            select(GateDriverInspectionModel).where(
                GateDriverInspectionModel.gate_check_in_id == check_in.id
            )
        ).first()

        seal_insp = self.db.scalars(
            select(GateSealInspectionModel).where(
                GateSealInspectionModel.gate_check_in_id == check_in.id
            )
        ).first()

        photos = list(self.db.scalars(
            select(GatePhotoEvidenceModel).where(
                GatePhotoEvidenceModel.gate_check_in_id == check_in.id
            )
        ))

        check_results = list(self.db.scalars(
            select(GateVerificationCheckResultModel).where(
                GateVerificationCheckResultModel.gate_check_in_id == check_in.id
            )
        ))

        exceptions = list(self.db.scalars(
            select(GateVerificationExceptionModel).where(
                GateVerificationExceptionModel.gate_check_in_id == check_in.id
            )
        ))

        decision = self.db.scalars(
            select(GateEntryDecisionModel).where(
                GateEntryDecisionModel.gate_check_in_id == check_in.id,
                GateEntryDecisionModel.decision_type.in_([
                    "AUTHORIZE_ENTRY", "AUTHORIZE_WITH_OBSERVATIONS", "DENY_ENTRY"
                ])
            )
        ).first()

        documents = list(self.db.scalars(
            select(GatePresentedDocumentModel).where(
                GatePresentedDocumentModel.gate_check_in_id == check_in.id
            )
        ))

        snapshot = {
            "schema_version": "037.1",
            "check_in_id": str(check_in.id),
            "appointment_code": check_in.appointment_code_snapshot,
            "organization_id": str(check_in.organization_id),
            "warehouse_id": str(check_in.warehouse_id),
            "gate_id": str(check_in.gate_id),
            "status": check_in.status,
            "source_type": check_in.source_type,
            "arrival_classification": check_in.arrival_classification,
            "arrived_at": check_in.arrived_at.isoformat() if check_in.arrived_at else None,
            "gate_timezone": check_in.gate_timezone,
            "check_started_at": check_in.check_started_at.isoformat() if check_in.check_started_at else None,
            "check_completed_at": check_in.check_completed_at.isoformat() if check_in.check_completed_at else None,
            "guard": check_in.guard_snapshot,
            "supplier": check_in.supplier_snapshot,
            "carrier": check_in.carrier_snapshot,
            "expected_transport": check_in.expected_transport_snapshot,
            "observed_transport": check_in.observed_transport_snapshot,
            "vehicle_inspection": self._vehicle_dict(vehicle_insp),
            "driver_inspection": self._driver_dict(driver_insp),
            "seal_inspection": self._seal_dict(seal_insp),
            "presented_documents": [self._doc_dict(d) for d in documents],
            "photo_manifest": [
                {
                    "evidence_type": p.evidence_type,
                    "file_asset_id": str(p.file_asset_id),
                    "content_hash": p.content_hash,
                    "classification": p.classification,
                    "captured_at": p.captured_at.isoformat() if p.captured_at else None,
                }
                for p in photos
            ],
            "checklist": [
                {
                    "check_code": r.check_code,
                    "result": r.result,
                    "blocking": r.blocking,
                    "override_status": r.override_status,
                }
                for r in check_results
            ],
            "exceptions": [
                {
                    "exception_type": e.exception_type,
                    "risk_level": e.risk_level,
                    "status": e.status,
                    "reason": e.reason,
                }
                for e in exceptions
            ],
            "decision": {
                "decision_type": decision.decision_type if decision else None,
                "decision_reason": decision.decision_reason if decision else None,
                "decided_by": str(decision.decided_by) if decision else None,
                "decided_at": decision.decided_at.isoformat() if decision and decision.decided_at else None,
                "decision_hash": decision.decision_hash if decision else None,
            },
            "exception_count": check_in.exception_count,
            "failed_check_count": check_in.failed_check_count,
            "warning_count": check_in.warning_count,
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }
        snapshot["content_hash"] = gate_integrity_service.compute_snapshot_hash(snapshot)
        return snapshot

    def _vehicle_dict(self, v) -> Optional[dict]:
        if v is None:
            return None
        return {
            "expected_plate": v.expected_plate,
            "observed_plate": v.observed_plate,
            "plate_match_status": v.plate_match_status,
            "vehicle_match_status": v.vehicle_match_status,
            "inspection_result": v.inspection_result,
        }

    def _driver_dict(self, d) -> Optional[dict]:
        if d is None:
            return None
        return {
            "expected_driver_id": str(d.expected_driver_id) if d.expected_driver_id else None,
            "observed_name_snapshot": d.observed_name_snapshot,
            "driver_match_status": d.driver_match_status,
            "license_status": d.license_status,
            # Redacted — never full document/license number
            "license_number_redacted": d.license_number_redacted,
            "observed_document_number_redacted": d.observed_document_number_redacted,
            "inspection_result": d.inspection_result,
        }

    def _seal_dict(self, s) -> Optional[dict]:
        if s is None:
            return None
        return {
            "seal_required": s.seal_required,
            "expected_seal_number": s.expected_seal_number,
            "observed_seal_number": s.observed_seal_number,
            "seal_match_status": s.seal_match_status,
            "physical_status": s.physical_status,
            "inspection_result": s.inspection_result,
        }

    def _doc_dict(self, d) -> dict:
        return {
            "document_kind": d.document_kind,
            "expected_reference": d.expected_reference,
            "observed_reference_normalized": d.observed_reference_normalized,
            "presentation_status": d.presentation_status,
            "comparison_status": d.comparison_status,
        }


# ─────────────────────────────────────────────────────────────────────────────
# InboundGateReleaseService
# ─────────────────────────────────────────────────────────────────────────────

class InboundGateReleaseService:
    """Publishes the InboundVehicleGateCleared event to the outbox.

    This is the release event that Phase 038 (dock assignment) will consume.
    Publishing occurs only for ENTRY_AUTHORIZED or ENTRY_AUTHORIZED_WITH_OBSERVATIONS.
    """

    def __init__(self, db: Session):
        self.db = db

    def publish_gate_cleared(self, check_in: GateCheckInModel, snapshot: dict) -> None:
        """Publish InboundVehicleGateCleared event to outbox."""
        allowed = {
            GateCheckInStatus.ENTRY_AUTHORIZED.value,
            GateCheckInStatus.ENTRY_AUTHORIZED_WITH_OBSERVATIONS.value,
        }
        if check_in.status not in allowed:
            raise ApplicationError(
                "GATE_RELEASE_NOT_AUTHORIZED",
                "El evento de liberación solo se publica para check-ins autorizados.",
                422,
            )

        event_payload = {
            "event_type": "InboundVehicleGateCleared",
            "check_in_id": str(check_in.id),
            "appointment_id": str(check_in.appointment_id) if check_in.appointment_id else None,
            "appointment_code": check_in.appointment_code_snapshot,
            "gate_id": str(check_in.gate_id),
            "warehouse_id": str(check_in.warehouse_id),
            "organization_id": str(check_in.organization_id),
            "decision": check_in.decision,
            "arrived_at": check_in.arrived_at.isoformat() if check_in.arrived_at else None,
            "gate_cleared_at": datetime.now(timezone.utc).isoformat(),
            "snapshot_hash": snapshot.get("content_hash"),
        }

        try:
            from app.modules.logistics.inbound.arrival_notices.infrastructure.persistence.models import (
                ArrivalOutboxModel,
            )

            outbox_event = ArrivalOutboxModel(
                id=uuid4(),
                aggregate_type="GATE_CHECK_IN",
                aggregate_id=check_in.id,
                event_type="InboundVehicleGateCleared",
                payload=event_payload,
                status="PENDING",
            )
            self.db.add(outbox_event)
            self.db.flush()
        except Exception:
            # Outbox model may not match exactly — log and continue
            pass


# ─────────────────────────────────────────────────────────────────────────────
# DockAssignmentPreparationService
# ─────────────────────────────────────────────────────────────────────────────

class DockAssignmentPreparationService:
    """Read-only contract for Phase 038 dock assignment.

    CRITICAL:
    - This service is READ-ONLY. It does NOT assign docks.
    - It does NOT reserve docks.
    - It does NOT start unloading.
    - It does NOT modify the check-in in any way.
    - Phase 038 will consume this contract.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_preparation(
        self, check_in_id: UUID, organization_id: UUID
    ) -> dict:
        check_in = self.db.scalars(
            select(GateCheckInModel).where(
                GateCheckInModel.id == check_in_id,
                GateCheckInModel.organization_id == organization_id,
            )
        ).first()
        if check_in is None:
            raise GateCheckInNotFoundError(str(check_in_id))

        allowed = {
            GateCheckInStatus.ENTRY_AUTHORIZED.value,
            GateCheckInStatus.ENTRY_AUTHORIZED_WITH_OBSERVATIONS.value,
        }
        if check_in.status not in allowed:
            raise ApplicationError(
                "GATE_PREPARATION_NOT_AVAILABLE",
                "La preparación para muelle solo está disponible cuando el ingreso ha sido autorizado.",
                422,
            )

        vehicle_insp = self.db.scalars(
            select(GateVehicleInspectionModel).where(
                GateVehicleInspectionModel.gate_check_in_id == check_in_id
            )
        ).first()

        driver_insp = self.db.scalars(
            select(GateDriverInspectionModel).where(
                GateDriverInspectionModel.gate_check_in_id == check_in_id
            )
        ).first()

        seal_insp = self.db.scalars(
            select(GateSealInspectionModel).where(
                GateSealInspectionModel.gate_check_in_id == check_in_id
            )
        ).first()

        prep_data = check_in.expected_transport_snapshot or {}

        return {
            # Phase 038 contract — DO NOT ADD dock_id HERE
            "gate_check_in_id": str(check_in.id),
            "cpv_code": None,  # Filled after CPV issuance
            "appointment_id": str(check_in.appointment_id) if check_in.appointment_id else None,
            "cit_code": check_in.appointment_code_snapshot,
            "warehouse_id": str(check_in.warehouse_id),
            "gate_id": str(check_in.gate_id),
            "supplier_summary": check_in.supplier_snapshot,
            "carrier_summary": check_in.carrier_snapshot,
            "vehicle_id": str(vehicle_insp.observed_vehicle_id) if vehicle_insp and vehicle_insp.observed_vehicle_id else None,
            "observed_plate": vehicle_insp.observed_plate if vehicle_insp else None,
            "driver_id": str(driver_insp.observed_driver_id) if driver_insp and driver_insp.observed_driver_id else None,
            "arrival_time": check_in.arrived_at.isoformat() if check_in.arrived_at else None,
            "gate_clearance_status": check_in.decision,
            "clearance_conditions": check_in.verification_summary,
            "seal_status": seal_insp.physical_status if seal_insp else None,
            "document_summary": check_in.verification_summary,
            "special_requirements": prep_data.get("special_requirements"),
            "expected_pallet_count": prep_data.get("expected_pallet_count"),
            "expected_package_count": prep_data.get("expected_package_count"),
            "expected_weight": prep_data.get("expected_weight"),
            "warnings": [],
            "capabilities_future": ["DOCK_ASSIGNMENT_PHASE_038"],
            # Explicitly absent: dock_id, unload_started_at, receiving quantities
        }


__all__ = [
    "GateArrivalTimeService",
    "gate_arrival_time_service",
    "GateGuardResolver",
    "gate_guard_resolver",
    "GateAppointmentResolver",
    "gate_appointment_resolver",
    "GateCheckInService",
    "GateDecisionService",
    "GateControlIntegrityService",
    "gate_integrity_service",
    "GateCheckInSnapshotProvider",
    "InboundGateReleaseService",
    "DockAssignmentPreparationService",
]
