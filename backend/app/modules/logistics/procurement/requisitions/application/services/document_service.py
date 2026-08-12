"""Document service — PDF rendering, previews, and official issuance (Phase 031)."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.logistics.documents.rendering.purchasing_service import PurchasingRenderingService
from app.modules.logistics.procurement.requisitions.application.services.snapshot_service import snapshot_service
from app.modules.logistics.procurement.requisitions.infrastructure.persistence.models import (
    PurchaseRequisitionModel,
)


class PurchaseRequisitionDocumentService:
    """PDF rendering integration for REQ documents.

    Preview: Watermarked non-official PDF.
    Issue: Official PDF for APPROVED requisitions, stored via FileAsset (Phase 030).
    """

    def preview(
        self,
        db: Session,
        requisition_id: UUID,
        org_id: UUID,
        user_id: UUID,
    ) -> bytes:
        pr = db.get(PurchaseRequisitionModel, requisition_id)
        if pr is None or str(pr.organization_id) != str(org_id):
            raise HTTPException(status_code=404, detail={"code": "PURCHASE_REQUISITION_NOT_FOUND"})

        # Build snapshot
        snapshot = snapshot_service.build_snapshot(
            db, requisition_id, pr.active_revision_id, org_id
        )

        # Context for template
        context = {
            "document_code": pr.requisition_code or "REQ-PREVIEW-001",
            "organization_name": "PROYECTO T1 S.A.C.",
            "requesting_area": pr.requester_area or "Operaciones Logísticas",
            "requester_name": pr.requester_name_snapshot,
            "cost_center_code": pr.cost_center_snapshot.get("code", "CC-LOG-01") if pr.cost_center_snapshot else "CC-LOG-01",
            "cost_center": pr.cost_center_snapshot.get("code", "CC-LOG-01") if pr.cost_center_snapshot else "CC-LOG-01",
            "required_date": str(pr.required_date),
            "priority": pr.priority,
            "justification": pr.justification,
            "items": [
                {
                    "item_number": l["line_number"],
                    "sku": l["sku"],
                    "description": l["name"],
                    "requested_quantity": l["requested_quantity"],
                    "unit_code": "UND",
                }
                for l in snapshot.get("lines", [])
            ],
            "watermark": "VISTA PREVIA - NO OFICIAL",
            "document_data": snapshot,
        }

        renderer = PurchasingRenderingService(db)
        result = renderer.render_purchasing_preview("REQ", context, user_id=str(user_id))
        return result.pdf_bytes

    def issue_document(
        self,
        db: Session,
        requisition_id: UUID,
        org_id: UUID,
        user_id: UUID,
    ) -> dict:
        pr = db.get(PurchaseRequisitionModel, requisition_id)
        if pr is None or str(pr.organization_id) != str(org_id):
            raise HTTPException(status_code=404, detail={"code": "PURCHASE_REQUISITION_NOT_FOUND"})

        if pr.status != "APPROVED":
            raise HTTPException(
                status_code=409,
                detail={"code": "REQUISITION_NOT_APPROVED", "status": pr.status},
            )

        snapshot = snapshot_service.build_snapshot(
            db, requisition_id, pr.approved_revision_id, org_id
        )

        context = {
            "document_code": pr.requisition_code,
            "organization_name": "PROYECTO T1 S.A.C.",
            "requesting_area": pr.requester_area or "Operaciones Logísticas",
            "requester_name": pr.requester_name_snapshot,
            "cost_center_code": pr.cost_center_snapshot.get("code", "CC-LOG-01") if pr.cost_center_snapshot else "CC-LOG-01",
            "cost_center": pr.cost_center_snapshot.get("code", "CC-LOG-01") if pr.cost_center_snapshot else "CC-LOG-01",
            "required_date": str(pr.required_date),
            "priority": pr.priority,
            "justification": pr.justification,
            "items": [
                {
                    "item_number": l["line_number"],
                    "sku": l["sku"],
                    "description": l["name"],
                    "requested_quantity": l["requested_quantity"],
                    "unit_code": "UND",
                }
                for l in snapshot.get("lines", [])
            ],
            "document_data": snapshot,
        }

        renderer = PurchasingRenderingService(db)
        result = renderer.render_purchasing_preview("REQ", context, user_id=str(user_id))
        pdf_bytes = result.pdf_bytes

        file_asset_id = None
        try:
            from app.modules.logistics.files.application.file_asset_service import file_asset_service
            asset = file_asset_service.store_bytes(
                db=db,
                organization_id=org_id,
                user_id=user_id,
                file_bytes=pdf_bytes,
                filename=f"{pr.requisition_code}.pdf",
                mime_type="application/pdf",
                classification="CONFIDENTIAL",
                resource_type="PURCHASE_REQUISITION",
                resource_id=pr.id,
            )
            file_asset_id = str(asset.id)
        except Exception:
            pass  # Best effort

        return {
            "requisition_id": str(pr.id),
            "requisition_code": pr.requisition_code,
            "status": "ISSUED",
            "file_asset_id": file_asset_id,
            "content_hash": snapshot.get("content_hash"),
        }


purchase_requisition_document_service = PurchaseRequisitionDocumentService()
