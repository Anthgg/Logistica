from __future__ import annotations

from typing import List, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.organization import Organization
from app.models.warehouse import Warehouse


class OrganizationRepository:
    def get_by_id(self, db: Session, org_id: UUID) -> Organization | None:
        return db.get(Organization, org_id)

    def exists_by_code(self, db: Session, code: str) -> bool:
        return db.scalar(select(Organization).where(Organization.code == code)) is not None

    def create(self, db: Session, **values) -> Organization:
        org = Organization(**values)
        db.add(org)
        db.flush()
        return org

    def list(
        self,
        db: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status: str | None = None,
    ) -> Tuple[List[Organization], int]:
        filters = []
        if status:
            filters.append(Organization.status == status)
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    Organization.code.ilike(pattern),
                    Organization.name.ilike(pattern),
                )
            )

        total = db.scalar(select(func.count()).select_from(Organization).where(*filters)) or 0
        items = list(
            db.scalars(
                select(Organization)
                .where(*filters)
                .order_by(Organization.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

    def update(self, db: Session, org: Organization, **values) -> Organization:
        for k, v in values.items():
            setattr(org, k, v)
        db.flush()
        return org

    def has_active_branches(self, db: Session, org_id: UUID) -> bool:
        stmt = select(Branch).where(
            Branch.organization_id == org_id,
            Branch.status == "active",
        ).limit(1)
        return db.scalar(stmt) is not None

    def set_status(self, db: Session, org: Organization, status: str) -> Organization:
        org.status = status
        db.flush()
        return org


class BranchRepository:
    def get_by_id(self, db: Session, branch_id: UUID) -> Branch | None:
        return db.get(Branch, branch_id)

    def get_by_code_for_org(self, db: Session, org_id: UUID, code: str) -> Branch | None:
        return db.scalar(
            select(Branch).where(
                Branch.organization_id == org_id,
                Branch.code == code,
            )
        )

    def create(self, db: Session, **values) -> Branch:
        branch = Branch(**values)
        db.add(branch)
        db.flush()
        return branch

    def list_by_organization(
        self,
        db: Session,
        org_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status: str | None = None,
    ) -> Tuple[List[Branch], int]:
        filters = [Branch.organization_id == org_id]
        if status:
            filters.append(Branch.status == status)
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    Branch.code.ilike(pattern),
                    Branch.name.ilike(pattern),
                )
            )

        total = db.scalar(select(func.count()).select_from(Branch).where(*filters)) or 0
        items = list(
            db.scalars(
                select(Branch)
                .where(*filters)
                .order_by(Branch.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

    def update(self, db: Session, branch: Branch, **values) -> Branch:
        for k, v in values.items():
            setattr(branch, k, v)
        db.flush()
        return branch

    def has_active_warehouses(self, db: Session, branch_id: UUID) -> bool:
        stmt = select(Warehouse).where(
            Warehouse.branch_id == branch_id,
            Warehouse.is_active.is_(True),
        ).limit(1)
        return db.scalar(stmt) is not None

    def set_status(self, db: Session, branch: Branch, status: str) -> Branch:
        branch.status = status
        db.flush()
        return branch


class LogisticsWarehouseRepository:
    def get_by_id(self, db: Session, wh_id: UUID) -> Warehouse | None:
        return db.get(Warehouse, wh_id)

    def get_by_code_for_branch(self, db: Session, branch_id: UUID, code: str) -> Warehouse | None:
        return db.scalar(
            select(Warehouse).where(
                Warehouse.branch_id == branch_id,
                Warehouse.code == code,
            )
        )

    def create(self, db: Session, **values) -> Warehouse:
        wh = Warehouse(**values)
        db.add(wh)
        db.flush()
        return wh

    def clear_default_for_branch(self, db: Session, branch_id: UUID, except_id: UUID | None = None) -> None:
        stmt = select(Warehouse).where(
            Warehouse.branch_id == branch_id,
            Warehouse.is_default.is_(True),
        )
        if except_id:
            stmt = stmt.where(Warehouse.id != except_id)
        defaults = db.scalars(stmt).all()
        for d in defaults:
            d.is_default = False
        db.flush()

    def list_by_branch(
        self,
        db: Session,
        branch_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status: str | None = None,
        warehouse_type: str | None = None,
        is_default: bool | None = None,
    ) -> Tuple[List[Warehouse], int]:
        filters = [Warehouse.branch_id == branch_id]
        if status == "active":
            filters.append(Warehouse.is_active.is_(True))
        elif status == "inactive":
            filters.append(Warehouse.is_active.is_(False))
        if warehouse_type:
            filters.append(Warehouse.warehouse_type == warehouse_type)
        if is_default is not None:
            filters.append(Warehouse.is_default == is_default)
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    Warehouse.code.ilike(pattern),
                    Warehouse.name.ilike(pattern),
                )
            )

        total = db.scalar(select(func.count()).select_from(Warehouse).where(*filters)) or 0
        items = list(
            db.scalars(
                select(Warehouse)
                .where(*filters)
                .order_by(Warehouse.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

    def update(self, db: Session, wh: Warehouse, **values) -> Warehouse:
        for k, v in values.items():
            setattr(wh, k, v)
        db.flush()
        return wh

    def set_active(self, db: Session, wh: Warehouse, is_active: bool) -> Warehouse:
        wh.is_active = is_active
        db.flush()
        return wh
