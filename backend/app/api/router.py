from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.clients import router as clients_router
from app.api.routes.continuous_auth import router as continuous_auth_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.inventory import router as inventory_router
from app.api.routes.i18n import router as i18n_router
from app.api.routes.logistics_routes import router as logistics_routes_router
from app.api.routes.model_status import router as model_status_router
from app.api.routes.reports import router as reports_router
from app.api.routes.research import router as research_router
from app.api.routes.shipments import router as shipments_router
from app.api.routes.warehouses import router as warehouses_router

from app.modules.logistics import create_logistics_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(i18n_router)
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(clients_router)
api_router.include_router(shipments_router)
api_router.include_router(warehouses_router)
api_router.include_router(inventory_router)
api_router.include_router(logistics_routes_router)
api_router.include_router(incidents_router)
api_router.include_router(reports_router)
api_router.include_router(research_router)
api_router.include_router(continuous_auth_router)
api_router.include_router(model_status_router)

# ---------------------------------------------------------------------------
# Logistics domain (Phase 003 — modular monolith)
# ---------------------------------------------------------------------------
logistics_router = create_logistics_router()
api_router.include_router(logistics_router)
