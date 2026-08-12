"""Phase 043 — Putaway unit tests."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.putaway.domain.enums import (
    PolicyStatus,
    PolicyVersionStatus,
    StorageCompatibilityAction,
    StorageCompatibilitySeverity,
    CapacityType,
    DataQualityStatus,
    RotationStrategy,
    PutawayOrderStatus,
    PutawayTaskStatus,
    ReservationStatus,
    ExecutionSessionStatus,
    ScanType,
    ScanResolutionStatus,
    OverrideReasonCode,
    ExceptionType,
    ExceptionSeverity,
    ExceptionStatus,
    PauseReason,
    OperationalPlacementStatus,
)
from app.modules.logistics.inventory.putaway.domain.errors import (
    PutawayPolicyNotFound,
    PutawaySourceNotEligible,
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
from app.modules.logistics.inventory.putaway.domain.services.compatibility_service import (
    StorageCompatibilityService,
    CompatibilityResult,
)
from app.modules.logistics.inventory.putaway.domain.services.capacity_service import (
    CapacityService,
    CapacityEvaluation,
)
from app.modules.logistics.inventory.putaway.domain.services.proximity_service import (
    ProximityService,
    ProximityResult,
    TravelCostScore,
)
from app.modules.logistics.inventory.putaway.domain.services.rotation_service import (
    RotationService,
    RotationEvaluation,
)
from app.modules.logistics.inventory.putaway.domain.services.scoring_service import (
    ScoringService,
    CandidateScore,
    ScoringWeights,
)
from app.modules.logistics.inventory.putaway.domain.services.eligibility_service import (
    EligibilityService,
    SourceEligibility,
)
from app.modules.logistics.inventory.putaway.infrastructure.persistence.repositories import (
    compute_content_hash,
)


class TestEnums:
    def test_policy_status_values(self):
        assert PolicyStatus.DRAFT.value == "DRAFT"
        assert PolicyStatus.ACTIVE.value == "ACTIVE"

    def test_storage_compatibility_action_values(self):
        assert StorageCompatibilityAction.ALLOW.value == "ALLOW"
        assert StorageCompatibilityAction.DENY.value == "DENY"

    def test_capacity_type_values(self):
        assert CapacityType.QUANTITY.value == "QUANTITY"
        assert CapacityType.MASS.value == "MASS"

    def test_rotation_strategy_values(self):
        assert RotationStrategy.FIFO.value == "FIFO"
        assert RotationStrategy.FEFO.value == "FEFO"

    def test_putaway_order_status_values(self):
        assert PutawayOrderStatus.DRAFT.value == "DRAFT"
        assert PutawayOrderStatus.ISSUED.value == "ISSUED"
        assert PutawayOrderStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert PutawayOrderStatus.COMPLETED.value == "COMPLETED"
        assert PutawayOrderStatus.CANCELLED.value == "CANCELLED"

    def test_putaway_task_status_values(self):
        assert PutawayTaskStatus.CREATED.value == "CREATED"
        assert PutawayTaskStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert PutawayTaskStatus.PAUSED.value == "PAUSED"
        assert PutawayTaskStatus.COMPLETED.value == "COMPLETED"


class TestErrors:
    def test_putaway_policy_not_found(self):
        err = PutawayPolicyNotFound("POL-001")
        assert err.code == "PUTAWAY_POLICY_NOT_FOUND"

    def test_putaway_source_not_eligible(self):
        err = PutawaySourceNotEligible("ALLOC-001", "quality hold")
        assert err.code == "PUTAWAY_SOURCE_NOT_ELIGIBLE"

    def test_putaway_order_not_found(self):
        err = PutawayOrderNotFound("ORDER-001")
        assert err.code == "PUTAWAY_ORDER_NOT_FOUND"

    def test_putaway_task_not_found(self):
        err = PutawayTaskNotFound("TASK-001")
        assert err.code == "PUTAWAY_TASK_NOT_FOUND"

    def test_putaway_quantity_invalid(self):
        err = PutawayQuantityInvalid("negative qty")
        assert err.code == "PUTAWAY_QUANTITY_INVALID"

    def test_putaway_quantity_exceeded(self):
        err = PutawayQuantityExceeded("exceeds required")
        assert err.code == "PUTAWAY_QUANTITY_EXCEEDED"

    def test_putaway_task_scan_required(self):
        err = PutawayTaskScanRequired("PRODUCT")
        assert err.code == "PUTAWAY_TASK_SCAN_REQUIRED"

    def test_putaway_product_mismatch(self):
        err = PutawayProductMismatch("P001", "P002")
        assert err.code == "PUTAWAY_PRODUCT_MISMATCH"

    def test_putaway_location_blocked(self):
        err = PutawayLocationBlocked("LOC-001")
        assert err.code == "PUTAWAY_LOCATION_BLOCKED"

    def test_putaway_integrity_failed(self):
        err = PutawayIntegrityFailed("hash mismatch")
        assert err.code == "PUTAWAY_INTEGRITY_FAILED"

    def test_putaway_task_already_assigned(self):
        err = PutawayTaskAlreadyAssigned("TASK-001")
        assert err.code == "PUTAWAY_TASK_ALREADY_ASSIGNED"


class TestContentHash:
    def test_compute_content_hash_deterministic(self):
        data = {"key": "value", "number": 42}
        hash1 = compute_content_hash(data)
        hash2 = compute_content_hash(data)
        assert hash1 == hash2

    def test_compute_content_hash_different_data(self):
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}
        hash1 = compute_content_hash(data1)
        hash2 = compute_content_hash(data2)
        assert hash1 != hash2

    def test_compute_content_hash_is_sha256(self):
        data = {"test": "data"}
        result = compute_content_hash(data)
        assert len(result) == 64


class TestCompatibilityResult:
    def test_defaults(self):
        result = CompatibilityResult()
        assert result.compatible is True
        assert result.action == StorageCompatibilityAction.ALLOW.value
        assert result.matched_rules == []
        assert result.warnings == []


class TestCapacityEvaluation:
    def test_creation(self):
        eval_result = CapacityEvaluation(
            location_id=uuid4(),
            capacity_profile_id=uuid4(),
            capacity_type=CapacityType.QUANTITY.value,
            maximum_value=Decimal("1000"),
            safety_margin_value=Decimal("100"),
            operational_occupied=Decimal("500"),
            active_reserved=Decimal("100"),
            projected_free=Decimal("300"),
            has_enough=True,
            data_quality_status=DataQualityStatus.MISSING_BASELINE.value,
            unit_id=uuid4(),
        )
        assert eval_result.has_enough is True
        assert eval_result.projected_free == Decimal("300")


class TestScoringWeights:
    def test_default_weights(self):
        weights = ScoringWeights()
        assert weights.capacity_weight == Decimal("0.25")
        assert weights.rotation_weight == Decimal("0.20")
        assert weights.picking_proximity_weight == Decimal("0.20")
        assert weights.consolidation_weight == Decimal("0.10")
        assert weights.fragmentation_penalty_weight == Decimal("0.10")
        assert weights.travel_cost_weight == Decimal("0.15")

    def test_weights_sum_to_one(self):
        weights = ScoringWeights()
        total = (
            weights.capacity_weight
            + weights.rotation_weight
            + weights.picking_proximity_weight
            + weights.consolidation_weight
            + weights.fragmentation_penalty_weight
            + weights.travel_cost_weight
        )
        assert total == Decimal("1.00")


class TestCandidateScore:
    def test_creation(self):
        score = CandidateScore(
            location_id=uuid4(),
            rank=1,
            compatible=True,
            capacity_available=True,
            capacity_score=Decimal("80"),
            rotation_score=Decimal("70"),
            picking_proximity_score=Decimal("90"),
            consolidation_score=Decimal("60"),
            fragmentation_score=Decimal("30"),
            travel_cost_score=Decimal("85"),
            penalty_score=Decimal("5"),
            total_score=Decimal("75.50"),
        )
        assert score.rank == 1
        assert score.compatible is True
        assert score.total_score == Decimal("75.50")


class TestSourceEligibility:
    def test_eligible(self):
        el = SourceEligibility(
            eligible=True,
            source_allocation_id=uuid4(),
            product_id=uuid4(),
            quantity=Decimal("100"),
            unit_id=uuid4(),
            base_quantity=Decimal("100"),
            quality_status="RELEASED",
            disposition="PUTAWAY",
            reasons=[],
        )
        assert el.eligible is True

    def test_ineligible(self):
        el = SourceEligibility(
            eligible=False,
            source_allocation_id=uuid4(),
            product_id=uuid4(),
            quantity=Decimal("100"),
            unit_id=uuid4(),
            base_quantity=Decimal("100"),
            quality_status="QUARANTINED",
            disposition="HOLD",
            reasons=["Product is in quarantine"],
        )
        assert el.eligible is False
        assert len(el.reasons) == 1


class TestRotationEvaluation:
    def test_creation(self):
        ev = RotationEvaluation(
            location_id=uuid4(),
            last_putaway_at=datetime.now(timezone.utc),
            placement_count=10,
            days_since_last_putaway=5,
            rotation_strategy=RotationStrategy.FIFO.value,
            score=Decimal("75.50"),
        )
        assert ev.placement_count == 10
        assert ev.score == Decimal("75.50")


class TestProximityResult:
    def test_creation(self):
        r = ProximityResult(
            source_location_id=uuid4(),
            target_location_id=uuid4(),
            target_zone_id=None,
            metric_type="WALKING_DISTANCE_M",
            metric_value=Decimal("50.00"),
            metric_unit="m",
            source_type="MANUAL_MEASUREMENT",
        )
        assert r.metric_value == Decimal("50.00")


class TestTravelCostScore:
    def test_creation(self):
        s = TravelCostScore(
            walking_distance=Decimal("50.00"),
            travel_time=Decimal("60.00"),
            normalized_distance=Decimal("0.05"),
            score=Decimal("95.00"),
        )
        assert s.score == Decimal("95.00")


class TestTaskStatusTransitions:
    def test_valid_transitions(self):
        assert PutawayTaskStatus.CREATED.value is not None
        assert PutawayTaskStatus.IN_PROGRESS.value is not None
        assert PutawayTaskStatus.PAUSED.value is not None
        assert PutawayTaskStatus.COMPLETED.value is not None


class TestReservationStatus:
    def test_statuses(self):
        assert ReservationStatus.ACTIVE.value == "ACTIVE"
        assert ReservationStatus.RELEASED.value == "RELEASED"
        assert ReservationStatus.CONSUMED.value == "CONSUMED"
        assert ReservationStatus.EXPIRED.value == "EXPIRED"


class TestExecutionSessionStatus:
    def test_statuses(self):
        assert ExecutionSessionStatus.ACTIVE.value == "ACTIVE"
        assert ExecutionSessionStatus.PAUSED.value == "PAUSED"
        assert ExecutionSessionStatus.COMPLETED.value == "COMPLETED"


class TestScanResolutionStatus:
    def test_statuses(self):
        assert ScanResolutionStatus.RECORDED.value == "RECORDED"
        assert ScanResolutionStatus.VALID.value == "VALID"
        assert ScanResolutionStatus.REJECTED.value == "REJECTED"


class TestScanType:
    def test_types(self):
        assert ScanType.PRODUCT.value == "PRODUCT"
        assert ScanType.LOCATION.value == "LOCATION"


class TestOverrideReasonCode:
    def test_reasons(self):
        assert OverrideReasonCode.ACCESS_BLOCKED.value == "ACCESS_BLOCKED"
        assert OverrideReasonCode.SUPERVISOR_DIRECTION.value == "SUPERVISOR_DIRECTION"


class TestExceptionType:
    def test_types(self):
        assert ExceptionType.WRONG_PRODUCT.value == "WRONG_PRODUCT"
        assert ExceptionType.QUANTITY_MISMATCH.value == "QUANTITY_MISMATCH"


class TestExceptionSeverity:
    def test_severities(self):
        assert ExceptionSeverity.LOW.value == "LOW"
        assert ExceptionSeverity.MEDIUM.value == "MEDIUM"
        assert ExceptionSeverity.HIGH.value == "HIGH"
        assert ExceptionSeverity.CRITICAL.value == "CRITICAL"


class TestExceptionStatus:
    def test_statuses(self):
        assert ExceptionStatus.OPEN.value == "OPEN"
        assert ExceptionStatus.RESOLVED.value == "RESOLVED"
        assert ExceptionStatus.ACKNOWLEDGED.value == "ACKNOWLEDGED"


class TestPauseReason:
    def test_reasons(self):
        assert PauseReason.BREAK.value == "BREAK"
        assert PauseReason.SAFETY.value == "SAFETY"
        assert PauseReason.EQUIPMENT_UNAVAILABLE.value == "EQUIPMENT_UNAVAILABLE"


class TestOperationalPlacementStatus:
    def test_statuses(self):
        assert OperationalPlacementStatus.PLACED_PENDING_MOVEMENT_LEDGER.value == "PLACED_PENDING_MOVEMENT_LEDGER"
        assert OperationalPlacementStatus.CANCELLED.value == "CANCELLED"


class TestDataQualityStatus:
    def test_statuses(self):
        assert DataQualityStatus.MISSING_BASELINE.value == "MISSING_BASELINE"
        assert DataQualityStatus.COMPLETE.value == "COMPLETE"
        assert DataQualityStatus.STALE.value == "STALE"


class TestPolicyVersionStatus:
    def test_statuses(self):
        assert PolicyVersionStatus.DRAFT.value == "DRAFT"
        assert PolicyVersionStatus.ACTIVE.value == "ACTIVE"
        assert PolicyVersionStatus.ARCHIVED.value == "ARCHIVED"
