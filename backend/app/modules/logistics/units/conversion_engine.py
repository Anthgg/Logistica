"""Unit conversion engine with strict Decimal arithmetic for Phase 024."""

from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_FLOOR, ROUND_CEILING, ROUND_DOWN, ROUND_UP, InvalidOperation
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status


class UnitConversionEngine:
    """Core mathematical conversion engine.

    Strictly uses Python Decimal and handles rounding policies and residuals.
    """

    ROUNDING_MAP = {
        "HALF_UP": ROUND_HALF_UP,
        "HALF_EVEN": ROUND_HALF_EVEN,
        "FLOOR": ROUND_FLOOR,
        "CEILING": ROUND_CEILING,
        "DOWN": ROUND_DOWN,
        "UP": ROUND_UP,
    }

    @classmethod
    def apply_rounding(
        cls,
        value: Decimal,
        precision: int = 4,
        policy: str = "HALF_UP",
    ) -> Tuple[Decimal, bool]:
        """Applies explicit rounding policy to Decimal value.

        Returns (rounded_value, rounding_applied_flag).
        """
        if policy == "NONE":
            return value, False

        q_str = "0." + "0" * precision if precision > 0 else "0"
        target_exp = Decimal(q_str)

        if policy == "EXACT_REQUIRED":
            quantized = value.quantize(target_exp)
            if quantized != value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Exact conversion required. Loss of precision detected ({value} vs {quantized}).",
                )
            return value, False

        py_rounding = cls.ROUNDING_MAP.get(policy, ROUND_HALF_UP)
        rounded = value.quantize(target_exp, rounding=py_rounding)
        rounding_applied = rounded != value
        return rounded, rounding_applied

    @classmethod
    def convert(
        cls,
        quantity: Decimal,
        source_code: str,
        target_code: str,
        effective_factor: Decimal,
        path: List[str],
        precision: int = 4,
        rounding_policy: str = "HALF_UP",
        integer_only_target: bool = False,
    ) -> Dict[str, Any]:
        """Performs exact Decimal conversion."""
        if quantity < Decimal("0"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity cannot be negative.")

        exact_res = (quantity * effective_factor).quantize(Decimal("0.000000000000000001"))

        if integer_only_target:
            rounded_res, _ = cls.apply_rounding(exact_res, precision=0, policy="FLOOR")
            residual = exact_res - rounded_res
        else:
            rounded_res, _ = cls.apply_rounding(exact_res, precision=precision, policy=rounding_policy)
            residual = exact_res - rounded_res

        return {
            "input_quantity": str(quantity),
            "input_unit": source_code,
            "exact_result": str(exact_res),
            "rounded_result": str(rounded_res),
            "target_unit": target_code,
            "effective_factor": str(effective_factor),
            "conversion_path": path,
            "rounding_applied": rounded_res != exact_res,
            "residual": str(residual) if residual != Decimal("0") else "0",
            "engine_version": "1.0.0",
        }
