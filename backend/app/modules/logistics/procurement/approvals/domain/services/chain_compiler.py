"""ApprovalChainCompiler — pure domain service compiling approval chains.

Transforms matched policy step definitions and context into an immutable
CompiledApprovalChain with a SHA-256 canonical hash.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.modules.logistics.procurement.approvals.domain.errors.exceptions import (
    ApprovalPolicyApproverUnresolved,
    ApprovalPolicyChainInvalid,
)


class ApprovalChainCompiler:
    """Compiles matched step definitions into a frozen approval chain."""

    @staticmethod
    def compile_chain(
        matched_policies: list[dict[str, Any]],
        context: dict[str, Any],
        user_resolver: Any = None,
    ) -> dict[str, Any]:
        """Compiles an immutable approval chain from matched policies and context.

        Returns compiled_chain dict containing:
        - chain_hash: SHA-256 hex string
        - policy_version_ids: list[str]
        - steps: list[dict]
        - resolved_assignments: dict[str, list[dict]]
        - compiled_at_utc: str
        """
        if not matched_policies:
            raise ApprovalPolicyChainInvalid("Cannot compile approval chain: no matched policies provided.")

        compiled_steps: list[dict[str, Any]] = []
        resolved_assignments: dict[str, list[dict[str, Any]]] = {}
        policy_version_ids: list[str] = []

        sequence_counter = 1

        for match_item in matched_policies:
            version = match_item["version"]
            steps = match_item.get("steps", [])
            version_id = str(version["id"])
            if version_id not in policy_version_ids:
                policy_version_ids.append(version_id)

            # Sort steps by order_index
            sorted_steps = sorted(steps, key=lambda s: s.get("order_index", 1))

            for s_def in sorted_steps:
                step_code = s_def["step_code"]
                step_id = str(s_def["id"])

                # Resolve initial approver candidates
                approvers = ApprovalChainCompiler._resolve_approvers(
                    s_def, context, user_resolver
                )

                if not approvers:
                    raise ApprovalPolicyApproverUnresolved(
                        f"Approver source {s_def['approver_source_type']!r} for step {step_code!r} "
                        f"could not be resolved to any active user."
                    )

                compiled_step = {
                    "step_definition_id": step_id,
                    "step_code": step_code,
                    "name": s_def["name"],
                    "sequence_number": sequence_counter,
                    "execution_mode": s_def.get("execution_mode", "SEQUENTIAL"),
                    "completion_mode": s_def.get("completion_mode", "ALL"),
                    "minimum_approvals": s_def.get("minimum_approvals", 1),
                    "required_approvals": s_def.get("required_approvals", 1),
                    "permission_required": s_def.get("permission_required", "logistics.purchase_orders.approve"),
                    "step_up_level": s_def.get("step_up_level", "HIGH"),
                    "deadline_hours": s_def.get("deadline_hours"),
                    "allow_delegation": s_def.get("allow_delegation", True),
                    "allow_abstention": s_def.get("allow_abstention", False),
                    "allow_return": s_def.get("allow_return", True),
                    "allow_request_information": s_def.get("allow_request_information", True),
                    "distinct_from_creator": s_def.get("distinct_from_creator", True),
                    "distinct_from_requester": s_def.get("distinct_from_requester", True),
                    "is_mandatory": s_def.get("is_mandatory", True),
                }

                compiled_steps.append(compiled_step)
                resolved_assignments[step_code] = approvers
                sequence_counter += 1

        if not compiled_steps:
            raise ApprovalPolicyChainInvalid("Compiled chain resulted in 0 steps.")

        # Compute SHA-256 chain hash
        chain_payload = {
            "policy_version_ids": policy_version_ids,
            "steps": compiled_steps,
            "resolved_assignments": resolved_assignments,
            "subject_type": context.get("subject_type"),
            "amount": str(context.get("amount") or context.get("total_amount")),
            "currency": context.get("currency_code"),
        }

        canonical_json = json.dumps(chain_payload, sort_keys=True, separators=(",", ":"))
        chain_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

        return {
            "chain_hash": chain_hash,
            "policy_version_ids": policy_version_ids,
            "steps": compiled_steps,
            "resolved_assignments": resolved_assignments,
            "canonical_payload": chain_payload,
        }

    @staticmethod
    def _resolve_approvers(
        step_def: dict[str, Any],
        context: dict[str, Any],
        user_resolver: Any = None,
    ) -> list[dict[str, Any]]:
        source_type = step_def["approver_source_type"]
        config = step_def.get("approver_source_config") or {}

        # 1. FIXED_USER
        if source_type == "FIXED_USER":
            user_id = config.get("user_id")
            if user_id:
                return [{
                    "user_id": str(user_id),
                    "full_name": config.get("user_name", "Fixed Approver"),
                    "source_type": "FIXED_USER",
                }]

        # 2. COST_CENTER_RESPONSIBLE
        elif source_type == "COST_CENTER_RESPONSIBLE":
            cc_snapshot = context.get("cost_center_snapshot") or {}
            resp_id = cc_snapshot.get("responsible_user_id") or config.get("fallback_user_id")
            if resp_id:
                return [{
                    "user_id": str(resp_id),
                    "full_name": cc_snapshot.get("responsible_name", "Cost Center Responsible"),
                    "source_type": "COST_CENTER_RESPONSIBLE",
                }]

        # 3. BRANCH_MANAGER
        elif source_type == "BRANCH_MANAGER":
            b_snapshot = context.get("branch_snapshot") or {}
            mgr_id = b_snapshot.get("manager_user_id") or config.get("fallback_user_id")
            if mgr_id:
                return [{
                    "user_id": str(mgr_id),
                    "full_name": b_snapshot.get("manager_name", "Branch Manager"),
                    "source_type": "BRANCH_MANAGER",
                }]

        # 4. REQUESTER_MANAGER
        elif source_type == "REQUESTER_MANAGER":
            req_snapshot = context.get("requester_snapshot") or {}
            mgr_id = req_snapshot.get("manager_user_id") or config.get("fallback_user_id")
            if mgr_id:
                return [{
                    "user_id": str(mgr_id),
                    "full_name": req_snapshot.get("manager_name", "Requester Manager"),
                    "source_type": "REQUESTER_MANAGER",
                }]

        # 5. FIXED_USER_GROUP / ROLE_SCOPE
        elif source_type in ("FIXED_USER_GROUP", "ROLE_SCOPE", "ORGANIZATION_ROLE"):
            users = config.get("users") or []
            if users:
                return [
                    {
                        "user_id": str(u["user_id"]),
                        "full_name": u.get("full_name", "Role Approver"),
                        "source_type": source_type,
                    }
                    for u in users
                ]

        # Dynamic fallback resolution via external resolver if provided
        if user_resolver:
            try:
                resolved = user_resolver(source_type, config, context)
                if resolved:
                    return resolved
            except Exception:
                pass

        # Global fallback if configured
        fb_id = config.get("fallback_user_id")
        if fb_id:
            return [{
                "user_id": str(fb_id),
                "full_name": config.get("fallback_name", "Fallback Approver"),
                "source_type": "FALLBACK_CONFIGURED",
            }]

        return []
