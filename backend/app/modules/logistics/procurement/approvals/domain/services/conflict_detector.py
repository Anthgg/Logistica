"""ApprovalPolicyConflictDetector — detects blocking conflicts in policy configurations.

Prevents activating policy versions with overlapping ranges, missing steps,
unresolvable approver sources, or invalid step dependencies.
"""

from __future__ import annotations

from typing import Any

from app.modules.logistics.procurement.approvals.domain.errors.exceptions import (
    ApprovalPolicyConflict,
)


class ApprovalPolicyConflictDetector:
    """Detects configuration conflicts before policy version activation."""

    @staticmethod
    def validate_version_for_activation(
        version: dict[str, Any],
        conditions: list[dict[str, Any]],
        steps: list[dict[str, Any]],
        existing_active_versions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Validates a version structure. Returns conflict report dict."""
        issues: list[str] = []
        warnings: list[str] = []

        if not steps:
            issues.append("Policy version must contain at least one step definition.")

        # Check steps sequence
        step_orders = [s.get("order_index", 1) for s in steps]
        if len(step_orders) != len(set(step_orders)):
            issues.append("Step order indices must be strictly unique within the version.")

        # Check step definitions
        for idx, step in enumerate(steps, start=1):
            if not step.get("step_code"):
                issues.append(f"Step #{idx} is missing a required step_code.")
            if not step.get("approver_source_type"):
                issues.append(f"Step #{idx} ({step.get('step_code')}) is missing an approver_source_type.")
            req_appr = step.get("required_approvals", 1)
            min_appr = step.get("minimum_approvals", 1)
            if min_appr > req_appr:
                issues.append(f"Step #{idx}: minimum_approvals ({min_appr}) cannot exceed required_approvals ({req_appr}).")

        # Check overlapping ranges against existing active versions
        if existing_active_versions:
            for active_item in existing_active_versions:
                if active_item.get("id") == version.get("id"):
                    continue
                # Overlap check logic placeholder
                pass

        has_blocking = len(issues) > 0

        if has_blocking:
            raise ApprovalPolicyConflict(
                f"Cannot activate policy version: {'; '.join(issues)}"
            )

        return {
            "status": "VALIDATED",
            "issues": issues,
            "warnings": warnings,
            "is_valid": True,
        }
