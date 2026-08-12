"""Application service for Organization, Branch and Warehouse logistics operations."""

from __future__ import annotations

from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.models.branch import Branch
from app.models.organization import Organization
from app.models.warehouse import Warehouse
from app.modules.logistics.organization.repository import (
    BranchRepository,
    LogisticsWarehouseRepository,
    OrganizationRepository,
)
from app.modules.logistics.organization.schemas import (
    BranchCreate,
    BranchResponse,
    BranchStatusUpdate,
    BranchUpdate,
    LogisticsWarehouseCreate,
    LogisticsWarehouseResponse,
    LogisticsWarehouseSetDefault,
    LogisticsWarehouseStatusUpdate,
    LogisticsWarehouseUpdate,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationStatusUpdate,
    OrganizationUpdate,
)
from app.schemas.common import PaginatedResponse


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def assert_organization_exists(db: Session, org_id: UUID, repo: OrganizationRepository) -> Organization:
    org = repo.get_by_id(db, org_id)
    if not org:
        raise ApplicationError("ORGANIZATION_NOT_FOUND", "La organización no existe.", 404)
    return org


def assert_organization_active(org: Organization) -> None:
    if org.status != "active":
        raise ApplicationError("ORGANIZATION_INACTIVE", "La organización está inactiva.", 409)


def assert_branch_exists(db: Session, branch_id: UUID, repo: BranchRepository) -> Branch:
    branch = repo.get_by_id(db, branch_id)
    if not branch:
        raise ApplicationError("BRANCH_NOT_FOUND", "La sede no existe.", 404)
    return branch


def assert_branch_active(branch: Branch) -> None:
    if branch.status != "active":
        raise ApplicationError("BRANCH_INACTIVE", "La sede está inactiva.", 409)


def assert_branch_belongs_to_org(branch: Branch, org_id: UUID) -> None:
    if branch.organization_id != org_id:
        raise ApplicationError("INVALID_BRANCH_HIERARCHY", "La sede no pertenece a esta organización.", 400)


def assert_warehouse_belongs_to_branch(wh: Warehouse, branch_id: UUID) -> None:
    if wh.branch_id != branch_id:
        raise ApplicationError("INVALID_WAREHOUSE_HIERARCHY", "El almacén no pertenece a esta sede.", 400)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class OrganizationService:
    def __init__(self) -> None:
        self.repo = OrganizationRepository()

    def create(self, db: Session, data: OrganizationCreate, user_id: UUID) -> Organization:
        if self.repo.exists_by_code(db, data.code):
            raise ApplicationError("ORGANIZATION_CODE_CONFLICT", "El código ya está en uso.", 409)
        org = self.repo.create(db, code=data.code, name=data.name, country_code=data.country_code, timezone=data.timezone, created_by=user_id, updated_by=user_id)
        return org

    def get(self, db: Session, org_id: UUID) -> Organization:
        return assert_organization_exists(db, org_id, self.repo)

    def list(self, db: Session, *, page: int, page_size: int, search: str | None, status: str | None) -> PaginatedResponse[OrganizationResponse]:
        items, total = self.repo.list(db, page=page, page_size=page_size, search=search, status=status)
        return PaginatedResponse(
            items=[OrganizationResponse.model_validate(o) for o in items],
            page=page, page_size=page_size, total=total,
            total_pages=ceil(total / page_size) if page_size else 0,
        )

    def update(self, db: Session, org_id: UUID, data: OrganizationUpdate, user_id: UUID) -> Organization:
        org = self.get(db, org_id)
        values = data.model_dump(exclude_unset=True)
        if values:
            self.repo.update(db, org, updated_by=user_id, **values)
        return org

    def change_status(self, db: Session, org_id: UUID, data: OrganizationStatusUpdate, user_id: UUID) -> Organization:
        org = self.get(db, org_id)
        if data.status == "inactive" and self.repo.has_active_branches(db, org_id):
            raise ApplicationError("ORGANIZATION_INACTIVE_CONFLICT", "No se puede inactivar una organización con sedes activas.", 409)
        self.repo.set_status(db, org, data.status)
        return org


class BranchService:
    def __init__(self) -> None:
        self.repo = BranchRepository()
        self.org_repo = OrganizationRepository()

    def create(self, db: Session, org_id: UUID, data: BranchCreate, user_id: UUID) -> Branch:
        org = assert_organization_exists(db, org_id, self.org_repo)
        assert_organization_active(org)
        if self.repo.get_by_code_for_org(db, org_id, data.code):
            raise ApplicationError("BRANCH_CODE_CONFLICT", "El código de sede ya existe en esta organización.", 409)
        branch = self.repo.create(
            db, organization_id=org_id, code=data.code, name=data.name,
            timezone=data.timezone, address_text=data.address_text,
            latitude=data.latitude, longitude=data.longitude,
            created_by=user_id, updated_by=user_id,
        )
        return branch

    def get(self, db: Session, branch_id: UUID) -> Branch:
        return assert_branch_exists(db, branch_id, self.repo)

    def list(self, db: Session, org_id: UUID, *, page: int, page_size: int, search: str | None, status: str | None) -> PaginatedResponse[BranchResponse]:
        items, total = self.repo.list_by_organization(db, org_id, page=page, page_size=page_size, search=search, status=status)
        return PaginatedResponse(
            items=[BranchResponse.model_validate(b) for b in items],
            page=page, page_size=page_size, total=total,
            total_pages=ceil(total / page_size) if page_size else 0,
        )

    def update(self, db: Session, branch_id: UUID, data: BranchUpdate, user_id: UUID) -> Branch:
        branch = self.get(db, branch_id)
        values = data.model_dump(exclude_unset=True)
        if values:
            self.repo.update(db, branch, updated_by=user_id, **values)
        return branch

    def change_status(self, db: Session, branch_id: UUID, data: BranchStatusUpdate, user_id: UUID) -> Branch:
        branch = self.get(db, branch_id)
        if data.status == "inactive" and self.repo.has_active_warehouses(db, branch_id):
            raise ApplicationError("BRANCH_INACTIVE_CONFLICT", "No se puede inactivar una sede con almacenes activos.", 409)
        self.repo.set_status(db, branch, data.status)
        return branch


class LogisticsWarehouseService:
    def __init__(self) -> None:
        self.repo = LogisticsWarehouseRepository()
        self.branch_repo = BranchRepository()

    def create(self, db: Session, branch_id: UUID, data: LogisticsWarehouseCreate, user_id: UUID) -> Warehouse:
        branch = assert_branch_exists(db, branch_id, self.branch_repo)
        assert_branch_active(branch)
        if self.repo.get_by_code_for_branch(db, branch_id, data.code):
            raise ApplicationError("WAREHOUSE_CODE_CONFLICT", "El código de almacén ya existe en esta sede.", 409)
        wh = self.repo.create(
            db, branch_id=branch_id, code=data.code, name=data.name,
            warehouse_type=data.warehouse_type, address=data.address,
            district=data.district, province=data.province, department=data.department,
            capacity=data.capacity, is_default=data.is_default, is_active=True,
        )
        if data.is_default:
            self.repo.clear_default_for_branch(db, branch_id, except_id=wh.id)
        return wh

    def get(self, db: Session, wh_id: UUID) -> Warehouse:
        wh = self.repo.get_by_id(db, wh_id)
        if not wh:
            raise ApplicationError("WAREHOUSE_NOT_FOUND", "El almacén no existe.", 404)
        return wh

    def list(self, db: Session, branch_id: UUID, *, page: int, page_size: int, search: str | None, status: str | None, warehouse_type: str | None, is_default: bool | None) -> PaginatedResponse[LogisticsWarehouseResponse]:
        items, total = self.repo.list_by_branch(db, branch_id, page=page, page_size=page_size, search=search, status=status, warehouse_type=warehouse_type, is_default=is_default)
        return PaginatedResponse(
            items=[LogisticsWarehouseResponse.model_validate(w) for w in items],
            page=page, page_size=page_size, total=total,
            total_pages=ceil(total / page_size) if page_size else 0,
        )

    def update(self, db: Session, wh_id: UUID, data: LogisticsWarehouseUpdate, user_id: UUID) -> Warehouse:
        wh = self.get(db, wh_id)
        values = data.model_dump(exclude_unset=True)
        if values:
            self.repo.update(db, wh, **values)
        return wh

    def change_status(self, db: Session, wh_id: UUID, data: LogisticsWarehouseStatusUpdate, user_id: UUID) -> Warehouse:
        wh = self.get(db, wh_id)
        is_active = data.status == "active"
        if is_active and wh.branch_id:
            branch = self.branch_repo.get_by_id(db, wh.branch_id)
            if branch and branch.status != "active":
                raise ApplicationError("WAREHOUSE_BRANCH_INACTIVE", "No se puede activar un almacén bajo una sede inactiva.", 409)
        self.repo.set_active(db, wh, is_active)
        return wh

    def set_default(self, db: Session, wh_id: UUID, data: LogisticsWarehouseSetDefault, user_id: UUID) -> Warehouse:
        wh = self.get(db, wh_id)
        if not wh.branch_id:
            raise ApplicationError("WAREHOUSE_NO_BRANCH", "El almacén no tiene sede asignada.", 409)
        if not wh.is_active:
            raise ApplicationError("WAREHOUSE_INACTIVE", "No se puede establecer como predeterminado un almacén inactivo.", 409)
        if data.is_default:
            self.repo.clear_default_for_branch(db, wh.branch_id, except_id=wh.id)
        wh.is_default = data.is_default
        db.flush()
        return wh