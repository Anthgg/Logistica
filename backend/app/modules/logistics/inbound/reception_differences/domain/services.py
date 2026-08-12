from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation

from .enums import CASE_TRANSITIONS, CaseStatus, ItemStatus
from .errors import reception_difference_error


def canonical_hash_diff(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def require_case_transition(current: str, target: str) -> None:
    try:
        allowed = CASE_TRANSITIONS[CaseStatus(current)]
        wanted = CaseStatus(target)
    except (KeyError, ValueError):
        raise reception_difference_error("RECEPTION_DIFFERENCE_CASE_STATUS_INVALID", "Estado de caso inválido.", 409)
    if wanted not in allowed:
        raise reception_difference_error("RECEPTION_DIFFERENCE_CASE_STATUS_INVALID", f"Transición {current} -> {target} no permitida.", 409)


ITEM_TRANSITIONS = {
    ItemStatus.OPEN: {ItemStatus.EVIDENCE_PENDING, ItemStatus.RESPONSIBILITY_PENDING, ItemStatus.READY_FOR_REVIEW, ItemStatus.DISMISSED_WITH_REASON, ItemStatus.CLOSED},
    ItemStatus.EVIDENCE_PENDING: {ItemStatus.OPEN, ItemStatus.READY_FOR_REVIEW, ItemStatus.CLOSED},
    ItemStatus.RESPONSIBILITY_PENDING: {ItemStatus.OPEN, ItemStatus.READY_FOR_REVIEW, ItemStatus.CLOSED},
    ItemStatus.READY_FOR_REVIEW: {ItemStatus.CONFIRMED, ItemStatus.DISMISSED_WITH_REASON, ItemStatus.FOLLOW_UP_REQUIRED},
    ItemStatus.CONFIRMED: {ItemStatus.CLOSED, ItemStatus.FOLLOW_UP_REQUIRED},
    ItemStatus.DISMISSED_WITH_REASON: set(),
    ItemStatus.DISPUTED: {ItemStatus.FOLLOW_UP_REQUIRED, ItemStatus.CLOSED},
    ItemStatus.FOLLOW_UP_REQUIRED: {ItemStatus.CLOSED},
    ItemStatus.CLOSED: set(),
    ItemStatus.SUPERSEDED: set(),
}


def require_item_transition(current: str, target: str) -> None:
    try:
        allowed = ITEM_TRANSITIONS[ItemStatus(current)]
        wanted = ItemStatus(target)
    except (KeyError, ValueError):
        raise reception_difference_error("RECEPTION_DIFFERENCE_ITEM_STATUS_INVALID", "Estado de ítem inválido.", 409)
    if wanted not in allowed:
        raise reception_difference_error("RECEPTION_DIFFERENCE_ITEM_STATUS_INVALID", f"Transición {current} -> {target} no permitida.", 409)


def strict_decimal_diff(value: str | Decimal, *, positive: bool = True) -> Decimal:
    if isinstance(value, float):
        raise reception_difference_error("RECEPTION_DIFFERENCE_QUANTITY_INVALID", "Las cantidades float no están permitidas.")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise reception_difference_error("RECEPTION_DIFFERENCE_QUANTITY_INVALID", "Cantidad decimal inválida.")
    if not result.is_finite():
        raise reception_difference_error("RECEPTION_DIFFERENCE_QUANTITY_INVALID", "La cantidad debe ser decimal y finita.")
    if positive and result <= 0:
        raise reception_difference_error("RECEPTION_DIFFERENCE_QUANTITY_INVALID", "La cantidad debe ser positiva.")
    return result


def validate_decimal_quantity(value: str | Decimal) -> Decimal:
    if isinstance(value, float):
        raise reception_difference_error("RECEPTION_DIFFERENCE_QUANTITY_INVALID", "Las cantidades float no están permitidas.")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise reception_difference_error("RECEPTION_DIFFERENCE_QUANTITY_INVALID", "Cantidad decimal inválida.")
    if not result.is_finite():
        raise reception_difference_error("RECEPTION_DIFFERENCE_QUANTITY_INVALID", "La cantidad debe ser decimal y finita.")
    return result
