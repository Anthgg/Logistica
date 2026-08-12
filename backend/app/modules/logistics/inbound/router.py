"""Router aggregation for expected inbound operations."""

from fastapi import APIRouter

from app.modules.logistics.inbound.arrival_notices.presentation.routes.router import (
    router as arrival_notice_router,
)
from app.modules.logistics.inbound.gate_control.presentation.router import (
    router as gate_control_router,
)
from app.modules.logistics.inbound.dock_operations.presentation.router import (
    router as dock_operations_router,
)
from app.modules.logistics.inbound.reception_calendar.presentation.routes.router import (
    router as reception_calendar_router,
)
from app.modules.logistics.inbound.receiving.presentation.router import router as receiving_router
from app.modules.logistics.inbound.reception_differences.presentation.router import router as reception_differences_router
from app.modules.logistics.inbound.reception_differences.presentation.quality_plan_router import router as quality_plan_router
from app.modules.logistics.inbound.quality_quarantine.presentation.router import router as quality_quarantine_router


def create_inbound_router() -> APIRouter:
    router = APIRouter()
    router.include_router(arrival_notice_router)
    router.include_router(reception_calendar_router)
    router.include_router(gate_control_router)
    router.include_router(dock_operations_router)
    router.include_router(receiving_router)
    router.include_router(reception_differences_router)
    router.include_router(quality_plan_router)
    router.include_router(quality_quarantine_router)
    return router


__all__ = ["create_inbound_router"]
