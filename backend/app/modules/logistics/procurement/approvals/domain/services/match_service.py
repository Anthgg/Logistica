"""ApprovalPolicyMatchService — deterministic policy matching engine.

Evaluates resource context against active policy versions within an organization.
Implements the MOST_RESTRICTIVE_UNION strategy for multi-category purchases.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.modules.logistics.procurement.approvals.domain.errors.exceptions import (
    ApprovalPolicyNoMatch,
)


class ApprovalPolicyMatchService:
    """Deterministic matcher for procurement approval policies."""

    @staticmethod
    def match_policies(
        policies_with_versions: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Find matching active policy versions for a given subject context.

        context dict expects:
        - subject_type: str
        - organization_id: str
        - total_amount: Decimal
        - currency_code: str
        - branch_id: str | None
        - cost_center_id: str | None
        - product_category_ids: list[str]
        - purchase_type: str | None
        - priority: int | None
        - supplier_id: str | None
        - supplier_risk_level: str | None
        - has_variances: bool
        - single_source: bool
        """
        matched_results: list[dict[str, Any]] = []

        for p_dict in policies_with_versions:
            policy = p_dict["policy"]
            version = p_dict["version"]
            conditions = p_dict.get("conditions", [])

            # Check basic subject_type
            if policy["subject_type"] != context["subject_type"]:
                continue

            # Check if all condition groups pass
            if ApprovalPolicyMatchService._evaluate_conditions(conditions, context):
                matched_results.append({
                    "policy": policy,
                    "version": version,
                    "conditions": conditions,
                    "steps": p_dict.get("steps", []),
                    "priority": policy["priority"],
                    "is_fallback": policy.get("is_fallback", False),
                })

        if not matched_results:
            # Fallback search
            fallbacks = [
                p for p in policies_with_versions
                if p["policy"]["subject_type"] == context["subject_type"] and p["policy"].get("is_fallback")
            ]
            if fallbacks:
                # Pick fallback with highest priority
                fallbacks.sort(key=lambda x: x["policy"]["priority"], reverse=True)
                return [fallbacks[0]]
            raise ApprovalPolicyNoMatch(
                f"No active policy matched subject {context['subject_type']} in organization {context.get('organization_id')}."
            )

        # Sort non-fallback matches by priority DESC
        non_fallbacks = [m for m in matched_results if not m["is_fallback"]]
        if not non_fallbacks:
            return [matched_results[0]]

        non_fallbacks.sort(key=lambda x: x["priority"], reverse=True)
        top_priority = non_fallbacks[0]["priority"]
        highest_matches = [m for m in non_fallbacks if m["priority"] == top_priority]

        return highest_matches

    @staticmethod
    def _evaluate_conditions(conditions: list[dict[str, Any]], context: dict[str, Any]) -> bool:
        if not conditions:
            return True

        for cond in conditions:
            field = cond["field_code"]
            op = cond["operator"]
            val_data = cond["value_data"]

            context_val = context.get(field.lower())
            if context_val is None and field == "TOTAL_AMOUNT":
                context_val = context.get("amount")

            if not ApprovalPolicyMatchService._evaluate_single(field, op, val_data, context_val, context):
                return False

        return True

    @staticmethod
    def _evaluate_single(field: str, op: str, val_data: dict[str, Any], context_val: Any, context: dict[str, Any]) -> bool:
        if field == "TOTAL_AMOUNT":
            ctx_amount = Decimal(str(context_val)) if context_val is not None else Decimal("0")
            if op == "BETWEEN":
                min_v = Decimal(str(val_data.get("min", "0")))
                max_v = Decimal(str(val_data.get("max", "999999999999")))
                return min_v <= ctx_amount <= max_v
            elif op in ("GREATER_THAN_OR_EQUAL", "GTE"):
                v = Decimal(str(val_data.get("value", "0")))
                return ctx_amount >= v
            elif op in ("GREATER_THAN", "GT"):
                v = Decimal(str(val_data.get("value", "0")))
                return ctx_amount > v
            elif op in ("LESS_THAN_OR_EQUAL", "LTE"):
                v = Decimal(str(val_data.get("value", "0")))
                return ctx_amount <= v
            elif op in ("LESS_THAN", "LT"):
                v = Decimal(str(val_data.get("value", "0")))
                return ctx_amount < v
            elif op == "EQUALS":
                v = Decimal(str(val_data.get("value", "0")))
                return ctx_amount == v

        elif field == "CURRENCY_CODE":
            target = str(val_data.get("value", "")).upper()
            ctx_curr = str(context_val or "").upper()
            if op == "EQUALS":
                return ctx_curr == target
            elif op == "IN":
                allowed = [str(x).upper() for x in val_data.get("values", [])]
                return ctx_curr in allowed

        elif field == "COST_CENTER_ID":
            ctx_cc = str(context_val) if context_val else ""
            if op == "EQUALS":
                return ctx_cc == str(val_data.get("value", ""))
            elif op == "IN":
                allowed = [str(x) for x in val_data.get("values", [])]
                return ctx_cc in allowed

        elif field == "PRODUCT_CATEGORY_ID":
            ctx_cats = set(str(x) for x in (context.get("product_category_ids") or []))
            target_cats = set(str(x) for x in val_data.get("values", []))
            if op == "CONTAINS_ANY":
                return bool(ctx_cats.intersection(target_cats))
            elif op == "CONTAINS_ALL":
                return target_cats.issubset(ctx_cats)
            elif op == "IN":
                return bool(ctx_cats.intersection(target_cats))

        elif field == "BRANCH_ID":
            ctx_b = str(context_val) if context_val else ""
            if op == "EQUALS":
                return ctx_b == str(val_data.get("value", ""))

        elif field == "HAS_VARIANCES":
            return bool(context.get("has_variances")) == bool(val_data.get("value"))

        elif field == "SINGLE_SOURCE":
            return bool(context.get("single_source")) == bool(val_data.get("value"))

        # Default pass for unhandled fields if not explicitly failing
        return True
