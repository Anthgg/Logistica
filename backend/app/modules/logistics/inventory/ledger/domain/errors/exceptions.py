"""Phase 044 — Inventory ledger domain errors."""

from __future__ import annotations


class InventoryLedgerError(Exception):
    """Base error for the inventory ledger module."""

    code: str = "INVENTORY_LEDGER_ERROR"
    status_code: int = 400

    def __init__(self, message: str = "", *, code: str | None = None) -> None:
        super().__init__(message or self.__class__.__name__)
        if code:
            self.code = code


class InventoryMovementNotFound(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_NOT_FOUND"
    status_code = 404


class InventoryMovementAlreadyPosted(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_ALREADY_POSTED"
    status_code = 409


class InventoryMovementSourceNotFound(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_SOURCE_NOT_FOUND"
    status_code = 422


class InventoryMovementSourceDuplicated(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_SOURCE_DUPLICATED"
    status_code = 409


class InventoryMovementSourceConflict(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_SOURCE_CONFLICT"
    status_code = 409


class InventoryMovementSourceNotAuthorized(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_SOURCE_NOT_AUTHORIZED"
    status_code = 403


class InventoryMovementTypeInvalid(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_TYPE_INVALID"
    status_code = 422


class InventoryMovementLineInvalid(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_LINE_INVALID"
    status_code = 422


class InventoryMovementQuantityInvalid(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_QUANTITY_INVALID"
    status_code = 422


class InventoryMovementUnitInvalid(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_UNIT_INVALID"
    status_code = 422


class InventoryMovementConversionMissing(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_CONVERSION_MISSING"
    status_code = 422


class InventoryMovementPositionInvalid(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_POSITION_INVALID"
    status_code = 422


class InventoryMovementStateTransitionInvalid(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_STATE_TRANSITION_INVALID"
    status_code = 422


class InventoryMovementExternalBoundaryInvalid(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_EXTERNAL_BOUNDARY_INVALID"
    status_code = 422


class InventoryLedgerPartitionNotFound(InventoryLedgerError):
    code = "INVENTORY_LEDGER_PARTITION_NOT_FOUND"
    status_code = 404


class InventoryLedgerSequenceConflict(InventoryLedgerError):
    code = "INVENTORY_LEDGER_SEQUENCE_CONFLICT"
    status_code = 409


class InventoryMovementCodeConflict(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_CODE_CONFLICT"
    status_code = 409


class InventoryMovementPostingFailed(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_POSTING_FAILED"
    status_code = 422


class InventoryMovementCompensationNotAllowed(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_COMPENSATION_NOT_ALLOWED"
    status_code = 422


class InventoryMovementAlreadyCompensated(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_ALREADY_COMPENSATED"
    status_code = 409


class InventoryMovementCompensationApprovalRequired(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_COMPENSATION_APPROVAL_REQUIRED"
    status_code = 403


class InventoryLedgerIntegrityFailed(InventoryLedgerError):
    code = "INVENTORY_LEDGER_INTEGRITY_FAILED"
    status_code = 422


class InventoryLedgerCheckpointFailed(InventoryLedgerError):
    code = "INVENTORY_LEDGER_CHECKPOINT_FAILED"
    status_code = 422


class InventoryLedgerReconciliationFailed(InventoryLedgerError):
    code = "INVENTORY_LEDGER_RECONCILIATION_FAILED"
    status_code = 422


class InventoryKardexScopeAmbiguous(InventoryLedgerError):
    code = "INVENTORY_KARDEX_SCOPE_AMBIGUOUS"
    status_code = 422


class InventoryKardexUnitMismatch(InventoryLedgerError):
    code = "INVENTORY_KARDEX_UNIT_MISMATCH"
    status_code = 422


class InventoryAvailabilityProviderUnavailable(InventoryLedgerError):
    code = "INVENTORY_AVAILABILITY_PROVIDER_UNAVAILABLE"
    status_code = 503


class InventoryMovementCompensationRequestNotFound(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_COMPENSATION_REQUEST_NOT_FOUND"
    status_code = 404


class InventoryPostingRequestNotFound(InventoryLedgerError):
    code = "INVENTORY_POSTING_REQUEST_NOT_FOUND"
    status_code = 404


class InventoryMovementLineContentMismatch(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_LINE_CONTENT_MISMATCH"
    status_code = 422


class InventoryMovementProductMismatch(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_PRODUCT_MISMATCH"
    status_code = 422


class InventoryMovementOrganizationMismatch(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_ORGANIZATION_MISMATCH"
    status_code = 403


class InventoryMovementAdapterMismatch(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_ADAPTER_MISMATCH"
    status_code = 409


class InventoryMovementIdempotencyConflict(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_IDEMPOTENCY_CONFLICT"
    status_code = 409


class InventoryMovementCheckpointNotFound(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_CHECKPOINT_NOT_FOUND"
    status_code = 404


class InventoryMovementReconciliationJobNotFound(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_RECONCILIATION_JOB_NOT_FOUND"
    status_code = 404


class InventoryMovementExportNotFound(InventoryLedgerError):
    code = "INVENTORY_MOVEMENT_EXPORT_NOT_FOUND"
    status_code = 404
