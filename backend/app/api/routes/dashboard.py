from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.permissions import LOGISTICS_READ_ROLES
from app.database.session import get_db
from app.dependencies.permissions import require_permissions
from app.i18n import locale_from_request, translate_event, translate_resource
from app.models.user import User
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
service = DashboardService()


@router.get("/summary", response_model=DashboardSummary, summary="Resumen operativo")
def dashboard_summary(
    request: Request,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*LOGISTICS_READ_ROLES)),
) -> DashboardSummary:
    summary = service.summary(database)
    locale = locale_from_request(request)
    return summary.model_copy(
        update={
            "recent_activity": [
                item.model_copy(
                    update={
                        "event_type_label": translate_event(item.event_type, locale),
                        "resource_type_label": translate_resource(
                            item.resource_type, locale
                        ),
                    }
                )
                for item in summary.recent_activity
            ]
        }
    )
