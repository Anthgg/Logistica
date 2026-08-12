"""Volume calculation service using Decimal for Phase 023."""

from decimal import Decimal
from typing import Dict, Any, Optional


class ProductVolumeCalculator:
    """Calculates volumetric measure from dimensions with strict Decimal precision."""

    UNIT_CONVERSIONS_TO_M3 = {
        "M": Decimal("1.0"),
        "CM": Decimal("0.000001"),
        "MM": Decimal("0.000000001"),
    }

    @classmethod
    def calculate_volume(
        cls,
        length: Optional[Decimal],
        width: Optional[Decimal],
        height: Optional[Decimal],
        dimension_unit: Optional[str],
    ) -> Dict[str, Any]:
        """Calculates 3D volume from length, width, and height.

        Returns dict with calculated_value, calculated_unit, and warnings.
        """
        warnings = []
        if length is None or width is None or height is None:
            return {
                "calculated_value": None,
                "calculated_unit": None,
                "warnings": ["Dimensions incomplete. Cannot calculate volume."],
            }

        if length <= 0 or width <= 0 or height <= 0:
            return {
                "calculated_value": None,
                "calculated_unit": None,
                "warnings": ["Dimensions must be greater than zero."],
            }

        unit = (dimension_unit or "CM").upper()
        if unit not in cls.UNIT_CONVERSIONS_TO_M3:
            warnings.append(f"Dimension unit '{unit}' not supported for automatic volume calculation.")
            return {
                "calculated_value": None,
                "calculated_unit": None,
                "warnings": warnings,
            }

        # Calculate volume in M3
        mult = cls.UNIT_CONVERSIONS_TO_M3[unit]
        raw_val = length * width * height
        calculated_m3 = (raw_val * mult).quantize(Decimal("0.0001"))

        return {
            "calculated_value": calculated_m3,
            "calculated_unit": "M3",
            "formula_version": "v1.0.0",
            "warnings": warnings,
        }
