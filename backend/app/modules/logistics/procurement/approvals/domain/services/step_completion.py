"""ApprovalStepCompletionService — step completion evaluation engine.

Evaluates completion criteria (ALL, ANY_ONE, QUORUM, UNANIMOUS) and rejection policies.
"""

from __future__ import annotations

from typing import Any


class ApprovalStepCompletionService:
    """Evaluates step completion status after a new decision is recorded."""

    @staticmethod
    def evaluate_step_completion(
        completion_mode: str,
        minimum_approvals: int,
        required_approvals: int,
        decisions: list[dict[str, Any]],
        assignments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Evaluates decisions recorded for a step.

        Returns result dict:
        - is_completed: bool
        - outcome: str ("APPROVED", "REJECTED", "RETURNED", "IN_PROGRESS")
        - approved_count: int
        - rejected_count: int
        - returned_count: int
        """
        approved_decisions = [d for d in decisions if d["decision_type"] == "APPROVE"]
        rejected_decisions = [d for d in decisions if d["decision_type"] == "REJECT"]
        returned_decisions = [d for d in decisions if d["decision_type"] == "RETURN_FOR_CHANGES"]

        appr_count = len(approved_decisions)
        rej_count = len(rejected_decisions)
        ret_count = len(returned_decisions)

        # Rejection/Return takes immediate precedence
        if rej_count > 0:
            return {
                "is_completed": True,
                "outcome": "REJECTED",
                "approved_count": appr_count,
                "rejected_count": rej_count,
                "returned_count": ret_count,
            }

        if ret_count > 0:
            return {
                "is_completed": True,
                "outcome": "RETURNED",
                "approved_count": appr_count,
                "rejected_count": rej_count,
                "returned_count": ret_count,
            }

        mode = str(completion_mode).upper()

        if mode == "ANY_ONE":
            if appr_count >= 1:
                return {
                    "is_completed": True,
                    "outcome": "APPROVED",
                    "approved_count": appr_count,
                    "rejected_count": rej_count,
                    "returned_count": ret_count,
                }

        elif mode in ("ALL", "UNANIMOUS"):
            if appr_count >= required_approvals or (len(assignments) > 0 and appr_count >= len(assignments)):
                return {
                    "is_completed": True,
                    "outcome": "APPROVED",
                    "approved_count": appr_count,
                    "rejected_count": rej_count,
                    "returned_count": ret_count,
                }

        elif mode == "QUORUM":
            if appr_count >= minimum_approvals:
                return {
                    "is_completed": True,
                    "outcome": "APPROVED",
                    "approved_count": appr_count,
                    "rejected_count": rej_count,
                    "returned_count": ret_count,
                }

        return {
            "is_completed": False,
            "outcome": "IN_PROGRESS",
            "approved_count": appr_count,
            "rejected_count": rej_count,
            "returned_count": ret_count,
        }
