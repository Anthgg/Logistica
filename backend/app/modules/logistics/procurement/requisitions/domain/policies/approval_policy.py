"""Approval policy resolver for Phase 031 — SINGLE_STEP_BASIC strategy.

Extensible interface for Phase 035 multi-level approval chains.
New strategies can be injected without changing the resolver interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass
class ApprovalContext:
    """Context passed to the policy resolver for approval decisions."""

    requisition_id: UUID
    requester_user_id: UUID
    approver_user_id: UUID
    priority: str
    organization_id: UUID
    self_approval_allowed: bool = False


@dataclass
class ApprovalPolicyResult:
    """Result of a policy resolution."""

    can_approve: bool
    reason: str | None
    policy_code: str
    policy_version: str
    requires_step_up: bool
    step_up_level: str  # LOW, MEDIUM, HIGH, CRITICAL


class PurchaseApprovalPolicyResolver:
    """Strategy-pattern resolver for purchase approval policies.

    Phase 031: SINGLE_STEP_BASIC — one approver, no multi-level chains.
    Phase 035: Will inject matrix-based, hierarchical, parallel strategies
               through the same interface without changing domain code.
    """

    POLICY_CODE = "SINGLE_STEP_BASIC"
    POLICY_VERSION = "1.0.0"

    # Step-up levels by operation type
    STEP_UP_BY_PRIORITY = {
        "LOW": "HIGH",
        "NORMAL": "HIGH",
        "HIGH": "HIGH",
        "URGENT": "HIGH",
        "CRITICAL": "HIGH",
    }

    def resolve(self, ctx: ApprovalContext) -> ApprovalPolicyResult:
        """Evaluate whether the approver can approve this requisition."""

        # Self-approval check — enforced at policy level, not RBAC level
        if not ctx.self_approval_allowed and ctx.requester_user_id == ctx.approver_user_id:
            return ApprovalPolicyResult(
                can_approve=False,
                reason=(
                    "Self-approval is denied by policy SINGLE_STEP_BASIC. "
                    "The requester and approver must be different users."
                ),
                policy_code=self.POLICY_CODE,
                policy_version=self.POLICY_VERSION,
                requires_step_up=True,
                step_up_level="HIGH",
            )

        step_up_level = self.STEP_UP_BY_PRIORITY.get(ctx.priority, "HIGH")

        return ApprovalPolicyResult(
            can_approve=True,
            reason=None,
            policy_code=self.POLICY_CODE,
            policy_version=self.POLICY_VERSION,
            requires_step_up=True,
            step_up_level=step_up_level,
        )

    def resolve_rejection(self, ctx: ApprovalContext) -> ApprovalPolicyResult:
        """Evaluate whether the approver can reject this requisition."""
        return ApprovalPolicyResult(
            can_approve=True,
            reason=None,
            policy_code=self.POLICY_CODE,
            policy_version=self.POLICY_VERSION,
            requires_step_up=True,
            step_up_level="HIGH",
        )


# Singleton for application use
purchase_approval_policy = PurchaseApprovalPolicyResolver()
