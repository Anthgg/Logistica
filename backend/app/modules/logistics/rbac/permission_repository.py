from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.rbac.models_permission import LogisticsPermission
from app.modules.logistics.rbac.models_role_permission import LogisticsRolePermission


class PermissionRepository:
    def get_by_id(self, db: Session, perm_id: UUID) -> LogisticsPermission | None:
        return db.get(LogisticsPermission, perm_id)

    def get_by_code(self, db: Session, code: str) -> LogisticsPermission | None:
        return db.scalar(select(LogisticsPermission).where(LogisticsPermission.code == code))

    def list_by_codes(
        self, db: Session, codes: list[str]
    ) -> list[LogisticsPermission]:
        if not codes:
            return []
        return list(
            db.scalars(
                select(LogisticsPermission).where(
                    LogisticsPermission.code.in_(codes),
                    LogisticsPermission.status == "active",
                )
            )
        )

    def list(
        self, db: Session, category: str | None = None, status: str | None = None
    ) -> List[LogisticsPermission]:
        filters = []
        if category:
            filters.append(LogisticsPermission.category == category)
        if status:
            filters.append(LogisticsPermission.status == status)
        return list(db.scalars(select(LogisticsPermission).where(*filters).order_by(LogisticsPermission.code)))

    def create(self, db: Session, **values) -> LogisticsPermission:
        perm = LogisticsPermission(**values)
        db.add(perm)
        db.flush()
        return perm


class RolePermissionRepository:
    def list_by_role(self, db: Session, role_id: UUID) -> List[LogisticsRolePermission]:
        return list(
            db.scalars(
                select(LogisticsRolePermission).where(LogisticsRolePermission.role_id == role_id)
            )
        )

    def set_role_permissions(self, db: Session, role_id: UUID, permission_ids: List[UUID]) -> List[LogisticsRolePermission]:
        existing = db.scalars(
            select(LogisticsRolePermission).where(LogisticsRolePermission.role_id == role_id)
        ).all()
        for e in existing:
            db.delete(e)
        db.flush()

        new_items = [
            LogisticsRolePermission(role_id=role_id, permission_id=pid)
            for pid in permission_ids
        ]
        db.add_all(new_items)
        db.flush()
        return new_items

    def list_permission_codes_by_role(self, db: Session, role_id: UUID) -> list[str]:
        rows = db.execute(
            select(LogisticsPermission.code)
            .join(LogisticsRolePermission, LogisticsRolePermission.permission_id == LogisticsPermission.id)
            .where(LogisticsRolePermission.role_id == role_id, LogisticsRolePermission.effect == "allow",
                   LogisticsPermission.status == "active")
        ).all()
        return [r[0] for r in rows]

    def list_permission_codes_by_roles(self, db: Session, role_ids: list[UUID]) -> list[str]:
        if not role_ids:
            return []
        rows = db.execute(
            select(LogisticsPermission.code)
            .join(LogisticsRolePermission, LogisticsRolePermission.permission_id == LogisticsPermission.id)
            .where(
                LogisticsRolePermission.role_id.in_(role_ids),
                LogisticsRolePermission.effect == "allow",
                LogisticsPermission.status == "active",
            )
        ).all()
        return list({r[0] for r in rows})

    def grant(self, db: Session, role_id: UUID, permission_id: UUID, created_by: UUID | None = None) -> LogisticsRolePermission:
        rp = LogisticsRolePermission(role_id=role_id, permission_id=permission_id, effect="allow", created_by=created_by)
        db.add(rp)
        db.flush()
        return rp

    def revoke(self, db: Session, rp: LogisticsRolePermission) -> None:
        db.delete(rp)
        db.flush()
