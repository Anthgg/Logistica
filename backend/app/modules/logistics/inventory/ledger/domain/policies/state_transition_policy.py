"""Inventory state transition policy for the ledger.

Quality and availability transitions never modify total physical quantity.
The resulting movement always carries the same base quantity for the
source and destination positions. The policy only governs the legal
``(availability_state, quality_state)`` pairs.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.logistics.inventory.ledger.domain.value_objects.enums import (
    AvailabilityState,
    DamageState,
    ExpirationState,
    QualityState,
    TransitState,
)


@dataclass(frozen=True)
class StateTransition:
    availability_from: AvailabilityState
    availability_to: AvailabilityState
    quality_from: QualityState
    quality_to: QualityState
    transit_from: TransitState
    transit_to: TransitState
    damage_from: DamageState
    damage_to: DamageState
    expiration_from: ExpirationState
    expiration_to: ExpirationState
    reason_code: str
    is_quantity_preserving: bool = True


# Legal transitions (Phase 044 set). Each entry declares source and target
# state components. ``is_quantity_preserving`` must always be True for
# transitions recorded through this policy.

LEGAL_STATE_TRANSITIONS: tuple[StateTransition, ...] = (
    StateTransition(
        availability_from=AvailabilityState.PENDING_PUTAWAY,
        availability_to=AvailabilityState.AVAILABLE,
        quality_from=QualityState.QUARANTINE,
        quality_to=QualityState.APPROVED,
        transit_from=TransitState.INBOUND_STAGING,
        transit_to=TransitState.NOT_IN_TRANSIT,
        damage_from=DamageState.NORMAL,
        damage_to=DamageState.NORMAL,
        expiration_from=ExpirationState.NOT_APPLICABLE,
        expiration_to=ExpirationState.VALID,
        reason_code="QUARANTINE_RELEASE_TO_STAGING",
    ),
    StateTransition(
        availability_from=AvailabilityState.PENDING_PUTAWAY,
        availability_to=AvailabilityState.AVAILABLE,
        quality_from=QualityState.APPROVED,
        quality_to=QualityState.APPROVED,
        transit_from=TransitState.INBOUND_STAGING,
        transit_to=TransitState.NOT_IN_TRANSIT,
        damage_from=DamageState.NORMAL,
        damage_to=DamageState.NORMAL,
        expiration_from=ExpirationState.VALID,
        expiration_to=ExpirationState.VALID,
        reason_code="PUTAWAY_COMPLETED",
    ),
    StateTransition(
        availability_from=AvailabilityState.AVAILABLE,
        availability_to=AvailabilityState.RESERVED,
        quality_from=QualityState.APPROVED,
        quality_to=QualityState.APPROVED,
        transit_from=TransitState.NOT_IN_TRANSIT,
        transit_to=TransitState.NOT_IN_TRANSIT,
        damage_from=DamageState.NORMAL,
        damage_to=DamageState.NORMAL,
        expiration_from=ExpirationState.VALID,
        expiration_to=ExpirationState.VALID,
        reason_code="RESERVATION_CREATED",
    ),
    StateTransition(
        availability_from=AvailabilityState.RESERVED,
        availability_to=AvailabilityState.AVAILABLE,
        quality_from=QualityState.APPROVED,
        quality_to=QualityState.APPROVED,
        transit_from=TransitState.NOT_IN_TRANSIT,
        transit_to=TransitState.NOT_IN_TRANSIT,
        damage_from=DamageState.NORMAL,
        damage_to=DamageState.NORMAL,
        expiration_from=ExpirationState.VALID,
        expiration_to=ExpirationState.VALID,
        reason_code="RESERVATION_RELEASED",
    ),
    StateTransition(
        availability_from=AvailabilityState.RESERVED,
        availability_to=AvailabilityState.PICKED_FUTURE,
        quality_from=QualityState.APPROVED,
        quality_to=QualityState.APPROVED,
        transit_from=TransitState.NOT_IN_TRANSIT,
        transit_to=TransitState.OUTBOUND_STAGING,
        damage_from=DamageState.NORMAL,
        damage_to=DamageState.NORMAL,
        expiration_from=ExpirationState.VALID,
        expiration_to=ExpirationState.VALID,
        reason_code="RESERVATION_CONSUMED",
    ),
    StateTransition(
        availability_from=AvailabilityState.AVAILABLE,
        availability_to=AvailabilityState.BLOCKED,
        quality_from=QualityState.APPROVED,
        quality_to=QualityState.REJECTED,
        transit_from=TransitState.NOT_IN_TRANSIT,
        transit_to=TransitState.NOT_IN_TRANSIT,
        damage_from=DamageState.NORMAL,
        damage_to=DamageState.NORMAL,
        expiration_from=ExpirationState.VALID,
        expiration_to=ExpirationState.VALID,
        reason_code="QUALITY_REJECTED",
    ),
    StateTransition(
        availability_from=AvailabilityState.BLOCKED,
        availability_to=AvailabilityState.AVAILABLE,
        quality_from=QualityState.REJECTED,
        quality_to=QualityState.APPROVED,
        transit_from=TransitState.NOT_IN_TRANSIT,
        transit_to=TransitState.NOT_IN_TRANSIT,
        damage_from=DamageState.NORMAL,
        damage_to=DamageState.NORMAL,
        expiration_from=ExpirationState.VALID,
        expiration_to=ExpirationState.VALID,
        reason_code="QUALITY_BLOCKED_RELEASE",
    ),
    StateTransition(
        availability_from=AvailabilityState.AVAILABLE,
        availability_to=AvailabilityState.BLOCKED,
        quality_from=QualityState.APPROVED,
        quality_to=QualityState.DAMAGED,
        transit_from=TransitState.NOT_IN_TRANSIT,
        transit_to=TransitState.NOT_IN_TRANSIT,
        damage_from=DamageState.NORMAL,
        damage_to=DamageState.DAMAGED,
        expiration_from=ExpirationState.VALID,
        expiration_to=ExpirationState.VALID,
        reason_code="DAMAGED_APPLIED",
    ),
    StateTransition(
        availability_from=AvailabilityState.AVAILABLE,
        availability_to=AvailabilityState.BLOCKED,
        quality_from=QualityState.APPROVED,
        quality_to=QualityState.EXPIRED,
        transit_from=TransitState.NOT_IN_TRANSIT,
        transit_to=TransitState.NOT_IN_TRANSIT,
        damage_from=DamageState.NORMAL,
        damage_to=DamageState.NORMAL,
        expiration_from=ExpirationState.VALID,
        expiration_to=ExpirationState.EXPIRED,
        reason_code="EXPIRED_APPLIED",
    ),
    StateTransition(
        availability_from=AvailabilityState.AVAILABLE,
        availability_to=AvailabilityState.IN_TRANSIT,
        quality_from=QualityState.APPROVED,
        quality_to=QualityState.APPROVED,
        transit_from=TransitState.NOT_IN_TRANSIT,
        transit_to=TransitState.BETWEEN_WAREHOUSES,
        damage_from=DamageState.NORMAL,
        damage_to=DamageState.NORMAL,
        expiration_from=ExpirationState.VALID,
        expiration_to=ExpirationState.VALID,
        reason_code="TRANSIT_APPLIED",
    ),
    StateTransition(
        availability_from=AvailabilityState.IN_TRANSIT,
        availability_to=AvailabilityState.AVAILABLE,
        quality_from=QualityState.APPROVED,
        quality_to=QualityState.APPROVED,
        transit_from=TransitState.BETWEEN_WAREHOUSES,
        transit_to=TransitState.NOT_IN_TRANSIT,
        damage_from=DamageState.NORMAL,
        damage_to=DamageState.NORMAL,
        expiration_from=ExpirationState.VALID,
        expiration_to=ExpirationState.VALID,
        reason_code="TRANSIT_RELEASED",
    ),
)


def is_legal_transition(
    *,
    availability_from: str,
    availability_to: str,
    quality_from: str,
    quality_to: str,
    transit_from: str,
    transit_to: str,
    damage_from: str,
    damage_to: str,
    expiration_from: str,
    expiration_to: str,
) -> bool:
    for transition in LEGAL_STATE_TRANSITIONS:
        if (
            transition.availability_from.value == availability_from
            and transition.availability_to.value == availability_to
            and transition.quality_from.value == quality_from
            and transition.quality_to.value == quality_to
            and transition.transit_from.value == transit_from
            and transition.transit_to.value == transit_to
            and transition.damage_from.value == damage_from
            and transition.damage_to.value == damage_to
            and transition.expiration_from.value == expiration_from
            and transition.expiration_to.value == expiration_to
        ):
            return True
    return False
