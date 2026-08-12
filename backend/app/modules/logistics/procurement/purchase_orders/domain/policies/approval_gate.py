"""PurchaseOrderApprovalGate — policy interface and transitional implementation.

The approval gate is decoupled from the PO service via an interface.
The TransitionalSingleStepPurchaseOrderApprovalPolicy is enabled by the
PURCHASE_ORDER_TRANSITIONAL_APPROVAL_ENABLED feature flag and will be
replaced by the full multi-step policy in Phase 035.

Security:
- Self-approval is prohibited by default (creator != approver).
- Step-up authentication CRITICAL is required for approval decisions.
- Rejected and returned POs require a mandatory reason (≥20 chars).
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from app.modules.logistics.procurement.purchase_orders.domain.errors.exceptions import (
    PurchaseOrderApprovalRequired,
    PurchaseOrderSelfApprovalDenied,
    PurchaseOrderAlreadyApproved,
    PurchaseOrderStatusInvalid,
)


# ---------------------------------------------------------------------------
# Approval Result
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ApprovalRequirement:
    """Resolved approval requirements for a purchase order."""
    policy_code: str
    policy_version: str
    requires_step_up: bool
    step_up_factor: str | None       # "COMBINED_FACE_PAD" | "FACE" | etc.
    min_approvers: int
    allow_self_approval: bool
    required_reason_min_chars: int
    description: str


@dataclass(frozen=True)
class ApprovalDecisionResult:
    """Result of submitting an approval decision."""
    decision_id: UUID | None
    decision_type: str               # APPROVE | REJECT | RETURN_FOR_CHANGES
    policy_code: str
    policy_version: str
    is_final: bool
    new_approval_status: str          # APPROVED | REJECTED | RETURNED | PENDING
    new_po_status: str               # APPROVED | REJECTED | RETURNED_FOR_CHANGES | PENDING_APPROVAL


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
class PurchaseOrderApprovalGate(ABC):
    """Abstract interface for purchase order approval policy."""

    @abstractmethod
    def resolve_requirements(self, po_status: str, grand_total_str: str) -> ApprovalRequirement:
        """Return the approval requirements for the given PO context."""
        ...

    @abstractmethod
    def submit_for_approval(
        self,
        purchase_order_id: UUID,
        revision_id: UUID,
        submitter_user_id: UUID,
        creator_user_id: UUID,
        current_approval_status: str,
        current_po_status: str,
    ) -> str:
        """Submit the PO for approval. Returns the new approval_status."""
        ...

    @abstractmethod
    def approve(
        self,
        purchase_order_id: UUID,
        revision_id: UUID,
        approver_user_id: UUID,
        creator_user_id: UUID,
        current_approval_status: str,
        reason: str | None,
    ) -> ApprovalDecisionResult:
        """Record an APPROVE decision."""
        ...

    @abstractmethod
    def reject(
        self,
        purchase_order_id: UUID,
        revision_id: UUID,
        approver_user_id: UUID,
        creator_user_id: UUID,
        current_approval_status: str,
        reason: str,
    ) -> ApprovalDecisionResult:
        """Record a REJECT decision."""
        ...

    @abstractmethod
    def return_for_changes(
        self,
        purchase_order_id: UUID,
        revision_id: UUID,
        approver_user_id: UUID,
        creator_user_id: UUID,
        current_approval_status: str,
        reason: str,
    ) -> ApprovalDecisionResult:
        """Record a RETURN_FOR_CHANGES decision."""
        ...


# ---------------------------------------------------------------------------
# Transitional Implementation (Phase 034)
# ---------------------------------------------------------------------------
_POLICY_CODE = "TRANSITIONAL_SINGLE_STEP_PO_APPROVAL"
_POLICY_VERSION = "1.0.0"
_FEATURE_FLAG_ENV = "PURCHASE_ORDER_TRANSITIONAL_APPROVAL_ENABLED"


class TransitionalSingleStepPurchaseOrderApprovalPolicy(PurchaseOrderApprovalGate):
    """Single-step, self-approval-prohibited approval policy.

    Enabled when PURCHASE_ORDER_TRANSITIONAL_APPROVAL_ENABLED=true.
    Requirements:
    - One approver.
    - Approver ≠ creator (self-approval denied).
    - Step-up COMBINED_FACE_PAD required for approval.
    - Rejection and return require reason ≥ 20 chars.

    This policy will be SUPERSEDED by Phase 035's full multi-step policy.
    """

    # The approval statuses recognized by this policy
    _SUBMITTABLE_PO_STATUSES = frozenset({"DRAFT", "VALIDATED", "RETURNED_FOR_CHANGES"})
    _APPROVABLE_APPROVAL_STATUSES = frozenset({"PENDING"})
    _REJECTABLE_APPROVAL_STATUSES = frozenset({"PENDING"})
    _RETURNABLE_APPROVAL_STATUSES = frozenset({"PENDING"})

    def __init__(self, allow_self_approval_override: bool = False) -> None:
        """
        Args:
            allow_self_approval_override: If True, self-approval is allowed.
                Only for test environments. Never set in production.
        """
        if not self._is_enabled():
            raise RuntimeError(
                f"TransitionalSingleStepPurchaseOrderApprovalPolicy is disabled. "
                f"Set {_FEATURE_FLAG_ENV}=true to enable."
            )
        self._allow_self_approval_override = allow_self_approval_override

    @staticmethod
    def _is_enabled() -> bool:
        return os.getenv(_FEATURE_FLAG_ENV, "false").lower() in ("true", "1", "yes")

    def resolve_requirements(self, po_status: str, grand_total_str: str) -> ApprovalRequirement:
        return ApprovalRequirement(
            policy_code=_POLICY_CODE,
            policy_version=_POLICY_VERSION,
            requires_step_up=True,
            step_up_factor="COMBINED_FACE_PAD",
            min_approvers=1,
            allow_self_approval=self._allow_self_approval_override,
            required_reason_min_chars=20,
            description=(
                "Single-step transitional PO approval. "
                "Requires Step-Up COMBINED_FACE_PAD. Creator may not be sole approver."
            ),
        )

    def submit_for_approval(
        self,
        purchase_order_id: UUID,
        revision_id: UUID,
        submitter_user_id: UUID,
        creator_user_id: UUID,
        current_approval_status: str,
        current_po_status: str,
    ) -> str:
        if current_po_status not in self._SUBMITTABLE_PO_STATUSES:
            raise PurchaseOrderStatusInvalid(
                f"Cannot submit for approval: PO is in status {current_po_status!r}. "
                f"Allowed: {sorted(self._SUBMITTABLE_PO_STATUSES)}."
            )
        if current_approval_status not in ("NOT_SUBMITTED", "RETURNED", "SUPERSEDED"):
            raise PurchaseOrderAlreadyApproved(
                f"Cannot submit for approval: approval_status is already {current_approval_status!r}."
            )
        return "PENDING"

    def approve(
        self,
        purchase_order_id: UUID,
        revision_id: UUID,
        approver_user_id: UUID,
        creator_user_id: UUID,
        current_approval_status: str,
        reason: str | None,
    ) -> ApprovalDecisionResult:
        self._assert_approval_status(current_approval_status, self._APPROVABLE_APPROVAL_STATUSES, "approve")
        self._check_self_approval(approver_user_id, creator_user_id)

        return ApprovalDecisionResult(
            decision_id=None,  # Will be assigned by the repository
            decision_type="APPROVE",
            policy_code=_POLICY_CODE,
            policy_version=_POLICY_VERSION,
            is_final=True,
            new_approval_status="APPROVED",
            new_po_status="APPROVED",
        )

    def reject(
        self,
        purchase_order_id: UUID,
        revision_id: UUID,
        approver_user_id: UUID,
        creator_user_id: UUID,
        current_approval_status: str,
        reason: str,
    ) -> ApprovalDecisionResult:
        self._assert_approval_status(current_approval_status, self._REJECTABLE_APPROVAL_STATUSES, "reject")
        self._check_self_approval(approver_user_id, creator_user_id)
        self._require_reason(reason, min_chars=20)

        return ApprovalDecisionResult(
            decision_id=None,
            decision_type="REJECT",
            policy_code=_POLICY_CODE,
            policy_version=_POLICY_VERSION,
            is_final=True,
            new_approval_status="REJECTED",
            new_po_status="PENDING_APPROVAL",
        )

    def return_for_changes(
        self,
        purchase_order_id: UUID,
        revision_id: UUID,
        approver_user_id: UUID,
        creator_user_id: UUID,
        current_approval_status: str,
        reason: str,
    ) -> ApprovalDecisionResult:
        self._assert_approval_status(current_approval_status, self._RETURNABLE_APPROVAL_STATUSES, "return")
        self._check_self_approval(approver_user_id, creator_user_id)
        self._require_reason(reason, min_chars=20)

        return ApprovalDecisionResult(
            decision_id=None,
            decision_type="RETURN_FOR_CHANGES",
            policy_code=_POLICY_CODE,
            policy_version=_POLICY_VERSION,
            is_final=False,
            new_approval_status="RETURNED",
            new_po_status="RETURNED_FOR_CHANGES",
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_self_approval(self, approver_user_id: UUID, creator_user_id: UUID) -> None:
        if not self._allow_self_approval_override and approver_user_id == creator_user_id:
            raise PurchaseOrderSelfApprovalDenied(
                "The creator of a purchase order cannot be its approver."
            )

    @staticmethod
    def _assert_approval_status(
        current: str,
        allowed: frozenset[str],
        action: str,
    ) -> None:
        if current not in allowed:
            raise PurchaseOrderStatusInvalid(
                f"Cannot {action}: approval_status is {current!r}. "
                f"Allowed: {sorted(allowed)}."
            )

    @staticmethod
    def _require_reason(reason: str, min_chars: int) -> None:
        if not reason or len(reason.strip()) < min_chars:
            raise PurchaseOrderApprovalRequired(
                f"A reason of at least {min_chars} characters is required. "
                f"Provided {len(reason or '')} chars."
            )


def get_approval_policy(
    allow_self_approval_override: bool = False,
) -> PurchaseOrderApprovalGate:
    """Factory function — returns the appropriate approval policy.

    By default in Phase 035, returns Phase035PurchaseOrderApprovalAdapter.
    If FEATURE_FLAG_ENV is explicitly set to true, returns the transitional policy for rollback compatibility.
    """
    if os.getenv(_FEATURE_FLAG_ENV, "false").lower() in ("true", "1", "yes"):
        return TransitionalSingleStepPurchaseOrderApprovalPolicy(
            allow_self_approval_override=allow_self_approval_override,
        )
    return Phase035PurchaseOrderApprovalAdapter(
        allow_self_approval_override=allow_self_approval_override,
    )


class Phase035PurchaseOrderApprovalAdapter(PurchaseOrderApprovalGate):
    """Phase 035 adapter delegating PO approvals to ProcurementApprovalEngine."""

    def __init__(self, allow_self_approval_override: bool = False) -> None:
        self._allow_self_approval_override = allow_self_approval_override

    def resolve_requirements(self, po_status: str, grand_total_str: str) -> ApprovalRequirement:
        return ApprovalRequirement(
            policy_code="PROCUREMENT_APPROVAL_ENGINE_035",
            policy_version="1.0.0",
            requires_step_up=True,
            step_up_factor="COMBINED_FACE_PAD",
            min_approvers=1,
            allow_self_approval=self._allow_self_approval_override,
            required_reason_min_chars=20,
            description=(
                "Phase 035 Configurable Multi-Step Procurement Approval Engine. "
                "Requires Step-Up COMBINED_FACE_PAD. Creator may not be sole approver."
            ),
        )

    def submit_for_approval(
        self,
        purchase_order_id: UUID,
        revision_id: UUID,
        submitter_user_id: UUID,
        creator_user_id: UUID,
        current_approval_status: str,
        current_po_status: str,
    ) -> str:
        if current_po_status not in ("DRAFT", "VALIDATED", "RETURNED_FOR_CHANGES"):
            raise PurchaseOrderStatusInvalid(
                f"Cannot submit for approval: PO is in status {current_po_status!r}."
            )
        if current_approval_status not in ("NOT_SUBMITTED", "RETURNED", "SUPERSEDED"):
            raise PurchaseOrderAlreadyApproved(
                f"Cannot submit for approval: approval_status is already {current_approval_status!r}."
            )
        return "PENDING"

    def approve(
        self,
        purchase_order_id: UUID,
        revision_id: UUID,
        approver_user_id: UUID,
        creator_user_id: UUID,
        current_approval_status: str,
        reason: str | None,
    ) -> ApprovalDecisionResult:
        if current_approval_status != "PENDING":
            raise PurchaseOrderStatusInvalid(
                f"Cannot approve: approval_status is {current_approval_status!r}. Allowed: ['PENDING']."
            )
        if not self._allow_self_approval_override and approver_user_id == creator_user_id:
            raise PurchaseOrderSelfApprovalDenied(
                "The creator of a purchase order cannot be its approver."
            )
        return ApprovalDecisionResult(
            decision_id=None,
            decision_type="APPROVE",
            policy_code="PROCUREMENT_APPROVAL_ENGINE_035",
            policy_version="1.0.0",
            is_final=True,
            new_approval_status="APPROVED",
            new_po_status="APPROVED",
        )

    def reject(
        self,
        purchase_order_id: UUID,
        revision_id: UUID,
        approver_user_id: UUID,
        creator_user_id: UUID,
        current_approval_status: str,
        reason: str,
    ) -> ApprovalDecisionResult:
        if current_approval_status != "PENDING":
            raise PurchaseOrderStatusInvalid(f"Cannot reject: approval_status is {current_approval_status!r}.")
        if not self._allow_self_approval_override and approver_user_id == creator_user_id:
            raise PurchaseOrderSelfApprovalDenied("The creator of a purchase order cannot be its approver.")
        if not reason or len(reason.strip()) < 20:
            raise PurchaseOrderApprovalRequired("A reason of at least 20 characters is required.")

        return ApprovalDecisionResult(
            decision_id=None,
            decision_type="REJECT",
            policy_code="PROCUREMENT_APPROVAL_ENGINE_035",
            policy_version="1.0.0",
            is_final=True,
            new_approval_status="REJECTED",
            new_po_status="PENDING_APPROVAL",
        )

    def return_for_changes(
        self,
        purchase_order_id: UUID,
        revision_id: UUID,
        approver_user_id: UUID,
        creator_user_id: UUID,
        current_approval_status: str,
        reason: str,
    ) -> ApprovalDecisionResult:
        if current_approval_status != "PENDING":
            raise PurchaseOrderStatusInvalid(f"Cannot return: approval_status is {current_approval_status!r}.")
        if not self._allow_self_approval_override and approver_user_id == creator_user_id:
            raise PurchaseOrderSelfApprovalDenied("The creator of a purchase order cannot be its approver.")
        if not reason or len(reason.strip()) < 20:
            raise PurchaseOrderApprovalRequired("A reason of at least 20 characters is required.")

        return ApprovalDecisionResult(
            decision_id=None,
            decision_type="RETURN_FOR_CHANGES",
            policy_code="PROCUREMENT_APPROVAL_ENGINE_035",
            policy_version="1.0.0",
            is_final=False,
            new_approval_status="RETURNED",
            new_po_status="RETURNED_FOR_CHANGES",
        )

