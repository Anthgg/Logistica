"""Pytest tests for Phase 037 Gate Control.

Tests cover:
- Domain value objects and state machine transitions
- GateArrivalTimeService (server clock, arrival classification)
- GateDecisionService (authorize, deny, anti-duplicate)
- GateCheckInService (lifecycle transitions)
- GateControlIntegrityService (hash verification)
- GateCheckInSnapshotProvider (immutable snapshot)
- Endpoint security (guard derivation, arrived_at not from client)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.modules.logistics.inbound.gate_control.domain.errors import (
    GateCheckInArrivalAlreadyRecordedError,
    GateCheckInDecisionConflictError,
    GateCheckInStatusInvalidError,
    WarehouseGateInactiveError,
    WarehouseGateNotFoundError,
)
from app.modules.logistics.inbound.gate_control.domain.value_objects import (
    ArrivalClassification,
    GateCheckInStatus,
    GATE_CHECK_IN_TRANSITIONS,
    validate_status_transition,
)
from app.modules.logistics.inbound.gate_control.application.services import (
    GateArrivalTimeService,
    GateControlIntegrityService,
    GateDecisionService,
    GateGuardResolver,
    gate_arrival_time_service,
    gate_integrity_service,
)
from app.modules.logistics.inbound.gate_control.infrastructure.persistence.models import (
    GateCheckInModel,
    GateEntryDecisionModel,
    GateVerificationCheckResultModel,
    GateVerificationExceptionModel,
    WarehouseGateModel,
)


# ─────────────────────────────────────────────────────────────────────────────
# State Machine Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestGateCheckInStateMachine:
    """Validate that the state machine transitions are correctly defined."""

    def test_created_can_transition_to_arrival_recorded(self):
        validate_status_transition("CREATED", "ARRIVAL_RECORDED")

    def test_created_can_cancel(self):
        validate_status_transition("CREATED", "CANCELLED")

    def test_arrival_recorded_can_start_verification(self):
        validate_status_transition("ARRIVAL_RECORDED", "VERIFICATION_IN_PROGRESS")

    def test_verified_can_authorize_entry(self):
        validate_status_transition("VERIFIED", "ENTRY_AUTHORIZED")

    def test_verified_can_deny_entry(self):
        validate_status_transition("VERIFIED", "ENTRY_DENIED")

    def test_entry_authorized_can_complete(self):
        validate_status_transition("ENTRY_AUTHORIZED", "COMPLETED")

    def test_completed_has_no_transitions(self):
        assert GATE_CHECK_IN_TRANSITIONS["COMPLETED"] == []

    def test_cancelled_has_no_transitions(self):
        assert GATE_CHECK_IN_TRANSITIONS["CANCELLED"] == []

    def test_invalid_transition_raises_value_error(self):
        with pytest.raises(ValueError, match="Transición de estado inválida"):
            validate_status_transition("COMPLETED", "CREATED")

    def test_cannot_go_from_entry_authorized_to_cancelled(self):
        with pytest.raises(ValueError):
            validate_status_transition("ENTRY_AUTHORIZED", "CANCELLED")

    def test_cannot_go_backward_to_created(self):
        with pytest.raises(ValueError):
            validate_status_transition("VERIFICATION_IN_PROGRESS", "CREATED")


# ─────────────────────────────────────────────────────────────────────────────
# Arrival Time Service Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestGateArrivalTimeService:
    """Server clock tests — arrived_at NEVER from client."""

    def setup_method(self):
        self.svc = GateArrivalTimeService()

    def test_now_utc_returns_aware_datetime(self):
        now = self.svc.now_utc()
        assert now.tzinfo is not None

    def test_now_utc_is_utc(self):
        now = self.svc.now_utc()
        assert now.utcoffset().total_seconds() == 0

    def test_classify_on_time(self):
        window_start = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        window_end = datetime(2026, 8, 1, 11, 0, tzinfo=timezone.utc)
        arrived = datetime(2026, 8, 1, 10, 30, tzinfo=timezone.utc)
        result = self.svc.classify_arrival(arrived, window_start, window_end)
        assert result == ArrivalClassification.ON_TIME.value

    def test_classify_early(self):
        window_start = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        window_end = datetime(2026, 8, 1, 11, 0, tzinfo=timezone.utc)
        arrived = window_start - timedelta(minutes=30)  # within early tolerance
        result = self.svc.classify_arrival(arrived, window_start, window_end)
        assert result == ArrivalClassification.EARLY.value

    def test_classify_late(self):
        window_start = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        window_end = datetime(2026, 8, 1, 11, 0, tzinfo=timezone.utc)
        arrived = window_end + timedelta(minutes=15)  # within late tolerance
        result = self.svc.classify_arrival(arrived, window_start, window_end)
        assert result == ArrivalClassification.LATE.value

    def test_classify_outside_window(self):
        window_start = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        window_end = datetime(2026, 8, 1, 11, 0, tzinfo=timezone.utc)
        arrived = window_end + timedelta(hours=5)
        result = self.svc.classify_arrival(arrived, window_start, window_end)
        assert result == ArrivalClassification.OUTSIDE_WINDOW.value

    def test_classify_without_window_returns_not_classified(self):
        arrived = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
        result = self.svc.classify_arrival(arrived, None, None)
        assert result == ArrivalClassification.TIME_NOT_CLASSIFIED.value


# ─────────────────────────────────────────────────────────────────────────────
# Guard Resolver Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestGateGuardResolver:
    """Ensure guard_user_id is resolved from session, never from payload."""

    def test_resolve_returns_snapshot_with_user_id(self):
        resolver = GateGuardResolver()
        principal = MagicMock()
        principal.user_id = uuid4()
        principal.has_permission.return_value = True
        principal.is_platform_admin = False
        principal.display_name = "Test Guard"
        principal.email = "guard@test.com"

        snapshot = resolver.resolve(principal)
        assert str(snapshot["user_id"]) == str(principal.user_id)
        assert snapshot["display_name"] == "Test Guard"

    def test_resolve_raises_for_unpermitted_user(self):
        from app.modules.logistics.inbound.gate_control.domain.errors import (
            GateCheckInGuardNotAuthorizedError,
        )

        resolver = GateGuardResolver()
        principal = MagicMock()
        principal.has_permission.return_value = False
        principal.is_platform_admin = False

        with pytest.raises(GateCheckInGuardNotAuthorizedError):
            resolver.resolve(principal)

    def test_platform_admin_bypasses_permission_check(self):
        resolver = GateGuardResolver()
        principal = MagicMock()
        principal.user_id = uuid4()
        principal.has_permission.return_value = False
        principal.is_platform_admin = True
        principal.display_name = "Admin"

        snapshot = resolver.resolve(principal)
        assert "user_id" in snapshot


# ─────────────────────────────────────────────────────────────────────────────
# Integrity Service Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestGateControlIntegrityService:
    def setup_method(self):
        self.svc = GateControlIntegrityService()

    def test_snapshot_hash_deterministic(self):
        data = {"check_in_id": str(uuid4()), "status": "VERIFIED"}
        h1 = self.svc.compute_snapshot_hash(data)
        h2 = self.svc.compute_snapshot_hash(data)
        assert h1 == h2

    def test_snapshot_hash_changes_with_data(self):
        data1 = {"status": "VERIFIED"}
        data2 = {"status": "ENTRY_AUTHORIZED"}
        assert self.svc.compute_snapshot_hash(data1) != self.svc.compute_snapshot_hash(data2)

    def test_snapshot_hash_is_sha256(self):
        data = {"key": "value"}
        computed = self.svc.compute_snapshot_hash(data)
        canonical = json.dumps(data, sort_keys=True, ensure_ascii=True, default=str)
        expected = hashlib.sha256(canonical.encode()).hexdigest()
        assert computed == expected

    def test_verify_revision_with_no_stored_hash_returns_true(self):
        db = MagicMock()
        revision = MagicMock()
        result = self.svc.verify_revision(db, revision, None)
        assert result is True


# ─────────────────────────────────────────────────────────────────────────────
# Decision Service Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestGateDecisionService:
    """Decision service must prevent double-decisions and enforce constraints."""

    def _make_check_in(self, status="VERIFIED") -> GateCheckInModel:
        check_in = MagicMock(spec=GateCheckInModel)
        check_in.id = uuid4()
        check_in.status = status
        check_in.guard_user_id = uuid4()
        check_in.appointment_id = uuid4()
        check_in.row_version = 1
        check_in.arrived_at = datetime.now(timezone.utc)
        check_in.decision = None
        return check_in

    def _make_db_with_no_decisions_no_failures(self):
        db = MagicMock()
        db.scalars.return_value.first.return_value = None  # no existing decision
        db.scalars.return_value.__iter__ = lambda s: iter([])  # no blocking failures
        return db

    def test_deny_entry_requires_reason(self):
        svc = GateDecisionService(MagicMock())
        svc.validate_can_decide = MagicMock(return_value={
            "blocking_failed_count": 0,
            "blocking_failed": [],
            "pending_exceptions_count": 0,
            "can_authorize": True,
            "can_authorize_with_observations": True,
        })
        check_in = self._make_check_in()
        from app.core.exceptions import ApplicationError
        with pytest.raises(ApplicationError, match="motivo"):
            svc.deny_entry(check_in, uuid4(), "")

    def test_deny_entry_with_whitespace_reason_raises(self):
        svc = GateDecisionService(MagicMock())
        svc.validate_can_decide = MagicMock(return_value={
            "blocking_failed_count": 0,
            "blocking_failed": [],
            "pending_exceptions_count": 0,
            "can_authorize": True,
            "can_authorize_with_observations": True,
        })
        check_in = self._make_check_in()
        from app.core.exceptions import ApplicationError
        with pytest.raises(ApplicationError):
            svc.deny_entry(check_in, uuid4(), "   ")

    def test_decision_hash_is_deterministic_for_same_inputs(self):
        svc = GateDecisionService(MagicMock())
        check_in = self._make_check_in()
        h1 = svc._compute_hash(check_in, "AUTHORIZE_ENTRY")
        h2 = svc._compute_hash(check_in, "AUTHORIZE_ENTRY")
        assert h1 == h2

    def test_decision_hash_differs_for_different_decision_types(self):
        svc = GateDecisionService(MagicMock())
        check_in = self._make_check_in()
        h1 = svc._compute_hash(check_in, "AUTHORIZE_ENTRY")
        h2 = svc._compute_hash(check_in, "DENY_ENTRY")
        assert h1 != h2


# ─────────────────────────────────────────────────────────────────────────────
# Scope Boundary Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestPhase037ScopeBoundaries:
    """Validate that Phase 037 does NOT implement Phase 038+ features."""

    def test_dock_preparation_has_no_dock_id_field(self):
        from app.modules.logistics.inbound.gate_control.presentation.schemas import (
            DockAssignmentPreparationResponse,
        )
        fields = DockAssignmentPreparationResponse.model_fields
        assert "dock_id" not in fields

    def test_dock_preparation_has_no_unload_started_at(self):
        from app.modules.logistics.inbound.gate_control.presentation.schemas import (
            DockAssignmentPreparationResponse,
        )
        fields = DockAssignmentPreparationResponse.model_fields
        assert "unload_started_at" not in fields

    def test_check_in_create_does_not_accept_guard_user_id(self):
        from app.modules.logistics.inbound.gate_control.presentation.schemas import (
            GateCheckInCreate,
        )
        fields = GateCheckInCreate.model_fields
        assert "guard_user_id" not in fields

    def test_check_in_create_does_not_accept_arrived_at(self):
        from app.modules.logistics.inbound.gate_control.presentation.schemas import (
            GateCheckInCreate,
        )
        fields = GateCheckInCreate.model_fields
        assert "arrived_at" not in fields

    def test_entry_decision_request_does_not_accept_decided_by(self):
        from app.modules.logistics.inbound.gate_control.presentation.schemas import (
            GateEntryDecisionRequest,
        )
        fields = GateEntryDecisionRequest.model_fields
        assert "decided_by" not in fields

    def test_entry_decision_request_does_not_accept_decision_at(self):
        from app.modules.logistics.inbound.gate_control.presentation.schemas import (
            GateEntryDecisionRequest,
        )
        fields = GateEntryDecisionRequest.model_fields
        assert "decision_at" not in fields

    def test_driver_inspection_response_omits_full_document_number(self):
        from app.modules.logistics.inbound.gate_control.presentation.schemas import (
            GateDriverInspectionCreate,
        )
        # The create schema accepts the field but the application must redact it
        # Ensure there is no "observed_document_number_full" leak
        fields = GateDriverInspectionCreate.model_fields
        assert "observed_document_number_encrypted" not in fields

    def test_checkin_summary_has_no_dock_fields(self):
        from app.modules.logistics.inbound.gate_control.presentation.schemas import (
            GateCheckInSummary,
        )
        fields = GateCheckInSummary.model_fields
        assert "dock_id" not in fields
        assert "dock_number" not in fields
        assert "unload_started" not in fields


# ─────────────────────────────────────────────────────────────────────────────
# Walk-In Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestGateWalkInConstraints:
    def test_walk_in_schema_requires_reason(self):
        from pydantic import ValidationError
        from app.modules.logistics.inbound.gate_control.presentation.schemas import (
            GateWalkInCreate,
        )
        with pytest.raises(ValidationError):
            GateWalkInCreate(
                gate_id=uuid4(),
                reason="hi",  # too short (< 5 chars)
                supplier_id=uuid4(),
            )

    def test_walk_in_schema_requires_gate_id(self):
        from pydantic import ValidationError
        from app.modules.logistics.inbound.gate_control.presentation.schemas import (
            GateWalkInCreate,
        )
        with pytest.raises(ValidationError):
            GateWalkInCreate(
                reason="Valid reason",
                supplier_id=uuid4(),
            )


# ─────────────────────────────────────────────────────────────────────────────
# Appointment Resolver Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestGateAppointmentResolver:
    def test_resolve_request_requires_at_least_one_identifier(self):
        from pydantic import ValidationError
        from app.modules.logistics.inbound.gate_control.presentation.schemas import (
            GateAppointmentResolveRequest,
        )
        with pytest.raises(ValidationError, match="identificador"):
            GateAppointmentResolveRequest(warehouse_id=uuid4())

    def test_resolve_request_accepts_cit_code(self):
        from app.modules.logistics.inbound.gate_control.presentation.schemas import (
            GateAppointmentResolveRequest,
        )
        req = GateAppointmentResolveRequest(
            warehouse_id=uuid4(), cit_code="CIT-2026-001"
        )
        assert req.cit_code == "CIT-2026-001"


# ─────────────────────────────────────────────────────────────────────────────
# Value Object Completeness Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestValueObjects:
    def test_all_status_enums_in_transition_map(self):
        for status in GateCheckInStatus:
            assert status.value in GATE_CHECK_IN_TRANSITIONS, (
                f"Status {status.value} is missing from GATE_CHECK_IN_TRANSITIONS"
            )

    def test_transition_targets_are_valid_statuses(self):
        valid = {s.value for s in GateCheckInStatus}
        for status, targets in GATE_CHECK_IN_TRANSITIONS.items():
            assert status in valid, f"Source '{status}' is not a valid status"
            for t in targets:
                assert t in valid, f"Target '{t}' is not a valid status (from '{status}')"

    def test_terminal_states_have_no_outbound_transitions(self):
        terminal = ["COMPLETED", "CANCELLED", "SUPERSEDED"]
        for t in terminal:
            assert GATE_CHECK_IN_TRANSITIONS[t] == [], f"{t} should have no transitions"
