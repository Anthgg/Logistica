"""API routes for Organization, Branch and Warehouse logistics endpoints.

Superficie canónica F004: Organization -> Branch -> Warehouse.

Autorización: se aplica el catálogo de permisos YA EXISTENTE
(``logistics.organizations.*``, ``logistics.branches.*``, ``logistics.warehouses.*``)
mediante ``require_permission`` y el aislamiento por organización mediante
``LogisticsPrincipal``. F004 no define permisos nuevos; eso pertenece a F006.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.csrf import verify_csrf
from app.modules.logistics.auth_dependencies import require_permission
from app.modules.logistics.organization.schemas import (
    BranchCreate,
    BranchResponse,
    BranchStatusUpdate,
    BranchUpdate,
    LogisticsWarehouseCreate,
    LogisticsWarehouseResponse,
    LogisticsWarehouseSetDefault,
    LogisticsWarehouseStatusUpdate,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationStatusUpdate,
    OrganizationUpdate,
)
from app.modules.logistics.organization.scope import (
    allowed_organization_ids,
    assert_can_access_branch,
    assert_can_access_organization,
    assert_can_access_warehouse,
)
from app.modules.logistics.organization.service import (
    BranchService,
    LogisticsWarehouseService,
    OrganizationService,
)
from app.modules.logistics.principal import LogisticsPrincipal
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
        principal: LogisticsPrincipal = Depends(
            require_permission("logistics.organizations.create")
        ),
        _csrf: None = Depends(verify_csrf),
    ):
        org = org_service.create(db, data, principal.user_id)
        db.commit()
        return OrganizationResponse.model_validate(org)

    @router.get("/organizations", response_model=PaginatedResponse[OrganizationResponse])
    def list_organizations(
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(
            require_permission("logistics.organizations.read")
        ),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        search: str | None = Query(None),
        status: str | None = Query(None),
    ):
        return org_service.list(
            db,
            page=page,
            page_size=page_size,
            search=search,
            status=status,
            allowed_organization_ids=allowed_organization_ids(principal),
        )

    @router.get("/organizations/{organization_id}", response_model=OrganizationResponse)
    def get_organization(
        organization_id: UUID,
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(
            require_permission("logistics.organizations.read")
        ),
    ):
        org = org_service.get(db, organization_id)
        assert_can_access_organization(principal, org.id)
        return OrganizationResponse.model_validate(org)

    @router.patch("/organizations/{organization_id}", response_model=OrganizationResponse)
    def update_organization(
        organization_id: UUID,
        data: OrganizationUpdate,
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(
            require_permission("logistics.organizations.update")
        ),
        _csrf: None = Depends(verify_csrf),
    ):
        assert_can_access_organization(principal, organization_id)
        org = org_service.update(db, organization_id, data, principal.user_id)
        db.commit()
        return OrganizationResponse.model_validate(org)

    @router.patch("/organizations/{organization_id}/status", response_model=OrganizationResponse)
    def change_org_status(
        organization_id: UUID,
        data: OrganizationStatusUpdate,
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(
            require_permission("logistics.organizations.change_status")
        ),
        _csrf: None = Depends(verify_csrf),
    ):
        assert_can_access_organization(principal, organization_id)
        org = org_service.change_status(db, organization_id, data, principal.user_id)
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
        principal: LogisticsPrincipal = Depends(
            require_permission("logistics.branches.create")
        ),
        _csrf: None = Depends(verify_csrf),
    ):
        assert_can_access_organization(principal, organization_id)
        branch = branch_service.create(db, organization_id, data, principal.user_id)
        db.commit()
        return BranchResponse.model_validate(branch)

    @router.get(
        "/organizations/{organization_id}/branches",
        response_model=PaginatedResponse[BranchResponse],
    )
    def list_branches(
        organization_id: UUID,
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(
            require_permission("logistics.branches.read")
        ),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        search: str | None = Query(None),
        status: str | None = Query(None),
    ):
        assert_can_access_organization(principal, organization_id)
        return branch_service.list(db, organization_id, page=page, page_size=page_size, search=search, status=status)

    @router.get("/branches/{branch_id}", response_model=BranchResponse)
    def get_branch(
        branch_id: UUID,
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(
            require_permission("logistics.branches.read")
        ),
    ):
        branch = branch_service.get(db, branch_id)
        assert_can_access_branch(principal, branch)
        return BranchResponse.model_validate(branch)

    @router.patch("/branches/{branch_id}", response_model=BranchResponse)
    def update_branch(
        branch_id: UUID,
        data: BranchUpdate,
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(
            require_permission("logistics.branches.update")
        ),
        _csrf: None = Depends(verify_csrf),
    ):
        assert_can_access_branch(principal, branch_service.get(db, branch_id))
        branch = branch_service.update(db, branch_id, data, principal.user_id)
        db.commit()
        return BranchResponse.model_validate(branch)

    @router.patch("/branches/{branch_id}/status", response_model=BranchResponse)
    def change_branch_status(
        branch_id: UUID,
        data: BranchStatusUpdate,
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(
            require_permission("logistics.branches.change_status")
        ),
        _csrf: None = Depends(verify_csrf),
    ):
        assert_can_access_branch(principal, branch_service.get(db, branch_id))
        branch = branch_service.change_status(db, branch_id, data, principal.user_id)
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
        principal: LogisticsPrincipal = Depends(
            require_permission("logistics.warehouses.create")
        ),
        _csrf: None = Depends(verify_csrf),
    ):
        assert_can_access_branch(principal, branch_service.get(db, branch_id))
        wh = wh_service.create(db, branch_id, data, principal.user_id)
        db.commit()
        return LogisticsWarehouseResponse.model_validate(wh)

    @router.get(
        "/branches/{branch_id}/warehouses",
        response_model=PaginatedResponse[LogisticsWarehouseResponse],
    )
    def list_warehouses(
        branch_id: UUID,
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(
            require_permission("logistics.warehouses.read")
        ),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        search: str | None = Query(None),
        status: str | None = Query(None),
        warehouse_type: str | None = Query(None),
        is_default: bool | None = Query(None),
    ):
        assert_can_access_branch(principal, branch_service.get(db, branch_id))
        return wh_service.list(db, branch_id, page=page, page_size=page_size, search=search, status=status, warehouse_type=warehouse_type, is_default=is_default)

    @router.get(
        "/branches/{branch_id}/warehouses/{warehouse_id}",
        response_model=LogisticsWarehouseResponse,
    )
    def get_warehouse(
        branch_id: UUID,
        warehouse_id: UUID,
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(
            require_permission("logistics.warehouses.read")
        ),
    ):
        """Detalle estructural del almacén.

        Anidado bajo la sede para no colisionar con ``GET /warehouses/{id}`` del
        módulo F022, que responde otro DTO.
        """
        assert_can_access_branch(principal, branch_service.get(db, branch_id))
        wh = wh_service.get_for_branch(db, branch_id, warehouse_id)
        return LogisticsWarehouseResponse.model_validate(wh)

    @router.patch("/warehouses/{warehouse_id}/status", response_model=LogisticsWarehouseResponse)
    def change_warehouse_status(
        warehouse_id: UUID,
        data: LogisticsWarehouseStatusUpdate,
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(
            require_permission("logistics.warehouses.change_status")
        ),
        _csrf: None = Depends(verify_csrf),
    ):
        assert_can_access_warehouse(db, principal, wh_service.get(db, warehouse_id))
        wh = wh_service.change_status(db, warehouse_id, data, principal.user_id)
        db.commit()
        return LogisticsWarehouseResponse.model_validate(wh)

    @router.post("/warehouses/{warehouse_id}/set-default", response_model=LogisticsWarehouseResponse)
    def set_default_warehouse(
        warehouse_id: UUID,
        data: LogisticsWarehouseSetDefault,
        db: Session = Depends(get_db),
        principal: LogisticsPrincipal = Depends(
            require_permission("logistics.warehouses.set_default")
        ),
        _csrf: None = Depends(verify_csrf),
    ):
        assert_can_access_warehouse(db, principal, wh_service.get(db, warehouse_id))
        wh = wh_service.set_default(db, warehouse_id, data, principal.user_id)
        db.commit()
        return LogisticsWarehouseResponse.model_validate(wh)

    return router
