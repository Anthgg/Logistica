"""Phase 044 — Inventory ledger enums, families, types and state catalogues."""

from __future__ import annotations

from enum import StrEnum


# ---------------------------------------------------------------------------
# Movement lifecycle
# ---------------------------------------------------------------------------

class MovementStatus(StrEnum):
    POSTED = "POSTED"
    COMPENSATED = "COMPENSATED"
    PARTIALLY_COMPENSATED = "PARTIALLY_COMPENSATED"
    INTEGRITY_FAILED = "INTEGRITY_FAILED"
    SUPERSEDED_BY_MIGRATION = "SUPERSEDED_BY_MIGRATION"


# ---------------------------------------------------------------------------
# Movement families
# ---------------------------------------------------------------------------

class MovementFamily(StrEnum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"
    INTERNAL_TRANSFER = "INTERNAL_TRANSFER"
    AVAILABILITY_TRANSITION = "AVAILABILITY_TRANSITION"
    QUALITY_TRANSITION = "QUALITY_TRANSITION"
    RESERVATION = "RESERVATION"
    ADJUSTMENT = "ADJUSTMENT"
    COUNT_VARIANCE = "COUNT_VARIANCE"
    WAREHOUSE_TRANSFER = "WAREHOUSE_TRANSFER"
    RETURN = "RETURN"
    COMPENSATION = "COMPENSATION"
    MIGRATION = "MIGRATION"
    SYSTEM_CORRECTION = "SYSTEM_CORRECTION"


# ---------------------------------------------------------------------------
# Movement types
# ---------------------------------------------------------------------------

class MovementType(StrEnum):
    # Ingresos
    INBOUND_RECEIPT_RECOGNIZED = "INBOUND_RECEIPT_RECOGNIZED"
    QUARANTINE_ENTRY = "QUARANTINE_ENTRY"
    QUALITY_RELEASE_TO_STAGING = "QUALITY_RELEASE_TO_STAGING"
    PUTAWAY_COMPLETED = "PUTAWAY_COMPLETED"
    TRANSFER_RECEIPT_FUTURE = "TRANSFER_RECEIPT_FUTURE"
    CUSTOMER_RETURN_RECEIPT_FUTURE = "CUSTOMER_RETURN_RECEIPT_FUTURE"
    MIGRATION_OPENING_ENTRY = "MIGRATION_OPENING_ENTRY"

    # Salidas
    OUTBOUND_PICK_ISSUE_FUTURE = "OUTBOUND_PICK_ISSUE_FUTURE"
    OUTBOUND_DISPATCH_FUTURE = "OUTBOUND_DISPATCH_FUTURE"
    TRANSFER_DISPATCH_FUTURE = "TRANSFER_DISPATCH_FUTURE"
    SUPPLIER_RETURN_FUTURE = "SUPPLIER_RETURN_FUTURE"
    DESTRUCTION_FUTURE = "DESTRUCTION_FUTURE"
    MIGRATION_OPENING_EXIT = "MIGRATION_OPENING_EXIT"

    # Traslados
    LOCATION_TRANSFER = "LOCATION_TRANSFER"
    STAGING_TO_STORAGE = "STAGING_TO_STORAGE"
    STORAGE_TO_STAGING_FUTURE = "STORAGE_TO_STAGING_FUTURE"
    WAREHOUSE_TRANSFER_IN_TRANSIT_FUTURE = "WAREHOUSE_TRANSFER_IN_TRANSIT_FUTURE"

    # Reservas
    RESERVATION_CREATED = "RESERVATION_CREATED"
    RESERVATION_RELEASED = "RESERVATION_RELEASED"
    RESERVATION_CONSUMED = "RESERVATION_CONSUMED"
    RESERVATION_EXPIRED = "RESERVATION_EXPIRED"

    # Calidad y estado
    QUARANTINE_APPLIED = "QUARANTINE_APPLIED"
    QUARANTINE_RELEASED = "QUARANTINE_RELEASED"
    QUALITY_BLOCKED = "QUALITY_BLOCKED"
    QUALITY_APPROVED = "QUALITY_APPROVED"
    DAMAGED_APPLIED = "DAMAGED_APPLIED"
    DAMAGED_RELEASED = "DAMAGED_RELEASED"
    EXPIRED_APPLIED = "EXPIRED_APPLIED"
    EXPIRATION_CORRECTED = "EXPIRATION_CORRECTED"
    TRANSIT_APPLIED = "TRANSIT_APPLIED"
    TRANSIT_RELEASED = "TRANSIT_RELEASED"

    # Ajustes futuros
    ADJUSTMENT_INCREASE_FUTURE = "ADJUSTMENT_INCREASE_FUTURE"
    ADJUSTMENT_DECREASE_FUTURE = "ADJUSTMENT_DECREASE_FUTURE"
    COUNT_VARIANCE_INCREASE_FUTURE = "COUNT_VARIANCE_INCREASE_FUTURE"
    COUNT_VARIANCE_DECREASE_FUTURE = "COUNT_VARIANCE_DECREASE_FUTURE"

    # Correcciones
    TECHNICAL_COMPENSATION = "TECHNICAL_COMPENSATION"
    SOURCE_EVENT_REPLAY_CORRECTION = "SOURCE_EVENT_REPLAY_CORRECTION"
    MIGRATION_CORRECTION = "MIGRATION_CORRECTION"


# Movement family inferred from type
MOVEMENT_TYPE_FAMILY: dict[str, str] = {
    MovementType.INBOUND_RECEIPT_RECOGNIZED: MovementFamily.INBOUND,
    MovementType.QUARANTINE_ENTRY: MovementFamily.INBOUND,
    MovementType.QUALITY_RELEASE_TO_STAGING: MovementFamily.INBOUND,
    MovementType.PUTAWAY_COMPLETED: MovementFamily.INBOUND,
    MovementType.TRANSFER_RECEIPT_FUTURE: MovementFamily.WAREHOUSE_TRANSFER,
    MovementType.CUSTOMER_RETURN_RECEIPT_FUTURE: MovementFamily.RETURN,
    MovementType.MIGRATION_OPENING_ENTRY: MovementFamily.MIGRATION,
    MovementType.OUTBOUND_PICK_ISSUE_FUTURE: MovementFamily.OUTBOUND,
    MovementType.OUTBOUND_DISPATCH_FUTURE: MovementFamily.OUTBOUND,
    MovementType.TRANSFER_DISPATCH_FUTURE: MovementFamily.WAREHOUSE_TRANSFER,
    MovementType.SUPPLIER_RETURN_FUTURE: MovementFamily.RETURN,
    MovementType.DESTRUCTION_FUTURE: MovementFamily.OUTBOUND,
    MovementType.MIGRATION_OPENING_EXIT: MovementFamily.MIGRATION,
    MovementType.LOCATION_TRANSFER: MovementFamily.INTERNAL_TRANSFER,
    MovementType.STAGING_TO_STORAGE: MovementFamily.INTERNAL_TRANSFER,
    MovementType.STORAGE_TO_STAGING_FUTURE: MovementFamily.INTERNAL_TRANSFER,
    MovementType.WAREHOUSE_TRANSFER_IN_TRANSIT_FUTURE: MovementFamily.WAREHOUSE_TRANSFER,
    MovementType.RESERVATION_CREATED: MovementFamily.RESERVATION,
    MovementType.RESERVATION_RELEASED: MovementFamily.RESERVATION,
    MovementType.RESERVATION_CONSUMED: MovementFamily.RESERVATION,
    MovementType.RESERVATION_EXPIRED: MovementFamily.RESERVATION,
    MovementType.QUARANTINE_APPLIED: MovementFamily.QUALITY_TRANSITION,
    MovementType.QUARANTINE_RELEASED: MovementFamily.QUALITY_TRANSITION,
    MovementType.QUALITY_BLOCKED: MovementFamily.QUALITY_TRANSITION,
    MovementType.QUALITY_APPROVED: MovementFamily.QUALITY_TRANSITION,
    MovementType.DAMAGED_APPLIED: MovementFamily.QUALITY_TRANSITION,
    MovementType.DAMAGED_RELEASED: MovementFamily.QUALITY_TRANSITION,
    MovementType.EXPIRED_APPLIED: MovementFamily.QUALITY_TRANSITION,
    MovementType.EXPIRATION_CORRECTED: MovementFamily.QUALITY_TRANSITION,
    MovementType.TRANSIT_APPLIED: MovementFamily.AVAILABILITY_TRANSITION,
    MovementType.TRANSIT_RELEASED: MovementFamily.AVAILABILITY_TRANSITION,
    MovementType.ADJUSTMENT_INCREASE_FUTURE: MovementFamily.ADJUSTMENT,
    MovementType.ADJUSTMENT_DECREASE_FUTURE: MovementFamily.ADJUSTMENT,
    MovementType.COUNT_VARIANCE_INCREASE_FUTURE: MovementFamily.COUNT_VARIANCE,
    MovementType.COUNT_VARIANCE_DECREASE_FUTURE: MovementFamily.COUNT_VARIANCE,
    MovementType.TECHNICAL_COMPENSATION: MovementFamily.COMPENSATION,
    MovementType.SOURCE_EVENT_REPLAY_CORRECTION: MovementFamily.SYSTEM_CORRECTION,
    MovementType.MIGRATION_CORRECTION: MovementFamily.SYSTEM_CORRECTION,
}


# Types whose adapters are still disabled in this phase (FUTURE).
DISABLED_MOVEMENT_TYPES: frozenset[str] = frozenset(
    {
        MovementType.TRANSFER_RECEIPT_FUTURE,
        MovementType.CUSTOMER_RETURN_RECEIPT_FUTURE,
        MovementType.OUTBOUND_PICK_ISSUE_FUTURE,
        MovementType.OUTBOUND_DISPATCH_FUTURE,
        MovementType.TRANSFER_DISPATCH_FUTURE,
        MovementType.SUPPLIER_RETURN_FUTURE,
        MovementType.DESTRUCTION_FUTURE,
        MovementType.STORAGE_TO_STAGING_FUTURE,
        MovementType.WAREHOUSE_TRANSFER_IN_TRANSIT_FUTURE,
        MovementType.ADJUSTMENT_INCREASE_FUTURE,
        MovementType.ADJUSTMENT_DECREASE_FUTURE,
        MovementType.COUNT_VARIANCE_INCREASE_FUTURE,
        MovementType.COUNT_VARIANCE_DECREASE_FUTURE,
    }
)


# ---------------------------------------------------------------------------
# Posting request lifecycle
# ---------------------------------------------------------------------------

class PostingRequestStatus(StrEnum):
    RECEIVED = "RECEIVED"
    VALIDATING = "VALIDATING"
    VALID = "VALID"
    POSTING = "POSTING"
    POSTED = "POSTED"
    DUPLICATE = "DUPLICATE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# ---------------------------------------------------------------------------
# Quantity direction (informational, line-level)
# ---------------------------------------------------------------------------

class QuantityDirection(StrEnum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    TRANSFER = "TRANSFER"
    STATE_CHANGE = "STATE_CHANGE"
    RESERVATION_CHANGE = "RESERVATION_CHANGE"
    COMPENSATION = "COMPENSATION"


# ---------------------------------------------------------------------------
# Position dimension states
# ---------------------------------------------------------------------------

class BoundaryType(StrEnum):
    INTERNAL_LOCATION = "INTERNAL_LOCATION"
    INTERNAL_STAGING = "INTERNAL_STAGING"
    INTERNAL_QUARANTINE = "INTERNAL_QUARANTINE"
    INTERNAL_TRANSIT = "INTERNAL_TRANSIT"
    EXTERNAL_SUPPLIER = "EXTERNAL_SUPPLIER"
    EXTERNAL_CUSTOMER = "EXTERNAL_CUSTOMER"
    EXTERNAL_CARRIER = "EXTERNAL_CARRIER"
    EXTERNAL_UNKNOWN = "EXTERNAL_UNKNOWN"
    SYSTEM_OPENING_BALANCE = "SYSTEM_OPENING_BALANCE"
    SYSTEM_COMPENSATION = "SYSTEM_COMPENSATION"


class AvailabilityState(StrEnum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    BLOCKED = "BLOCKED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    PENDING_PUTAWAY = "PENDING_PUTAWAY"
    PICKED_FUTURE = "PICKED_FUTURE"
    DISPATCHED_FUTURE = "DISPATCHED_FUTURE"
    IN_TRANSIT = "IN_TRANSIT"
    UNKNOWN = "UNKNOWN"


class QualityState(StrEnum):
    NOT_ASSESSED = "NOT_ASSESSED"
    QUARANTINE = "QUARANTINE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DAMAGED = "DAMAGED"
    EXPIRED = "EXPIRED"
    CONDITIONAL = "CONDITIONAL"
    UNKNOWN = "UNKNOWN"


class TransitState(StrEnum):
    NOT_IN_TRANSIT = "NOT_IN_TRANSIT"
    INBOUND_STAGING = "INBOUND_STAGING"
    INTERNAL_TRANSFER = "INTERNAL_TRANSFER"
    BETWEEN_WAREHOUSES = "BETWEEN_WAREHOUSES"
    OUTBOUND_STAGING = "OUTBOUND_STAGING"
    EXTERNAL_TRANSIT = "EXTERNAL_TRANSIT"


class DamageState(StrEnum):
    NORMAL = "NORMAL"
    DAMAGED = "DAMAGED"
    SUSPECTED_DAMAGE = "SUSPECTED_DAMAGE"
    REWORK_FUTURE = "REWORK_FUTURE"
    UNKNOWN = "UNKNOWN"


class ExpirationState(StrEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    VALID = "VALID"
    NEAR_EXPIRATION = "NEAR_EXPIRATION"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# External boundary catalogue
# ---------------------------------------------------------------------------

class ExternalBoundaryKind(StrEnum):
    SUPPLIER = "SUPPLIER"
    CUSTOMER = "CUSTOMER"
    CARRIER = "CARRIER"
    OUTSIDE_WAREHOUSE = "OUTSIDE_WAREHOUSE"
    OPENING_BALANCE = "OPENING_BALANCE"
    TECHNICAL_COMPENSATION = "TECHNICAL_COMPENSATION"
    UNKNOWN_EXTERNAL = "UNKNOWN_EXTERNAL"


# ---------------------------------------------------------------------------
# Compensation request lifecycle
# ---------------------------------------------------------------------------

class CompensationRequestStatus(StrEnum):
    REQUESTED = "REQUESTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"


# ---------------------------------------------------------------------------
# Reconciliation and verification
# ---------------------------------------------------------------------------

class ReconciliationResult(StrEnum):
    RECONCILED = "RECONCILED"
    SOURCE_EVENT_MISSING_MOVEMENT = "SOURCE_EVENT_MISSING_MOVEMENT"
    MOVEMENT_WITHOUT_SOURCE = "MOVEMENT_WITHOUT_SOURCE"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    DUPLICATE_SOURCE = "DUPLICATE_SOURCE"
    HASH_MISMATCH = "HASH_MISMATCH"
    ADAPTER_VERSION_MISMATCH = "ADAPTER_VERSION_MISMATCH"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class CheckpointStatus(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    INCOMPLETE = "INCOMPLETE"
    VERIFYING = "VERIFYING"
    FAILED = "FAILED"


class VerificationStatus(StrEnum):
    OK = "OK"
    HASH_MISMATCH = "HASH_MISMATCH"
    GAPS_DETECTED = "GAPS_DETECTED"
    INVALID = "INVALID"


# ---------------------------------------------------------------------------
# Kardex technical scope
# ---------------------------------------------------------------------------

class RunningDataQuality(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    AMBIGUOUS_SCOPE = "AMBIGUOUS_SCOPE"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    NOT_APPLICABLE = "NOT_APPLICABLE"


# ---------------------------------------------------------------------------
# Step-up
# ---------------------------------------------------------------------------

class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ---------------------------------------------------------------------------
# Source adapter registry
# ---------------------------------------------------------------------------

class SourceAdapterName(StrEnum):
    QUALITY_QUARANTINE_APPLIED = "QUALITY_QUARANTINE_APPLIED"
    QUALITY_APPROVED = "QUALITY_APPROVED"
    QUARANTINE_RELEASED = "QUARANTINE_RELEASED"
    QUALITY_REJECTED = "QUALITY_REJECTED"
    DISPOSITION_SPLIT = "DISPOSITION_SPLIT"
    PUTAWAY_COMPLETED = "PUTAWAY_COMPLETED"
    ADJUSTMENT_APPROVED = "ADJUSTMENT_APPROVED"
    PHYSICAL_COUNT_VARIANCE_APPROVED = "PHYSICAL_COUNT_VARIANCE_APPROVED"
    TRANSFER_DISPATCHED = "TRANSFER_DISPATCHED"
    TRANSFER_RECEIVED = "TRANSFER_RECEIVED"
    RESERVATION_CREATED = "RESERVATION_CREATED"
    RESERVATION_RELEASED = "RESERVATION_RELEASED"
    OUTBOUND_PICK_CONFIRMED = "OUTBOUND_PICK_CONFIRMED"
    OUTBOUND_DISPATCH_CONFIRMED = "OUTBOUND_DISPATCH_CONFIRMED"
    RETURN_RECEIVED = "RETURN_RECEIVED"


ENABLED_ADAPTERS: frozenset[str] = frozenset(
    {
        SourceAdapterName.QUALITY_QUARANTINE_APPLIED,
        SourceAdapterName.QUALITY_APPROVED,
        SourceAdapterName.QUARANTINE_RELEASED,
        SourceAdapterName.QUALITY_REJECTED,
        SourceAdapterName.DISPOSITION_SPLIT,
        SourceAdapterName.PUTAWAY_COMPLETED,
    }
)


ADAPTER_VERSION: str = "1.0.0"
CANONICALIZATION_VERSION: str = "1.0.0"
SCHEMA_VERSION: str = "1.0.0"
HASH_ALGORITHM: str = "sha256"


# Mapping source adapter name -> movement type produced.
ADAPTER_TO_MOVEMENT_TYPE: dict[str, str] = {
    SourceAdapterName.QUALITY_QUARANTINE_APPLIED: MovementType.QUARANTINE_APPLIED,
    SourceAdapterName.QUALITY_APPROVED: MovementType.QUALITY_RELEASE_TO_STAGING,
    SourceAdapterName.QUARANTINE_RELEASED: MovementType.QUARANTINE_RELEASED,
    SourceAdapterName.QUALITY_REJECTED: MovementType.QUALITY_BLOCKED,
    SourceAdapterName.DISPOSITION_SPLIT: MovementType.QUALITY_RELEASE_TO_STAGING,
    SourceAdapterName.PUTAWAY_COMPLETED: MovementType.PUTAWAY_COMPLETED,
}
