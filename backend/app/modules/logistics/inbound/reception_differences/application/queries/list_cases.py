from __future__ import annotations
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ...infrastructure.persistence.models import ReceptionDifferenceCaseModel


def list_cases_query(db: Session, organization_id: UUID, *, search: str | None = None, status: str | None = None, severity: str | None = None, warehouse_id: UUID | None = None, supplier_id: UUID | None = None, carrier_id: UUID | None = None, receipt_id: UUID | None = None, difference_type: str | None = None, has_disputes: bool | None = None, has_critical_items: bool | None = None, created_from=None, created_to=None, page: int = 1, page_size: int = 50, sort_by: str = "created_at", sort_direction: str = "desc") -> tuple[list, int]:
    query = select(ReceptionDifferenceCaseModel).where(ReceptionDifferenceCaseModel.organization_id == organization_id)
    if search:
        from sqlalchemy import or_
        query = query.where(or_(ReceptionDifferenceCaseModel.case_code.ilike(f"%{search}%"), ReceptionDifferenceCaseModel.status.ilike(f"%{search}%")))
    if status: query = query.where(ReceptionDifferenceCaseModel.status == status)
    if severity: query = query.where(ReceptionDifferenceCaseModel.severity == severity)
    if warehouse_id: query = query.where(ReceptionDifferenceCaseModel.warehouse_id == warehouse_id)
    if supplier_id: query = query.where(ReceptionDifferenceCaseModel.supplier_business_partner_id == supplier_id)
    if carrier_id: query = query.where(ReceptionDifferenceCaseModel.carrier_business_partner_id == carrier_id)
    if receipt_id: query = query.where(ReceptionDifferenceCaseModel.inbound_receipt_id == receipt_id)
    if has_critical_items is not None: query = query.where((ReceptionDifferenceCaseModel.critical_item_count > 0) == has_critical_items)
    if created_from: query = query.where(ReceptionDifferenceCaseModel.created_at >= created_from)
    if created_to: query = query.where(ReceptionDifferenceCaseModel.created_at <= created_to)
    allowed_sort = {"created_at", "updated_at", "case_code", "status", "severity"}
    column = getattr(ReceptionDifferenceCaseModel, sort_by if sort_by in allowed_sort else "created_at")
    query = query.order_by(column.asc() if sort_direction.lower() == "asc" else column.desc())
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    rows = list(db.scalars(query.offset((page - 1) * page_size).limit(page_size)))
    return rows, total
