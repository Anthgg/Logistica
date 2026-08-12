"""Application service for Inbound & Quality Document Previews and Reception Package Manifests (Phase 016)."""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

from app.modules.logistics.documents.rendering.inbound_schemas import (
    InboundCpvContext,
    ReceptionPackageManifestResponse,
)
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

INBOUND_TEMPLATES = {
    "CIT": ("inbound.cit", "INBOUND", "CITA DE RECEPCIÓN"),
    "CPV": ("inbound.cpv", "INBOUND", "CONTROL DE PUERTA VEHICULAR"),
    "AREC": ("inbound.arec", "INBOUND", "ACTA DE RECEPCIÓN"),
    "NI": ("inbound.ni", "INBOUND", "NOTA DE INGRESO"),
    "DIF": ("inbound.dif", "INBOUND", "ACTA DE DIFERENCIAS"),
    "NC": ("quality.nc", "QUALITY", "INFORME DE NO CONFORMIDAD"),
}


class InboundRenderingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.template_repo = DocumentTemplateRepository(db)
        self.version_repo = DocumentTemplateVersionRepository(db)
        self.engine = DocumentRendererEngine()

    def seed_inbound_templates(self) -> None:
        """Seeds catalog with INBOUND and QUALITY family templates if missing."""
        for doc_type, (t_key, family, t_name) in INBOUND_TEMPLATES.items():
            tpl = self.template_repo.get_by_key(t_key)
            if not tpl:
                tpl = DocumentTemplateModel(
                    template_key=t_key,
                    document_family_code=family,
                    document_type_code=doc_type,
                    name=t_name,
                    description=f"Plantilla especializada de recepción para {doc_type}",
                    status="ACTIVE",
                    is_system=True,
                )
                self.template_repo.save(tpl)

                ver = DocumentTemplateVersionModel(
                    template_id=tpl.id,
                    version="1.0.0",
                    engine="Jinja2+WeasyPrint/Fallback",
                    html_path=f"{family.lower()}/{doc_type.lower()}_v1.html",
                    css_paths={"print": "shared/print.css", "inbound": "inbound/shared/inbound.css"},
                    content_hash=f"{family.lower()}_{doc_type.lower()}_v1_hash",
                    status="ACTIVE",
                )
                self.version_repo.save(ver)
        self.db.commit()

    def render_inbound_preview(
        self,
        document_type_code: str,
        data: dict[str, Any],
        user_id: str | None = None,
    ) -> PdfRenderResult:
        doc_type = document_type_code.upper()
        if doc_type not in INBOUND_TEMPLATES:
            t_key = "base.document"
            t_name = f"DOCUMENTO {doc_type}"
        else:
            t_key, family, t_name = INBOUND_TEMPLATES[doc_type]

        self.seed_inbound_templates()

        # Apply privacy masking for CPV driver DNI / License
        render_data = data.copy()
        if doc_type == "CPV":
            cpv_ctx = InboundCpvContext(**data)
            render_data = cpv_ctx.get_masked_context()

        cmd = DocumentRenderCommand(
            document_type_code=doc_type,
            template_key=t_key,
            template_version="1.0.0",
            document_code=render_data.get("document_code", f"{doc_type}-LIM-2026-000001"),
            document_status="PREVIEW",
            document_title=t_name,
            organization_name=render_data.get("organization_name", "PROYECTO T1 LOGÍSTICA S.A.C."),
            branch_name=render_data.get("branch_name", "SEDE LIMA PRINCIPAL"),
            document_data=render_data,
            watermark_text="VISTA PREVIA",
            qr_data=render_data.get("document_code", f"PREVIEW_{doc_type}"),
            preview_mode=True,
            requested_by=user_id,
        )

        return self.engine.render_pdf(cmd)

    def build_reception_package_manifest(
        self, payload: dict[str, Any]
    ) -> ReceptionPackageManifestResponse:
        included = []
        missing = []
        warnings = []

        # Rule evaluation
        if payload.get("has_appointment", True):
            included.append("CIT")
        else:
            missing.append("CIT")

        if payload.get("has_vehicle_entry", True):
            included.append("CPV")

        included.append("AREC")

        if payload.get("accepted_quantity", 1) > 0:
            included.append("NI")

        if payload.get("has_differences", False):
            included.append("DIF")

        if payload.get("has_non_conformity", False):
            included.append("NC")

        if "NC" in included:
            warnings.append("El paquete incluye No Conformidad (Familia QUALITY). Requiere revisión de inspector.")

        return ReceptionPackageManifestResponse(
            manifest_version="1.0.0",
            package_mode="PREVIEW",
            organization_name=payload.get("organization_name", "PROYECTO T1 LOGÍSTICA S.A.C."),
            branch_name=payload.get("branch_name", "SEDE LIMA PRINCIPAL"),
            warehouse_name=payload.get("warehouse_name", "Almacén Principal"),
            included_documents=included,
            missing_documents=missing,
            warnings=warnings,
        )
