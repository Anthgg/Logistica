from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import REPORT_ROLES
from app.database.session import get_db
from app.dependencies.permissions import require_permissions
from app.models.user import User
from app.schemas.report import CountGroup, DateCount, LowStockRow, RouteSummaryRow
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])
service = ReportService()


@router.get("/shipments-by-status", response_model=list[CountGroup])
def shipments_by_status(
    date_from: date | None = None,
    date_to: date | None = None,
    route_id: UUID | None = None,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*REPORT_ROLES)),
) -> list[CountGroup]:
    return service.shipments_by_status(database, date_from, date_to, route_id)


@router.get("/shipments-by-priority", response_model=list[CountGroup])
def shipments_by_priority(
    date_from: date | None = None,
    date_to: date | None = None,
    route_id: UUID | None = None,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*REPORT_ROLES)),
) -> list[CountGroup]:
    return service.shipments_by_priority(database, date_from, date_to, route_id)


@router.get("/deliveries-by-date", response_model=list[DateCount])
def deliveries_by_date(
    date_from: date | None = None,
    date_to: date | None = None,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*REPORT_ROLES)),
) -> list[DateCount]:
    return service.deliveries_by_date(database, date_from, date_to)


@router.get("/incidents-summary", response_model=list[CountGroup])
def incidents_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*REPORT_ROLES)),
) -> list[CountGroup]:
    return service.incidents_summary(database, date_from, date_to)


@router.get("/low-stock", response_model=list[LowStockRow])
def low_stock(
    warehouse_id: UUID | None = None,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*REPORT_ROLES)),
) -> list[LowStockRow]:
    return service.low_stock(database, warehouse_id)


@router.get("/routes-summary", response_model=list[RouteSummaryRow])
def routes_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    route_id: UUID | None = None,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*REPORT_ROLES)),
) -> list[RouteSummaryRow]:
    return service.routes_summary(database, date_from, date_to, route_id)
