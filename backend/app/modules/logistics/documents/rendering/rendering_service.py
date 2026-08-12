"""Application service for Document Template management and Preview Rendering (Phase 014)."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.logistics.documents.rendering.rendering import (
    HAS_WEASYPRINT,
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
from app.modules.logistics.documents.rendering.template_schemas import (
    DocumentPreviewRenderRequest,
    DocumentRendererStatusResponse,
    DocumentTemplateResponse,
    DocumentTemplateVersionResponse,
)


class DocumentRenderingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.template_repo = DocumentTemplateRepository(db)
        self.version_repo = DocumentTemplateVersionRepository(db)
        self.engine = DocumentRendererEngine()

    def get_or_create_base_template(self) -> DocumentTemplateModel:
        tpl = self.template_repo.get_by_key("base.document")
        if not tpl:
            tpl = DocumentTemplateModel(
                template_key="base.document",
                document_family_code="GENERIC",
                name="Plantilla Documental Base Genérica v1.0.0",
                description="Plantilla central estandarizada para renderizado HTML y PDF con encabeza, pie, marca de agua y QR.",
                status="ACTIVE",
                is_system=True,
            )
            self.template_repo.save(tpl)

            ver = DocumentTemplateVersionModel(
                template_id=tpl.id,
                version="1.0.0",
                engine="Jinja2+WeasyPrint/Fallback",
                html_path="base/base_v1.html",
                css_paths={"print": "shared/print.css"},
                content_hash="base_v1_hash_initial",
                status="ACTIVE",
            )
            self.version_repo.save(ver)
            self.db.commit()
        return tpl

    def list_templates(self) -> list[DocumentTemplateResponse]:
        self.get_or_create_base_template()
        tpls = self.template_repo.list()
        return [DocumentTemplateResponse.model_validate(t) for t in tpls]

    def get_template(self, template_key: str) -> DocumentTemplateResponse:
        tpl = self.template_repo.get_by_key(template_key)
        if not tpl:
            if template_key == "base.document":
                tpl = self.get_or_create_base_template()
            else:
                raise HTTPException(status_code=404, detail=f"DocumentTemplate '{template_key}' not found")
        return DocumentTemplateResponse.model_validate(tpl)

    def list_versions(self, template_key: str) -> list[DocumentTemplateVersionResponse]:
        tpl = self.get_template(template_key)
        vers = self.version_repo.list_versions(tpl.id)
        return [DocumentTemplateVersionResponse.model_validate(v) for v in vers]

    def get_status(self) -> DocumentRendererStatusResponse:
        self.get_or_create_base_template()
        renderer_name = "WeasyPrint" if HAS_WEASYPRINT else "FallbackPdfEngine"
        return DocumentRendererStatusResponse(
            renderer_available=True,
            renderer_name=renderer_name,
            active_engine=f"Jinja2+{renderer_name}",
            base_template_available=True,
            active_template_key="base.document",
            active_template_version="1.0.0",
            qr_generator_available=True,
        )

    def render_preview_pdf(
        self, template_key: str, req: DocumentPreviewRenderRequest, user_id: str | None = None
    ) -> PdfRenderResult:
        if template_key != "base.document":
            self.get_template(template_key)

        cmd = DocumentRenderCommand(
            document_type_code=req.document_type_code,
            template_key=template_key,
            template_version="1.0.0",
            document_code=req.document_code,
            document_status="PREVIEW",
            document_title=req.document_title,
            organization_name=req.organization_name,
            branch_name=req.branch_name,
            document_data=req.document_data,
            watermark_text=req.watermark_text or "VISTA PREVIA",
            qr_data=req.qr_data or req.document_code or "PREVIEW_DOC",
            signature_data=req.signature_data,
            preview_mode=True,
            requested_by=user_id,
        )

        return self.engine.render_pdf(cmd)
