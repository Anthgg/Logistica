"""ProcurementApprovalEngine — application service orchestrating procurement approvals.

Handles policy versioning, deterministic matching, chain compilation, step instance lifecycle,
decision recording, separation of duties, delegations, escalations, outbox events,
and audit seal generation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.modules.logistics.procurement.approvals.domain.entities.subject_registry import (
    ApprovalSubjectRegistry,
)
from app.modules.logistics.procurement.approvals.domain.errors.exceptions import (
    ApprovalAssignmentNotAuthorized,
    ApprovalAssignmentNotFound,
    ApprovalDecisionAlreadyRecorded,
    ApprovalPolicyNotFound,
    ApprovalPolicyVersionNotFound,
    ApprovalRequestAlreadyCompleted,
    ApprovalRequestNotFound,
    ApprovalRequestStatusInvalid,
    ProcurementApprovalDomainError,
)
from app.modules.logistics.procurement.approvals.domain.services.audit_seal_service import (
    ApprovalAuditSealService,
    ApprovalIntegrityService,
)
from app.modules.logistics.procurement.approvals.domain.services.chain_compiler import (
    ApprovalChainCompiler,
)
from app.modules.logistics.procurement.approvals.domain.services.conflict_detector import (
    ApprovalPolicyConflictDetector,
)
from app.modules.logistics.procurement.approvals.domain.services.match_service import (
    ApprovalPolicyMatchService,
)
from app.modules.logistics.procurement.approvals.domain.services.separation_of_duties import (
    ApprovalSeparationOfDutiesService,
)
from app.modules.logistics.procurement.approvals.domain.services.step_completion import (
    ApprovalStepCompletionService,
)
from app.modules.logistics.procurement.approvals.domain.services.validator import (
    ProcurementApprovalPolicyValidator,
)
from app.modules.logistics.procurement.approvals.infrastructure.persistence.models import (
    ApprovalAssignmentModel,
    ApprovalAuditSealModel,
    ApprovalDecisionModel,
    ApprovalDelegationModel,
    ApprovalIntegrityEventModel,
    ApprovalPolicyConditionModel,
    ApprovalPolicyStepDefinitionModel,
    ApprovalStepInstanceModel,
    ProcurementApprovalPolicyModel,
    ProcurementApprovalPolicyVersionModel,
    ProcurementApprovalRequestModel,
)


class ProcurementApprovalEngine:
    """Core application engine for procurement approvals."""

    def __init__(self, db_session: Any) -> None:
        self.db = db_session

    # ---------------------------------------------------------------------------
    # Policy Management
    # ---------------------------------------------------------------------------
    def create_policy(
        self,
        organization_id: UUID | str,
        code: str,
        name: str,
        subject_type: str,
        created_by: UUID | str,
        description: str | None = None,
        priority: int = 100,
        effective_scope: str = "ORGANIZATION",
        is_fallback: bool = False,
    ) -> ProcurementApprovalPolicyModel:
        """Create a new policy aggregate root."""
        subj_def = ApprovalSubjectRegistry.get(subject_type)
        norm_code = str(code).upper().strip()

        policy = ProcurementApprovalPolicyModel(
            id=uuid.uuid4(),
            organization_id=UUID(str(organization_id)),
            code=code.strip(),
            normalized_code=norm_code,
            name=name.strip(),
            description=description,
            subject_type=subj_def.code,
            priority=priority,
            status="DRAFT",
            effective_scope=effective_scope,
            is_fallback=is_fallback,
            created_by=UUID(str(created_by)),
        )
        self.db.add(policy)

        # Create initial draft version 1
        version = ProcurementApprovalPolicyVersionModel(
            id=uuid.uuid4(),
            policy_id=policy.id,
            version_number=1,
            status="DRAFT",
            compiler_version="1.0.0",
            created_by=UUID(str(created_by)),
        )
        self.db.add(version)
        self.db.flush()
        return policy

    def create_policy_version(
        self,
        policy_id: UUID | str,
        created_by: UUID | str,
    ) -> ProcurementApprovalPolicyVersionModel:
        """Create a new draft version from an existing policy."""
        policy = self.db.query(ProcurementApprovalPolicyModel).filter_by(id=UUID(str(policy_id))).first()
        if not policy:
            raise ApprovalPolicyNotFound("Policy not found.")

        last_v = (
            self.db.query(ProcurementApprovalPolicyVersionModel)
            .filter_by(policy_id=policy.id)
            .order_by(ProcurementApprovalPolicyVersionModel.version_number.desc())
            .first()
        )
        new_v_num = (last_v.version_number + 1) if last_v else 1

        version = ProcurementApprovalPolicyVersionModel(
            id=uuid.uuid4(),
            policy_id=policy.id,
            version_number=new_v_num,
            status="DRAFT",
            compiler_version="1.0.0",
            created_by=UUID(str(created_by)),
        )
        self.db.add(version)
        self.db.flush()
        return version

    def add_condition(
        self,
        version_id: UUID | str,
        field_code: str,
        operator: str,
        value_data: dict[str, Any],
        condition_group: str = "ALL",
        order_index: int = 1,
    ) -> ApprovalPolicyConditionModel:
        """Add a condition parameter to a draft version."""
        v = self.db.query(ProcurementApprovalPolicyVersionModel).filter_by(id=UUID(str(version_id))).first()
        if not v or v.status in ("ACTIVE", "RETIRED", "ARCHIVED"):
            raise ProcurementApprovalDomainError("Cannot modify non-draft policy version.")

        ProcurementApprovalPolicyValidator.validate_condition(field_code, operator, value_data)

        cond = ApprovalPolicyConditionModel(
            id=uuid.uuid4(),
            policy_version_id=v.id,
            condition_group=condition_group.upper(),
            field_code=field_code.upper().strip(),
            operator=operator.upper().strip(),
            value_type="JSON",
            value_data=value_data,
            order_index=order_index,
        )
        self.db.add(cond)
        self.db.flush()
        return cond

    def add_step_definition(
        self,
        version_id: UUID | str,
        step_code: str,
        name: str,
        approver_source_type: str,
        approver_source_config: dict[str, Any],
        order_index: int = 1,
        execution_mode: str = "SEQUENTIAL",
        completion_mode: str = "ALL",
        minimum_approvals: int = 1,
        required_approvals: int = 1,
        step_up_level: str = "HIGH",
        distinct_from_creator: bool = True,
    ) -> ApprovalPolicyStepDefinitionModel:
        """Add a step definition to a draft version."""
        v = self.db.query(ProcurementApprovalPolicyVersionModel).filter_by(id=UUID(str(version_id))).first()
        if not v or v.status in ("ACTIVE", "RETIRED", "ARCHIVED"):
            raise ProcurementApprovalDomainError("Cannot modify non-draft policy version.")

        step = ApprovalPolicyStepDefinitionModel(
            id=uuid.uuid4(),
            policy_version_id=v.id,
            step_code=step_code.strip(),
            name=name.strip(),
            order_index=order_index,
            execution_mode=execution_mode.upper(),
            completion_mode=completion_mode.upper(),
            minimum_approvals=minimum_approvals,
            required_approvals=required_approvals,
            approver_source_type=approver_source_type.upper().strip(),
            approver_source_config=approver_source_config,
            permission_required="logistics.purchase_orders.approve",
            step_up_level=step_up_level.upper(),
            distinct_from_creator=distinct_from_creator,
        )
        self.db.add(step)
        self.db.flush()
        return step

    def activate_policy_version(
        self,
        version_id: UUID | str,
        activated_by: UUID | str,
    ) -> ProcurementApprovalPolicyVersionModel:
        """Validate and activate a policy version."""
        v = self.db.query(ProcurementApprovalPolicyVersionModel).filter_by(id=UUID(str(version_id))).first()
        if not v:
            raise ApprovalPolicyVersionNotFound("Version not found.")

        policy = self.db.query(ProcurementApprovalPolicyModel).filter_by(id=v.policy_id).first()
        conditions = self.db.query(ApprovalPolicyConditionModel).filter_by(policy_version_id=v.id).all()
        steps = self.db.query(ApprovalPolicyStepDefinitionModel).filter_by(policy_version_id=v.id).all()

        # Conflict check
        v_dict = {"id": str(v.id), "policy_id": str(v.policy_id)}
        conds_list = [{"field_code": c.field_code, "operator": c.operator, "value_data": c.value_data} for c in conditions]
        steps_list = [
            {
                "step_code": s.step_code,
                "order_index": s.order_index,
                "approver_source_type": s.approver_source_type,
                "minimum_approvals": s.minimum_approvals,
                "required_approvals": s.required_approvals,
            }
            for s in steps
        ]

        ApprovalPolicyConflictDetector.validate_version_for_activation(v_dict, conds_list, steps_list)

        # Retire old active version if any
        old_active = (
            self.db.query(ProcurementApprovalPolicyVersionModel)
            .filter_by(policy_id=v.policy_id, status="ACTIVE")
            .all()
        )
        for old in old_active:
            old.status = "RETIRED"
            old.retired_by = UUID(str(activated_by))
            old.retired_at = datetime.now(timezone.utc)

        v.status = "ACTIVE"
        v.activated_by = UUID(str(activated_by))
        v.activated_at = datetime.now(timezone.utc)

        policy.status = "ACTIVE"
        policy.active_version_id = v.id

        self.db.flush()
        return v

    # ---------------------------------------------------------------------------
    # Request Lifecycle & Submissions
    # ---------------------------------------------------------------------------
    def submit_for_approval(
        self,
        organization_id: UUID | str,
        subject_type: str,
        subject_id: UUID | str,
        subject_revision_id: UUID | str | None,
        subject_code: str | None,
        subject_snapshot: dict[str, Any],
        amount: Decimal | str,
        currency_code: str,
        creator_user_id: UUID | str,
        requester_user_id: UUID | str,
        submitted_by: UUID | str,
        cost_center_snapshot: dict[str, Any] | None = None,
        category_snapshots: list[dict[str, Any]] | None = None,
        branch_snapshot: dict[str, Any] | None = None,
    ) -> ProcurementApprovalRequestModel:
        """Submits a purchasing resource for approval, compiling the chain."""

        subj_def = ApprovalSubjectRegistry.get(subject_type)
        dec_amount = Decimal(str(amount))
        org_uuid = UUID(str(organization_id))
        subj_uuid = UUID(str(subject_id))

        # Check existing active request for same revision
        if subject_revision_id:
            existing = (
                self.db.query(ProcurementApprovalRequestModel)
                .filter_by(
                    organization_id=org_uuid,
                    subject_type=subj_def.code,
                    subject_id=subj_uuid,
                    subject_revision_id=UUID(str(subject_revision_id)),
                    status="IN_PROGRESS",
                )
                .first()
            )
            if existing:
                return existing

        # Fetch active policies for organization
        active_policies = (
            self.db.query(ProcurementApprovalPolicyModel)
            .filter_by(organization_id=org_uuid, status="ACTIVE", subject_type=subj_def.code)
            .all()
        )

        p_list: list[dict[str, Any]] = []
        for pol in active_policies:
            if not pol.active_version_id:
                continue
            ver = self.db.query(ProcurementApprovalPolicyVersionModel).filter_by(id=pol.active_version_id).first()
            if not ver:
                continue
            conds = self.db.query(ApprovalPolicyConditionModel).filter_by(policy_version_id=ver.id).all()
            steps = self.db.query(ApprovalPolicyStepDefinitionModel).filter_by(policy_version_id=ver.id).all()

            p_list.append({
                "policy": {"id": str(pol.id), "subject_type": pol.subject_type, "priority": pol.priority, "is_fallback": pol.is_fallback},
                "version": {"id": str(ver.id), "version_number": ver.version_number},
                "conditions": [{"field_code": c.field_code, "operator": c.operator, "value_data": c.value_data} for c in conds],
                "steps": [
                    {
                        "id": str(s.id),
                        "step_code": s.step_code,
                        "name": s.name,
                        "order_index": s.order_index,
                        "execution_mode": s.execution_mode,
                        "completion_mode": s.completion_mode,
                        "minimum_approvals": s.minimum_approvals,
                        "required_approvals": s.required_approvals,
                        "approver_source_type": s.approver_source_type,
                        "approver_source_config": s.approver_source_config,
                        "permission_required": s.permission_required,
                        "step_up_level": s.step_up_level,
                        "allow_delegation": s.allow_delegation,
                        "distinct_from_creator": s.distinct_from_creator,
                    }
                    for s in steps
                ],
            })

        cat_ids = [str(c.get("id")) for c in (category_snapshots or []) if c.get("id")]
        ctx = {
            "subject_type": subj_def.code,
            "organization_id": str(org_uuid),
            "amount": dec_amount,
            "total_amount": dec_amount,
            "currency_code": str(currency_code).upper(),
            "cost_center_id": str(cost_center_snapshot.get("id")) if cost_center_snapshot else None,
            "branch_id": str(branch_snapshot.get("id")) if branch_snapshot else None,
            "product_category_ids": cat_ids,
            "cost_center_snapshot": cost_center_snapshot,
            "branch_snapshot": branch_snapshot,
            "requester_snapshot": {"user_id": str(requester_user_id), "full_name": "Requester"},
        }

        matched = ApprovalPolicyMatchService.match_policies(p_list, ctx)
        compiled = ApprovalChainCompiler.compile_chain(matched, ctx)

        req_id = uuid.uuid4()
        req_code = f"APRQ-{datetime.now(timezone.utc).year}-{str(req_id.int)[:6]}"

        req = ProcurementApprovalRequestModel(
            id=req_id,
            organization_id=org_uuid,
            request_code=req_code,
            subject_type=subj_def.code,
            subject_id=subj_uuid,
            subject_revision_id=UUID(str(subject_revision_id)) if subject_revision_id else None,
            subject_code=subject_code,
            subject_snapshot=subject_snapshot,
            subject_snapshot_hash=compiled["chain_hash"],
            policy_resolution_snapshot={"matched_policy_ids": [m["policy"]["id"] for m in matched]},
            compiled_chain=compiled["canonical_payload"],
            chain_hash=compiled["chain_hash"],
            status="IN_PROGRESS",
            current_sequence=1,
            amount=dec_amount,
            currency_code=str(currency_code).upper(),
            cost_center_snapshot=cost_center_snapshot,
            category_snapshots=category_snapshots,
            branch_snapshot=branch_snapshot,
            requester_user_id=UUID(str(requester_user_id)),
            requester_snapshot={"user_id": str(requester_user_id)},
            creator_user_id=UUID(str(creator_user_id)),
            creator_snapshot={"user_id": str(creator_user_id)},
            submitted_by=UUID(str(submitted_by)),
        )
        self.db.add(req)

        # Instantiate StepInstances and Assignments
        for c_step in compiled["steps"]:
            step_inst = ApprovalStepInstanceModel(
                id=uuid.uuid4(),
                approval_request_id=req.id,
                step_definition_id=UUID(c_step["step_definition_id"]),
                step_code=c_step["step_code"],
                name_snapshot=c_step["name"],
                sequence_number=c_step["sequence_number"],
                execution_mode=c_step["execution_mode"],
                completion_mode=c_step["completion_mode"],
                minimum_approvals=c_step["minimum_approvals"],
                required_approvals=c_step["required_approvals"],
                status="ACTIVE" if c_step["sequence_number"] == 1 else "PENDING",
                activated_at=datetime.now(timezone.utc) if c_step["sequence_number"] == 1 else None,
            )
            self.db.add(step_inst)

            # Create assignments
            approvers = compiled["resolved_assignments"].get(c_step["step_code"], [])
            for app_user in approvers:
                assign = ApprovalAssignmentModel(
                    id=uuid.uuid4(),
                    approval_request_id=req.id,
                    step_instance_id=step_inst.id,
                    original_approver_user_id=UUID(app_user["user_id"]),
                    effective_approver_user_id=UUID(app_user["user_id"]),
                    approver_snapshot=app_user,
                    assignment_source_type=app_user["source_type"],
                    status="ASSIGNED",
                )
                self.db.add(assign)

        # First integrity log entry
        p_hash, e_hash = ApprovalIntegrityService.compute_event_hash(
            sequence_number=1,
            event_type="REQUEST_CREATED",
            actor_reference=str(submitted_by),
            payload={"request_id": str(req.id), "amount": str(dec_amount)},
        )
        ev_log = ApprovalIntegrityEventModel(
            id=uuid.uuid4(),
            approval_request_id=req.id,
            sequence_number=1,
            event_type="REQUEST_CREATED",
            actor_reference=str(submitted_by),
            payload_hash=p_hash,
            event_hash=e_hash,
        )
        self.db.add(ev_log)

        self.db.flush()
        return req

    # ---------------------------------------------------------------------------
    # Decision Recording & State Machine Transitions
    # ---------------------------------------------------------------------------
    def record_decision(
        self,
        assignment_id: UUID | str,
        acting_user_id: UUID | str,
        decision_type: str,
        reason: str | None = None,
        conditions: dict[str, Any] | None = None,
        step_up_assurance_level: str = "HIGH",
    ) -> ApprovalDecisionModel:
        """Records an append-only approval decision."""

        clean_decision = str(decision_type).upper().strip()
        if clean_decision not in ("APPROVE", "REJECT", "RETURN_FOR_CHANGES", "ABSTAIN"):
            raise ProcurementApprovalDomainError(f"Decision type {decision_type!r} is invalid.")

        assign = self.db.query(ApprovalAssignmentModel).filter_by(id=UUID(str(assignment_id))).first()
        if not assign or assign.status not in ("ASSIGNED", "VIEWED"):
            raise ApprovalAssignmentNotFound("Assignment not found or not active.")

        if str(assign.effective_approver_user_id) != str(acting_user_id):
            raise ApprovalAssignmentNotAuthorized("Acting user does not match the assigned effective approver.")

        req = self.db.query(ProcurementApprovalRequestModel).filter_by(id=assign.approval_request_id).first()
        if not req or req.status != "IN_PROGRESS":
            raise ApprovalRequestStatusInvalid("Approval request is not in progress.")

        step_inst = self.db.query(ApprovalStepInstanceModel).filter_by(id=assign.step_instance_id).first()
        if not step_inst or step_inst.status != "ACTIVE":
            raise ApprovalRequestStatusInvalid("Approval step is not currently active.")

        # Fetch previous decisions for SoD check
        prev_decs = (
            self.db.query(ApprovalDecisionModel)
            .filter_by(approval_request_id=req.id)
            .all()
        )
        prev_list = [
            {"decided_by_user_id": str(d.decided_by_user_id), "step_sequence_number": 1}
            for d in prev_decs
        ]

        # SoD Verification
        total_steps = self.db.query(ApprovalStepInstanceModel).filter_by(approval_request_id=req.id).count()
        step_dict = {
            "sequence_number": step_inst.sequence_number,
            "distinct_from_creator": True,
            "distinct_from_requester": True,
        }
        ApprovalSeparationOfDutiesService.validate_decision_acting_user(
            acting_user_id=acting_user_id,
            creator_user_id=req.creator_user_id,
            requester_user_id=req.requester_user_id,
            step_instance=step_dict,
            total_steps_in_chain=total_steps,
            previous_decisions=prev_list,
        )

        dec_id = uuid.uuid4()
        req_hash = req.chain_hash
        step_hash = step_inst.step_code

        # Hash computation
        dec_payload = {
            "assignment_id": str(assign.id),
            "decision_type": clean_decision,
            "decided_by": str(acting_user_id),
            "reason": reason,
        }
        p_hash, d_hash = ApprovalIntegrityService.compute_event_hash(
            sequence_number=len(prev_decs) + 2,
            event_type=f"DECISION_{clean_decision}",
            actor_reference=str(acting_user_id),
            payload=dec_payload,
        )

        decision = ApprovalDecisionModel(
            id=dec_id,
            approval_request_id=req.id,
            step_instance_id=step_inst.id,
            assignment_id=assign.id,
            decision_type=clean_decision,
            status="RECORDED",
            decided_by_user_id=UUID(str(acting_user_id)),
            approver_snapshot={"user_id": str(acting_user_id)},
            delegation_id=assign.delegation_id,
            reason=reason,
            conditions=conditions,
            step_up_assurance_level=step_up_assurance_level,
            decision_at=datetime.now(timezone.utc),
            request_snapshot_hash=req_hash,
            step_snapshot_hash=step_hash,
            previous_event_hash=req.chain_hash,
            decision_hash=d_hash,
        )
        self.db.add(decision)
        assign.status = "ACTED"
        assign.acted_at = datetime.now(timezone.utc)

        # Evaluate Step Completion
        all_step_decs = (
            self.db.query(ApprovalDecisionModel)
            .filter_by(step_instance_id=step_inst.id)
            .all()
        )
        all_step_decs_list = [{"decision_type": d.decision_type} for d in all_step_decs] + [{"decision_type": clean_decision}]
        all_step_assigns = self.db.query(ApprovalAssignmentModel).filter_by(step_instance_id=step_inst.id).all()

        evaluation = ApprovalStepCompletionService.evaluate_step_completion(
            completion_mode=step_inst.completion_mode,
            minimum_approvals=step_inst.minimum_approvals,
            required_approvals=step_inst.required_approvals,
            decisions=all_step_decs_list,
            assignments=[{"id": str(a.id)} for a in all_step_assigns],
        )

        if evaluation["is_completed"]:
            step_inst.status = evaluation["outcome"]
            step_inst.completed_at = datetime.now(timezone.utc)
            step_inst.completion_result = evaluation["outcome"]

            if evaluation["outcome"] == "APPROVED":
                # Activate next step or complete request
                next_step = (
                    self.db.query(ApprovalStepInstanceModel)
                    .filter_by(approval_request_id=req.id, sequence_number=step_inst.sequence_number + 1)
                    .first()
                )
                if next_step:
                    next_step.status = "ACTIVE"
                    next_step.activated_at = datetime.now(timezone.utc)
                    req.current_sequence = next_step.sequence_number
                else:
                    # Final request approval
                    req.status = "APPROVED"
                    req.final_decision = "APPROVED"
                    req.final_decision_at = datetime.now(timezone.utc)
                    req.completed_at = datetime.now(timezone.utc)

                    # Create Audit Seal
                    self._create_audit_seal(req)

            elif evaluation["outcome"] in ("REJECTED", "RETURNED"):
                req.status = "REJECTED" if evaluation["outcome"] == "REJECTED" else "RETURNED_FOR_CHANGES"
                req.final_decision = evaluation["outcome"]
                req.final_decision_at = datetime.now(timezone.utc)
                req.completed_at = datetime.now(timezone.utc)
                if clean_decision == "RETURN_FOR_CHANGES":
                    req.return_reason = reason
                elif clean_decision == "REJECT":
                    req.cancellation_reason = reason

                self._create_audit_seal(req)

        self.db.flush()
        return decision

    def _create_audit_seal(self, req: ProcurementApprovalRequestModel) -> ApprovalAuditSealModel:
        """Helper creating the audit seal upon request completion."""
        decisions = self.db.query(ApprovalDecisionModel).filter_by(approval_request_id=req.id).all()
        events = self.db.query(ApprovalIntegrityEventModel).filter_by(approval_request_id=req.id).all()

        seal_dict = ApprovalAuditSealService.create_seal(
            organization_id=req.organization_id,
            approval_request_id=req.id,
            subject_type=req.subject_type,
            subject_id=req.subject_id,
            subject_revision_id=req.subject_revision_id,
            subject_snapshot=req.subject_snapshot,
            policy_versions=[{"version_id": str(req.id)}],
            compiled_chain=req.compiled_chain,
            decisions=[{"id": str(d.id), "type": d.decision_type} for d in decisions],
            integrity_events=[{"seq": e.sequence_number, "hash": e.event_hash} for e in events],
            final_status=req.status,
            final_decision=req.final_decision or req.status,
        )

        seal = ApprovalAuditSealModel(
            id=uuid.uuid4(),
            organization_id=req.organization_id,
            approval_request_id=req.id,
            subject_type=req.subject_type,
            subject_id=req.subject_id,
            subject_revision_id=req.subject_revision_id,
            subject_snapshot_hash=seal_dict["subject_snapshot_hash"],
            policy_versions_hash=seal_dict["policy_versions_hash"],
            chain_hash=seal_dict["chain_hash"],
            decisions_hash=seal_dict["decisions_hash"],
            event_chain_hash=seal_dict["event_chain_hash"],
            final_status=req.status,
            final_decision=req.final_decision or req.status,
            sealed_by_service="ProcurementApprovalEngine",
            hash_algorithm="SHA-256",
            canonicalization_version="1.0.0",
            seal_hash=seal_dict["seal_hash"],
            signature_algorithm=seal_dict["signature_algorithm"],
            signature_value=seal_dict["signature_value"],
            verification_status="HASH_VERIFIED",
        )
        self.db.add(seal)
        req.audit_seal_id = seal.id
        self.db.flush()
        return seal
