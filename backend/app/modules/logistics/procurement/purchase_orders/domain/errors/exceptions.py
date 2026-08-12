"""Domain exceptions for Phase 034 — Purchase Orders."""

from __future__ import annotations


class PurchaseOrderDomainError(Exception):
    """Base class for all purchase order domain errors."""

    code: str = "PURCHASE_ORDER_ERROR"
    http_status: int = 400

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.__doc__ or self.code
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Not Found
# ---------------------------------------------------------------------------
class PurchaseOrderNotFound(PurchaseOrderDomainError):
    """The purchase order does not exist or belongs to another organization."""
    code = "PURCHASE_ORDER_NOT_FOUND"
    http_status = 404


class PurchaseOrderRevisionNotFound(PurchaseOrderDomainError):
    """The purchase order revision does not exist."""
    code = "PURCHASE_ORDER_REVISION_NOT_FOUND"
    http_status = 404


class PurchaseOrderLineNotFound(PurchaseOrderDomainError):
    """The purchase order line does not exist."""
    code = "PURCHASE_ORDER_LINE_NOT_FOUND"
    http_status = 404


# ---------------------------------------------------------------------------
# State Transitions
# ---------------------------------------------------------------------------
class PurchaseOrderStatusInvalid(PurchaseOrderDomainError):
    """The requested operation is not allowed in the current status."""
    code = "PURCHASE_ORDER_STATUS_INVALID"
    http_status = 409


class PurchaseOrderNotEditable(PurchaseOrderDomainError):
    """The purchase order revision is frozen and cannot be modified."""
    code = "PURCHASE_ORDER_NOT_EDITABLE"
    http_status = 409


class PurchaseOrderRevisionConflict(PurchaseOrderDomainError):
    """Optimistic lock conflict: row_version mismatch."""
    code = "PURCHASE_ORDER_REVISION_CONFLICT"
    http_status = 409


# ---------------------------------------------------------------------------
# Generation Plan
# ---------------------------------------------------------------------------
class PurchaseOrderGenerationPlanInvalid(PurchaseOrderDomainError):
    """The generation plan contains blocking issues and cannot be executed."""
    code = "PURCHASE_ORDER_GENERATION_PLAN_INVALID"
    http_status = 422


class PurchaseOrderSourceDecisionInvalid(PurchaseOrderDomainError):
    """The source evaluation decision is invalid or not usable."""
    code = "PURCHASE_ORDER_SOURCE_DECISION_INVALID"
    http_status = 422


class PurchaseOrderSourceDecisionNotRecorded(PurchaseOrderDomainError):
    """The source evaluation decision is not in RECORDED status."""
    code = "PURCHASE_ORDER_SOURCE_DECISION_NOT_RECORDED"
    http_status = 422


# ---------------------------------------------------------------------------
# Supplier / Product Validation
# ---------------------------------------------------------------------------
class PurchaseOrderSupplierMismatch(PurchaseOrderDomainError):
    """The supplier does not match the decision or is not eligible."""
    code = "PURCHASE_ORDER_SUPPLIER_MISMATCH"
    http_status = 422


class PurchaseOrderCurrencyMismatch(PurchaseOrderDomainError):
    """Cannot mix currencies within a purchase order."""
    code = "PURCHASE_ORDER_CURRENCY_MISMATCH"
    http_status = 422


class PurchaseOrderUnitInvalid(PurchaseOrderDomainError):
    """The unit of measure is invalid or incompatible."""
    code = "PURCHASE_ORDER_UNIT_INVALID"
    http_status = 422


# ---------------------------------------------------------------------------
# Quantity / Allocation
# ---------------------------------------------------------------------------
class PurchaseOrderAllocationConflict(PurchaseOrderDomainError):
    """Concurrency conflict in source allocation — another process allocated first."""
    code = "PURCHASE_ORDER_ALLOCATION_CONFLICT"
    http_status = 409


class PurchaseOrderQuantityExceeded(PurchaseOrderDomainError):
    """The requested quantity exceeds the adjudicated quantity in the decision."""
    code = "PURCHASE_ORDER_QUANTITY_EXCEEDED"
    http_status = 422


# ---------------------------------------------------------------------------
# Pricing / Money
# ---------------------------------------------------------------------------
class PurchaseOrderPriceVarianceRequiresApproval(PurchaseOrderDomainError):
    """A price deviation from the original proposal requires explicit approval."""
    code = "PURCHASE_ORDER_PRICE_VARIANCE_REQUIRES_APPROVAL"
    http_status = 422


class PurchaseOrderMonetaryCalculationMismatch(PurchaseOrderDomainError):
    """Recalculated totals do not match stored totals — recalculate before proceeding."""
    code = "PURCHASE_ORDER_MONETARY_CALCULATION_MISMATCH"
    http_status = 422


class PurchaseOrderTaxInvalid(PurchaseOrderDomainError):
    """A tax component is invalid."""
    code = "PURCHASE_ORDER_TAX_INVALID"
    http_status = 422


class PurchaseOrderDiscountInvalid(PurchaseOrderDomainError):
    """A discount value is invalid (negative, exceeds subtotal, etc.)."""
    code = "PURCHASE_ORDER_DISCOUNT_INVALID"
    http_status = 422


class PurchaseOrderChargeInvalid(PurchaseOrderDomainError):
    """An additional charge is invalid."""
    code = "PURCHASE_ORDER_CHARGE_INVALID"
    http_status = 422


# ---------------------------------------------------------------------------
# Offer Validity
# ---------------------------------------------------------------------------
class PurchaseOrderOfferExpired(PurchaseOrderDomainError):
    """The supplier quotation offer has expired and no ratification was registered."""
    code = "PURCHASE_ORDER_OFFER_EXPIRED"
    http_status = 422


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------
class PurchaseOrderScheduleInvalid(PurchaseOrderDomainError):
    """A delivery schedule entry is invalid."""
    code = "PURCHASE_ORDER_SCHEDULE_INVALID"
    http_status = 422


class PurchaseOrderScheduleQuantityMismatch(PurchaseOrderDomainError):
    """The sum of scheduled quantities exceeds the ordered quantity."""
    code = "PURCHASE_ORDER_SCHEDULE_QUANTITY_MISMATCH"
    http_status = 422


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------
class PurchaseOrderAttachmentInvalid(PurchaseOrderDomainError):
    """An attachment is not in AVAILABLE status or has a non-CLEAN file version."""
    code = "PURCHASE_ORDER_ATTACHMENT_INVALID"
    http_status = 422


# ---------------------------------------------------------------------------
# Approval
# ---------------------------------------------------------------------------
class PurchaseOrderApprovalRequired(PurchaseOrderDomainError):
    """The purchase order must be approved before it can be issued."""
    code = "PURCHASE_ORDER_APPROVAL_REQUIRED"
    http_status = 422


class PurchaseOrderSelfApprovalDenied(PurchaseOrderDomainError):
    """The creator of the purchase order cannot be the sole approver."""
    code = "PURCHASE_ORDER_SELF_APPROVAL_DENIED"
    http_status = 403


class PurchaseOrderAlreadyApproved(PurchaseOrderDomainError):
    """The purchase order already has an active approval decision."""
    code = "PURCHASE_ORDER_ALREADY_APPROVED"
    http_status = 409


# ---------------------------------------------------------------------------
# Issuance
# ---------------------------------------------------------------------------
class PurchaseOrderAlreadyIssued(PurchaseOrderDomainError):
    """The purchase order has already been issued."""
    code = "PURCHASE_ORDER_ALREADY_ISSUED"
    http_status = 409


class PurchaseOrderIssueFailed(PurchaseOrderDomainError):
    """The issuance process failed. Check the issuance_status for details."""
    code = "PURCHASE_ORDER_ISSUE_FAILED"
    http_status = 500


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
class PurchaseOrderDispatchNotAllowed(PurchaseOrderDomainError):
    """The purchase order cannot be dispatched in its current state."""
    code = "PURCHASE_ORDER_DISPATCH_NOT_ALLOWED"
    http_status = 422


class PurchaseOrderDeliveryFailed(PurchaseOrderDomainError):
    """The delivery attempt failed at the provider level."""
    code = "PURCHASE_ORDER_DELIVERY_FAILED"
    http_status = 502


# ---------------------------------------------------------------------------
# Acknowledgement
# ---------------------------------------------------------------------------
class PurchaseOrderAcknowledgementInvalid(PurchaseOrderDomainError):
    """The acknowledgement data is invalid."""
    code = "PURCHASE_ORDER_ACKNOWLEDGEMENT_INVALID"
    http_status = 422


# ---------------------------------------------------------------------------
# Cancellation / Amendment
# ---------------------------------------------------------------------------
class PurchaseOrderCancellationBlocked(PurchaseOrderDomainError):
    """The purchase order cannot be cancelled — dependencies must be resolved first."""
    code = "PURCHASE_ORDER_CANCELLATION_BLOCKED"
    http_status = 409


class PurchaseOrderAmendmentRequired(PurchaseOrderDomainError):
    """An issued purchase order requires an amendment, not a direct edit."""
    code = "PURCHASE_ORDER_AMENDMENT_REQUIRED"
    http_status = 409


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------
class PurchaseOrderIdempotencyConflict(PurchaseOrderDomainError):
    """Same idempotency key was submitted with a different payload."""
    code = "PURCHASE_ORDER_IDEMPOTENCY_CONFLICT"
    http_status = 409


class PurchaseOrderConcurrencyError(PurchaseOrderDomainError):
    """The purchase order was updated by another process (row_version mismatch)."""
    code = "PURCHASE_ORDER_CONCURRENCY_ERROR"
    http_status = 409

