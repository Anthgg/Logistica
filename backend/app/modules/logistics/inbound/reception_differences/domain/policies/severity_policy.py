from __future__ import annotations

from decimal import Decimal

from ..enums import DifferenceType, Severity


class ReceptionDifferenceSeverityPolicy:
    VERSION = "1"

    _SEAL_TYPES = {"SEAL_BROKEN", "SEAL_TAMPERED", "SEAL_MISSING"}
    _SAFETY_TYPES = {"CONTAMINATION_SUSPECTED", "TEMPERATURE_CONCERN", "TEMPERATURE_EXCURSION_SUSPECTED"}
    _DOCUMENT_TYPES = {"DOCUMENT_MISSING", "GUIDE_MISSING", "CERTIFICATE_MISSING"}
    _PRODUCT_DAMAGE_TYPES = {"PRODUCT_DAMAGED", "PACKAGING_DAMAGED"}

    @classmethod
    def suggest(cls, difference_type: str, *, variance_percentage: Decimal | None = None, has_damage: bool = False, has_safety_concern: bool = False, is_seal_issue: bool = False, is_document_issue: bool = False, is_expired: bool = False, is_recurring: bool = False) -> Severity:
        dt = difference_type
        if dt in cls._SAFETY_TYPES or has_safety_concern:
            return Severity.CRITICAL
        if dt in cls._SEAL_TYPES or is_seal_issue:
            return Severity.HIGH
        if is_expired:
            return Severity.HIGH
        if has_damage:
            return Severity.HIGH
        if dt == DifferenceType.WRONG_PRODUCT:
            return Severity.HIGH
        if dt in {DifferenceType.SHORTAGE, DifferenceType.OVERAGE} and variance_percentage is not None:
            if variance_percentage >= Decimal("20"):
                return Severity.HIGH
            if variance_percentage >= Decimal("5"):
                return Severity.MEDIUM
            return Severity.LOW
        if dt in cls._DOCUMENT_TYPES or is_document_issue:
            return Severity.MEDIUM
        if dt in {DifferenceType.SERIAL_DUPLICATE, DifferenceType.SERIAL_MISSING, DifferenceType.LOT_MISSING}:
            return Severity.MEDIUM
        if dt == DifferenceType.UNKNOWN_PRODUCT:
            return Severity.MEDIUM
        if is_recurring:
            return Severity.HIGH
        return Severity.LOW
