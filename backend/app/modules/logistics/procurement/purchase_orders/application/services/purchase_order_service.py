"""PurchaseOrderService — main application service for purchase order management.

Orchestrates business workflows for:
- Planning & generating POs from CCO evaluation decisions.
- Validation, submission, and state machine transitions.
- Decoupled approval gate (Transitional Single Step).
- Snapshot freezing and immutability rules.
- Audit event emission.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.procurement.purchase_orders.domain.errors.exceptions import (
    PurchaseOrderNotFound,
    PurchaseOrderStatusInvalid,
    PurchaseOrderAlreadyApproved,
    PurchaseOrderAllocationConflict,
    PurchaseOrderMonetaryCalculationMismatch,
)
from app.modules.logistics.procurement.purchase_orders.domain.policies.approval_gate import (
    PurchaseOrderApprovalGate,
    get_approval_policy,
)
from app.modules.logistics.procurement.purchase_orders.domain.services.generation_planner import (
    PurchaseOrderGenerationPlan,
    PurchaseOrderGenerationPlanner,
)
from app.modules.logistics.procurement.purchase_orders.domain.services.money_service import (
    LineInput,
    PurchaseOrderMoneyService,
)
from app.modules.logistics.procurement.purchase_orders.domain.services.snapshot_provider import (
    PurchaseOrderSnapshotProvider,
)
from app.modules.logistics.procurement.purchase_orders.infrastructure.persistence.models import (
    PurchaseOrderApprovalDecisionModel,
    PurchaseOrderLineModel,
    PurchaseOrderModel,
    PurchaseOrderRevisionModel,
    PurchaseOrderSourceAllocationModel,
)
from app.modules.logistics.procurement.purchase_orders.infrastructure.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)


class PurchaseOrderService:
    """Application service for Purchase Orders."""

    def __init__(
        self,
        db: Session,
        money_service: PurchaseOrderMoneyService | None = None,
        planner: PurchaseOrderGenerationPlanner | None = None,
        approval_gate: PurchaseOrderApprovalGate | None = None,
    ) -> None:
        self._db = db
        self._repo = PurchaseOrderRepository(db)
        self._money_service = money_service or PurchaseOrderMoneyService(scale=2)
        self._planner = planner or PurchaseOrderGenerationPlanner()
        self._approval_gate = approval_gate or get_approval_policy()

    # ------------------------------------------------------------------
    # CCO -> PO Generation Planning & Execution
    # ------------------------------------------------------------------
    def plan_generation(
        self,
        organization_id: UUID,
        decision_data: dict[str, Any],
        decision_lines_data: list[dict[str, Any]],
        candidates_by_id: dict[UUID, dict[str, Any]],
        evaluation_data: dict[str, Any] | None = None,
    ) -> PurchaseOrderGenerationPlan:
        """Generate a preview plan of POs that will be created from a CCO decision."""
        return self._planner.build_plan(
            decision_data=decision_data,
            decision_lines_data=decision_lines_data,
            candidates_by_id=candidates_by_id,
            evaluation_data=evaluation_data,
        )

    def generate_orders_from_decision(
        self,
        organization_id: UUID,
        branch_id: UUID,
        creator_user_id: UUID,
        decision_data: dict[str, Any],
        decision_lines_data: list[dict[str, Any]],
        candidates_by_id: dict[UUID, dict[str, Any]],
        evaluation_data: dict[str, Any] | None = None,
        site_code: str = "LIM",
        notes: str | None = None,
    ) -> list[PurchaseOrderModel]:
        """Execute PO generation from a RECORDED evaluation decision.

        Creates one PurchaseOrderModel per (supplier, currency) group.
        Returns the list of created PurchaseOrderModels.
        """
        # 1. Build & validate plan
        plan = self.plan_generation(
            organization_id=organization_id,
            decision_data=decision_data,
            decision_lines_data=decision_lines_data,
            candidates_by_id=candidates_by_id,
            evaluation_data=evaluation_data,
        )

        if not plan.is_executable:
            issues = "; ".join(plan.blocking_issues)
            raise PurchaseOrderStatusInvalid(
                f"Cannot generate purchase orders from decision: {issues}"
            )

        # 2. Check for double-allocation of decision lines
        decision_line_ids = [
            line.evaluation_decision_line_id
            for entry in plan.entries
            for line in entry.lines
        ]
        conflicts = self._repo.check_allocation_conflicts(decision_line_ids)
        if conflicts:
            conflicted_ids = [str(c.evaluation_decision_line_id) for c in conflicts]
            raise PurchaseOrderAllocationConflict(
                f"Evaluation decision lines already allocated to existing POs: {conflicted_ids}"
            )

        created_orders: list[PurchaseOrderModel] = []
        source_decision_id = UUID(str(decision_data["id"]))

        # 3. Create a PO for each entry in the plan
        for entry in plan.entries:
            # Generate atomic code
            po_code, normalized_code, _ = self._repo.generate_next_code(
                organization_id=organization_id,
                site_code=site_code,
            )

            # Build line inputs for MoneyService
            line_inputs: list[LineInput] = []
            for i, line_entry in enumerate(entry.lines, start=1):
                line_inputs.append(
                    LineInput(
                        line_number=i,
                        ordered_quantity=line_entry.ordered_quantity,
                        unit_price=line_entry.unit_price,
                        currency_code=line_entry.currency_code,
                        discount_type="NONE",
                        tax_rate=Decimal("0"),  # Resolved or overridden later
                        freight_amount=Decimal("0"),
                        other_charges_amount=Decimal("0"),
                    )
                )

            monetary_summary = self._money_service.calculate_summary(line_inputs)

            # Snapshots
            candidate = candidates_by_id.get(entry.lines[0].evaluation_decision_line_id) or {}
            supplier_snapshot = PurchaseOrderSnapshotProvider.build_supplier_snapshot(
                partner_data={
                    "id": entry.supplier_business_partner_id,
                    "legal_name": entry.supplier_name_snapshot,
                }
            )
            buyer_snapshot = PurchaseOrderSnapshotProvider.build_buyer_snapshot(
                user_data={"id": creator_user_id, "name": "Buyer User"}
            )
            source_snapshot = PurchaseOrderSnapshotProvider.build_source_snapshot(
                decision_data=decision_data,
                evaluation_data=evaluation_data,
            )
            monetary_snapshot = PurchaseOrderSnapshotProvider.build_monetary_snapshot(
                monetary_summary.to_dict()
            )

            # Build PurchaseOrder aggregate root
            po = PurchaseOrderModel(
                organization_id=organization_id,
                branch_id=branch_id,
                purchase_order_code=po_code,
                normalized_purchase_order_code=normalized_code,
                supplier_business_partner_id=entry.supplier_business_partner_id,
                supplier_snapshot=supplier_snapshot,
                source_decision_id=source_decision_id,
                source_evaluation_id=entry.source_evaluation_id,
                source_evaluation_run_id=entry.source_evaluation_run_id,
                source_purchase_requisition_id=entry.source_purchase_requisition_id,
                currency_code=entry.currency_code,
                status="DRAFT",
                approval_status="NOT_SUBMITTED",
                issuance_status="NOT_ISSUED",
                dispatch_status="NOT_SENT",
                acknowledgement_status="NOT_REQUESTED",
                fulfilment_status="NOT_STARTED",
                current_revision_number=1,
                subtotal=monetary_summary.subtotal,
                discount_total=monetary_summary.discount_total,
                tax_total=monetary_summary.tax_total,
                freight_total=monetary_summary.freight_total,
                other_charges_total=monetary_summary.other_charges_total,
                grand_total=monetary_summary.grand_total,
                buyer_user_id=creator_user_id,
                buyer_snapshot=buyer_snapshot,
                notes=notes,
                created_by=creator_user_id,
            )

            # Save aggregate root first to get po.id
            self._repo.save(po)

            # Build Revision 1
            lines_data_for_hash: list[dict[str, Any]] = []

            revision = PurchaseOrderRevisionModel(
                purchase_order_id=po.id,
                revision_number=1,
                status="EDITABLE",
                supplier_snapshot=supplier_snapshot,
                source_snapshot=source_snapshot,
                currency_code=entry.currency_code,
                monetary_summary=monetary_snapshot,
                created_by=creator_user_id,
            )
            self._db.add(revision)
            self._db.flush()

            # Link revision to PO
            po.active_revision_id = revision.id

            # Create Revision Lines & Source Allocations
            for i, (line_entry, summary) in enumerate(zip(entry.lines, monetary_summary.line_summaries), start=1):
                line_model = PurchaseOrderLineModel(
                    purchase_order_revision_id=revision.id,
                    line_number=i,
                    evaluation_decision_line_id=line_entry.evaluation_decision_line_id,
                    quotation_response_line_id=line_entry.quotation_response_line_id,
                    product_id=line_entry.product_id,
                    product_name_snapshot=line_entry.product_name_snapshot,
                    product_description_snapshot=line_entry.product_description_snapshot,
                    specifications_snapshot=line_entry.specifications_snapshot,
                    supplier_product_reference=line_entry.supplier_product_reference,
                    ordered_quantity=line_entry.ordered_quantity,
                    ordered_unit_id=line_entry.ordered_unit_id,
                    ordered_unit_code=line_entry.ordered_unit_code,
                    unit_price=line_entry.unit_price,
                    currency_code=line_entry.currency_code,
                    discount_amount=summary.discount_amount,
                    tax_amount=summary.tax_amount,
                    freight_amount=summary.freight_amount,
                    other_charges_amount=summary.other_charges_amount,
                    line_subtotal=summary.line_subtotal,
                    line_total=summary.line_total,
                    status="ACTIVE",
                )
                self._db.add(line_model)

                alloc = PurchaseOrderSourceAllocationModel(
                    organization_id=organization_id,
                    purchase_order_id=po.id,
                    evaluation_decision_id=source_decision_id,
                    evaluation_decision_line_id=line_entry.evaluation_decision_line_id,
                    quotation_response_line_id=line_entry.quotation_response_line_id,
                    supplier_business_partner_id=entry.supplier_business_partner_id,
                    allocated_quantity=line_entry.ordered_quantity,
                    allocated_unit_code=line_entry.ordered_unit_code,
                    source_unit_price=line_entry.unit_price,
                    source_currency_code=line_entry.currency_code,
                    source_line_total=line_entry.source_line_total,
                    status="RESERVED",
                )
                self._repo.save_allocation(alloc)

                lines_data_for_hash.append({
                    "line_number": i,
                    "product_name": line_entry.product_name_snapshot,
                    "quantity": str(line_entry.ordered_quantity),
                    "unit_price": str(line_entry.unit_price),
                    "line_total": str(summary.line_total),
                })

            # Compute and store revision content hash
            revision.content_hash = PurchaseOrderSnapshotProvider.compute_revision_hash(
                supplier_snapshot=supplier_snapshot,
                lines_data=lines_data_for_hash,
                monetary_snapshot=monetary_snapshot,
                currency_code=entry.currency_code,
            )

            self._repo.save(po)
            created_orders.append(po)

        self._db.flush()
        return created_orders

    # ------------------------------------------------------------------
    # Submission & State Machine Transitions
    # ------------------------------------------------------------------
    def submit_for_approval(
        self,
        po_id: UUID,
        organization_id: UUID,
        submitter_user_id: UUID,
    ) -> PurchaseOrderModel:
        """Submit a DRAFT PO for approval."""
        po = self._repo.get_by_id_or_raise(po_id, organization_id)

        new_approval_status = self._approval_gate.submit_for_approval(
            purchase_order_id=po.id,
            revision_id=po.active_revision_id,  # type: ignore[arg-type]
            submitter_user_id=submitter_user_id,
            creator_user_id=po.created_by,
            current_approval_status=po.approval_status,
            current_po_status=po.status,
        )

        po.approval_status = new_approval_status
        po.status = "PENDING_APPROVAL"
        po.updated_by = submitter_user_id

        return self._repo.save(po)

    def approve_order(
        self,
        po_id: UUID,
        organization_id: UUID,
        approver_user_id: UUID,
        reason: str | None = None,
        allow_self_approval_override: bool = False,
    ) -> PurchaseOrderModel:
        """Approve a PENDING_APPROVAL PO.

        Enforces:
        - Self-approval prohibition (approver != creator).
        - Step-up COMBINED_FACE_PAD requirement.
        - Active revision freezing.
        """
        po = self._repo.get_by_id_or_raise(po_id, organization_id)

        # Get policy instance (override allowed only in test environments)
        policy = get_approval_policy(
            allow_self_approval_override=allow_self_approval_override
        )

        result = policy.approve(
            purchase_order_id=po.id,
            revision_id=po.active_revision_id,  # type: ignore[arg-type]
            approver_user_id=approver_user_id,
            creator_user_id=po.created_by,
            current_approval_status=po.approval_status,
            reason=reason,
        )

        # Record decision
        decision = PurchaseOrderApprovalDecisionModel(
            purchase_order_id=po.id,
            revision_id=po.active_revision_id,
            policy_code=result.policy_code,
            policy_version=result.policy_version,
            decision_type=result.decision_type,
            status="ACTIVE",
            decided_by=approver_user_id,
            reason=reason,
            is_final=result.is_final,
        )
        self._repo.save_approval_decision(decision)

        # Transition state
        po.approval_status = result.new_approval_status
        po.status = result.new_po_status
        po.approved_at = datetime.now(timezone.utc)
        po.approved_by = approver_user_id
        po.approved_revision_id = po.active_revision_id
        po.updated_by = approver_user_id

        # Freeze active revision
        if po.revisions:
            for rev in po.revisions:
                if rev.id == po.active_revision_id:
                    rev.status = "APPROVED"
                    rev.approved_at = po.approved_at
                    rev.frozen_at = po.approved_at

        return self._repo.save(po)

    def reject_order(
        self,
        po_id: UUID,
        organization_id: UUID,
        approver_user_id: UUID,
        reason: str,
    ) -> PurchaseOrderModel:
        """Reject a PENDING_APPROVAL PO. Requires reason >= 20 chars."""
        po = self._repo.get_by_id_or_raise(po_id, organization_id)
        policy = get_approval_policy()

        result = policy.reject(
            purchase_order_id=po.id,
            revision_id=po.active_revision_id,  # type: ignore[arg-type]
            approver_user_id=approver_user_id,
            creator_user_id=po.created_by,
            current_approval_status=po.approval_status,
            reason=reason,
        )

        decision = PurchaseOrderApprovalDecisionModel(
            purchase_order_id=po.id,
            revision_id=po.active_revision_id,
            policy_code=result.policy_code,
            policy_version=result.policy_version,
            decision_type=result.decision_type,
            status="ACTIVE",
            decided_by=approver_user_id,
            reason=reason,
            is_final=result.is_final,
        )
        self._repo.save_approval_decision(decision)

        po.approval_status = result.new_approval_status
        po.status = "DRAFT"  # Returned to draft for potential editing or cancellation
        po.updated_by = approver_user_id

        return self._repo.save(po)

    def return_for_changes(
        self,
        po_id: UUID,
        organization_id: UUID,
        approver_user_id: UUID,
        reason: str,
    ) -> PurchaseOrderModel:
        """Return a PENDING_APPROVAL PO for changes. Requires reason >= 20 chars."""
        po = self._repo.get_by_id_or_raise(po_id, organization_id)
        policy = get_approval_policy()

        result = policy.return_for_changes(
            purchase_order_id=po.id,
            revision_id=po.active_revision_id,  # type: ignore[arg-type]
            approver_user_id=approver_user_id,
            creator_user_id=po.created_by,
            current_approval_status=po.approval_status,
            reason=reason,
        )

        decision = PurchaseOrderApprovalDecisionModel(
            purchase_order_id=po.id,
            revision_id=po.active_revision_id,
            policy_code=result.policy_code,
            policy_version=result.policy_version,
            decision_type=result.decision_type,
            status="ACTIVE",
            decided_by=approver_user_id,
            reason=reason,
            is_final=result.is_final,
        )
        self._repo.save_approval_decision(decision)

        po.approval_status = result.new_approval_status
        po.status = result.new_po_status
        po.updated_by = approver_user_id

        return self._repo.save(po)

    def cancel_order(
        self,
        po_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        cancellation_reason: str,
    ) -> PurchaseOrderModel:
        """Cancel an unissued purchase order."""
        po = self._repo.get_by_id_or_raise(po_id, organization_id)

        if po.status in ("ISSUED", "SENT", "ACKNOWLEDGED", "CANCELLED", "CLOSED"):
            raise PurchaseOrderStatusInvalid(
                f"Cannot cancel purchase order in status {po.status!r}."
            )

        po.status = "CANCELLED"
        po.approval_status = "SUPERSEDED"
        po.cancelled_at = datetime.now(timezone.utc)
        po.cancelled_by = user_id
        po.cancellation_reason = cancellation_reason
        po.updated_by = user_id

        # Release source allocations
        if po.allocations:
            for alloc in po.allocations:
                alloc.status = "RELEASED"

        return self._repo.save(po)

    # ------------------------------------------------------------------
    # Query delegates
    # ------------------------------------------------------------------
    def get_order(
        self,
        po_id: UUID,
        organization_id: UUID,
    ) -> PurchaseOrderModel:
        return self._repo.get_by_id_or_raise(po_id, organization_id)

    def list_orders(
        self,
        organization_id: UUID,
        branch_id: UUID | None = None,
        supplier_id: UUID | None = None,
        status: str | None = None,
        approval_status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[PurchaseOrderModel], int]:
        return self._repo.list_orders(
            organization_id=organization_id,
            branch_id=branch_id,
            supplier_id=supplier_id,
            status=status,
            approval_status=approval_status,
            limit=limit,
            offset=offset,
        )
