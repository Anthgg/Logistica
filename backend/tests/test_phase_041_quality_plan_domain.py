"""Phase 041. Quality inspection plan domain tests."""

from decimal import Decimal
import pytest

from app.modules.logistics.inbound.reception_differences.domain.quality_plan_enums import (
    PlanStatus,
    VersionStatus,
    PlanFamily,
    ScopeType,
    ResolutionSpecificity,
    ToleranceType,
    ControlType,
    SamplingType,
    PLAN_STATUS_TRANSITIONS,
    VERSION_STATUS_TRANSITIONS,
    CONTROL_TYPE_TOLERANCE_MAP,
)
from app.modules.logistics.inbound.reception_differences.domain.quality_plan_services import (
    canonical_hash_quality_plan,
    require_plan_transition,
    require_version_transition,
    validate_tolerance_values,
    validate_control_type_tolerance,
    compute_specificity_rank,
    evaluate_tolerance,
    resolve_plan_specificity,
)


class TestPlanEnums:
    def test_plan_status_values(self):
        assert PlanStatus.DRAFT == "DRAFT"
        assert PlanStatus.ACTIVE == "ACTIVE"
        assert PlanStatus.INACTIVE == "INACTIVE"
        assert PlanStatus.ARCHIVED == "ARCHIVED"

    def test_version_status_values(self):
        assert VersionStatus.DRAFT == "DRAFT"
        assert VersionStatus.VALIDATED == "VALIDATED"
        assert VersionStatus.ACTIVE == "ACTIVE"
        assert VersionStatus.RETIRED == "RETIRED"

    def test_plan_family_values(self):
        assert PlanFamily.INBOUND_RECEIVING == "INBOUND_RECEIVING"
        assert PlanFamily.GENERAL_QUALITY == "GENERAL_QUALITY"

    def test_scope_type_values(self):
        assert ScopeType.PRODUCT == "PRODUCT"
        assert ScopeType.PRODUCT_CATEGORY == "PRODUCT_CATEGORY"

    def test_plan_status_transitions(self):
        assert PlanStatus.ACTIVE in PLAN_STATUS_TRANSITIONS[PlanStatus.DRAFT]
        assert PlanStatus.ARCHIVED in PLAN_STATUS_TRANSITIONS[PlanStatus.ACTIVE]
        assert len(PLAN_STATUS_TRANSITIONS[PlanStatus.ARCHIVED]) == 0

    def test_version_status_transitions(self):
        assert VersionStatus.VALIDATED in VERSION_STATUS_TRANSITIONS[VersionStatus.DRAFT]
        assert VersionStatus.ACTIVE in VERSION_STATUS_TRANSITIONS[VersionStatus.VALIDATED]
        assert len(VERSION_STATUS_TRANSITIONS[VersionStatus.ARCHIVED]) == 0

    def test_control_type_tolerance_map_completeness(self):
        for ct in ControlType:
            assert ct in CONTROL_TYPE_TOLERANCE_MAP, f"ControlType {ct} missing from CONTROL_TYPE_TOLERANCE_MAP"


class TestDomainServices:
    def test_canonical_hash_deterministic(self):
        data = {"key": "value", "number": 42}
        h1 = canonical_hash_quality_plan(data)
        h2 = canonical_hash_quality_plan(data)
        assert h1 == h2
        assert len(h1) == 64

    def test_canonical_hash_different_data(self):
        h1 = canonical_hash_quality_plan({"a": 1})
        h2 = canonical_hash_quality_plan({"a": 2})
        assert h1 != h2

    def test_require_plan_transition_valid(self):
        require_plan_transition("DRAFT", "ACTIVE")
        require_plan_transition("ACTIVE", "INACTIVE")
        require_plan_transition("INACTIVE", "ACTIVE")

    def test_require_plan_transition_invalid(self):
        from app.modules.logistics.inbound.reception_differences.domain.quality_plan_errors import (
            QualityPlanStatusInvalid,
        )
        with pytest.raises(QualityPlanStatusInvalid):
            require_plan_transition("DRAFT", "ARCHIVED")
        with pytest.raises(QualityPlanStatusInvalid):
            require_plan_transition("ARCHIVED", "ACTIVE")

    def test_require_version_transition_valid(self):
        require_version_transition("DRAFT", "VALIDATED")
        require_version_transition("VALIDATED", "ACTIVE")

    def test_require_version_transition_invalid(self):
        from app.modules.logistics.inbound.reception_differences.domain.quality_plan_errors import (
            QualityPlanVersionStatusInvalid,
        )
        with pytest.raises(QualityPlanVersionStatusInvalid):
            require_version_transition("DRAFT", "ACTIVE")
        with pytest.raises(QualityPlanVersionStatusInvalid):
            require_version_transition("ARCHIVED", "DRAFT")

    def test_validate_tolerance_values_boolean(self):
        assert validate_tolerance_values("BOOLEAN_REQUIRED", {}) is True

    def test_validate_tolerance_values_option_set(self):
        assert validate_tolerance_values("OPTION_SET", {"valid_options": ["A", "B"]}) is True
        assert validate_tolerance_values("OPTION_SET", {"valid_options": []}) is False

    def test_validate_tolerance_values_min_only(self):
        assert validate_tolerance_values("MINIMUM_ONLY", {"min_value": Decimal("10")}) is True
        assert validate_tolerance_values("MINIMUM_ONLY", {}) is False

    def test_validate_tolerance_values_exact(self):
        assert validate_tolerance_values("EXACT_VALUE", {"target_value": Decimal("100")}) is True

    def test_validate_control_type_tolerance_valid(self):
        assert validate_control_type_tolerance("WEIGHT_MEASUREMENT", "ABSOLUTE_RANGE") is True
        assert validate_control_type_tolerance("WEIGHT_MEASUREMENT", "BOOLEAN_REQUIRED") is False

    def test_validate_control_type_tolerance_boolean_control(self):
        assert validate_control_type_tolerance("PACKAGING_INTEGRITY", "BOOLEAN_REQUIRED") is True
        assert validate_control_type_tolerance("PACKAGING_INTEGRITY", "ABSOLUTE_RANGE") is False

    def test_compute_specificity_rank(self):
        assert compute_specificity_rank("PRODUCT_WAREHOUSE") == 1
        assert compute_specificity_rank("PRODUCT_BRANCH") == 2
        assert compute_specificity_rank("PRODUCT_GLOBAL") == 3
        assert compute_specificity_rank("NO_PLAN") == 8

    def test_evaluate_tolerance_absolute_range(self):
        values = {"min_value": Decimal("10"), "max_value": Decimal("20")}
        result = evaluate_tolerance("ABSOLUTE_RANGE", values, Decimal("15"))
        assert result["passed"] is True
        result = evaluate_tolerance("ABSOLUTE_RANGE", values, Decimal("25"))
        assert result["passed"] is False

    def test_evaluate_tolerance_boolean(self):
        result = evaluate_tolerance("BOOLEAN_REQUIRED", {}, True)
        assert result["passed"] is True
        result = evaluate_tolerance("BOOLEAN_REQUIRED", {}, False)
        assert result["passed"] is False

    def test_evaluate_tolerance_option_set(self):
        values = {"valid_options": ["RED", "BLUE", "GREEN"]}
        result = evaluate_tolerance("OPTION_SET", values, "RED")
        assert result["passed"] is True
        result = evaluate_tolerance("OPTION_SET", values, "YELLOW")
        assert result["passed"] is False

    def test_evaluate_tolerance_exact_value(self):
        values = {"target_value": Decimal("100")}
        result = evaluate_tolerance("EXACT_VALUE", values, Decimal("100"))
        assert result["passed"] is True
        result = evaluate_tolerance("EXACT_VALUE", values, Decimal("99"))
        assert result["passed"] is False

    def test_evaluate_tolerance_min_only(self):
        values = {"min_value": Decimal("10")}
        result = evaluate_tolerance("MINIMUM_ONLY", values, Decimal("15"))
        assert result["passed"] is True
        result = evaluate_tolerance("MINIMUM_ONLY", values, Decimal("5"))
        assert result["passed"] is False

    def test_evaluate_tolerance_max_only(self):
        values = {"max_value": Decimal("20")}
        result = evaluate_tolerance("MAXIMUM_ONLY", values, Decimal("15"))
        assert result["passed"] is True
        result = evaluate_tolerance("MAXIMUM_ONLY", values, Decimal("25"))
        assert result["passed"] is False

    def test_evaluate_tolerance_target_with_absolute_deviation(self):
        values = {"target_value": Decimal("100"), "absolute_deviation": Decimal("5")}
        result = evaluate_tolerance("TARGET_WITH_ABSOLUTE_DEVIATION", values, Decimal("103"))
        assert result["passed"] is True
        result = evaluate_tolerance("TARGET_WITH_ABSOLUTE_DEVIATION", values, Decimal("110"))
        assert result["passed"] is False

    def test_evaluate_tolerance_target_with_percentage_deviation(self):
        values = {"target_value": Decimal("100"), "percentage_deviation": Decimal("10")}
        result = evaluate_tolerance("TARGET_WITH_PERCENTAGE_DEVIATION", values, Decimal("105"))
        assert result["passed"] is True
        result = evaluate_tolerance("TARGET_WITH_PERCENTAGE_DEVIATION", values, Decimal("115"))
        assert result["passed"] is False

    def test_resolve_plan_specificity_no_plans(self):
        plan_id, specificity = resolve_plan_specificity(
            product_id=None,
            product_category_id=None,
            warehouse_id=None,
            branch_id=None,
            plans=[],
        )
        assert plan_id is None
        assert specificity == "NO_PLAN"
