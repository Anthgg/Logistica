"""ProcurementApprovalPolicyValidator — domain validator for policies, versions, and conditions."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.modules.logistics.procurement.approvals.domain.errors.exceptions import (
    ApprovalPolicyAmountRangeInvalid,
    ApprovalPolicyConditionInvalid,
)

VALID_OPERATORS = {
    "EQUALS",
    "NOT_EQUALS",
    "IN",
    "NOT_IN",
    "GREATER_THAN",
    "GREATER_THAN_OR_EQUAL",
    "LESS_THAN",
    "LESS_THAN_OR_EQUAL",
    "BETWEEN",
    "EXISTS",
    "NOT_EXISTS",
    "CONTAINS_ANY",
    "CONTAINS_ALL",
}

VALID_FIELDS = {
    "SUBJECT_TYPE",
    "TOTAL_AMOUNT",
    "CURRENCY_CODE",
    "BASE_AMOUNT",
    "BRANCH_ID",
    "COST_CENTER_ID",
    "COST_CENTER_PARENT_ID",
    "PRODUCT_CATEGORY_ID",
    "PURCHASE_TYPE",
    "PRIORITY",
    "SUPPLIER_ID",
    "SUPPLIER_RISK_LEVEL",
    "HAS_VARIANCES",
    "VARIANCE_AMOUNT",
    "SINGLE_SOURCE",
    "URGENT",
    "AMENDMENT_TYPE",
    "CREATED_BY_USER_ID",
    "REQUESTER_AREA",
}


class ProcurementApprovalPolicyValidator:
    """Validates policy conditions, operators, and monetary amounts."""

    @staticmethod
    def validate_condition(field_code: str, operator: str, value_data: dict[str, Any]) -> None:
        clean_field = str(field_code).upper().strip()
        clean_op = str(operator).upper().strip()

        if clean_field not in VALID_FIELDS:
            raise ApprovalPolicyConditionInvalid(
                f"Field code {field_code!r} is invalid. Allowed: {sorted(VALID_FIELDS)}"
            )

        if clean_op not in VALID_OPERATORS:
            raise ApprovalPolicyConditionInvalid(
                f"Operator {operator!r} is invalid. Allowed: {sorted(VALID_OPERATORS)}"
            )

        if not isinstance(value_data, dict):
            raise ApprovalPolicyConditionInvalid("value_data must be a JSON object.")

        if clean_field in ("TOTAL_AMOUNT", "BASE_AMOUNT", "VARIANCE_AMOUNT"):
            ProcurementApprovalPolicyValidator._validate_monetary_condition(clean_op, value_data)

    @staticmethod
    def _validate_monetary_condition(operator: str, value_data: dict[str, Any]) -> None:
        if operator == "BETWEEN":
            min_val = value_data.get("min")
            max_val = value_data.get("max")
            if min_val is None or max_val is None:
                raise ApprovalPolicyAmountRangeInvalid("BETWEEN condition requires 'min' and 'max' values.")
            try:
                dec_min = Decimal(str(min_val))
                dec_max = Decimal(str(max_val))
            except Exception as exc:
                raise ApprovalPolicyAmountRangeInvalid(f"Invalid monetary range string: {exc}") from exc
            if dec_min < Decimal("0") or dec_max < Decimal("0"):
                raise ApprovalPolicyAmountRangeInvalid("Monetary values cannot be negative.")
            if dec_min > dec_max:
                raise ApprovalPolicyAmountRangeInvalid(
                    f"Minimum amount ({dec_min}) cannot exceed maximum amount ({dec_max})."
                )
        elif operator in ("GREATER_THAN", "GREATER_THAN_OR_EQUAL", "LESS_THAN", "LESS_THAN_OR_EQUAL", "EQUALS"):
            val = value_data.get("value")
            if val is None:
                raise ApprovalPolicyAmountRangeInvalid(f"Operator {operator} requires a 'value' field.")
            try:
                dec_val = Decimal(str(val))
            except Exception as exc:
                raise ApprovalPolicyAmountRangeInvalid(f"Invalid monetary value string: {exc}") from exc
            if dec_val < Decimal("0"):
                raise ApprovalPolicyAmountRangeInvalid("Monetary value cannot be negative.")
