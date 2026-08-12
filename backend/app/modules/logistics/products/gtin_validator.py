"""GTIN and barcode validation and internal generation for Phase 023."""

import re
from typing import Tuple, Dict, Any


class ProductIdentifierValidator:
    """Validates GTIN/EAN/UPC barcodes using Modulo 10 check digit algorithm."""

    GTIN_LENGTHS = {
        "GTIN_8": 8,
        "EAN_8": 8,
        "GTIN_12": 12,
        "UPC_A": 12,
        "GTIN_13": 13,
        "EAN_13": 13,
        "GTIN_14": 14,
    }

    @classmethod
    def calculate_check_digit(cls, number_str: str) -> int:
        """Calculates Modulo 10 check digit for GTIN/EAN/UPC."""
        digits = [int(d) for d in number_str]
        total = 0
        reverse_digits = digits[::-1]
        for idx, digit in enumerate(reverse_digits):
            weight = 3 if idx % 2 == 0 else 1
            total += digit * weight
        remainder = total % 10
        return 0 if remainder == 0 else 10 - remainder

    @classmethod
    def validate_gtin(cls, identifier_type: str, value: str) -> Tuple[bool, str, str, str]:
        """Validates GTIN value.

        Returns: (is_valid, normalized_val, verified_status, error_msg)
        """
        if not value:
            return False, "", "INVALID", "Barcode value cannot be empty."

        normalized = value.strip().upper()

        if identifier_type == "INTERNAL_BARCODE":
            if not re.match(r"^[A-Z0-9_\-]+$", normalized):
                return False, normalized, "INVALID", "Internal barcode must contain valid ASCII characters."
            return True, normalized, "FORMAT_VALID", ""

        if identifier_type in cls.GTIN_LENGTHS:
            expected_len = cls.GTIN_LENGTHS[identifier_type]
            clean_digits = re.sub(r"\D", "", normalized)
            if len(clean_digits) != expected_len:
                return False, normalized, "INVALID", f"{identifier_type} must be exactly {expected_len} digits."

            payload_digits = clean_digits[:-1]
            provided_check = int(clean_digits[-1])
            calc_check = cls.calculate_check_digit(payload_digits)

            if provided_check != calc_check:
                return False, clean_digits, "INVALID", f"Invalid check digit. Expected {calc_check}, got {provided_check}."

            return True, clean_digits, "CHECK_DIGIT_VALID", ""

        # Other types
        return True, normalized, "FORMAT_VALID", ""

    @classmethod
    def generate_internal_barcode(cls, product_id_hex: str) -> str:
        """Generates internal opaque barcode in format T1P-{ref}-{checksum}."""
        ref = product_id_hex[:8].upper()
        checksum = cls.calculate_check_digit(str(sum(ord(c) for c in ref)))
        return f"T1P-{ref}-{checksum}"
