"""Application service for Purchasing Documents Preview and Rendering (Phase 015)."""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

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

PURCHASING_TEMPLATES = {
    "REQ": ("purchasing.req", "REQUERIMIENTO DE COMPRA"),
    "SCOT": ("purchasing.scot", "SOLICITUD DE COTIZACIÓN"),
    "CCO": ("purchasing.cco", "CUADRO COMPARATIVO DE OFERTAS"),
    "OC": ("purchasing.oc", "ORDEN DE COMPRA"),
    "APC": ("purchasing.apc", "APROBACIÓN DE COMPRA"),
    "CEP": ("purchasing.cep", "CONSTANCIA DE ENVÍO AL PROVEEDOR"),
}


class PurchasingRenderingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.template_repo = DocumentTemplateRepository(db)
        self.version_repo = DocumentTemplateVersionRepository(db)
        self.engine = DocumentRendererEngine()

    def seed_purchasing_templates(self) -> None:
        """Seeds catalog with PURCHASING family templates if missing."""
        for doc_type, (t_key, t_name) in PURCHASING_TEMPLATES.items():
            tpl = self.template_repo.get_by_key(t_key)
            if not tpl:
                tpl = DocumentTemplateModel(
                    template_key=t_key,
                    document_family_code="PURCHASING",
                    document_type_code=doc_type,
                    name=t_name,
                    description=f"Plantilla especializada de compras para {doc_type}",
                    status="ACTIVE",
                    is_system=True,
                )
                self.template_repo.save(tpl)

                ver = DocumentTemplateVersionModel(
                    template_id=tpl.id,
                    version="1.0.0",
                    engine="Jinja2+WeasyPrint/Fallback",
                    html_path=f"purchasing/{doc_type.lower()}_v1.html",
                    css_paths={"print": "shared/print.css", "purchasing": "purchasing/shared/purchasing.css"},
                    content_hash=f"purchasing_{doc_type.lower()}_v1_hash",
                    status="ACTIVE",
                )
                self.version_repo.save(ver)
        self.db.flush()

    def render_purchasing_preview(
        self,
        document_type_code: str,
        data: dict[str, Any],
        user_id: str | None = None,
    ) -> PdfRenderResult:
        doc_type = document_type_code.upper()
        if doc_type not in PURCHASING_TEMPLATES:
            t_key = "base.document"
            t_title = f"DOCUMENTO {doc_type}"
        else:
            t_key, t_title = PURCHASING_TEMPLATES[doc_type]

        self.seed_purchasing_templates()

        cmd = DocumentRenderCommand(
            document_type_code=doc_type,
            template_key=t_key,
            template_version="1.0.0",
            document_code=data.get("document_code", f"{doc_type}-LIM-2026-000001"),
            document_status="PREVIEW",
            document_title=t_title,
            organization_name=data.get("organization_name", "PROYECTO T1 LOGÍSTICA S.A.C."),
            branch_name=data.get("branch_name", "SEDE LIMA PRINCIPAL"),
            document_data=data,
            watermark_text="VISTA PREVIA",
            qr_data=data.get("document_code", f"PREVIEW_{doc_type}"),
            preview_mode=True,
            requested_by=user_id,
        )

        return self.engine.render_pdf(cmd)
