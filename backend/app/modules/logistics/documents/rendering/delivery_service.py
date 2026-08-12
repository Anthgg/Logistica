"""Application service for Delivery Document Previews and Package Manifests (Phase 019).

Covers: POD, EP, RECH
Phase boundaries:
  - Seed and initialize Jinja2 templates.
  - Receiver and driver data masking.
  - Verification of delivery quantities and balances.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session

from app.modules.logistics.documents.rendering.delivery_schemas import (
    DeliveryPodContext,
    DeliveryPartialContext,
    DeliveryRejectionContext,
)
from app.modules.logistics.documents.rendering.transport_service import mask_sensitive_val
from app.modules.logistics.documents.rendering.rendering import (
    DocumentRenderCommand,
    DocumentRendererEngine,
    PdfRenderResult,
)
from app.modules.logistics.documents.rendering.template_models import (
    DocumentTemplateModel,
    DocumentTemplateVersionModel,
)
from app.modules.logistics.documents.rendering.template_repository import (
    DocumentTemplateRepository,
    DocumentTemplateVersionRepository,
)


DELIVERY_TEMPLATES: dict[str, tuple[str, str, str]] = {
    "POD": ("delivery.proof_of_delivery", "DELIVERY", "PRUEBA DE ENTREGA"),
    "EP": ("delivery.partial_delivery", "DELIVERY", "ACTA DE ENTREGA PARCIAL"),
    "RECH": ("delivery.rejection_act", "DELIVERY", "ACTA DE RECHAZO"),
}

_TEMPLATE_HTML_PATHS: dict[str, str] = {
    "POD": "delivery/proof_of_delivery/pod_v1.html",
    "EP": "delivery/partial_delivery/ep_v1.html",
    "RECH": "delivery/rejection/rech_v1.html",
}


class DeliveryRenderingService:
    """Service for rendering delivery document previews.

    Phase 019 — preview only. No real operations.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.template_repo = DocumentTemplateRepository(db)
        self.version_repo = DocumentTemplateVersionRepository(db)
        self.engine = DocumentRendererEngine()

    def seed_delivery_templates(self) -> None:
        """Seeds catalog with DELIVERY family templates if missing. Idempotent."""
        for doc_type, (t_key, family, t_name) in DELIVERY_TEMPLATES.items():
            tpl = self.template_repo.get_by_key(t_key)
            if not tpl:
                tpl = DocumentTemplateModel(
                    template_key=t_key,
                    document_family_code=family,
                    document_type_code=doc_type,
                    name=t_name,
                    description=f"Plantilla de entrega para {doc_type} (Fase 019)",
                    status="ACTIVE",
                    is_system=True,
                )
                self.template_repo.save(tpl)

                ver = DocumentTemplateVersionModel(
                    template_id=tpl.id,
                    version="1.0.0",
                    engine="Jinja2+WeasyPrint/Fallback",
                    html_path=_TEMPLATE_HTML_PATHS[doc_type],
                    css_paths={
                        "print": "shared/print.css",
                        "delivery": "delivery/shared/delivery.css",
                    },
                    content_hash=f"delivery_{doc_type.lower()}_v1_hash",
                    status="ACTIVE",
                )
                self.version_repo.save(ver)
        self.db.commit()

    def render_delivery_preview(
        self,
        document_type_code: str,
        data: dict[str, Any],
        user_id: str,
        sensitive_read: bool = False,
    ) -> PdfRenderResult:
        """Validates and renders a delivery document preview."""
        dtype = document_type_code.upper()
        if dtype not in DELIVERY_TEMPLATES:
            raise ValueError(f"Document type {dtype} not supported by Delivery service")

        t_key, _, t_name = DELIVERY_TEMPLATES[dtype]

        # 1. Parse & validate payload
        if dtype == "POD":
            context = DeliveryPodContext(**data)
        elif dtype == "EP":
            context = DeliveryPartialContext(**data)
        elif dtype == "RECH":
            context = DeliveryRejectionContext(**data)
        else:
            raise ValueError(f"Invalid document type: {dtype}")

        ctx_dict = context.model_dump()

        # 2. Apply privacy masking if not authorized
        if not sensitive_read:
            # Mask driver
            if "driver_snapshot" in ctx_dict and ctx_dict["driver_snapshot"]:
                driver = ctx_dict["driver_snapshot"]
                driver["document_number"] = mask_sensitive_val(driver.get("document_number"))
                driver["license_number"] = mask_sensitive_val(driver.get("license_number"))
            # Mask receiver
            if "receiver_snapshot" in ctx_dict and ctx_dict["receiver_snapshot"]:
                rec = ctx_dict["receiver_snapshot"]
                rec["document_number_masked"] = mask_sensitive_val(rec.get("document_number_masked"))
                rec["phone_masked"] = mask_sensitive_val(rec.get("phone_masked"))
                rec["email_masked"] = mask_sensitive_val(rec.get("email_masked"))
            # Mask signatures
            if "signatures" in ctx_dict:
                for sig in ctx_dict["signatures"]:
                    sig["asset_reference"] = "Firma protegida"
                    sig["asset_hash"] = "******"
            # Mask photos
            if "photos" in ctx_dict:
                for photo in ctx_dict["photos"]:
                    photo["file_reference"] = "Evidencia protegida"
                    photo["hash"] = "******"

        # 3. Create document render command
        cmd = DocumentRenderCommand(
            document_type_code=dtype,
            template_key=t_key,
            template_version="1.0.0",
            document_title=f"{t_name} - VISTA PREVIA",
            document_data=ctx_dict,
            preview_mode=True,
            requested_by=user_id,
        )

        html_res = self.engine.render_html(cmd)
        return self.engine.render_pdf(cmd)
