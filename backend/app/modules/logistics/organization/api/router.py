"""API routes for Organization, Branch and Warehouse logistics endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user, require_active_user
from app.dependencies.csrf import verify_csrf
from app.models.user import User
from app.modules.logistics.organization.schemas import (
    BranchCreate, BranchResponse, BranchStatusUpdate, BranchUpdate,
    LogisticsWarehouseCreate, LogisticsWarehouseResponse,
    LogisticsWarehouseSetDefault, LogisticsWarehouseStatusUpdate,
    OrganizationCreate, OrganizationResponse,
    OrganizationStatusUpdate, OrganizationUpdate,
)
from app.modules.logistics.organization.service import (
    BranchService,
    LogisticsWarehouseService,
    OrganizationService,
)
from app.schemas.common import PaginatedResponse


def _create_organization_router() -> APIRouter:
    router = APIRouter()
    org_service = OrganizationService()
    branch_service = BranchService()
    wh_service = LogisticsWarehouseService()

    # ------------------------------------------------------------------
    # Organizations
    # ------------------------------------------------------------------
    @router.post("/organizations", response_model=OrganizationResponse, status_code=201)
    def create_organization(
        data: OrganizationCreate,
        db: Session = Depends(get_db),
        user: User = Depends(require_active_user),
        _csrf: None = Depends(verify_csrf),
    ):
        org = org_service.create(db, data, user.id)
        db.commit()
        return OrganizationResponse.model_validate(org)

    @router.get("/organizations", response_model=PaginatedResponse[OrganizationResponse])
    def list_organizations(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        search: str | None = Query(None),
        status: str | None = Query(None),
    ):
        return org_service.list(db, page=page, page_size=page_size, search=search, status=status)

    @router.get("/organizations/{organization_id}", response_model=OrganizationResponse)
    def get_organization(
        organization_id: UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        return OrganizationResponse.model_validate(org_service.get(db, organization_id))

    @router.patch("/organizations/{organization_id}", response_model=OrganizationResponse)
    def update_organization(
        organization_id: UUID,
        data: OrganizationUpdate,
        db: Session = Depends(get_db),
        user: User = Depends(require_active_user),
        _csrf: None = Depends(verify_csrf),
    ):
        org = org_service.update(db, organization_id, data, user.id)
        db.commit()
        return OrganizationResponse.model_validate(org)

    @router.patch("/organizations/{organization_id}/status", response_model=OrganizationResponse)
    def change_org_status(
        organization_id: UUID,
        data: OrganizationStatusUpdate,
        db: Session = Depends(get_db),
        user: User = Depends(require_active_user),
        _csrf: None = Depends(verify_csrf),
    ):
        org = org_service.change_status(db, organization_id, data, user.id)
        db.commit()
        return OrganizationResponse.model_validate(org)

    # ------------------------------------------------------------------
    # Branches (nested under organization)
    # ------------------------------------------------------------------
    @router.post(
        "/organizations/{organization_id}/branches",
        response_model=BranchResponse,
        status_code=201,
    )
    def create_branch(
        organization_id: UUID,
        data: BranchCreate,
        db: Session = Depends(get_db),
        user: User = Depends(require_active_user),
        _csrf: None = Depends(verify_csrf),
    ):
        branch = branch_service.create(db, organization_id, data, user.id)
        db.commit()
        return BranchResponse.model_validate(branch)

    @router.get(
        "/organizations/{organization_id}/branches",
        response_model=PaginatedResponse[BranchResponse],
    )
    def list_branches(
        organization_id: UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        search: str | None = Query(None),
        status: str | None = Query(None),
    ):
        return branch_service.list(db, organization_id, page=page, page_size=page_size, search=search, status=status)

    @router.get("/branches/{branch_id}", response_model=BranchResponse)
    def get_branch(
        branch_id: UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        return BranchResponse.model_validate(branch_service.get(db, branch_id))

    @router.patch("/branches/{branch_id}", response_model=BranchResponse)
    def update_branch(
        branch_id: UUID,
        data: BranchUpdate,
        db: Session = Depends(get_db),
        user: User = Depends(require_active_user),
        _csrf: None = Depends(verify_csrf),
    ):
        branch = branch_service.update(db, branch_id, data, user.id)
        db.commit()
        return BranchResponse.model_validate(branch)

    @router.patch("/branches/{branch_id}/status", response_model=BranchResponse)
    def change_branch_status(
        branch_id: UUID,
        data: BranchStatusUpdate,
        db: Session = Depends(get_db),
        user: User = Depends(require_active_user),
        _csrf: None = Depends(verify_csrf),
    ):
        branch = branch_service.change_status(db, branch_id, data, user.id)
        db.commit()
        return BranchResponse.model_validate(branch)

    # ------------------------------------------------------------------
    # Warehouses (nested under branch)
    # ------------------------------------------------------------------
    @router.post(
        "/branches/{branch_id}/warehouses",
        response_model=LogisticsWarehouseResponse,
        status_code=201,
    )
    def create_warehouse(
        branch_id: UUID,
        data: LogisticsWarehouseCreate,
        db: Session = Depends(get_db),
        user: User = Depends(require_active_user),
        _csrf: None = Depends(verify_csrf),
    ):
        wh = wh_service.create(db, branch_id, data, user.id)
        db.commit()
        return LogisticsWarehouseResponse.model_validate(wh)

    @router.get(
        "/branches/{branch_id}/warehouses",
        response_model=PaginatedResponse[LogisticsWarehouseResponse],
    )
    def list_warehouses(
        branch_id: UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        search: str | None = Query(None),
        status: str | None = Query(None),
        warehouse_type: str | None = Query(None),
        is_default: bool | None = Query(None),
    ):
        return wh_service.list(db, branch_id, page=page, page_size=page_size, search=search, status=status, warehouse_type=warehouse_type, is_default=is_default)

    @router.patch("/warehouses/{warehouse_id}/status", response_model=LogisticsWarehouseResponse)
    def change_warehouse_status(
        warehouse_id: UUID,
        data: LogisticsWarehouseStatusUpdate,
        db: Session = Depends(get_db),
        user: User = Depends(require_active_user),
        _csrf: None = Depends(verify_csrf),
    ):
        wh = wh_service.change_status(db, warehouse_id, data, user.id)
        db.commit()
        return LogisticsWarehouseResponse.model_validate(wh)

    @router.post("/warehouses/{warehouse_id}/set-default", response_model=LogisticsWarehouseResponse)
    def set_default_warehouse(
        warehouse_id: UUID,
        data: LogisticsWarehouseSetDefault,
        db: Session = Depends(get_db),
        user: User = Depends(require_active_user),
        _csrf: None = Depends(verify_csrf),
    ):
        wh = wh_service.set_default(db, warehouse_id, data, user.id)
        db.commit()
        return LogisticsWarehouseResponse.model_validate(wh)

    return router
