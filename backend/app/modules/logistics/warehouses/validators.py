"""Validators for Warehouse Code, Segment Format, and Restrictions (Phase 022)."""

import re
from typing import Tuple

WAREHOUSE_CODE_REGEX = re.compile(r"^[A-Z0-9]{2,20}$")
LOCATION_SEGMENT_REGEX = re.compile(r"^[A-Z0-9_-]{1,50}$")

VALID_WAREHOUSE_TYPES = {
    "GENERAL", "DISTRIBUTION_CENTER", "TRANSIT", "CROSS_DOCK",
    "COLD_STORAGE", "QUARANTINE", "RETURNS", "PROJECT", "TEMPORARY", "OTHER"
}

VALID_LOCATION_TYPES = {
    "ZONE", "AISLE", "RACK", "LEVEL", "POSITION",
    "DOCK", "STAGING", "RECEIVING", "DISPATCH", "CROSS_DOCK",
    "QUARANTINE", "RETURNS", "DAMAGED", "COLD_STORAGE",
    "BULK_STORAGE", "FLOOR_STORAGE", "VIRTUAL", "OTHER"
}

VALID_USAGE_TYPES = {
    "GENERAL_STORAGE", "RECEIVING", "STAGING", "PICKING",
    "BULK_STORAGE", "COLD_STORAGE", "QUARANTINE", "DAMAGED",
    "RETURNS", "DISPATCH", "CROSS_DOCK", "HAZARDOUS",
    "HIGH_VALUE", "VIRTUAL", "OTHER"
}

VALID_CAPACITY_TYPES = {
    "WEIGHT", "VOLUME", "PALLET_COUNT", "BOX_COUNT",
    "UNIT_COUNT", "FLOOR_AREA", "LENGTH", "CUSTOM"
}

VALID_RESTRICTION_TYPES = {
    "MAX_WEIGHT", "MAX_VOLUME", "MAX_HEIGHT",
    "TEMPERATURE_MIN", "TEMPERATURE_MAX", "HUMIDITY_MIN", "HUMIDITY_MAX",
    "HAZARDOUS_NOT_ALLOWED", "HAZARDOUS_ONLY", "FOOD_GRADE_ONLY",
    "COLD_CHAIN_ONLY", "HIGH_VALUE_ONLY", "QUARANTINE_ONLY",
    "DAMAGED_ONLY", "EXPIRATION_REQUIRED", "LOT_TRACKING_REQUIRED",
    "SERIAL_TRACKING_REQUIRED", "NO_MIXED_PRODUCTS", "NO_MIXED_LOTS",
    "PRODUCT_CATEGORY_ALLOWED", "PRODUCT_CATEGORY_DENIED",
    "MANUAL_APPROVAL_REQUIRED", "OTHER"
}


def validate_warehouse_code(code: str) -> Tuple[bool, str]:
    if not code:
        return False, "El código de almacén no puede estar vacío."
    clean = code.strip().upper()
    if not WAREHOUSE_CODE_REGEX.match(clean):
        return False, "Código de almacén inválido. Usar 2-20 letras mayúsculas ASCII o números."
    return True, clean


def validate_location_segment(segment: str) -> Tuple[bool, str]:
    if not segment:
        return False, "El segmento de ubicación no puede estar vacío."
    clean = segment.strip().upper()
    if not LOCATION_SEGMENT_REGEX.match(clean):
        return False, "Segmento de ubicación inválido. Solo caracteres ASCII A-Z, 0-9, guion o guion bajo."
    return True, clean
