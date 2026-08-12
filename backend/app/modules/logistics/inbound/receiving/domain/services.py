from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .enums import ParseStatus, RECEIPT_TRANSITIONS, ReceiptStatus
from .errors import receiving_error


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def require_receipt_transition(current: str, target: str) -> None:
    try:
        allowed = RECEIPT_TRANSITIONS[ReceiptStatus(current)]
        wanted = ReceiptStatus(target)
    except (KeyError, ValueError):
        raise receiving_error("INBOUND_RECEIPT_STATUS_INVALID", "Estado de recepción inválido.", 409)
    if wanted not in allowed:
        raise receiving_error("INBOUND_RECEIPT_STATUS_INVALID", f"Transición {current} -> {target} no permitida.", 409)


def strict_decimal(value: str | Decimal, *, positive: bool = True) -> Decimal:
    if isinstance(value, float):
        raise receiving_error("INBOUND_RECEIPT_QUANTITY_INVALID", "Las cantidades float no están permitidas.")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise receiving_error("INBOUND_RECEIPT_QUANTITY_INVALID", "Cantidad decimal inválida.")
    if not result.is_finite() or (positive and result <= 0):
        raise receiving_error("INBOUND_RECEIPT_QUANTITY_INVALID", "La cantidad debe ser decimal, finita y positiva.")
    return result


@dataclass(frozen=True)
class ParsedCode:
    normalized_code: str
    symbology: str
    parser_code: str
    parser_version: str
    parse_status: str
    elements: dict[str, str]


class BarcodeParserRegistry:
    """Deterministic local parsers. QR values are data only; URLs are never opened."""

    MAX_LENGTH = 512
    CONTROL = re.compile(r"[\x00-\x1f\x7f]")

    @classmethod
    def parse(cls, raw_code: str, symbology: str | None = None) -> ParsedCode:
        if not raw_code:
            return ParsedCode("", symbology or "UNKNOWN", "EMPTY", "1", ParseStatus.EMPTY, {})
        if len(raw_code) > cls.MAX_LENGTH:
            return ParsedCode("", symbology or "UNKNOWN", "LENGTH_GUARD", "1", ParseStatus.TOO_LONG, {})
        if cls.CONTROL.search(raw_code):
            return ParsedCode("", symbology or "UNKNOWN", "CONTROL_GUARD", "1", ParseStatus.INVALID_FORMAT, {})
        value = raw_code.strip()
        kind = (symbology or cls._detect(value)).upper()
        if kind in {"EAN8", "EAN13", "UPC_A"} and not cls._valid_gtin(value):
            return ParsedCode(value, kind, "GTIN", "1", ParseStatus.INVALID_FORMAT, {})
        elements = cls._parse_gs1(value) if kind in {"GS1_128", "GS1_DATAMATRIX"} else {"identifier": value}
        status = ParseStatus.PARSED if elements else ParseStatus.PARTIALLY_PARSED
        return ParsedCode(value, kind, kind, "1", status, elements)

    @staticmethod
    def _detect(value: str) -> str:
        if value.startswith("]C1") or value.startswith("01") and len(value) >= 16:
            return "GS1_128"
        if value.isdigit() and len(value) == 8:
            return "EAN8"
        if value.isdigit() and len(value) == 12:
            return "UPC_A"
        if value.isdigit() and len(value) == 13:
            return "EAN13"
        if value.startswith(("SKU:", "INT:")):
            return "INTERNAL_SKU"
        if value.startswith("{"):
            return "QR_INTERNAL"
        return "CODE128"

    @staticmethod
    def _valid_gtin(value: str) -> bool:
        if not value.isdigit() or len(value) not in {8, 12, 13, 14}:
            return False
        digits = [int(x) for x in value]
        total = sum(n * (3 if index % 2 == 0 else 1) for index, n in enumerate(reversed(digits[:-1])))
        return (10 - total % 10) % 10 == digits[-1]

    @staticmethod
    def _parse_gs1(value: str) -> dict[str, str]:
        clean = value.removeprefix("]C1")
        result: dict[str, str] = {}
        if clean.startswith("01") and len(clean) >= 16:
            result["gtin"] = clean[2:16]
        for ai, key, width in (("17", "expiration", 6), ("11", "manufacturing", 6)):
            match = re.search(ai + r"(\d{" + str(width) + r"})", clean)
            if match:
                result[key] = match.group(1)
        for ai, key in (("10", "lot"), ("21", "serial")):
            match = re.search(ai + r"([^\x1d]{1,40})", clean)
            if match:
                result[key] = match.group(1)
        return result
