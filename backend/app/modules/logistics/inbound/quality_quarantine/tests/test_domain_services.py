"""Phase 042 — Unit tests for quality quarantine domain services."""

from __future__ import annotations

import pytest
from decimal import Decimal
from uuid import uuid4

from app.modules.logistics.inbound.quality_quarantine.domain.enums import (
    AllocationStatus,
    AvailabilityClass,
    QuarantineStatus,
    QualityStatus,
    InspectionOverallResult,
    ReleaseStatus,
    RejectionStatus,
    TriggerEvaluationResult,
)
from app.modules.logistics.inbound.quality_quarantine.domain.errors import (
    InboundInventoryAllocationSplitInvalid,
    InboundInventoryAllocationStatusInvalid,
    QualityQuarantineStatusInvalid,
)
from app.modules.logistics.inbound.quality_quarantine.domain.services.allocation_service import (
    derive_availability_class,
    derive_quality_status,
    require_allocation_transition,
)
from app.modules.logistics.inbound.quality_quarantine.domain.services.quarantine_case_service import (
    require_quarantine_transition,
    derive_quarantine_quality_result,
)
from app.modules.logistics.inbound.quality_quarantine.domain.services.inspection_result_service import (
    calculate_overall_result,
)
from app.modules.logistics.inbound.quality_quarantine.domain.services.split_service import (
    validate_split,
)
from app.modules.logistics.inbound.quality_quarantine.domain.services.trigger_service import (
    QuarantineTriggerService,
)
from app.modules.logistics.inbound.quality_quarantine.domain.services.integrity_service import (
    canonical_hash,
    verify_hash,
)
from app.modules.logistics.inbound.quality_quarantine.domain.services.measurement_service import (
    evaluate_measurement_tolerance,
)
from app.modules.logistics.inbound.quality_quarantine.domain.services.preparation_services import (
    PutawayPreparationService,
    FutureInventoryMovementPreparationService,
    FutureInventoryBalancePreparationService,
    FutureTraceabilityPreparationService,
)


# ---------------------------------------------------------------------------
# Allocation tests
# ---------------------------------------------------------------------------

class TestAllocationTransitions:
    def test_valid_transition(self):
        require_allocation_transition(
            AllocationStatus.PENDING_QUALITY_ASSESSMENT,
            AllocationStatus.QUARANTINE_REQUIRED,
        )

    def test_invalid_transition_raises(self):
        with pytest.raises(InboundInventoryAllocationStatusInvalid):
            require_allocation_transition(
                AllocationStatus.RELEASED_FOR_PUTAWAY,
                AllocationStatus.PENDING_QUALITY_ASSESSMENT,
            )

    def test_derive_availability_quarantined(self):
        assert derive_availability_class(AllocationStatus.QUARANTINED) == "QUARANTINE"

    def test_derive_availability_released(self):
        assert derive_availability_class(AllocationStatus.RELEASED_FOR_PUTAWAY) == "AVAILABLE_FOR_PUTAWAY"

    def test_derive_availability_rejected(self):
        assert derive_availability_class(AllocationStatus.REJECTED_PENDING_DISPOSITION) == "REJECTED_NOT_AVAILABLE"

    def test_derive_quality_status_pass(self):
        assert derive_quality_status("PASS", AllocationStatus.DECISION_PENDING) == "PASSED"

    def test_derive_quality_status_not_assessed(self):
        assert derive_quality_status(None, AllocationStatus.PENDING_QUALITY_ASSESSMENT) == "NOT_ASSESSED"

    def test_derive_quality_status_cancelled(self):
        assert derive_quality_status("PASS", AllocationStatus.CANCELLED) == "NOT_APPLICABLE"


# ---------------------------------------------------------------------------
# Quarantine case tests
# ---------------------------------------------------------------------------

class TestQuarantineCaseTransitions:
    def test_valid_transition(self):
        require_quarantine_transition(
            QuarantineStatus.DRAFT,
            QuarantineStatus.ACTIVE,
        )

    def test_invalid_transition_raises(self):
        with pytest.raises(QualityQuarantineStatusInvalid):
            require_quarantine_transition(
                QuarantineStatus.RELEASED,
                QuarantineStatus.DRAFT,
            )

    def test_derive_quality_result(self):
        assert derive_quarantine_quality_result("PASS") == "PASSED"
        assert derive_quarantine_quality_result("FAIL") == "FAILED"
        assert derive_quarantine_quality_result(None) is None


# ---------------------------------------------------------------------------
# Trigger tests
# ---------------------------------------------------------------------------

class TestTriggerService:
    def test_damage_triggers_quarantine(self):
        result = QuarantineTriggerService.evaluate_triggers(has_damage=True)
        assert result["result"] == TriggerEvaluationResult.QUARANTINE_REQUIRED
        assert "DAMAGE_DETECTED" in result["reasons"]

    def test_expired_triggers_quarantine(self):
        result = QuarantineTriggerService.evaluate_triggers(product_expired=True)
        assert result["result"] == TriggerEvaluationResult.QUARANTINE_REQUIRED

    def test_no_triggers_direct_release(self):
        result = QuarantineTriggerService.evaluate_triggers()
        assert result["result"] == TriggerEvaluationResult.DIRECT_RELEASE_ELIGIBLE
        assert result["triggers_applied"] == 0

    def test_inspection_required(self):
        result = QuarantineTriggerService.evaluate_triggers(product_requires_inspection=True)
        assert result["result"] == TriggerEvaluationResult.INSPECTION_REQUIRED

    def test_high_severity_triggers_quarantine(self):
        result = QuarantineTriggerService.evaluate_triggers(difference_severity="HIGH")
        assert result["result"] == TriggerEvaluationResult.QUARANTINE_REQUIRED

    def test_temperature_concern_manual_review(self):
        result = QuarantineTriggerService.evaluate_triggers(temperature_observed=True)
        assert result["result"] == TriggerEvaluationResult.MANUAL_REVIEW_REQUIRED


# ---------------------------------------------------------------------------
# Split tests
# ---------------------------------------------------------------------------

class TestSplitService:
    def test_valid_split(self):
        validate_split(
            original_quantity=Decimal("100"),
            original_base_quantity=Decimal("100"),
            first_child_quantity=Decimal("60"),
            first_child_base_quantity=Decimal("60"),
            second_child_quantity=Decimal("40"),
            second_child_base_quantity=Decimal("40"),
        )

    def test_invalid_split_raises(self):
        with pytest.raises(InboundInventoryAllocationSplitInvalid):
            validate_split(
                original_quantity=Decimal("100"),
                original_base_quantity=Decimal("100"),
                first_child_quantity=Decimal("60"),
                first_child_base_quantity=Decimal("60"),
                second_child_quantity=Decimal("50"),
                second_child_base_quantity=Decimal("50"),
            )

    def test_zero_child_raises(self):
        with pytest.raises(InboundInventoryAllocationSplitInvalid):
            validate_split(
                original_quantity=Decimal("100"),
                original_base_quantity=Decimal("100"),
                first_child_quantity=Decimal("0"),
                first_child_base_quantity=Decimal("50"),
                second_child_quantity=Decimal("100"),
                second_child_base_quantity=Decimal("50"),
            )


# ---------------------------------------------------------------------------
# Inspection result tests
# ---------------------------------------------------------------------------

class TestInspectionResult:
    def test_all_pass(self):
        controls = [
            {"required": True, "status": "COMPLETED", "blocking_on_fail": False, "result_status": "PASS"},
            {"required": True, "status": "COMPLETED", "blocking_on_fail": False, "result_status": "PASS"},
        ]
        result = calculate_overall_result(controls, [], [], [])
        assert result == InspectionOverallResult.PASS

    def test_blocking_fail(self):
        controls = [
            {"required": True, "status": "COMPLETED", "blocking_on_fail": True, "result_status": "FAIL"},
        ]
        result = calculate_overall_result(controls, [], [], [])
        assert result == InspectionOverallResult.FAIL

    def test_pending_control(self):
        controls = [
            {"required": True, "status": "NOT_STARTED", "blocking_on_fail": False, "result_status": None},
        ]
        result = calculate_overall_result(controls, [], [], [])
        assert result == InspectionOverallResult.INCONCLUSIVE

    def test_pass_with_warnings(self):
        controls = [
            {"required": True, "status": "COMPLETED", "blocking_on_fail": False, "result_status": "PASS_WITH_OBSERVATION"},
        ]
        result = calculate_overall_result(controls, [], [], [])
        assert result == InspectionOverallResult.PASS_WITH_OBSERVATIONS


# ---------------------------------------------------------------------------
# Measurement tests
# ---------------------------------------------------------------------------

class TestMeasurement:
    def test_within_tolerance_range(self):
        result = evaluate_measurement_tolerance(
            tolerance_type="ABSOLUTE_RANGE",
            measured_value=Decimal("50"),
            tolerance_config={"min_value": "40", "max_value": "60"},
        )
        assert result["tolerance_result"] == "WITHIN_TOLERANCE"

    def test_below_minimum(self):
        result = evaluate_measurement_tolerance(
            tolerance_type="ABSOLUTE_RANGE",
            measured_value=Decimal("30"),
            tolerance_config={"min_value": "40", "max_value": "60"},
        )
        assert result["tolerance_result"] == "BELOW_MINIMUM"

    def test_exact_match(self):
        result = evaluate_measurement_tolerance(
            tolerance_type="EXACT_VALUE",
            measured_value=Decimal("100"),
            tolerance_config={"target_value": "100"},
        )
        assert result["tolerance_result"] == "EXACT_MATCH"

    def test_percentage_deviation(self):
        result = evaluate_measurement_tolerance(
            tolerance_type="TARGET_WITH_PERCENTAGE_DEVIATION",
            measured_value=Decimal("105"),
            tolerance_config={"target_value": "100", "percentage_deviation": "10"},
        )
        assert result["tolerance_result"] == "WITHIN_TOLERANCE"


# ---------------------------------------------------------------------------
# Integrity tests
# ---------------------------------------------------------------------------

class TestIntegrity:
    def test_canonical_hash_deterministic(self):
        data = {"key": "value", "number": 42}
        h1 = canonical_hash(data)
        h2 = canonical_hash(data)
        assert h1 == h2

    def test_canonical_hash_differs_for_different_data(self):
        h1 = canonical_hash({"a": 1})
        h2 = canonical_hash({"a": 2})
        assert h1 != h2

    def test_verify_hash(self):
        data = {"test": True}
        h = canonical_hash(data)
        assert verify_hash(data, h)

    def test_verify_hash_wrong(self):
        assert not verify_hash({"test": True}, "wrong_hash")


# ---------------------------------------------------------------------------
# Preparation services tests
# ---------------------------------------------------------------------------

class TestPreparationServices:
    def test_putaway_filters_correctly(self):
        allocs = [
            {"id": "a1", "allocation_status": "RELEASED_FOR_PUTAWAY", "product_id": "p1"},
            {"id": "a2", "allocation_status": "QUARANTINED", "product_id": "p2"},
        ]
        result = PutawayPreparationService.prepare_putaway_data(allocs)
        assert len(result) == 1
        assert result[0]["eligible_for_putaway"] is True

    def test_movement_events_filters(self):
        allocs = [
            {"id": "a1", "allocation_status": "RELEASED_FOR_PUTAWAY", "product_id": "p1", "quantity": "100"},
            {"id": "a2", "allocation_status": "QUARANTINED", "product_id": "p2", "quantity": "50"},
        ]
        result = FutureInventoryMovementPreparationService.prepare_movement_events(allocs)
        assert len(result) == 1
        assert result[0]["event_type"] == "QUARANTINE_RELEASED"


# ---------------------------------------------------------------------------
# Import tests (verify all modules import cleanly)
# ---------------------------------------------------------------------------

class TestImports:
    def test_import_enums(self):
        from app.modules.logistics.inbound.quality_quarantine.domain import enums
        assert hasattr(enums, "AllocationStatus")

    def test_import_errors(self):
        from app.modules.logistics.inbound.quality_quarantine.domain import errors
        assert hasattr(errors, "QualityQuarantineError")

    def test_import_models(self):
        from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence import models
        assert hasattr(models, "InboundInventoryDispositionAllocationModel")

    def test_import_schemas(self):
        from app.modules.logistics.inbound.quality_quarantine.presentation import schemas
        assert hasattr(schemas, "AllocationResponse")

    def test_import_router(self):
        from app.modules.logistics.inbound.quality_quarantine.presentation import router
        assert hasattr(router, "router")
