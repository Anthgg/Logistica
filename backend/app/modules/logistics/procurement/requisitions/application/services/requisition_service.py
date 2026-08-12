"""Main purchase requisition service — CRUD, listing, capabilities (Phase 031)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session

from app.modules.logistics.cost_centers.models import CostCenterModel
from app.modules.logistics.procurement.requisitions.domain.errors.exceptions import (
    PurchaseRequisitionNotFound,
    PurchaseRequisitionNotEditable,
    PurchaseRequisitionRevisionConflict,
    PurchaseRequisitionStatusInvalid,
    CostCenterInactive,
    CostCenterNotFound,
)
from app.modules.logistics.procurement.requisitions.domain.services.services import (
    build_branch_snapshot,
    build_cost_center_snapshot,
    build_destination_snapshot,
    build_requester_snapshot,
    validate_justification,
    validate_required_date,
    normalize_code,
)
from app.modules.logistics.procurement.requisitions.domain.value_objects.enums import (
    RequisitionStatus,
    RevisionStatus,
)
from app.modules.logistics.procurement.requisitions.infrastructure.persistence.models import (
    PurchaseRequisitionModel,
    PurchaseRequisitionRevisionModel,
    PurchaseRequisitionDecisionModel,
)


class PurchaseRequisitionService:
    """Core CRUD + capability service for purchase requisitions."""

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _get_or_404(db: Session, requisition_id: UUID, org_id: UUID) -> PurchaseRequisitionModel:
        pr = (
            db.query(PurchaseRequisitionModel)
            .filter(
                PurchaseRequisitionModel.id == requisition_id,
                PurchaseRequisitionModel.organization_id == org_id,
            )
            .first()
        )
        if pr is None:
            raise PurchaseRequisitionNotFound(requisition_id)
        return pr

    @staticmethod
    def _active_revision(db: Session, pr: PurchaseRequisitionModel) -> PurchaseRequisitionRevisionModel | None:
        if pr.active_revision_id is None:
            return None
        return db.get(PurchaseRequisitionRevisionModel, pr.active_revision_id)

    # ------------------------------------------------------------------ #
    # Create draft                                                         #
    # ------------------------------------------------------------------ #

    def create_draft(
        self,
        db: Session,
        org_id: UUID,
        branch_id: UUID,
        user_id: UUID,
        user_name: str,
        cost_center_id: UUID,
        priority: str,
        required_date: object,  # date
        justification: str,
        requester_area: str | None = None,
        business_purpose: str | None = None,
        destination_warehouse_id: UUID | None = None,
        delivery_location_description: str | None = None,
    ) -> PurchaseRequisitionModel:
        from datetime import date as date_cls

        # Validate justification
        clean_justification = validate_justification(justification)

        # Validate date
        if isinstance(required_date, str):
            from datetime import date
            required_date = date.fromisoformat(required_date)
        validate_required_date(required_date)

        # Resolve cost center
        cc = (
            db.query(CostCenterModel)
            .filter(
                CostCenterModel.id == cost_center_id,
                CostCenterModel.organization_id == org_id,
            )
            .first()
        )
        if cc is None:
            raise CostCenterNotFound(cost_center_id)
        if cc.status != "ACTIVE":
            raise CostCenterInactive(cost_center_id, cc.status)

        # Snapshots
        cc_snapshot = build_cost_center_snapshot(cc.id, cc.code, cc.name, org_id)
        requester_snapshot = build_requester_snapshot(user_id, user_name, requester_area)
        dest_snapshot = build_destination_snapshot(
            destination_warehouse_id, None, delivery_location_description
        )
        # Resolve branch name (best-effort)
        try:
            from app.models.branch import Branch
            branch = db.get(Branch, branch_id)
            branch_name = branch.name if branch else str(branch_id)
            branch_code = branch.code if branch else str(branch_id)
        except Exception:
            branch_name = str(branch_id)
            branch_code = str(branch_id)
        branch_snap = build_branch_snapshot(branch_id, branch_code, branch_name)

        # Create requisition
        pr = PurchaseRequisitionModel(
            organization_id=org_id,
            branch_id=branch_id,
            requester_user_id=user_id,
            requester_name_snapshot=user_name,
            requester_area=requester_area,
            cost_center_id=cost_center_id,
            cost_center_snapshot=cc_snapshot,
            priority=priority,
            required_date=required_date,
            destination_warehouse_id=destination_warehouse_id,
            delivery_location_description=delivery_location_description,
            justification=clean_justification,
            business_purpose=business_purpose,
            status=RequisitionStatus.DRAFT,
            current_revision_number=0,
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(pr)
        db.flush()  # Get ID

        # Create initial revision
        rev = PurchaseRequisitionRevisionModel(
            requisition_id=pr.id,
            revision_number=1,
            status=RevisionStatus.EDITABLE,
            branch_snapshot=branch_snap,
            requester_snapshot=requester_snapshot,
            cost_center_snapshot=cc_snapshot,
            priority=priority,
            required_date=required_date,
            destination_snapshot=dest_snapshot,
            justification=clean_justification,
            business_purpose=business_purpose,
            line_count=0,
            created_by=user_id,
        )
        db.add(rev)
        db.flush()

        # Link revision to requisition
        pr.active_revision_id = rev.id
        pr.current_revision_number = 1

        return pr

    # ------------------------------------------------------------------ #
    # Read                                                                 #
    # ------------------------------------------------------------------ #

    def get(self, db: Session, requisition_id: UUID, org_id: UUID) -> PurchaseRequisitionModel:
        return self._get_or_404(db, requisition_id, org_id)

    def list(
        self,
        db: Session,
        org_id: UUID,
        status_filter: str | None = None,
        priority: str | None = None,
        cost_center_id: UUID | None = None,
        branch_id: UUID | None = None,
        requester_user_id: UUID | None = None,
        required_from: object = None,
        required_to: object = None,
        mine: bool = False,
        current_user_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[PurchaseRequisitionModel], int]:
        q = db.query(PurchaseRequisitionModel).filter(
            PurchaseRequisitionModel.organization_id == org_id
        )
        if status_filter:
            q = q.filter(PurchaseRequisitionModel.status == status_filter)
        if priority:
            q = q.filter(PurchaseRequisitionModel.priority == priority)
        if cost_center_id:
            q = q.filter(PurchaseRequisitionModel.cost_center_id == cost_center_id)
        if branch_id:
            q = q.filter(PurchaseRequisitionModel.branch_id == branch_id)
        if requester_user_id:
            q = q.filter(PurchaseRequisitionModel.requester_user_id == requester_user_id)
        if required_from:
            q = q.filter(PurchaseRequisitionModel.required_date >= required_from)
        if required_to:
            q = q.filter(PurchaseRequisitionModel.required_date <= required_to)
        if mine and current_user_id:
            q = q.filter(PurchaseRequisitionModel.requester_user_id == current_user_id)

        total = q.count()
        items = (
            q.order_by(PurchaseRequisitionModel.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    # ------------------------------------------------------------------ #
    # Update draft                                                         #
    # ------------------------------------------------------------------ #

    def update_draft(
        self,
        db: Session,
        requisition_id: UUID,
        org_id: UUID,
        user_id: UUID,
        expected_row_version: int,
        **fields,
    ) -> PurchaseRequisitionModel:
        pr = self._get_or_404(db, requisition_id, org_id)

        if pr.status not in (RequisitionStatus.DRAFT, RequisitionStatus.RETURNED_FOR_CHANGES):
            raise PurchaseRequisitionNotEditable(pr.status)

        if pr.row_version != expected_row_version:
            raise PurchaseRequisitionRevisionConflict(expected_row_version, pr.row_version)

        rev = self._active_revision(db, pr)
        if rev is None or rev.status != RevisionStatus.EDITABLE:
            raise PurchaseRequisitionNotEditable(pr.status)

        updatable_header = {
            "priority", "required_date", "justification", "business_purpose",
            "destination_warehouse_id", "delivery_location_description", "requester_area",
        }
        for field, value in fields.items():
            if field in updatable_header and value is not None:
                if field == "justification":
                    value = validate_justification(value)
                setattr(pr, field, value)
                setattr(rev, field, value)  # Keep revision in sync

        pr.updated_by = user_id
        pr.row_version += 1
        return pr

    # ------------------------------------------------------------------ #
    # Capabilities                                                         #
    # ------------------------------------------------------------------ #

    def get_capabilities(
        self,
        db: Session,
        requisition_id: UUID,
        org_id: UUID,
        user_id: UUID,
    ) -> dict:
        pr = self._get_or_404(db, requisition_id, org_id)
        st = RequisitionStatus(pr.status)

        # Check if a final decision already exists
        has_final_decision = (
            db.query(PurchaseRequisitionDecisionModel)
            .filter(
                PurchaseRequisitionDecisionModel.requisition_id == pr.id,
                PurchaseRequisitionDecisionModel.is_final == True,
            )
            .first()
        ) is not None

        is_requester = pr.requester_user_id == user_id

        return {
            "can_edit": st in (RequisitionStatus.DRAFT, RequisitionStatus.RETURNED_FOR_CHANGES) and is_requester,
            "can_submit": st in (RequisitionStatus.DRAFT, RequisitionStatus.RETURNED_FOR_CHANGES) and is_requester,
            "can_start_review": st == RequisitionStatus.SUBMITTED,
            "can_approve": st in (RequisitionStatus.SUBMITTED, RequisitionStatus.UNDER_REVIEW) and not has_final_decision,
            "can_reject": st in (RequisitionStatus.SUBMITTED, RequisitionStatus.UNDER_REVIEW) and not has_final_decision,
            "can_return": st in (RequisitionStatus.SUBMITTED, RequisitionStatus.UNDER_REVIEW),
            "can_withdraw": st in (RequisitionStatus.SUBMITTED, RequisitionStatus.UNDER_REVIEW) and is_requester and not has_final_decision,
            "can_cancel": st in (RequisitionStatus.DRAFT, RequisitionStatus.APPROVED),
            "can_preview": True,
            "can_issue_document": st == RequisitionStatus.APPROVED,
            "can_copy": st in (RequisitionStatus.REJECTED, RequisitionStatus.WITHDRAWN, RequisitionStatus.APPROVED),
            "current_status": pr.status,
            "current_revision_number": pr.current_revision_number,
        }

    # ------------------------------------------------------------------ #
    # History                                                              #
    # ------------------------------------------------------------------ #

    def get_history(self, db: Session, requisition_id: UUID, org_id: UUID) -> list[dict]:
        pr = self._get_or_404(db, requisition_id, org_id)
        decisions = (
            db.query(PurchaseRequisitionDecisionModel)
            .filter(PurchaseRequisitionDecisionModel.requisition_id == pr.id)
            .order_by(PurchaseRequisitionDecisionModel.created_at)
            .all()
        )
        history = []
        history.append({
            "event": "created",
            "actor": str(pr.created_by),
            "timestamp": pr.created_at.isoformat() if pr.created_at else None,
            "details": {"status": "DRAFT"},
        })
        for d in decisions:
            history.append({
                "event": d.decision_type,
                "actor": str(d.decided_by),
                "timestamp": d.decided_at.isoformat() if d.decided_at else None,
                "details": {
                    "reason": d.reason,
                    "is_final": d.is_final,
                    "revision_id": str(d.revision_id),
                },
            })
        return history


purchase_requisition_service = PurchaseRequisitionService()
