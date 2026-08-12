"""Application service for Outbound Document Previews and Package Manifests (Phase 018).

Covers: PED, ODS, PICK, PACK
Phase boundaries:
  - No real inventory allocation, picking tasks, packing boxes, or dispatch.
  - No official document emission or correlative reservation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.modules.logistics.documents.rendering.outbound_schemas import (
    OutboundOdsContext,
    OutboundPedContext,
    OutboundPickingContext,
    OutboundPackContext,
    DestinationSnapshot,
)
from app.modules.logistics.documents.rendering.dispatch_schemas import (
    OutboundDispatchDocumentPackageManifest,
    OutboundDispatchDocumentEntry,
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

# ---------------------------------------------------------------------------
# Outbound Template registry
# ---------------------------------------------------------------------------

OUTBOUND_TEMPLATES: dict[str, tuple[str, str, str]] = {
    "PED": ("outbound.ped", "OUTBOUND", "PEDIDO DE SALIDA"),
    "ODS": ("outbound.ods", "OUTBOUND", "ORDEN DE SALIDA"),
    "PICK": ("outbound.picking_list", "OUTBOUND", "LISTA DE PICKING"),
    "PACK": ("outbound.packing_list", "OUTBOUND", "PACKING LIST"),
}

_TEMPLATE_HTML_PATHS: dict[str, str] = {
    "PED": "outbound/request/ped_v1.html",
    "ODS": "outbound/outbound_order/ods_v1.html",
    "PICK": "outbound/picking/pick_v1.html",
    "PACK": "outbound/packing/pack_v1.html",
}


class OutboundRenderingService:
    """Service for rendering outbound document previews and manifests.

    Phase 018 — preview only. No real operations.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.template_repo = DocumentTemplateRepository(db)
        self.version_repo = DocumentTemplateVersionRepository(db)
        self.engine = DocumentRendererEngine()

    def seed_outbound_templates(self) -> None:
        """Seeds catalog with OUTBOUND family templates if missing. Idempotent."""
        for doc_type, (t_key, family, t_name) in OUTBOUND_TEMPLATES.items():
            tpl = self.template_repo.get_by_key(t_key)
            if not tpl:
                tpl = DocumentTemplateModel(
                    template_key=t_key,
                    document_family_code=family,
                    document_type_code=doc_type,
                    name=t_name,
                    description=f"Plantilla de salida para {doc_type} (Fase 018)",
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
                        "outbound": "outbound/shared/outbound.css",
                    },
                    content_hash=f"outbound_{doc_type.lower()}_v1_hash",
                    status="ACTIVE",
                )
                self.version_repo.save(ver)
        self.db.commit()

    def render_outbound_preview(
        self,
        document_type_code: str,
        data: dict[str, Any],
        user_id: str | None = None,
        sensitive_read: bool = False,
    ) -> PdfRenderResult:
        """Render preview PDF for Outbound documents."""
        doc_type = document_type_code.upper()

        if doc_type not in OUTBOUND_TEMPLATES:
            t_key = "base.document"
            t_name = f"DOCUMENTO SALIDA {doc_type}"
        else:
            t_key, _family, t_name = OUTBOUND_TEMPLATES[doc_type]

        self.seed_outbound_templates()

        render_data = data.copy()

        # Apply schema validation & gating/masking logic
        render_data = self._prepare_render_data(doc_type, render_data, sensitive_read)

        cmd = DocumentRenderCommand(
            document_type_code=doc_type,
            template_key=t_key,
            template_version="1.0.0",
            document_code=render_data.get("document_code", f"{doc_type}-PREVIEW"),
            document_status="PREVIEW",
            document_title=t_name,
            organization_name=render_data.get("organization_name", "PROYECTO T1 LOGÍSTICA S.A.C."),
            branch_name=render_data.get("branch_name", "SEDE LIMA PRINCIPAL"),
            document_data=render_data,
            watermark_text="VISTA PREVIA",
            qr_data=render_data.get("document_code") or f"PREVIEW_{doc_type}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            preview_mode=True,
            requested_by=user_id,
        )

        return self.engine.render_pdf(cmd)

    def _prepare_render_data(
        self,
        doc_type: str,
        data: dict[str, Any],
        sensitive_read: bool,
    ) -> dict[str, Any]:
        """Validate context and apply sensitive data gating (DNI, licencias, contact details)."""
        # Utility helper to mask contact details
        def _mask_dest(dest_dict: dict[str, Any] | None) -> dict[str, Any] | None:
            if not dest_dict:
                return None
            out = dest_dict.copy()
            if not sensitive_read and "contact_phone" in out and out["contact_phone"]:
                phone = str(out["contact_phone"])
                if len(phone) > 4:
                    out["contact_phone"] = phone[:2] + "****" + phone[-2:]
                else:
                    out["contact_phone"] = "****"
            return out

        if doc_type == "PED":
            try:
                ctx = OutboundPedContext(**data)
                out = ctx.model_dump()
                # Apply destination phone masking
                if "destination_snapshot" in out:
                    out["destination_snapshot"] = _mask_dest(out["destination_snapshot"])
                return out
            except Exception:
                pass

        elif doc_type == "ODS":
            try:
                ctx = OutboundOdsContext(**data)
                out = ctx.model_dump()
                if "destination" in out:
                    out["destination"] = _mask_dest(out["destination"])
                return out
            except Exception:
                pass

        elif doc_type == "PICK":
            try:
                ctx = OutboundPickingContext(**data)
                return ctx.model_dump()
            except Exception:
                pass

        elif doc_type == "PACK":
            try:
                ctx = OutboundPackContext(**data)
                out = ctx.model_dump()
                if "destination" in out:
                    out["destination"] = _mask_dest(out["destination"])
                return out
            except Exception:
                pass

        return data

    def build_outbound_package_manifest(
        self, payload: dict[str, Any]
    ) -> OutboundDispatchDocumentPackageManifest:
        """Evaluate inclusion rules and return package manifest.

        Outbound package modes: OUTBOUND_REQUEST | OUTBOUND_AUTHORIZATION | PICKING | PACKING
        """
        mode = payload.get("package_mode", "PICKING").upper()
        generated_at = datetime.now(timezone.utc).isoformat()
        warnings: list[str] = []
        entries: list[OutboundDispatchDocumentEntry] = []

        def _entry(code: str, required: bool = True, reason: str | None = None) -> OutboundDispatchDocumentEntry:
            t_key = OUTBOUND_TEMPLATES.get(code, (f"outbound.{code.lower()}", "OUTBOUND", ""))[0]
            return OutboundDispatchDocumentEntry(
                document_type_code=code,
                family_code="OUTBOUND",
                template_key=t_key,
                required=required,
                included=reason is None,
                reason_if_missing=reason,
                filename_suggestion=f"PREVIEW_{code}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf",
            )

        if mode == "OUTBOUND_REQUEST":
            entries.append(_entry("PED"))

        elif mode == "OUTBOUND_AUTHORIZATION":
            entries.append(_entry("ODS"))
            if payload.get("has_request", False):
                entries.append(_entry("PED", required=False))

        elif mode == "PICKING":
            entries.append(_entry("PICK"))
            if payload.get("has_order", True):
                entries.append(_entry("ODS"))
            if payload.get("has_exceptions", False):
                warnings.append("Lista de picking contiene excepciones registradas por el operador.")

        elif mode == "PACKING":
            entries.append(_entry("PACK"))
            if payload.get("has_picking", True):
                entries.append(_entry("PICK"))
            if payload.get("has_order", True):
                entries.append(_entry("ODS"))

        package_status = "READY_FOR_PREVIEW" if all(
            e.included for e in entries if e.required
        ) else "INCOMPLETE"

        # Safe extraction of destination snapshot
        dest = None
        if "destination" in payload:
            try:
                dest = DestinationSnapshot(**payload["destination"])
            except Exception:
                pass

        return OutboundDispatchDocumentPackageManifest(
            manifest_version="1.0.0",
            package_mode=mode,
            package_status=package_status,
            warehouse=payload.get("warehouse", "Almacén Principal"),
            destination=dest,
            outbound_request_reference=payload.get("outbound_request_reference"),
            outbound_order_reference=payload.get("outbound_order_reference"),
            picking_reference=payload.get("picking_reference"),
            packing_reference=payload.get("packing_reference"),
            document_entries=entries,
            preview_mode=True,
            generated_at=generated_at,
            warnings=warnings,
            correlation_id=payload.get("correlation_id"),
        )
