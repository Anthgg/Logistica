"""ApprovalSeparationOfDutiesService — separation of duties enforcement engine.

Prevents anti-self-approval, conflict of interest, and single-user multi-level bypasses.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.modules.logistics.procurement.approvals.domain.errors.exceptions import (
    ApprovalSelfApprovalDenied,
    ApprovalSeparationOfDutiesViolation,
)


class ApprovalSeparationOfDutiesService:
    """Enforces separation of duties policies during chain compilation and decision execution."""

    @staticmethod
    def validate_decision_acting_user(
        acting_user_id: UUID | str,
        creator_user_id: UUID | str,
        requester_user_id: UUID | str,
        step_instance: dict[str, Any],
        total_steps_in_chain: int,
        previous_decisions: list[dict[str, Any]],
        sod_policy: str = "CREATOR_CANNOT_BE_SOLE_APPROVER",
        is_variance: bool = False,
        variance_requester_id: UUID | str | None = None,
    ) -> None:
        """Validates if acting_user_id is permitted to record a decision on the given step."""

        act_id_str = str(acting_user_id).lower()
        creator_id_str = str(creator_user_id).lower()
        req_id_str = str(requester_user_id).lower()

        # 1. Self-approval rule check
        if step_instance.get("distinct_from_creator", True):
            if total_steps_in_chain == 1 and act_id_str == creator_id_str:
                raise ApprovalSelfApprovalDenied(
                    "Self-approval prohibited: creator cannot be the sole approver for a 1-step approval request."
                )

        if sod_policy == "CREATOR_CANNOT_APPROVE" and act_id_str == creator_id_str:
            raise ApprovalSelfApprovalDenied(
                "Self-approval prohibited: creator is strictly barred from approving this purchase."
            )

        # 2. Requester final approver check
        is_final_step = step_instance.get("sequence_number", 1) == total_steps_in_chain
        if is_final_step and step_instance.get("distinct_from_requester", True):
            if sod_policy in ("REQUESTER_CANNOT_BE_FINAL_APPROVER", "DISTINCT_FINAL_APPROVER_REQUIRED"):
                if act_id_str == req_id_str and total_steps_in_chain > 1:
                    raise ApprovalSeparationOfDutiesViolation(
                        "Separation of duties violation: requester cannot be the final approver in a multi-level chain."
                    )

        # 3. Variance requester check
        if is_variance and variance_requester_id:
            var_req_str = str(variance_requester_id).lower()
            if act_id_str == var_req_str:
                raise ApprovalSeparationOfDutiesViolation(
                    "Separation of duties violation: the user who requested a price variance cannot approve it."
                )

        # 4. Multi-level single user check (same user cannot approve multiple mandatory levels)
        if total_steps_in_chain > 1:
            for prev_dec in previous_decisions:
                decided_by = str(prev_dec.get("decided_by_user_id") or "").lower()
                prev_step_seq = prev_dec.get("step_sequence_number", 0)
                curr_step_seq = step_instance.get("sequence_number", 1)
                if decided_by == act_id_str and prev_step_seq != curr_step_seq:
                    raise ApprovalSeparationOfDutiesViolation(
                        f"Separation of duties violation: user {acting_user_id} has already approved step #{prev_step_seq} "
                        f"and cannot approve step #{curr_step_seq}."
                    )
