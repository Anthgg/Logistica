"""CostCenter application service (Phase 031)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.logistics.cost_centers.models import CostCenterModel


class CostCenterService:
    """CRUD and lifecycle management for cost centers.
    
    No budget management. No accounting. No financial commitments.
    """

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _get_or_404(db: Session, cost_center_id: UUID, org_id: UUID) -> CostCenterModel:
        cc = (
            db.query(CostCenterModel)
            .filter(
                CostCenterModel.id == cost_center_id,
                CostCenterModel.organization_id == org_id,
            )
            .first()
        )
        if cc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "COST_CENTER_NOT_FOUND", "cost_center_id": str(cost_center_id)},
            )
        return cc

    @staticmethod
    def _normalize_code(raw: str) -> str:
        return raw.strip().upper().replace(" ", "_")

    def _detect_cycle(self, db: Session, cost_center_id: UUID, parent_id: UUID, max_depth: int = 10) -> bool:
        """Return True if setting parent_id would create a cycle."""
        current_id: UUID | None = parent_id
        for _ in range(max_depth):
            if current_id is None:
                return False
            if current_id == cost_center_id:
                return True
            parent = db.query(CostCenterModel.parent_cost_center_id).filter_by(id=current_id).first()
            current_id = parent[0] if parent else None
        return True  # Exceeded max depth — treat as cycle

    # ------------------------------------------------------------------ #
    # CRUD                                                                 #
    # ------------------------------------------------------------------ #

    def create(
        self,
        db: Session,
        org_id: UUID,
        user_id: UUID,
        code: str,
        name: str,
        description: str | None = None,
        branch_id: UUID | None = None,
        responsible_user_id: UUID | None = None,
        parent_cost_center_id: UUID | None = None,
        valid_from: date | None = None,
        valid_until: date | None = None,
    ) -> CostCenterModel:
        normalized = self._normalize_code(code)

        # Uniqueness check
        exists = (
            db.query(CostCenterModel)
            .filter(
                CostCenterModel.organization_id == org_id,
                CostCenterModel.normalized_code == normalized,
            )
            .first()
        )
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "COST_CENTER_CODE_CONFLICT", "normalized_code": normalized},
            )

        # Parent validation
        if parent_cost_center_id is not None:
            parent = db.query(CostCenterModel).filter_by(
                id=parent_cost_center_id, organization_id=org_id
            ).first()
            if parent is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "COST_CENTER_PARENT_NOT_FOUND"},
                )

        cc = CostCenterModel(
            organization_id=org_id,
            branch_id=branch_id,
            code=code.strip(),
            normalized_code=normalized,
            name=name.strip(),
            description=description,
            responsible_user_id=responsible_user_id,
            parent_cost_center_id=parent_cost_center_id,
            status="DRAFT",
            valid_from=valid_from or date.today(),
            valid_until=valid_until,
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(cc)
        db.flush()
        return cc

    def get(self, db: Session, cost_center_id: UUID, org_id: UUID) -> CostCenterModel:
        return self._get_or_404(db, cost_center_id, org_id)

    def list(
        self,
        db: Session,
        org_id: UUID,
        status: str | None = None,
        branch_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[CostCenterModel]:
        q = db.query(CostCenterModel).filter(CostCenterModel.organization_id == org_id)
        if status:
            q = q.filter(CostCenterModel.status == status)
        if branch_id:
            q = q.filter(CostCenterModel.branch_id == branch_id)
        return q.order_by(CostCenterModel.code).offset(skip).limit(limit).all()

    def update(
        self,
        db: Session,
        cost_center_id: UUID,
        org_id: UUID,
        user_id: UUID,
        row_version: int,
        **fields,
    ) -> CostCenterModel:
        cc = self._get_or_404(db, cost_center_id, org_id)
        if cc.row_version != row_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "COST_CENTER_VERSION_CONFLICT",
                    "expected": row_version,
                    "actual": cc.row_version,
                },
            )
        allowed = {"name", "description", "responsible_user_id", "valid_until"}
        for field, value in fields.items():
            if field in allowed and value is not None:
                setattr(cc, field, value)
        cc.updated_by = user_id
        cc.row_version += 1
        return cc

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    def activate(self, db: Session, cost_center_id: UUID, org_id: UUID, user_id: UUID) -> CostCenterModel:
        cc = self._get_or_404(db, cost_center_id, org_id)
        if cc.status not in ("DRAFT", "INACTIVE"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "COST_CENTER_STATUS_INVALID", "current_status": cc.status},
            )
        cc.status = "ACTIVE"
        cc.updated_by = user_id
        cc.row_version += 1
        return cc

    def deactivate(self, db: Session, cost_center_id: UUID, org_id: UUID, user_id: UUID) -> CostCenterModel:
        cc = self._get_or_404(db, cost_center_id, org_id)
        if cc.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "COST_CENTER_STATUS_INVALID", "current_status": cc.status},
            )
        cc.status = "INACTIVE"
        cc.updated_by = user_id
        cc.row_version += 1
        return cc

    def archive(self, db: Session, cost_center_id: UUID, org_id: UUID, user_id: UUID) -> CostCenterModel:
        from app.modules.logistics.procurement.requisitions.infrastructure.persistence.models import (
            PurchaseRequisitionModel,
        )
        cc = self._get_or_404(db, cost_center_id, org_id)
        # Cannot archive if referenced by open requisitions
        open_count = (
            db.query(func.count(PurchaseRequisitionModel.id))
            .filter(
                PurchaseRequisitionModel.cost_center_id == cost_center_id,
                PurchaseRequisitionModel.status.in_(["DRAFT", "SUBMITTED", "UNDER_REVIEW"]),
            )
            .scalar()
        )
        if open_count and open_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "COST_CENTER_IN_USE",
                    "open_requisitions": open_count,
                },
            )
        cc.status = "ARCHIVED"
        cc.updated_by = user_id
        cc.row_version += 1
        return cc


cost_center_service = CostCenterService()
