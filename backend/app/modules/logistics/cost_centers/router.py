"""FastAPI router for Cost Centers (Phase 031)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import (
    require_permission,
    resolve_organization_id,
)
from app.modules.logistics.cost_centers.dto import (
    CostCenterCreate,
    CostCenterResponse,
    CostCenterUpdate,
)
from app.modules.logistics.cost_centers.service import cost_center_service
from app.modules.logistics.principal import LogisticsPrincipal

router = APIRouter(
    prefix="/cost-centers",
    tags=["Logistics - Cost Centers"],
)


@router.post(
    "",
    response_model=CostCenterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new cost center",
)
def create_cost_center(
    data: CostCenterCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.cost_centers.manage")),
    db: Session = Depends(get_db),
) -> CostCenterResponse:
    org_id = resolve_organization_id(principal)
    cc = cost_center_service.create(
        db=db,
        org_id=org_id,
        user_id=principal.user_id,
        code=data.code,
        name=data.name,
        description=data.description,
        branch_id=data.branch_id,
        responsible_user_id=data.responsible_user_id,
        parent_cost_center_id=data.parent_cost_center_id,
        valid_from=data.valid_from,
        valid_until=data.valid_until,
    )
    db.commit()
    db.refresh(cc)
    return CostCenterResponse.model_validate(cc)


@router.get(
    "",
    response_model=list[CostCenterResponse],
    summary="List cost centers for the organization",
)
def list_cost_centers(
    status_param: str | None = Query(default=None, alias="status"),
    branch_id: UUID | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.cost_centers.read")),
    db: Session = Depends(get_db),
) -> list[CostCenterResponse]:
    org_id = resolve_organization_id(principal)
    ccs = cost_center_service.list(
        db=db,
        org_id=org_id,
        status=status_param,
        branch_id=branch_id,
        skip=skip,
        limit=limit,
    )
    return [CostCenterResponse.model_validate(cc) for cc in ccs]


@router.get(
    "/{cost_center_id}",
    response_model=CostCenterResponse,
    summary="Get cost center details",
)
def get_cost_center(
    cost_center_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.cost_centers.read")),
    db: Session = Depends(get_db),
) -> CostCenterResponse:
    org_id = resolve_organization_id(principal)
    cc = cost_center_service.get(db=db, cost_center_id=cost_center_id, org_id=org_id)
    return CostCenterResponse.model_validate(cc)


@router.patch(
    "/{cost_center_id}",
    response_model=CostCenterResponse,
    summary="Update cost center fields",
)
def update_cost_center(
    cost_center_id: UUID,
    data: CostCenterUpdate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.cost_centers.manage")),
    db: Session = Depends(get_db),
) -> CostCenterResponse:
    org_id = resolve_organization_id(principal)
    fields = data.model_dump(exclude_unset=True)
    row_version = fields.pop("row_version")
    cc = cost_center_service.update(
        db=db,
        cost_center_id=cost_center_id,
        org_id=org_id,
        user_id=principal.user_id,
        row_version=row_version,
        **fields,
    )
    db.commit()
    db.refresh(cc)
    return CostCenterResponse.model_validate(cc)


@router.post(
    "/{cost_center_id}/activate",
    response_model=CostCenterResponse,
    summary="Activate a cost center",
)
def activate_cost_center(
    cost_center_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.cost_centers.manage")),
    db: Session = Depends(get_db),
) -> CostCenterResponse:
    org_id = resolve_organization_id(principal)
    cc = cost_center_service.activate(
        db=db, cost_center_id=cost_center_id, org_id=org_id, user_id=principal.user_id
    )
    db.commit()
    db.refresh(cc)
    return CostCenterResponse.model_validate(cc)


@router.post(
    "/{cost_center_id}/deactivate",
    response_model=CostCenterResponse,
    summary="Deactivate a cost center",
)
def deactivate_cost_center(
    cost_center_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.cost_centers.manage")),
    db: Session = Depends(get_db),
) -> CostCenterResponse:
    org_id = resolve_organization_id(principal)
    cc = cost_center_service.deactivate(
        db=db, cost_center_id=cost_center_id, org_id=org_id, user_id=principal.user_id
    )
    db.commit()
    db.refresh(cc)
    return CostCenterResponse.model_validate(cc)


@router.post(
    "/{cost_center_id}/archive",
    response_model=CostCenterResponse,
    summary="Archive a cost center",
)
def archive_cost_center(
    cost_center_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.cost_centers.manage")),
    db: Session = Depends(get_db),
) -> CostCenterResponse:
    org_id = resolve_organization_id(principal)
    cc = cost_center_service.archive(
        db=db, cost_center_id=cost_center_id, org_id=org_id, user_id=principal.user_id
    )
    db.commit()
    db.refresh(cc)
    return CostCenterResponse.model_validate(cc)
