"""Phase 042 — Measurement tolerance evaluation service."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.modules.logistics.inbound.quality_quarantine.domain.enums import (
    ToleranceResult,
)


def evaluate_measurement_tolerance(
    *,
    tolerance_type: str,
    measured_value: Decimal,
    tolerance_config: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate a measurement against its tolerance configuration.

    Returns dict with tolerance_result and details.
    """
    if tolerance_type == "BOOLEAN_REQUIRED":
        return {
            "tolerance_result": ToleranceResult.EXACT_MATCH,
            "details": {"message": "Boolean check completed"},
        }

    if tolerance_type == "EXACT_VALUE":
        target = Decimal(str(tolerance_config.get("target_value", 0)))
        if measured_value == target:
            return {"tolerance_result": ToleranceResult.EXACT_MATCH, "details": {}}
        return {"tolerance_result": ToleranceResult.BELOW_MINIMUM, "details": {"expected": str(target), "actual": str(measured_value)}}

    if tolerance_type == "MINIMUM_ONLY":
        min_val = Decimal(str(tolerance_config.get("min_value", 0)))
        if measured_value >= min_val:
            return {"tolerance_result": ToleranceResult.WITHIN_TOLERANCE, "details": {"min": str(min_val)}}
        return {"tolerance_result": ToleranceResult.BELOW_MINIMUM, "details": {"min": str(min_val), "actual": str(measured_value)}}

    if tolerance_type == "MAXIMUM_ONLY":
        max_val = Decimal(str(tolerance_config.get("max_value", 0)))
        if measured_value <= max_val:
            return {"tolerance_result": ToleranceResult.WITHIN_TOLERANCE, "details": {"max": str(max_val)}}
        return {"tolerance_result": ToleranceResult.ABOVE_MAXIMUM, "details": {"max": str(max_val), "actual": str(measured_value)}}

    if tolerance_type == "ABSOLUTE_RANGE":
        min_val = Decimal(str(tolerance_config.get("min_value", 0)))
        max_val = Decimal(str(tolerance_config.get("max_value", 0)))
        if min_val <= measured_value <= max_val:
            return {"tolerance_result": ToleranceResult.WITHIN_TOLERANCE, "details": {"min": str(min_val), "max": str(max_val)}}
        if measured_value < min_val:
            return {"tolerance_result": ToleranceResult.BELOW_MINIMUM, "details": {"min": str(min_val), "actual": str(measured_value)}}
        return {"tolerance_result": ToleranceResult.ABOVE_MAXIMUM, "details": {"max": str(max_val), "actual": str(measured_value)}}

    if tolerance_type == "TARGET_WITH_ABSOLUTE_DEVIATION":
        target = Decimal(str(tolerance_config.get("target_value", 0)))
        deviation = Decimal(str(tolerance_config.get("absolute_deviation", 0)))
        if abs(measured_value - target) <= deviation:
            return {"tolerance_result": ToleranceResult.WITHIN_TOLERANCE, "details": {"target": str(target), "deviation": str(deviation)}}
        return {"tolerance_result": ToleranceResult.ABOVE_MAXIMUM, "details": {"target": str(target), "deviation": str(deviation), "actual": str(measured_value)}}

    if tolerance_type == "TARGET_WITH_PERCENTAGE_DEVIATION":
        target = Decimal(str(tolerance_config.get("target_value", 0)))
        pct = Decimal(str(tolerance_config.get("percentage_deviation", 0)))
        if target == 0:
            return {"tolerance_result": ToleranceResult.INVALID_UNIT, "details": {"reason": "Target is zero"}}
        max_deviation = abs(target * pct / Decimal("100"))
        if abs(measured_value - target) <= max_deviation:
            return {"tolerance_result": ToleranceResult.WITHIN_TOLERANCE, "details": {"target": str(target), "pct": str(pct)}}
        return {"tolerance_result": ToleranceResult.ABOVE_MAXIMUM, "details": {"target": str(target), "pct": str(pct), "actual": str(measured_value)}}

    if tolerance_type == "OPTION_SET":
        valid_options = tolerance_config.get("valid_options", [])
        if str(measured_value) in valid_options:
            return {"tolerance_result": ToleranceResult.EXACT_MATCH, "details": {"valid_options": valid_options}}
        return {"tolerance_result": ToleranceResult.INVALID_UNIT, "details": {"valid_options": valid_options}}

    return {"tolerance_result": ToleranceResult.NOT_EVALUATED, "details": {"reason": f"Unknown tolerance type: {tolerance_type}"}}
