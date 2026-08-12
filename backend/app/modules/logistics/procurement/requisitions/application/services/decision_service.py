"""Decision service — approve, reject, return, withdraw, cancel (Phase 031)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.logistics.procurement.requisitions.domain.errors.exceptions import (
    PurchaseRequisitionAlreadyDecided,
    PurchaseRequisitionCannotBeApproved,
    PurchaseRequisitionCannotBeCancelled,
    PurchaseRequisitionCannotBeRejected,
    PurchaseRequisitionCannotBeWithdrawn,
    PurchaseRequisitionSelfApprovalDenied,
    PurchaseRequisitionStatusInvalid,
)
from app.modules.logistics.procurement.requisitions.domain.policies.approval_policy import (
    ApprovalContext,
    purchase_approval_policy,
)
from app.modules.logistics.procurement.requisitions.domain.value_objects.enums import (
    DecisionType,
    FINAL_DECISION_TYPES,
    RequisitionStatus,
    RevisionStatus,
)
from app.modules.logistics.procurement.requisitions.infrastructure.persistence.models import (
    PurchaseRequisitionDecisionModel,
    PurchaseRequisitionLineModel,
    PurchaseRequisitionModel,
    PurchaseRequisitionRevisionModel,
)


class PurchaseRequisitionDecisionService:
    """Handles all approval workflow decisions for purchase requisitions."""

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _get_pr_with_lock(db: Session, requisition_id: UUID, org_id: UUID) -> PurchaseRequisitionModel:
        pr = (
            db.query(PurchaseRequisitionModel)
            .filter(
                PurchaseRequisitionModel.id == requisition_id,
                PurchaseRequisitionModel.organization_id == org_id,
            )
            .with_for_update()
            .first()
        )
        if pr is None:
            raise HTTPException(status_code=404, detail={"code": "PURCHASE_REQUISITION_NOT_FOUND"})
        return pr

    @staticmethod
    def _check_no_final_decision(db: Session, requisition_id: UUID) -> None:
        existing = (
            db.query(PurchaseRequisitionDecisionModel)
            .filter(
                PurchaseRequisitionDecisionModel.requisition_id == requisition_id,
                PurchaseRequisitionDecisionModel.is_final == True,
            )
            .first()
        )
        if existing:
            raise PurchaseRequisitionAlreadyDecided(existing.decision_type)

    def _create_decision(
        self,
        db: Session,
        pr: PurchaseRequisitionModel,
        decision_type: DecisionType,
        actor_id: UUID,
        reason: str | None,
        is_final: bool,
    ) -> PurchaseRequisitionDecisionModel:
        now = datetime.now(timezone.utc)
        rev_id = pr.submitted_revision_id or pr.active_revision_id
        decision = PurchaseRequisitionDecisionModel(
            requisition_id=pr.id,
            revision_id=rev_id,
            decision_type=decision_type,
            decided_by=actor_id,
            decided_at=now,
            reason=reason,
            is_final=is_final,
            approval_policy_code=purchase_approval_policy.POLICY_CODE,
            approval_policy_version=purchase_approval_policy.POLICY_VERSION,
        )
        db.add(decision)
        db.flush()
        pr.last_decision_id = decision.id
        return decision

    # ------------------------------------------------------------------ #
    # Start review                                                         #
    # ------------------------------------------------------------------ #

    def start_review(
        self,
        db: Session,
        requisition_id: UUID,
        org_id: UUID,
        user_id: UUID,
    ) -> PurchaseRequisitionModel:
        pr = self._get_pr_with_lock(db, requisition_id, org_id)
        if pr.status != RequisitionStatus.SUBMITTED:
            raise PurchaseRequisitionStatusInvalid(pr.status, RequisitionStatus.SUBMITTED)

        self._create_decision(db, pr, DecisionType.START_REVIEW, user_id, None, False)
        now = datetime.now(timezone.utc)
        pr.status = RequisitionStatus.UNDER_REVIEW
        pr.updated_by = user_id
        pr.row_version += 1
        return pr

    # ------------------------------------------------------------------ #
    # Approve                                                              #
    # ------------------------------------------------------------------ #

    def approve(
        self,
        db: Session,
        requisition_id: UUID,
        org_id: UUID,
        user_id: UUID,
        reason: str | None = None,
    ) -> PurchaseRequisitionModel:
        pr = self._get_pr_with_lock(db, requisition_id, org_id)
        if pr.status not in (RequisitionStatus.SUBMITTED, RequisitionStatus.UNDER_REVIEW):
            raise PurchaseRequisitionStatusInvalid(
                pr.status, [RequisitionStatus.SUBMITTED, RequisitionStatus.UNDER_REVIEW]
            )
        self._check_no_final_decision(db, requisition_id)

        # Policy check (self-approval, step-up level)
        ctx = ApprovalContext(
            requisition_id=pr.id,
            requester_user_id=pr.requester_user_id,
            approver_user_id=user_id,
            priority=pr.priority,
            organization_id=org_id,
        )
        policy_result = purchase_approval_policy.resolve(ctx)
        if not policy_result.can_approve:
            if pr.requester_user_id == user_id:
                raise PurchaseRequisitionSelfApprovalDenied()
            raise PurchaseRequisitionCannotBeApproved(policy_result.reason or "Policy denied.")

        self._create_decision(db, pr, DecisionType.APPROVE, user_id, reason, True)
        now = datetime.now(timezone.utc)
        pr.status = RequisitionStatus.APPROVED
        pr.approved_at = now
        pr.approved_by = user_id
        pr.approved_revision_id = pr.submitted_revision_id or pr.active_revision_id

        # Mark revision as APPROVED
        if pr.approved_revision_id:
            rev = db.get(PurchaseRequisitionRevisionModel, pr.approved_revision_id)
            if rev:
                rev.status = RevisionStatus.APPROVED

        pr.updated_by = user_id
        pr.row_version += 1
        return pr

    # ------------------------------------------------------------------ #
    # Reject                                                               #
    # ------------------------------------------------------------------ #

    def reject(
        self,
        db: Session,
        requisition_id: UUID,
        org_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> PurchaseRequisitionModel:
        if not reason or len(reason.strip()) < 15:
            raise HTTPException(
                status_code=422,
                detail={"code": "REJECTION_REASON_TOO_SHORT", "min_length": 15},
            )
        pr = self._get_pr_with_lock(db, requisition_id, org_id)
        if pr.status not in (RequisitionStatus.SUBMITTED, RequisitionStatus.UNDER_REVIEW):
            raise PurchaseRequisitionStatusInvalid(
                pr.status, [RequisitionStatus.SUBMITTED, RequisitionStatus.UNDER_REVIEW]
            )
        self._check_no_final_decision(db, requisition_id)

        self._create_decision(db, pr, DecisionType.REJECT, user_id, reason, True)
        now = datetime.now(timezone.utc)
        pr.status = RequisitionStatus.REJECTED
        pr.rejected_at = now
        pr.rejected_by = user_id

        if pr.submitted_revision_id:
            rev = db.get(PurchaseRequisitionRevisionModel, pr.submitted_revision_id)
            if rev:
                rev.status = RevisionStatus.REJECTED

        pr.updated_by = user_id
        pr.row_version += 1
        return pr

    # ------------------------------------------------------------------ #
    # Return for changes                                                   #
    # ------------------------------------------------------------------ #

    def return_for_changes(
        self,
        db: Session,
        requisition_id: UUID,
        org_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> PurchaseRequisitionModel:
        if not reason or len(reason.strip()) < 10:
            raise HTTPException(
                status_code=422,
                detail={"code": "RETURN_REASON_TOO_SHORT", "min_length": 10},
            )
        pr = self._get_pr_with_lock(db, requisition_id, org_id)
        if pr.status not in (RequisitionStatus.SUBMITTED, RequisitionStatus.UNDER_REVIEW):
            raise PurchaseRequisitionStatusInvalid(
                pr.status, [RequisitionStatus.SUBMITTED, RequisitionStatus.UNDER_REVIEW]
            )

        # Mark current revision as SUPERSEDED
        if pr.submitted_revision_id:
            old_rev = db.get(PurchaseRequisitionRevisionModel, pr.submitted_revision_id)
            if old_rev:
                old_rev.status = RevisionStatus.SUPERSEDED

        # Create new editable revision
        now = datetime.now(timezone.utc)
        new_revision_number = pr.current_revision_number + 1
        old_rev_obj = db.get(PurchaseRequisitionRevisionModel, pr.submitted_revision_id or pr.active_revision_id)

        new_rev = PurchaseRequisitionRevisionModel(
            requisition_id=pr.id,
            revision_number=new_revision_number,
            status=RevisionStatus.EDITABLE,
            branch_snapshot=old_rev_obj.branch_snapshot if old_rev_obj else {},
            requester_snapshot=old_rev_obj.requester_snapshot if old_rev_obj else {},
            cost_center_snapshot=old_rev_obj.cost_center_snapshot if old_rev_obj else {},
            priority=pr.priority,
            required_date=pr.required_date,
            destination_snapshot=old_rev_obj.destination_snapshot if old_rev_obj else None,
            justification=pr.justification,
            business_purpose=pr.business_purpose,
            line_count=old_rev_obj.line_count if old_rev_obj else 0,
            created_from_revision_id=pr.submitted_revision_id or pr.active_revision_id,
            change_summary=reason,
            created_by=user_id,
        )
        db.add(new_rev)
        db.flush()

        # Copy active lines to new revision
        if old_rev_obj:
            old_lines = (
                db.query(PurchaseRequisitionLineModel)
                .filter(
                    PurchaseRequisitionLineModel.requisition_revision_id == old_rev_obj.id,
                    PurchaseRequisitionLineModel.status == "ACTIVE",
                )
                .all()
            )
            for line in old_lines:
                new_line = PurchaseRequisitionLineModel(
                    requisition_revision_id=new_rev.id,
                    line_number=line.line_number,
                    product_id=line.product_id,
                    product_version_id=line.product_version_id,
                    sku_snapshot=line.sku_snapshot,
                    product_name_snapshot=line.product_name_snapshot,
                    product_description_snapshot=line.product_description_snapshot,
                    requested_quantity=line.requested_quantity,
                    requested_unit_id=line.requested_unit_id,
                    base_quantity=line.base_quantity,
                    base_unit_id=line.base_unit_id,
                    conversion_rule_id=line.conversion_rule_id,
                    conversion_factor_snapshot=line.conversion_factor_snapshot,
                    line_justification=line.line_justification,
                    notes=line.notes,
                    status="ACTIVE",
                    created_by=user_id,
                )
                db.add(new_line)

        self._create_decision(db, pr, DecisionType.RETURN_FOR_CHANGES, user_id, reason, False)

        pr.status = RequisitionStatus.RETURNED_FOR_CHANGES
        pr.returned_at = now
        pr.returned_by = user_id
        pr.active_revision_id = new_rev.id
        pr.current_revision_number = new_revision_number
        pr.updated_by = user_id
        pr.row_version += 1
        return pr

    # ------------------------------------------------------------------ #
    # Withdraw                                                             #
    # ------------------------------------------------------------------ #

    def withdraw(
        self,
        db: Session,
        requisition_id: UUID,
        org_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> PurchaseRequisitionModel:
        pr = self._get_pr_with_lock(db, requisition_id, org_id)
        if pr.status not in (RequisitionStatus.SUBMITTED, RequisitionStatus.UNDER_REVIEW):
            raise PurchaseRequisitionCannotBeWithdrawn(
                f"Cannot withdraw from status '{pr.status}'."
            )
        # Only the requester or authorized user can withdraw
        if pr.requester_user_id != user_id:
            raise PurchaseRequisitionCannotBeWithdrawn(
                "Only the requester can withdraw a requisition."
            )
        # Cannot withdraw if already decided
        self._check_no_final_decision(db, requisition_id)

        self._create_decision(db, pr, DecisionType.WITHDRAW, user_id, reason, True)
        now = datetime.now(timezone.utc)
        pr.status = RequisitionStatus.WITHDRAWN
        pr.withdrawn_at = now
        pr.withdrawn_by = user_id
        pr.updated_by = user_id
        pr.row_version += 1
        return pr

    # ------------------------------------------------------------------ #
    # Cancel                                                               #
    # ------------------------------------------------------------------ #

    def cancel(
        self,
        db: Session,
        requisition_id: UUID,
        org_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> PurchaseRequisitionModel:
        if not reason or len(reason.strip()) < 10:
            raise HTTPException(
                status_code=422,
                detail={"code": "CANCEL_REASON_TOO_SHORT", "min_length": 10},
            )
        pr = self._get_pr_with_lock(db, requisition_id, org_id)
        cancellable = {RequisitionStatus.DRAFT, RequisitionStatus.APPROVED}
        if pr.status not in cancellable:
            raise PurchaseRequisitionCannotBeCancelled(
                f"Cannot cancel from status '{pr.status}'."
            )

        self._create_decision(db, pr, DecisionType.CANCEL, user_id, reason, True)
        now = datetime.now(timezone.utc)
        pr.status = RequisitionStatus.CANCELLED
        pr.cancelled_at = now
        pr.cancelled_by = user_id
        pr.updated_by = user_id
        pr.row_version += 1
        return pr


purchase_requisition_decision_service = PurchaseRequisitionDecisionService()
