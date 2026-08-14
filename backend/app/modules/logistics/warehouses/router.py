"""FastAPI router for Phase 022 — Warehouses & Locations Hierarchy."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.pdf_response import PDF_RESPONSE_SCHEMA, build_pdf_download_response
from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.warehouses.bulk_generation_service import WarehouseLocationBulkService
from app.modules.logistics.warehouses.capacity_restriction_service import WarehouseCapacityRestrictionService
from app.modules.logistics.warehouses.label_service import WarehouseLocationLabelService
from app.modules.logistics.warehouses.layout_service import WarehouseLayoutService
from app.modules.logistics.warehouses.location_service import WarehouseLocationService
from app.modules.logistics.warehouses.qr_service import WarehouseLocationQRService
from app.modules.logistics.warehouses.schemas import (
    WarehouseCreate,
    WarehouseLayoutNodeCreate,
    WarehouseLayoutVersionCreate,
    WarehouseLocationBulkExecuteRequest,
    WarehouseLocationBulkPreviewRequest,
    WarehouseLocationCapacityCreate,
    WarehouseLocationCapacityResponse,
    WarehouseLocationCreate,
    WarehouseLocationMovePreviewResponse,
    WarehouseLocationMoveRequest,
    WarehouseLocationQRRotateRequest,
    WarehouseLocationResponse,
    WarehouseLocationRestrictionCreate,
    WarehouseLocationRestrictionResponse,
    WarehouseLocationUpdate,
    WarehouseResponse,
    WarehouseUpdate,
)
from app.modules.logistics.warehouses.warehouse_service import WarehouseService

router = APIRouter(prefix="/warehouses", tags=["logistics-warehouses-locations"])


def _resolve_org_id(principal: LogisticsPrincipal) -> UUID:
    if principal.default_organization_id:
        return UUID(str(principal.default_organization_id))
    if principal.organization_ids:
        return UUID(str(principal.organization_ids[0]))
    raise HTTPException(status_code=400, detail="No se encontró una organización válida en el contexto de sesión.")


# --- WAREHOUSES ENDPOINTS ---
@router.get("", response_model=list[WarehouseResponse])
def list_warehouses(
    branch_id: UUID | None = Query(None),
    warehouse_type: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouses.read")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseService(db)
    return service.list_warehouses(
        organization_id=org_id,
        branch_id=branch_id,
        warehouse_type=warehouse_type,
        status=status_filter,
        search=search,
    )


@router.post("", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    req: WarehouseCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouses.manage")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseService(db)
    return service.create_warehouse(organization_id=org_id, req=req, actor_id=principal.user_id)


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse(
    warehouse_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouses.read")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseService(db)
    wh = service.get_warehouse(organization_id=org_id, warehouse_id=warehouse_id)
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse no encontrado.")
    return wh


@router.put("/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(
    warehouse_id: UUID,
    req: WarehouseUpdate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouses.manage")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseService(db)
    return service.update_warehouse(
        organization_id=org_id, warehouse_id=warehouse_id, req=req, actor_id=principal.user_id
    )


@router.post("/{warehouse_id}/status", response_model=WarehouseResponse)
def set_warehouse_status(
    warehouse_id: UUID,
    status_val: str = Query(..., alias="status"),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouses.manage")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseService(db)
    return service.set_warehouse_status(
        organization_id=org_id, warehouse_id=warehouse_id, status=status_val, actor_id=principal.user_id
    )


# --- LOCATIONS ENDPOINTS ---
@router.get("/{warehouse_id}/locations", response_model=list[WarehouseLocationResponse])
def list_locations(
    warehouse_id: UUID,
    parent_location_id: UUID | None = Query(None),
    location_type: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouses.read")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseLocationService(db)
    return service.list_locations(
        organization_id=org_id,
        warehouse_id=warehouse_id,
        parent_location_id=parent_location_id,
        location_type=location_type,
        status=status_filter,
    )


@router.post("/{warehouse_id}/locations", response_model=WarehouseLocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(
    warehouse_id: UUID,
    req: WarehouseLocationCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouse_locations.create")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    req.warehouse_id = warehouse_id
    service = WarehouseLocationService(db)
    return service.create_location(organization_id=org_id, req=req, actor_id=principal.user_id)


@router.get("/locations/{location_id}", response_model=WarehouseLocationResponse)
def get_location(
    location_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouses.read")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseLocationService(db)
    loc = service.get_location(organization_id=org_id, location_id=location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="WarehouseLocation no encontrada.")
    return loc


@router.put("/locations/{location_id}", response_model=WarehouseLocationResponse)
def update_location(
    location_id: UUID,
    req: WarehouseLocationUpdate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouse_locations.manage")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseLocationService(db)
    return service.update_location(
        organization_id=org_id, location_id=location_id, req=req, actor_id=principal.user_id
    )


@router.get("/{warehouse_id}/location-tree")
def get_location_tree(
    warehouse_id: UUID,
    root_location_id: UUID | None = Query(None),
    max_depth: int = Query(10, ge=1, le=10),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouses.read")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseLocationService(db)
    return service.get_tree(
        organization_id=org_id, warehouse_id=warehouse_id, root_location_id=root_location_id, max_depth=max_depth
    )


@router.post("/locations/{location_id}/move-preview", response_model=WarehouseLocationMovePreviewResponse)
def move_location_preview(
    location_id: UUID,
    new_parent_location_id: UUID | None = Query(None),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouse_locations.move")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseLocationService(db)
    return service.move_preview(
        organization_id=org_id, location_id=location_id, new_parent_location_id=new_parent_location_id
    )


@router.post("/locations/{location_id}/move", response_model=WarehouseLocationResponse)
def move_location(
    location_id: UUID,
    req: WarehouseLocationMoveRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouse_locations.move")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseLocationService(db)
    return service.move_location(
        organization_id=org_id,
        location_id=location_id,
        new_parent_location_id=req.new_parent_location_id,
        reason=req.reason,
        actor_id=principal.user_id,
    )


# --- BULK LOCATIONS ENDPOINTS ---
@router.post("/{warehouse_id}/bulk-locations/preview")
def bulk_locations_preview(
    warehouse_id: UUID,
    req: WarehouseLocationBulkPreviewRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouse_locations.create")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    req.warehouse_id = warehouse_id
    service = WarehouseLocationBulkService(db)
    return service.generate_preview(organization_id=org_id, req=req)


@router.post("/{warehouse_id}/bulk-locations/execute")
def bulk_locations_execute(
    warehouse_id: UUID,
    req: WarehouseLocationBulkExecuteRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouse_locations.create")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    req.preview_request.warehouse_id = warehouse_id
    service = WarehouseLocationBulkService(db)
    return service.execute_bulk(organization_id=org_id, req=req, actor_id=principal.user_id)


# --- CAPACITIES & RESTRICTIONS ENDPOINTS ---
@router.post("/locations/{location_id}/capacities", response_model=WarehouseLocationCapacityResponse, status_code=status.HTTP_201_CREATED)
def add_location_capacity(
    location_id: UUID,
    req: WarehouseLocationCapacityCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouse_locations.manage")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseCapacityRestrictionService(db)
    return service.add_capacity(organization_id=org_id, location_id=location_id, req=req, actor_id=principal.user_id)


@router.get("/locations/{location_id}/capacities", response_model=list[WarehouseLocationCapacityResponse])
def list_location_capacities(
    location_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouses.read")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseCapacityRestrictionService(db)
    return service.list_capacities(organization_id=org_id, location_id=location_id)


@router.post("/locations/{location_id}/restrictions", response_model=WarehouseLocationRestrictionResponse, status_code=status.HTTP_201_CREATED)
def add_location_restriction(
    location_id: UUID,
    req: WarehouseLocationRestrictionCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouse_locations.manage")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseCapacityRestrictionService(db)
    return service.add_restriction(organization_id=org_id, location_id=location_id, req=req, actor_id=principal.user_id)


@router.get("/locations/{location_id}/restrictions", response_model=list[WarehouseLocationRestrictionResponse])
def list_location_restrictions(
    location_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouses.read")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseCapacityRestrictionService(db)
    return service.list_restrictions(organization_id=org_id, location_id=location_id)


# --- LAYOUT ENDPOINTS ---
@router.post("/{warehouse_id}/layouts", status_code=status.HTTP_201_CREATED)
def create_layout_version(
    warehouse_id: UUID,
    req: WarehouseLayoutVersionCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouse_layouts.manage")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseLayoutService(db)
    ver = service.create_layout_version(
        organization_id=org_id, warehouse_id=warehouse_id, req=req, actor_id=principal.user_id
    )
    return {"id": str(ver.id), "version": ver.version, "status": ver.status}


@router.post("/layouts/{layout_version_id}/nodes", status_code=status.HTTP_201_CREATED)
def add_layout_node(
    layout_version_id: UUID,
    req: WarehouseLayoutNodeCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouse_layouts.manage")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseLayoutService(db)
    node = service.add_node_to_layout(
        organization_id=org_id, layout_version_id=layout_version_id, req=req, actor_id=principal.user_id
    )
    return {"id": str(node.id), "location_id": str(node.location_id) if node.location_id else None}


@router.post("/layouts/{layout_version_id}/activate")
def activate_layout_version(
    layout_version_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouse_layouts.activate")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseLayoutService(db)
    ver = service.activate_layout_version(
        organization_id=org_id, layout_version_id=layout_version_id, actor_id=principal.user_id
    )
    return {"id": str(ver.id), "version": ver.version, "status": ver.status}


@router.get("/{warehouse_id}/logical-map")
def get_logical_map(
    warehouse_id: UUID,
    floor_index: int = Query(1, ge=1),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouses.read")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseLayoutService(db)
    return service.get_logical_map(organization_id=org_id, warehouse_id=warehouse_id, floor_index=floor_index)


# --- QR & LABELS ENDPOINTS ---
@router.get("/locations/{location_id}/qr")
def get_location_qr(
    location_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouses.read")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseLocationQRService(db)
    qr_png = service.render_qr_png(organization_id=org_id, location_id=location_id)
    return Response(content=qr_png, media_type="image/png")


@router.post("/locations/{location_id}/qr/rotate")
def rotate_location_qr(
    location_id: UUID,
    req: WarehouseLocationQRRotateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouse_locations.manage")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseLocationQRService(db)
    new_qr = service.rotate_qr(
        organization_id=org_id, location_id=location_id, reason=req.reason, actor_id=principal.user_id
    )
    return {"public_reference": new_qr.public_reference, "qr_version": new_qr.qr_version}


@router.get("/location-qr/{public_reference}")
def resolve_location_qr(
    public_reference: str,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouses.read")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseLocationQRService(db)
    return service.resolve_public_qr(organization_id=org_id, public_reference=public_reference)


@router.get("/locations/{location_id}/label.pdf", responses=PDF_RESPONSE_SCHEMA)
def download_location_label_pdf(
    location_id: UUID,
    paper_size: str = Query("A6"),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouses.read")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseLocationLabelService(db)
    pdf_bytes, filename = service.render_single_label_pdf(
        organization_id=org_id, location_id=location_id, paper_size=paper_size
    )
    response = build_pdf_download_response(pdf_bytes, filename)
    service.record_single_label_download(
        organization_id=org_id,
        location_id=location_id,
        paper_size=paper_size,
        actor_id=principal.user_id,
    )
    return response


@router.post("/locations/labels/export", responses=PDF_RESPONSE_SCHEMA)
def export_batch_labels_pdf(
    location_ids: list[UUID],
    paper_size: str = Query("A6"),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.warehouses.read")),
    db: Session = Depends(get_db),
):
    org_id = _resolve_org_id(principal)
    service = WarehouseLocationLabelService(db)
    pdf_bytes, filename, rendered_count = service.export_batch_labels_pdf(
        organization_id=org_id, location_ids=location_ids, paper_size=paper_size
    )
    response = build_pdf_download_response(pdf_bytes, filename)
    service.record_batch_labels_download(
        organization_id=org_id,
        rendered_count=rendered_count,
        paper_size=paper_size,
        actor_id=principal.user_id,
    )
    return response
