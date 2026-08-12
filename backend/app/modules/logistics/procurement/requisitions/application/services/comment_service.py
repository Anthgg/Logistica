"""Comment service — manages comments and notes on requisitions (Phase 031)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.logistics.procurement.requisitions.domain.value_objects.enums import IMMUTABLE_COMMENT_TYPES
from app.modules.logistics.procurement.requisitions.infrastructure.persistence.models import (
    PurchaseRequisitionCommentModel,
    PurchaseRequisitionModel,
)


class PurchaseRequisitionCommentService:
    """Manages comments and notes attached to requisitions."""

    def add_comment(
        self,
        db: Session,
        requisition_id: UUID,
        org_id: UUID,
        user_id: UUID,
        body: str,
        comment_type: str = "GENERAL",
        visibility: str = "INTERNAL",
    ) -> PurchaseRequisitionCommentModel:
        if not body or not body.strip():
            raise HTTPException(status_code=422, detail={"code": "COMMENT_EMPTY"})
        clean_body = body.strip()
        if re.search(r"<[^>]+>", clean_body):
            raise HTTPException(status_code=422, detail={"code": "COMMENT_HTML_NOT_ALLOWED"})
        if len(clean_body) < 3 or len(clean_body) > 2000:
            raise HTTPException(
                status_code=422,
                detail={"code": "COMMENT_LENGTH_INVALID", "min": 3, "max": 2000},
            )

        pr = (
            db.query(PurchaseRequisitionModel)
            .filter(
                PurchaseRequisitionModel.id == requisition_id,
                PurchaseRequisitionModel.organization_id == org_id,
            )
            .first()
        )
        if pr is None:
            raise HTTPException(status_code=404, detail={"code": "PURCHASE_REQUISITION_NOT_FOUND"})

        c = PurchaseRequisitionCommentModel(
            requisition_id=requisition_id,
            revision_id=pr.active_revision_id,
            comment_type=comment_type,
            body=clean_body,
            visibility=visibility,
            created_by=user_id,
            status="ACTIVE",
        )
        db.add(c)
        db.flush()
        return c

    def list_comments(
        self,
        db: Session,
        requisition_id: UUID,
        org_id: UUID,
        user_id: UUID,
    ) -> list[PurchaseRequisitionCommentModel]:
        return (
            db.query(PurchaseRequisitionCommentModel)
            .filter(
                PurchaseRequisitionCommentModel.requisition_id == requisition_id,
                PurchaseRequisitionCommentModel.status == "ACTIVE",
            )
            .order_by(PurchaseRequisitionCommentModel.created_at)
            .all()
        )

    def archive_comment(
        self,
        db: Session,
        comment_id: UUID,
        org_id: UUID,
        user_id: UUID,
    ) -> PurchaseRequisitionCommentModel:
        c = db.get(PurchaseRequisitionCommentModel, comment_id)
        if c is None:
            raise HTTPException(status_code=404, detail={"code": "COMMENT_NOT_FOUND"})
        if c.comment_type in IMMUTABLE_COMMENT_TYPES:
            raise HTTPException(
                status_code=409,
                detail={"code": "DECISION_COMMENT_IMMUTABLE", "type": c.comment_type},
            )
        c.status = "ARCHIVED"
        return c


comment_service = PurchaseRequisitionCommentService()
