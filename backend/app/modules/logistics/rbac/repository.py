"""RBAC repository — data access for roles, assignments and conflicts."""

from __future__ import annotations

from datetime import datetime
from typing import List, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.logistics.rbac.models_assignment import LogisticsRoleAssignment
from app.modules.logistics.rbac.models_conflict import LogisticsRoleConflictRule
from app.modules.logistics.rbac.models_role import LogisticsRole
from app.modules.logistics.rbac.models_scope_rule import LogisticsRoleScopeRule


class RoleRepository:
    def get_by_id(self, db: Session, role_id: UUID) -> LogisticsRole | None:
        return db.get(LogisticsRole, role_id)

    def get_by_code(self, db: Session, code: str) -> LogisticsRole | None:
        return db.scalar(select(LogisticsRole).where(LogisticsRole.code == code))

    def list_by_ids(self, db: Session, role_ids: list[UUID]) -> list[LogisticsRole]:
        if not role_ids:
            return []
        return list(
            db.scalars(
                select(LogisticsRole).where(
                    LogisticsRole.id.in_(role_ids),
                    LogisticsRole.status == "active",
                )
            )
        )

    def list(self, db: Session, *, status: str | None = None) -> List[LogisticsRole]:
        filters = []
        if status:
            filters.append(LogisticsRole.status == status)
        return list(db.scalars(select(LogisticsRole).where(*filters).order_by(LogisticsRole.code)))

    def list_scope_rules(self, db: Session, role_id: UUID) -> List[LogisticsRoleScopeRule]:
        return list(db.scalars(
            select(LogisticsRoleScopeRule).where(LogisticsRoleScopeRule.role_id == role_id)
        ))

    def create(self, db: Session, **values) -> LogisticsRole:
        role = LogisticsRole(**values)
        db.add(role)
        db.flush()
        return role

    def add_scope_rule(self, db: Session, role_id: UUID, scope_type: str) -> LogisticsRoleScopeRule:
        rule = LogisticsRoleScopeRule(role_id=role_id, allowed_scope_type=scope_type)
        db.add(rule)
        db.flush()
        return rule


class RoleAssignmentRepository:
    def get_by_id(self, db: Session, assignment_id: UUID) -> LogisticsRoleAssignment | None:
        return db.get(LogisticsRoleAssignment, assignment_id)

    def list_by_user(
        self, db: Session, user_id: UUID, *, status: str | None = None,
        page: int = 1, page_size: int = 20,
    ) -> Tuple[List[LogisticsRoleAssignment], int]:
        filters = [LogisticsRoleAssignment.user_id == user_id]
        if status:
            filters.append(LogisticsRoleAssignment.status == status)
        total = db.scalar(select(func.count()).select_from(LogisticsRoleAssignment).where(*filters)) or 0
        items = list(db.scalars(
            select(LogisticsRoleAssignment).where(*filters)
            .order_by(LogisticsRoleAssignment.assigned_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
        ))
        return items, total

    def list_active_by_user(self, db: Session, user_id: UUID) -> List[LogisticsRoleAssignment]:
        """Asignaciones vigentes del usuario.

        El estado se compara en minúsculas. La escritura siempre produce `active`, y
        el enum canónico lo declara así, pero hay filas sembradas antes con `ACTIVE`:
        una comparación exacta las descartaba en silencio, de modo que el usuario
        perdía esos permisos sin que nada lo indicara. Normalizar al leer resuelve el
        caso sin tocar datos productivos ni añadir una migración.
        """
        now = func.now()
        return list(db.scalars(
            select(LogisticsRoleAssignment).where(
                LogisticsRoleAssignment.user_id == user_id,
                func.lower(LogisticsRoleAssignment.status) == "active",
                or_(LogisticsRoleAssignment.starts_at.is_(None), LogisticsRoleAssignment.starts_at <= now),
                or_(LogisticsRoleAssignment.ends_at.is_(None), LogisticsRoleAssignment.ends_at > now),
            )
        ))

    def find_equivalent(
        self, db: Session, user_id: UUID, role_id: UUID, scope_type: str,
        organization_id: UUID | None, branch_id: UUID | None, warehouse_id: UUID | None,
    ) -> LogisticsRoleAssignment | None:
        return db.scalar(
            select(LogisticsRoleAssignment).where(
                LogisticsRoleAssignment.user_id == user_id,
                LogisticsRoleAssignment.role_id == role_id,
                LogisticsRoleAssignment.scope_type == scope_type,
                LogisticsRoleAssignment.organization_id == organization_id if organization_id else LogisticsRoleAssignment.organization_id.is_(None),
                LogisticsRoleAssignment.branch_id == branch_id if branch_id else LogisticsRoleAssignment.branch_id.is_(None),
                LogisticsRoleAssignment.warehouse_id == warehouse_id if warehouse_id else LogisticsRoleAssignment.warehouse_id.is_(None),
                LogisticsRoleAssignment.status == "active",
            )
        )

    def create(self, db: Session, **values) -> LogisticsRoleAssignment:
        assignment = LogisticsRoleAssignment(**values)
        db.add(assignment)
        db.flush()
        return assignment

    def revoke(self, db: Session, assignment: LogisticsRoleAssignment, revoked_by: UUID, reason: str) -> LogisticsRoleAssignment:
        assignment.status = "revoked"
        assignment.revoked_by = revoked_by
        assignment.revoked_at = datetime.now(assignment.revoked_at.tzinfo) if assignment.revoked_at else datetime.utcnow()
        assignment.revocation_reason = reason
        db.flush()
        return assignment

    def update_dates(self, db: Session, assignment: LogisticsRoleAssignment, starts_at: datetime | None, ends_at: datetime | None) -> LogisticsRoleAssignment:
        if starts_at is not None:
            assignment.starts_at = starts_at
        if ends_at is not None:
            assignment.ends_at = ends_at
        db.flush()
        return assignment


class RoleConflictRepository:
    def list_conflicts(self, db: Session) -> List[LogisticsRoleConflictRule]:
        return list(db.scalars(
            select(LogisticsRoleConflictRule).where(LogisticsRoleConflictRule.status == "active")
        ))

    def get_conflict(self, db: Session, role_a_id: UUID, role_b_id: UUID) -> LogisticsRoleConflictRule | None:
        return db.scalar(
            select(LogisticsRoleConflictRule).where(
                or_(
                    (LogisticsRoleConflictRule.role_a_id == role_a_id) & (LogisticsRoleConflictRule.role_b_id == role_b_id),
                    (LogisticsRoleConflictRule.role_a_id == role_b_id) & (LogisticsRoleConflictRule.role_b_id == role_a_id),
                ),
                LogisticsRoleConflictRule.status == "active",
            )
        )

    def create(self, db: Session, **values) -> LogisticsRoleConflictRule:
        rule = LogisticsRoleConflictRule(**values)
        db.add(rule)
        db.flush()
        return rule
