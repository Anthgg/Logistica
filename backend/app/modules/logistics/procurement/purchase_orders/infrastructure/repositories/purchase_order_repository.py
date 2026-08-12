"""PurchaseOrderRepository — SQLAlchemy 2 persistence repository for Purchase Orders.

Handles atomic code generation, transaction boundaries, eager loading of
revisions/lines/allocations, and optimistic concurrency checks via row_version.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Sequence
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.modules.logistics.procurement.purchase_orders.domain.errors.exceptions import (
    PurchaseOrderNotFound,
    PurchaseOrderConcurrencyError,
    PurchaseOrderAllocationConflict,
)
from app.modules.logistics.procurement.purchase_orders.domain.value_objects.money import PurchaseOrderCode
from app.modules.logistics.procurement.purchase_orders.infrastructure.persistence.models import (
    PurchaseOrderModel,
    PurchaseOrderRevisionModel,
    PurchaseOrderLineModel,
    PurchaseOrderSourceAllocationModel,
    PurchaseOrderSourceVarianceModel,
    PurchaseOrderApprovalDecisionModel,
    PurchaseOrderDispatchModel,
    PurchaseOrderAcknowledgementModel,
    PurchaseOrderAmendmentModel,
)


class PurchaseOrderRepository:
    """SQLAlchemy 2 persistence repository for Purchase Orders."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------
    def get_by_id(
        self,
        po_id: UUID,
        organization_id: UUID | None = None,
        include_children: bool = True,
    ) -> PurchaseOrderModel | None:
        """Fetch a purchase order by primary key."""
        stmt = select(PurchaseOrderModel).where(PurchaseOrderModel.id == po_id)
        if organization_id:
            stmt = stmt.where(PurchaseOrderModel.organization_id == organization_id)

        if include_children:
            stmt = stmt.options(
                selectinload(PurchaseOrderModel.revisions).selectinload(PurchaseOrderRevisionModel.lines),
                selectinload(PurchaseOrderModel.revisions).selectinload(PurchaseOrderRevisionModel.tax_components),
                selectinload(PurchaseOrderModel.revisions).selectinload(PurchaseOrderRevisionModel.charges),
                selectinload(PurchaseOrderModel.revisions).selectinload(PurchaseOrderRevisionModel.payment_terms),
                selectinload(PurchaseOrderModel.revisions).selectinload(PurchaseOrderRevisionModel.delivery_terms),
                selectinload(PurchaseOrderModel.revisions).selectinload(PurchaseOrderRevisionModel.delivery_schedules),
                selectinload(PurchaseOrderModel.allocations),
                selectinload(PurchaseOrderModel.variances),
                selectinload(PurchaseOrderModel.approval_decisions),
                selectinload(PurchaseOrderModel.dispatches),
                selectinload(PurchaseOrderModel.acknowledgements),
                selectinload(PurchaseOrderModel.amendments),
            )

        return self._db.execute(stmt).scalar_one_or_none()

    def get_by_id_or_raise(
        self,
        po_id: UUID,
        organization_id: UUID | None = None,
        include_children: bool = True,
    ) -> PurchaseOrderModel:
        """Fetch by primary key or raise PurchaseOrderNotFound."""
        po = self.get_by_id(po_id, organization_id, include_children)
        if not po:
            raise PurchaseOrderNotFound(f"Purchase order {po_id} not found.")
        return po

    def get_by_code(
        self,
        organization_id: UUID,
        code: str,
    ) -> PurchaseOrderModel | None:
        """Fetch by normalized code."""
        normalized = PurchaseOrderCode.normalize(code)
        stmt = (
            select(PurchaseOrderModel)
            .where(
                PurchaseOrderModel.organization_id == organization_id,
                PurchaseOrderModel.normalized_purchase_order_code == normalized,
            )
            .options(
                selectinload(PurchaseOrderModel.revisions).selectinload(PurchaseOrderRevisionModel.lines),
                selectinload(PurchaseOrderModel.allocations),
            )
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def get_by_source_decision_id(
        self,
        organization_id: UUID,
        source_decision_id: UUID,
    ) -> list[PurchaseOrderModel]:
        """Fetch all POs generated from a specific evaluation decision."""
        stmt = (
            select(PurchaseOrderModel)
            .where(
                PurchaseOrderModel.organization_id == organization_id,
                PurchaseOrderModel.source_decision_id == source_decision_id,
            )
            .order_by(PurchaseOrderModel.created_at)
        )
        return list(self._db.execute(stmt).scalars().all())

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
        """List purchase orders with pagination and filtering."""
        stmt = select(PurchaseOrderModel).where(PurchaseOrderModel.organization_id == organization_id)
        count_stmt = select(func.count(PurchaseOrderModel.id)).where(PurchaseOrderModel.organization_id == organization_id)

        if branch_id:
            stmt = stmt.where(PurchaseOrderModel.branch_id == branch_id)
            count_stmt = count_stmt.where(PurchaseOrderModel.branch_id == branch_id)
        if supplier_id:
            stmt = stmt.where(PurchaseOrderModel.supplier_business_partner_id == supplier_id)
            count_stmt = count_stmt.where(PurchaseOrderModel.supplier_business_partner_id == supplier_id)
        if status:
            stmt = stmt.where(PurchaseOrderModel.status == status)
            count_stmt = count_stmt.where(PurchaseOrderModel.status == status)
        if approval_status:
            stmt = stmt.where(PurchaseOrderModel.approval_status == approval_status)
            count_stmt = count_stmt.where(PurchaseOrderModel.approval_status == approval_status)

        total = self._db.execute(count_stmt).scalar_one()

        stmt = stmt.order_by(PurchaseOrderModel.created_at.desc()).limit(limit).offset(offset)
        orders = list(self._db.execute(stmt).scalars().all())

        return orders, total

    # ------------------------------------------------------------------
    # Atomic Code Generation
    # ------------------------------------------------------------------
    def generate_next_code(
        self,
        organization_id: UUID,
        site_code: str,
        year: int | None = None,
    ) -> tuple[str, str, int]:
        """Atomically generate the next PO code for the site and year.

        Pattern: OC-{SITE}-{YEAR}-{CORRELATOR:06d}
        Returns: (code, normalized_code, correlator)
        """
        target_year = year or datetime.now(timezone.utc).year
        site_clean = site_code.strip().upper()

        # Count existing orders for this org, site prefix, and year
        prefix_pattern = f"OC-{site_clean}-{target_year}-%"
        stmt = select(func.count(PurchaseOrderModel.id)).where(
            PurchaseOrderModel.organization_id == organization_id,
            PurchaseOrderModel.purchase_order_code.like(prefix_pattern),
        )
        count = self._db.execute(stmt).scalar_one()
        next_correlator = count + 1

        po_code_vo = PurchaseOrderCode.build(
            site_code=site_clean,
            year=target_year,
            correlator=next_correlator,
        )
        return str(po_code_vo), po_code_vo.normalized_value, next_correlator

    # ------------------------------------------------------------------
    # Write / Mutation methods
    # ------------------------------------------------------------------
    def save(self, order: PurchaseOrderModel) -> PurchaseOrderModel:
        """Persist a new or modified purchase order."""
        self._db.add(order)
        self._db.flush()
        return order

    def update_with_optimistic_lock(
        self,
        order: PurchaseOrderModel,
        expected_row_version: int,
    ) -> PurchaseOrderModel:
        """Update a purchase order enforcing row_version matching."""
        current_version = order.row_version or 1
        if current_version != expected_row_version:
            raise PurchaseOrderConcurrencyError(
                f"Purchase order {order.id} row_version mismatch: "
                f"expected {expected_row_version}, found {current_version}."
            )

        order.row_version = current_version + 1
        self._db.add(order)
        self._db.flush()
        return order

    def check_allocation_conflicts(
        self,
        decision_line_ids: Sequence[UUID],
    ) -> list[PurchaseOrderSourceAllocationModel]:
        """Check if any decision lines are already allocated to active POs."""
        if not decision_line_ids:
            return []

        stmt = select(PurchaseOrderSourceAllocationModel).where(
            PurchaseOrderSourceAllocationModel.evaluation_decision_line_id.in_(decision_line_ids),
            PurchaseOrderSourceAllocationModel.status.in_(["RESERVED", "ACTIVE"]),
        )
        return list(self._db.execute(stmt).scalars().all())

    def save_allocation(
        self,
        allocation: PurchaseOrderSourceAllocationModel,
    ) -> PurchaseOrderSourceAllocationModel:
        """Persist a source allocation record."""
        self._db.add(allocation)
        self._db.flush()
        return allocation

    def save_approval_decision(
        self,
        decision: PurchaseOrderApprovalDecisionModel,
    ) -> PurchaseOrderApprovalDecisionModel:
        """Persist an approval decision."""
        self._db.add(decision)
        self._db.flush()
        return decision
