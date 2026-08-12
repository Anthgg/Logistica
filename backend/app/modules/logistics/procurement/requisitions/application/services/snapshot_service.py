"""Snapshot service — builds immutable REQ snapshot (Phase 031)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.logistics.procurement.requisitions.infrastructure.persistence.models import (
    PurchaseRequisitionLineModel,
    PurchaseRequisitionModel,
    PurchaseRequisitionRevisionModel,
)


class PurchaseRequisitionSnapshotService:
    """Builds immutable snapshot payload of a requisition at issuance/approval.
    
    NEVER queries current master data — always relies on stored *_snapshot fields.
    """

    def build_snapshot(
        self,
        db: Session,
        requisition_id: UUID,
        revision_id: UUID | None,
        org_id: UUID,
    ) -> dict:
        pr = db.get(PurchaseRequisitionModel, requisition_id)
        if pr is None:
            raise ValueError(f"Requisition {requisition_id} not found.")

        target_rev_id = revision_id or pr.approved_revision_id or pr.submitted_revision_id or pr.active_revision_id
        rev = db.get(PurchaseRequisitionRevisionModel, target_rev_id) if target_rev_id else None

        lines = []
        if rev:
            db_lines = (
                db.query(PurchaseRequisitionLineModel)
                .filter(
                    PurchaseRequisitionLineModel.requisition_revision_id == rev.id,
                    PurchaseRequisitionLineModel.status == "ACTIVE",
                )
                .order_by(PurchaseRequisitionLineModel.line_number)
                .all()
            )
            for l in db_lines:
                lines.append({
                    "line_number": l.line_number,
                    "product_id": str(l.product_id),
                    "sku": l.sku_snapshot,
                    "name": l.product_name_snapshot,
                    "description": l.product_description_snapshot,
                    "requested_quantity": str(l.requested_quantity),
                    "requested_unit_id": str(l.requested_unit_id),
                    "base_quantity": str(l.base_quantity),
                    "base_unit_id": str(l.base_unit_id),
                    "line_justification": l.line_justification,
                })

        snapshot_payload = {
            "requisition_id": str(pr.id),
            "requisition_code": pr.requisition_code or "DRAFT-PREVIEW",
            "organization_id": str(pr.organization_id),
            "branch_id": str(pr.branch_id),
            "branch_snapshot": rev.branch_snapshot if rev else {},
            "cost_center_snapshot": pr.cost_center_snapshot,
            "requester_snapshot": rev.requester_snapshot if rev else {"name": pr.requester_name_snapshot},
            "priority": pr.priority,
            "required_date": str(pr.required_date),
            "destination_snapshot": rev.destination_snapshot if rev else None,
            "justification": pr.justification,
            "business_purpose": pr.business_purpose,
            "status": pr.status,
            "revision_number": rev.revision_number if rev else 1,
            "lines": lines,
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }

        serialized = json.dumps(snapshot_payload, sort_keys=True, ensure_ascii=True, default=str)
        snapshot_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        snapshot_payload["content_hash"] = snapshot_hash
        return snapshot_payload


snapshot_service = PurchaseRequisitionSnapshotService()
