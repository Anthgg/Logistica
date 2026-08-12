"""Phase 041 domain services. Pure functions for quality inspection plan resolution, validation, and hashing."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.modules.logistics.inbound.reception_differences.domain.quality_plan_enums import (
    CONTROL_TYPE_TOLERANCE_MAP,
    PLAN_STATUS_TRANSITIONS,
    VERSION_STATUS_TRANSITIONS,
    ResolutionSpecificity,
    ToleranceType,
    VersionStatus,
)


def canonical_hash_quality_plan(data: dict[str, Any]) -> str:
    canonical = json.dumps(data, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def require_plan_transition(current: str, target: str) -> None:
    from app.modules.logistics.inbound.reception_differences.domain.quality_plan_errors import (
        QualityPlanStatusInvalid,
    )
    allowed = PLAN_STATUS_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise QualityPlanStatusInvalid(
            "QualityPlanStatusInvalid",
            f"Transición de plan '{current}' a '{target}' no está permitida. Permitidos: {allowed or 'ninguno'}",
            409,
        )


def require_version_transition(current: str, target: str) -> None:
    from app.modules.logistics.inbound.reception_differences.domain.quality_plan_errors import (
        QualityPlanVersionStatusInvalid,
    )
    allowed = VERSION_STATUS_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise QualityPlanVersionStatusInvalid(
            "QualityPlanVersionStatusInvalid",
            f"Transición de versión '{current}' a '{target}' no está permitida. Permitidos: {allowed or 'ninguno'}",
            409,
        )


_RESOLUTION_SPECIFICITY_ORDER = {
    ResolutionSpecificity.PRODUCT_WAREHOUSE: 1,
    ResolutionSpecificity.PRODUCT_BRANCH: 2,
    ResolutionSpecificity.PRODUCT_GLOBAL: 3,
    ResolutionSpecificity.CATEGORY_WAREHOUSE: 4,
    ResolutionSpecificity.CATEGORY_BRANCH: 5,
    ResolutionSpecificity.CATEGORY_GLOBAL: 6,
    ResolutionSpecificity.PARENT_CATEGORY: 7,
    ResolutionSpecificity.NO_PLAN: 8,
}


def resolve_plan_specificity(
    product_id: UUID | None,
    product_category_id: UUID | None,
    warehouse_id: UUID | None,
    branch_id: UUID | None,
    plans: list[dict[str, Any]],
) -> tuple[str | None, str]:
    candidates: list[tuple[int, dict[str, Any]]] = []
    for plan in plans:
        scope = plan.get("scope_type")
        scope_product_id = plan.get("scope_product_id")
        scope_category_id = plan.get("scope_category_id")
        scope_warehouse_id = plan.get("scope_warehouse_id")
        scope_branch_id = plan.get("scope_branch_id")

        if scope == "PRODUCT" and scope_product_id:
            if product_id and str(scope_product_id) == str(product_id):
                if warehouse_id and scope_warehouse_id and str(scope_warehouse_id) == str(warehouse_id):
                    candidates.append((1, plan))
                elif branch_id and scope_branch_id and str(scope_branch_id) == str(branch_id):
                    candidates.append((2, plan))
                elif not scope_warehouse_id and not scope_branch_id:
                    candidates.append((3, plan))
        elif scope == "PRODUCT_CATEGORY" and scope_category_id:
            effective_category = product_category_id
            specificity = 4
            if warehouse_id and scope_warehouse_id and str(scope_warehouse_id) == str(warehouse_id):
                specificity = 4
            elif branch_id and scope_branch_id and str(scope_branch_id) == str(branch_id):
                specificity = 5
            elif not scope_warehouse_id and not scope_branch_id:
                specificity = 6
            if effective_category and str(scope_category_id) == str(effective_category):
                candidates.append((specificity, plan))

    if not candidates:
        return None, ResolutionSpecificity.NO_PLAN

    candidates.sort(key=lambda x: x[0])
    best_specificity_value, best_plan = candidates[0]
    specificity_map = {v: k for k, v in _RESOLUTION_SPECIFICITY_ORDER.items()}
    specificity_name = specificity_map.get(best_specificity_value, ResolutionSpecificity.NO_PLAN)
    return str(best_plan.get("plan_id") or best_plan.get("id")), specificity_name


def validate_tolerance_values(tolerance_type: str, values: dict[str, Any]) -> bool:
    if tolerance_type == ToleranceType.BOOLEAN_REQUIRED:
        return True
    if tolerance_type == ToleranceType.OPTION_SET:
        return bool(values.get("valid_options"))
    if tolerance_type in (
        ToleranceType.MINIMUM_ONLY,
        ToleranceType.MAXIMUM_ONLY,
        ToleranceType.EXACT_VALUE,
    ):
        key = "target_value" if tolerance_type == ToleranceType.EXACT_VALUE else (
            "min_value" if tolerance_type == ToleranceType.MINIMUM_ONLY else "max_value"
        )
        return key in values and values[key] is not None
    if tolerance_type == ToleranceType.ABSOLUTE_RANGE:
        return "min_value" in values and "max_value" in values
    if tolerance_type in (
        ToleranceType.TARGET_WITH_ABSOLUTE_DEVIATION,
        ToleranceType.TARGET_WITH_PERCENTAGE_DEVIATION,
    ):
        return "target_value" in values and (
            "absolute_deviation" in values or "percentage_deviation" in values
        )
    return False


def evaluate_tolerance(tolerance_type: str, values: dict[str, Any], observed: Any) -> dict[str, Any]:
    result = {"passed": False, "details": {}}
    if tolerance_type == ToleranceType.BOOLEAN_REQUIRED:
        result["passed"] = observed is True
        result["details"] = {"expected": True, "observed": observed}
    elif tolerance_type == ToleranceType.OPTION_SET:
        valid = values.get("valid_options", [])
        result["passed"] = observed in valid
        result["details"] = {"valid_options": valid, "observed": observed}
    elif tolerance_type == ToleranceType.EXACT_VALUE:
        target = values.get("target_value")
        result["passed"] = Decimal(str(observed)) == Decimal(str(target))
        result["details"] = {"target": target, "observed": observed}
    elif tolerance_type == ToleranceType.MINIMUM_ONLY:
        min_val = values.get("min_value")
        result["passed"] = Decimal(str(observed)) >= Decimal(str(min_val))
        result["details"] = {"min_value": min_val, "observed": observed}
    elif tolerance_type == ToleranceType.MAXIMUM_ONLY:
        max_val = values.get("max_value")
        result["passed"] = Decimal(str(observed)) <= Decimal(str(max_val))
        result["details"] = {"max_value": max_val, "observed": observed}
    elif tolerance_type == ToleranceType.ABSOLUTE_RANGE:
        min_val = values.get("min_value")
        max_val = values.get("max_value")
        d = Decimal(str(observed))
        result["passed"] = Decimal(str(min_val)) <= d <= Decimal(str(max_val))
        result["details"] = {"min_value": min_val, "max_value": max_val, "observed": observed}
    elif tolerance_type == ToleranceType.TARGET_WITH_ABSOLUTE_DEVIATION:
        target = Decimal(str(values.get("target_value", 0)))
        dev = Decimal(str(values.get("absolute_deviation", 0)))
        d = Decimal(str(observed))
        result["passed"] = (target - dev) <= d <= (target + dev)
        result["details"] = {"target": str(target), "deviation": str(dev), "observed": observed}
    elif tolerance_type == ToleranceType.TARGET_WITH_PERCENTAGE_DEVIATION:
        target = Decimal(str(values.get("target_value", 0)))
        pct = Decimal(str(values.get("percentage_deviation", 0))) / Decimal("100")
        dev = target * pct
        d = Decimal(str(observed))
        result["passed"] = (target - dev) <= d <= (target + dev)
        result["details"] = {"target": str(target), "percentage": str(pct * 100), "observed": observed}
    return result


def validate_control_type_tolerance(control_type: str, tolerance_type: str) -> bool:
    allowed = CONTROL_TYPE_TOLERANCE_MAP.get(control_type, [])
    return tolerance_type in allowed


def compute_specificity_rank(specificity: str) -> int:
    return _RESOLUTION_SPECIFICITY_ORDER.get(specificity, 99)
