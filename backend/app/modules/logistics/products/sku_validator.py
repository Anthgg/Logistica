"""SKU normalization and validation service for Phase 023."""

import re
from typing import Tuple


class ProductSKUValidator:
    """Validates and normalizes Product SKUs according to Phase 023 rules."""

    MIN_LENGTH = 2
    MAX_LENGTH = 50
    ALLOWED_PATTERN = re.compile(r"^[A-Z0-9_\-]+$")

    @classmethod
    def normalize(cls, raw_sku: str) -> str:
        if not raw_sku:
            return ""
        # Strip outer spaces and convert to uppercase
        s = raw_sku.strip().upper()
        # Replace spaces inside with hyphens
        s = re.sub(r"\s+", "-", s)
        return s

    @classmethod
    def validate(cls, raw_sku: str) -> Tuple[bool, str, str]:
        """Validates raw SKU.

        Returns: (is_valid, normalized_sku, error_message)
        """
        if not raw_sku or not raw_sku.strip():
            return False, "", "SKU cannot be empty."

        normalized = cls.normalize(raw_sku)

        if len(normalized) < cls.MIN_LENGTH:
            return False, normalized, f"SKU must be at least {cls.MIN_LENGTH} characters."

        if len(normalized) > cls.MAX_LENGTH:
            return False, normalized, f"SKU cannot exceed {cls.MAX_LENGTH} characters."

        if ".." in normalized or "/" in normalized or "\\" in normalized:
            return False, normalized, "SKU cannot contain path traversal or slashes ('..', '/', '\\')."

        if not cls.ALLOWED_PATTERN.match(normalized):
            return False, normalized, "SKU can only contain ASCII uppercase letters, numbers, hyphens, and underscores."

        return True, normalized, ""
