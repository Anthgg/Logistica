"""Logistics module - root router factory.

Creates and returns the `/logistics` APIRouter with all sub-module
routers attached.  The main application router includes the result of
:func:create_logistics_router under the existing `/api` prefix.
"""

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_session
from app.modules.logistics.constants import LOGISTICS_PHASE
from app.modules.logistics.dependencies import get_logistics_current_user


def _create_logistics_router() -> APIRouter:
    router = APIRouter(
        prefix="/logistics",
        tags=["Logistics"],
    )

    @router.get(
        "/health",
        summary="Logistics domain health",
        description="Technical endpoint that reports the logistics module status.",
    )
    def logistics_health(
        _user=Depends(get_logistics_current_user),
    ) -> dict[str, str]:
        return {
            "status": "ok",
            "domain": "logistics",
            "version": LOGISTICS_PHASE,
        }

    # Sub-module routers (imported lazily to avoid circular deps)
    from app.modules.logistics.audit import create_audit_event_router as audit_event_router
    from app.modules.logistics.rbac import create_rbac_router as rbac_router
    from app.modules.logistics.organization import create_organization_router as organization_router
    from app.modules.logistics.documents.codes.code_router import (
        router as document_code_router,
        site_codes_router,
    )
    from app.modules.logistics.documents.router import router as document_catalog_router
    from app.modules.logistics.documents.api.router import (
        create_router as documents_router,
        create_packages_router,
    )
    from app.modules.logistics.routes_module.api.router import create_router as routes_router
    from app.modules.logistics.files.api.router import create_router as files_router
    from app.modules.logistics.integrations.api.router import create_router as integrations_router
    from app.modules.logistics.me_router import create_me_router as me_router
    from app.modules.logistics.security import create_security_router as security_router

    from app.modules.logistics.documents.series.series_router import (
        router as document_series_router,
        talonarios_router as document_talonarios_router,
    )
    from app.modules.logistics.documents.rendering.rendering_router import (
        router as document_templates_router,
        status_router as document_renderer_status_router,
    )
    from app.modules.logistics.documents.rendering.purchasing_router import (
        router as purchasing_documents_router,
    )
    from app.modules.logistics.documents.rendering.inbound_router import (
        router as inbound_documents_router,
    )
    from app.modules.logistics.documents.rendering.inventory_router import (
        router as inventory_documents_router,
    )
    from app.modules.logistics.documents.rendering.outbound_router import (
        router as outbound_documents_router,
    )
    from app.modules.logistics.documents.rendering.dispatch_router import (
        router as dispatch_documents_router,
    )
    from app.modules.logistics.documents.rendering.transport_router import (
        router as transport_documents_router,
    )
    from app.modules.logistics.documents.rendering.delivery_router import (
        router as delivery_documents_router,
    )

    from app.modules.logistics.company_profile.router import router as company_profile_router
    from app.modules.logistics.warehouses.router import router as warehouses_router
    from app.modules.logistics.products.router import (
        products_router,
        categories_router,
        brands_router,
    )
    from app.modules.logistics.units.router import (
        dimensions_router,
        units_router,
        conversion_rules_router,
        conversion_engine_router,
        product_units_router,
    )
    from app.modules.logistics.partners.router import router as partners_router
    from app.modules.logistics.procurement.purchase_orders.presentation.routes.router import (
        router as purchase_orders_router,
    )
    from app.modules.logistics.ruc.presentation.routes.router import router as ruc_router
    from app.modules.logistics.vehicles.presentation.routes.router import (
        vehicles_router,
        makes_router as vehicle_makes_router,
        models_router as vehicle_models_router,
    )
    from app.modules.logistics.vehicle_verifications.presentation.routes.router import (
        router as vehicle_verifications_router,
    )
    from app.modules.logistics.drivers.presentation.routes.router import router as drivers_router
    from app.modules.logistics.files.presentation.routes.router import (
        router as files_v2_router,
        evidence_router as files_evidence_router,
    )
    from app.modules.logistics.inbound import create_inbound_router
    from app.modules.logistics.inventory.putaway.presentation.router import router as putaway_router
    from app.modules.logistics.inventory.ledger.presentation.routes.router import (
        router as inventory_ledger_router,
    )
    from app.modules.logistics.inventory.balances.presentation.routes.router import (
        router as inventory_balances_router,
    )

    from app.modules.logistics.cost_centers.router import router as cost_centers_router
    from app.modules.logistics.procurement.requisitions.presentation.routes.router import (
        router as requisitions_router,
    )
    from app.modules.logistics.procurement.evaluations.presentation.routes.router import (
        router as evaluations_router,
    )
    from app.modules.logistics.procurement.approvals.presentation.routes.router import (
        router as procurement_approvals_router,
    )

    router.include_router(company_profile_router)
    router.include_router(cost_centers_router)
    router.include_router(requisitions_router)
    router.include_router(evaluations_router)
    router.include_router(procurement_approvals_router)

    router.include_router(drivers_router)
    router.include_router(files_v2_router)
    router.include_router(files_evidence_router)
    router.include_router(warehouses_router)
    router.include_router(products_router)
    router.include_router(categories_router)
    router.include_router(brands_router)
    router.include_router(dimensions_router)
    router.include_router(units_router)
    router.include_router(conversion_rules_router)
    router.include_router(conversion_engine_router)
    router.include_router(product_units_router)
    router.include_router(partners_router)
    router.include_router(purchase_orders_router)
    router.include_router(ruc_router)
    router.include_router(vehicles_router)
    router.include_router(vehicle_makes_router)
    router.include_router(vehicle_models_router)
    router.include_router(vehicle_verifications_router)
    router.include_router(create_inbound_router())
    router.include_router(putaway_router)
    router.include_router(inventory_ledger_router, prefix="/inventory")
    router.include_router(inventory_balances_router, prefix="/inventory")

    router.include_router(document_catalog_router)
    router.include_router(document_code_router)
    router.include_router(site_codes_router)
    router.include_router(document_series_router)
    router.include_router(document_talonarios_router)
    router.include_router(document_templates_router)
    router.include_router(document_renderer_status_router)
    router.include_router(purchasing_documents_router)
    router.include_router(inbound_documents_router)
    router.include_router(inventory_documents_router)
    router.include_router(outbound_documents_router)
    router.include_router(dispatch_documents_router)
    router.include_router(transport_documents_router)
    router.include_router(delivery_documents_router)
    router.include_router(security_router(), prefix="/security", tags=["Logistics - Security"])
    router.include_router(me_router(), tags=["Logistics - Me"])
    router.include_router(audit_event_router(), tags=["Logistics - Audit Events"])
    router.include_router(rbac_router(), tags=["Logistics - RBAC"])
    router.include_router(organization_router(), tags=["Logistics - Organization"])
    router.include_router(documents_router(), prefix="/documents", tags=["Logistics - Documents"])
    router.include_router(create_packages_router())
    router.include_router(routes_router(), prefix="/routes", tags=["Logistics - Routes"])
    router.include_router(integrations_router(), prefix="/integrations", tags=["Logistics - Integrations"])

    return router
