"""Application service for Organization, Branch and Warehouse logistics operations."""

from __future__ import annotations

from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.models.branch import Branch
from app.models.organization import Organization
from app.models.warehouse import Warehouse
from app.modules.logistics.organization.code_generator import entity_code_generator
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
        # El código lo genera el backend salvo que el cliente envíe uno explícito,
        # que se sigue aceptando por compatibilidad.
        code = data.code or entity_code_generator.next_code(db, "organization")
        if self.repo.exists_by_code(db, code):
            raise ApplicationError("ORGANIZATION_CODE_CONFLICT", "El código ya está en uso.", 409)
        org = self.repo.create(db, code=code, name=data.name, country_code=data.country_code, timezone=data.timezone, created_by=user_id, updated_by=user_id)
        return org

    def get(self, db: Session, org_id: UUID) -> Organization:
        return assert_organization_exists(db, org_id, self.repo)

    def list(
        self,
        db: Session,
        *,
        page: int,
        page_size: int,
        search: str | None,
        status: str | None,
        allowed_organization_ids: list[UUID] | None = None,
    ) -> PaginatedResponse[OrganizationResponse]:
        items, total = self.repo.list(
            db,
            page=page,
            page_size=page_size,
            search=search,
            status=status,
            allowed_organization_ids=allowed_organization_ids,
        )
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


from app.modules.logistics.geography.service import GeographyService


def to_branch_response(db: Session, branch: Branch) -> BranchResponse:
    res = BranchResponse.model_validate(branch)
    if branch.ubigeo_code:
        res.ubigeo = GeographyService.resolve_ubigeo(db, branch.ubigeo_code)
    return res


class BranchService:
    def __init__(self) -> None:
        self.repo = BranchRepository()
        self.org_repo = OrganizationRepository()

    def create(self, db: Session, org_id: UUID, data: BranchCreate, user_id: UUID) -> Branch:
        org = assert_organization_exists(db, org_id, self.org_repo)
        assert_organization_active(org)
        code = data.code or entity_code_generator.next_code(db, "branch")
        if self.repo.get_by_code_for_org(db, org_id, code):
            raise ApplicationError("BRANCH_CODE_CONFLICT", "El código de sede ya existe en esta organización.", 409)
        if data.ubigeo_code:
            dist = GeographyService.get_district_by_code(db, data.ubigeo_code)
            if not dist:
                raise ApplicationError("UBIGEO_NOT_FOUND", f"Código UBIGEO '{data.ubigeo_code}' no existe en el catálogo.", 422)
        branch = self.repo.create(
            db, organization_id=org_id, code=code, name=data.name,
            timezone=data.timezone, ubigeo_code=data.ubigeo_code, address_text=data.address_text,
            latitude=data.latitude, longitude=data.longitude,
            created_by=user_id, updated_by=user_id,
        )
        return branch

    def get(self, db: Session, branch_id: UUID) -> Branch:
        return assert_branch_exists(db, branch_id, self.repo)

    def list(self, db: Session, org_id: UUID, *, page: int, page_size: int, search: str | None, status: str | None) -> PaginatedResponse[BranchResponse]:
        items, total = self.repo.list_by_organization(db, org_id, page=page, page_size=page_size, search=search, status=status)
        return PaginatedResponse(
            items=[to_branch_response(db, b) for b in items],
            page=page, page_size=page_size, total=total,
            total_pages=ceil(total / page_size) if page_size else 0,
        )

    def update(self, db: Session, branch_id: UUID, data: BranchUpdate, user_id: UUID) -> Branch:
        branch = self.get(db, branch_id)
        if data.ubigeo_code:
            dist = GeographyService.get_district_by_code(db, data.ubigeo_code)
            if not dist:
                raise ApplicationError("UBIGEO_NOT_FOUND", f"Código UBIGEO '{data.ubigeo_code}' no existe en el catálogo.", 422)
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
        code = data.code or entity_code_generator.next_code(db, "warehouse")
        if self.repo.get_by_code_for_branch(db, branch_id, code):
            raise ApplicationError("WAREHOUSE_CODE_CONFLICT", "El código de almacén ya existe en esta sede.", 409)

        district, province, department = self._resolve_location(db, branch, data)

        wh = self.repo.create(
            db,
            branch_id=branch.id,
            # La organizacion se deriva de la sede persistida, nunca del cliente.
            # Sin esto el almacen nace huerfano e invisible para todo listado que
            # filtre por organization_id.
            organization_id=branch.organization_id,
            code=code, name=data.name,
            warehouse_type=data.warehouse_type, address=data.address,
            uses_branch_location=data.uses_branch_location,
            latitude=None if data.uses_branch_location else data.latitude,
            longitude=None if data.uses_branch_location else data.longitude,
            district=district, province=province, department=department,
            capacity=data.capacity, is_default=data.is_default, is_active=True,
            status="ACTIVE",
            created_by=user_id, updated_by=user_id,
        )
        if data.is_default:
            self.repo.clear_default_for_branch(db, branch_id, except_id=wh.id)
        return wh

    def get(self, db: Session, wh_id: UUID) -> Warehouse:
        wh = self.repo.get_by_id(db, wh_id)
        if not wh:
            raise ApplicationError("WAREHOUSE_NOT_FOUND", "El almacén no existe.", 404)
        return wh

    @staticmethod
    def _resolve_location(
        db: Session, branch: Branch, data: LogisticsWarehouseCreate
    ) -> tuple[str | None, str | None, str | None]:
        """Ubicación administrativa del almacén, derivada de su sede.

        Un almacén está donde está su sede. Si la sede tiene UBIGEO normalizado, se
        deriva de ahí e **ignora** lo que envíe el cliente: así es imposible
        registrar un almacén de una sede de Lima declarando Arequipa.

        Si la sede aún no tiene UBIGEO —quedó nullable en F004.5 y ninguna sede
        existente lo tiene todavía— se conserva el texto recibido para no dejar el
        alta inoperativa. Ese caso queda marcado como pendiente de normalizar.
        """
        if branch.ubigeo_code:
            district = GeographyService.resolve_ubigeo(db, branch.ubigeo_code)
            if district is not None:
                return (
                    district.district_name,
                    district.province_name,
                    district.department_name,
                )
        return data.district, data.province, data.department

    def get_for_branch(self, db: Session, branch_id: UUID, wh_id: UUID) -> Warehouse:
        wh = self.get(db, wh_id)
        assert_warehouse_belongs_to_branch(wh, branch_id)
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
        if values.get("uses_branch_location") is True:
            # No conservar coordenadas propias dormidas: podrían quedar obsoletas
            # mientras la sede continúa moviéndose.
            values["latitude"] = None
            values["longitude"] = None
        elif (
            ("latitude" in values or "longitude" in values)
            and values.get("uses_branch_location") is not False
            and wh.uses_branch_location
        ):
            raise ApplicationError(
                "WAREHOUSE_LOCATION_MODE_REQUIRED",
                "Desactiva la ubicación heredada antes de guardar coordenadas propias.",
                422,
            )
        if values:
            self.repo.update(db, wh, updated_by=user_id, **values)
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
