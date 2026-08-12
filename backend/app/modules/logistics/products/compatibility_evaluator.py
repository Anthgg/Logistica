"""Qualitative compatibility evaluator between Product and WarehouseLocation for Phase 023."""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import UUID


class EvaluateProductLocationCompatibility:
    """Evaluates qualitative compatibility between Product Storage/Handling conditions and WarehouseLocation restrictions.

    No inventory, stock, or putaway space calculations are performed.
    """

    @classmethod
    def evaluate(
        cls,
        product_dict: Dict[str, Any],
        storage_conditions: List[Dict[str, Any]],
        handling_conditions: List[Dict[str, Any]],
        location_dict: Dict[str, Any],
        location_restrictions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        blocking_reasons = []
        warnings = []

        loc_type = location_dict.get("location_type", "")
        loc_status = location_dict.get("status", "ACTIVE")

        # 1. Location Status Check
        if loc_status in ["BLOCKED", "MAINTENANCE"]:
            blocking_reasons.append(f"Warehouse location is in '{loc_status}' state.")

        # 2. Temperature & Cold Chain Evaluation
        has_cold_chain = any(c.get("condition_type") in ["COLD_CHAIN", "FROZEN", "REFRIGERATED"] for c in storage_conditions)
        if has_cold_chain and loc_type not in ["COLD_STORAGE", "REFRIGERATED_ZONE", "FREEZER"]:
            # Check if location has temp control flag
            if not location_dict.get("temperature_controlled", False):
                blocking_reasons.append("Product requires COLD_CHAIN / Refrigerated storage, but location is not temperature controlled.")

        # 3. Hazardous Materials Evaluation
        is_hazmat = any(c.get("condition_type") in ["HAZARDOUS", "FLAMMABLE", "CORROSIVE"] for c in storage_conditions)
        if is_hazmat:
            hazmat_restricted = any(r.get("restriction_type") == "HAZMAT_PROHIBITED" for r in location_restrictions)
            if hazmat_restricted or not location_dict.get("hazardous_materials_allowed", False):
                blocking_reasons.append("Product contains HAZARDOUS materials, which are prohibited in this location.")

        # 4. Quarantine Evaluation
        requires_quarantine = product_dict.get("requires_quarantine_on_receipt", False)
        if requires_quarantine and loc_type != "QUARANTINE":
            warnings.append("Product requires Quarantine on receipt, but location is not a dedicated QUARANTINE zone.")

        # Determine overall compatibility status
        if blocking_reasons:
            status = "INCOMPATIBLE"
        elif warnings:
            status = "REQUIRES_REVIEW"
        else:
            status = "COMPATIBLE"

        return {
            "status": status,
            "blocking_reasons": blocking_reasons,
            "warnings": warnings,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "evaluator_version": "v1.0.0",
        }
