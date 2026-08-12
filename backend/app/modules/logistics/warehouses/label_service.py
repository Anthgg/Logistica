"""Service for Location PDF Label rendering and batch export (Phase 022)."""

import base64
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.warehouse import Warehouse
from app.modules.logistics.audit.service import audit_service, AuditEventCommand
from app.modules.logistics.documents.rendering.rendering import (
    DocumentRenderCommand,
    DocumentRendererEngine,
)
from app.modules.logistics.warehouses.models import WarehouseLocationModel
from app.modules.logistics.warehouses.qr_service import WarehouseLocationQRService


class WarehouseLocationLabelService:
    """Service for rendering location PDF labels individually or in bulk multipage."""

    def __init__(self, db: Session):
        self.db = db
        self.renderer = DocumentRendererEngine()
        self.qr_service = WarehouseLocationQRService(db)

    def _write_audit(
        self, event_code: str, organization_id: UUID, actor_id: UUID | None, resource_id: Any, details: dict
    ):
        cmd = AuditEventCommand(
            event_code=event_code,
            actor_user_id=actor_id,
            organization_id=organization_id,
            resource_type="location_label",
            resource_id=str(resource_id),
            new_data=details,
        )
        audit_service.write_event(self.db, cmd)

    def render_single_label_pdf(
        self, organization_id: UUID, location_id: UUID, paper_size: str = "A6", actor_id: UUID | None = None
    ) -> tuple[bytes, str]:
        loc = self.db.get(WarehouseLocationModel, location_id)
        if not loc or loc.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="WarehouseLocation no encontrada.")

        org = self.db.get(Organization, organization_id)
        wh = self.db.get(Warehouse, loc.warehouse_id)

        qr_bytes = self.qr_service.render_qr_png(organization_id, location_id)
        qr_b64 = base64.b64encode(qr_bytes).decode("utf-8")

        data = {
            "title": f"Etiqueta de Ubicación {loc.full_code}",
            "company_name": org.name if org else "EMPRESA",
            "warehouse_name": wh.name if wh else "ALMACÉN",
            "location_full_code": loc.full_code,
            "location_code": loc.code,
            "location_type": loc.location_type,
            "usage_type": loc.usage_type,
            "status": loc.status,
            "qr_image_b64": f"data:image/png;base64,{qr_b64}",
            "paper_size": paper_size.upper(),
        }

        cmd = DocumentRenderCommand(
            document_type_code="EUB",
            template_key="inventory.location_label",
            document_title=f"ETIQUETA UBICACIÓN {loc.full_code}",
            organization_name=org.name if org else "EMPRESA",
            branch_name=wh.name if wh else "ALMACÉN",
            document_data=data,
            preview_mode=False,
        )

        res = self.renderer.render_pdf(cmd)
        filename = f"etiqueta_{loc.full_code.replace('-', '_')}.pdf"

        self._write_audit(
            event_code="logistics.warehouse_location.label_downloaded",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=loc.id,
            details={"full_code": loc.full_code, "paper_size": paper_size},
        )

        return res.pdf_bytes, filename

    def export_batch_labels_pdf(
        self, organization_id: UUID, location_ids: list[UUID], paper_size: str = "A6", actor_id: UUID | None = None
    ) -> tuple[bytes, str]:
        if not location_ids:
            raise HTTPException(status_code=400, detail="Debe proporcionar al menos una ubicación para exportar etiquetas.")

        org = self.db.get(Organization, organization_id)

        labels_data = []
        for loc_id in location_ids:
            loc = self.db.get(WarehouseLocationModel, loc_id)
            if loc and loc.organization_id == organization_id:
                wh = self.db.get(Warehouse, loc.warehouse_id)
                qr_bytes = self.qr_service.render_qr_png(organization_id, loc_id)
                qr_b64 = base64.b64encode(qr_bytes).decode("utf-8")

                labels_data.append({
                    "location_full_code": loc.full_code,
                    "location_code": loc.code,
                    "location_type": loc.location_type,
                    "warehouse_name": wh.name if wh else "ALMACÉN",
                    "qr_image_b64": f"data:image/png;base64,{qr_b64}",
                })

        data = {
            "title": f"Lote de Etiquetas ({len(labels_data)} ubicaciones)",
            "company_name": org.name if org else "EMPRESA",
            "paper_size": paper_size.upper(),
            "labels": labels_data,
        }

        cmd = DocumentRenderCommand(
            document_type_code="EUB",
            template_key="inventory.location_label",
            document_title=f"LOTE DE ETIQUETAS ({len(labels_data)})",
            organization_name=org.name if org else "EMPRESA",
            branch_name="Sedes Múltiples",
            document_data=data,
            preview_mode=False,
        )

        res = self.renderer.render_pdf(cmd)
        filename = f"lote_etiquetas_{len(labels_data)}_ubicaciones.pdf"

        self._write_audit(
            event_code="logistics.warehouse_location.batch_labels_downloaded",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=organization_id,
            details={"count": len(labels_data), "paper_size": paper_size},
        )

        return res.pdf_bytes, filename
