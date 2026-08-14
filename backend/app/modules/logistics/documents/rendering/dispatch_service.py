"""Application service for Dispatch Document Previews and Package Manifests (Phase 018).

Covers: MAN, ADSP, CPR
Phase boundaries:
  - No real vehicle planning, loading checkpoints, trip routes, or seal registration.
  - No official document emission or correlative reservation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.modules.logistics.documents.rendering.dispatch_schemas import (
    DispatchManContext,
    DispatchAdspContext,
    DispatchCprContext,
    OutboundDispatchDocumentPackageManifest,
    OutboundDispatchDocumentEntry,
)
from app.modules.logistics.documents.rendering.outbound_schemas import DestinationSnapshot
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
# Dispatch Template registry
# ---------------------------------------------------------------------------

DISPATCH_TEMPLATES: dict[str, tuple[str, str, str]] = {
    "MAN": ("dispatch.load_manifest", "DISPATCH", "MANIFIESTO DE CARGA"),
    "ADSP": ("dispatch.dispatch_act", "DISPATCH", "ACTA DE DESPACHO"),
    "CPR": ("dispatch.seal_control", "DISPATCH", "CONTROL DE PRECINTO"),
}

_TEMPLATE_HTML_PATHS: dict[str, str] = {
    "MAN": "dispatch/load_manifest/man_v1.html",
    "ADSP": "dispatch/dispatch_act/adsp_v1.html",
    "CPR": "dispatch/seal_control/cpr_v1.html",
}

PROPOSED_DISPATCH_CODES = {"CPR"}


def mask_driver_id(val: str | None, visible_end: int = 2) -> str:
    """Utility to mask driver DNI or license for privacy protection."""
    if not val:
        return "******"
    val_str = str(val).strip()
    if len(val_str) <= visible_end:
        return "*" * len(val_str)
    return "*" * (len(val_str) - visible_end) + val_str[-visible_end:]


class DispatchRenderingService:
    """Service for rendering dispatch document previews and manifests.

    Phase 018 — preview only. No real operations.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.template_repo = DocumentTemplateRepository(db)
        self.version_repo = DocumentTemplateVersionRepository(db)
        self.engine = DocumentRendererEngine()

    def seed_dispatch_templates(self) -> None:
        """Seeds catalog with DISPATCH family templates if missing. Idempotent."""
        for doc_type, (t_key, family, t_name) in DISPATCH_TEMPLATES.items():
            tpl = self.template_repo.get_by_key(t_key)
            if not tpl:
                status = "ACTIVE_FOR_PREVIEW" if doc_type in PROPOSED_DISPATCH_CODES else "ACTIVE"
                tpl = DocumentTemplateModel(
                    template_key=t_key,
                    document_family_code=family,
                    document_type_code=doc_type,
                    name=t_name,
                    description=f"Plantilla de despacho para {doc_type} (Fase 018)",
                    status=status,
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
                        "dispatch": "dispatch/shared/dispatch.css",
                    },
                    content_hash=f"dispatch_{doc_type.lower()}_v1_hash",
                    status="ACTIVE",
                )
                self.version_repo.save(ver)
        self.db.flush()

    def render_dispatch_preview(
        self,
        document_type_code: str,
        data: dict[str, Any],
        user_id: str | None = None,
        sensitive_read: bool = False,
    ) -> PdfRenderResult:
        """Render preview PDF for Dispatch documents."""
        doc_type = document_type_code.upper()

        if doc_type not in DISPATCH_TEMPLATES:
            t_key = "base.document"
            t_name = f"DOCUMENTO DESPACHO {doc_type}"
        else:
            t_key, _family, t_name = DISPATCH_TEMPLATES[doc_type]

        self.seed_dispatch_templates()

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
        """Validate context, apply enmascaramiento for DNI/License and sensitive client gating."""
        def _mask_driver(driver_dict: dict[str, Any] | None) -> dict[str, Any] | None:
            if not driver_dict:
                return None
            out = driver_dict.copy()
            # Driver DNI & License must be masked for privacy in all preview documents
            if "document_number" in out:
                out["document_number"] = mask_driver_id(out["document_number"])
            if "license_number" in out:
                out["license_number"] = mask_driver_id(out["license_number"])
            return out

        if doc_type == "MAN":
            try:
                ctx = DispatchManContext(**data)
                out = ctx.model_dump()
                if "driver_snapshot" in out:
                    out["driver_snapshot"] = _mask_driver(out["driver_snapshot"])
                return out
            except Exception:
                pass

        elif doc_type == "ADSP":
            try:
                ctx = DispatchAdspContext(**data)
                out = ctx.model_dump()
                if "driver_snapshot" in out:
                    out["driver_snapshot"] = _mask_driver(out["driver_snapshot"])
                return out
            except Exception:
                pass

        elif doc_type == "CPR":
            try:
                ctx = DispatchCprContext(**data)
                return ctx.model_dump()
            except Exception:
                pass

        return data

    def build_dispatch_package_manifest(
        self, payload: dict[str, Any]
    ) -> OutboundDispatchDocumentPackageManifest:
        """Evaluate inclusion rules and return package manifest.

        Dispatch package modes: DISPATCH | TRANSPORT_HANDOFF
        """
        mode = payload.get("package_mode", "DISPATCH").upper()
        generated_at = datetime.now(timezone.utc).isoformat()
        warnings: list[str] = []
        entries: list[OutboundDispatchDocumentEntry] = []

        def _entry(code: str, required: bool = True, reason: str | None = None) -> OutboundDispatchDocumentEntry:
            t_key = DISPATCH_TEMPLATES.get(code, (f"dispatch.{code.lower()}", "DISPATCH", ""))[0]
            return OutboundDispatchDocumentEntry(
                document_type_code=code,
                family_code="DISPATCH",
                template_key=t_key,
                required=required,
                included=reason is None,
                reason_if_missing=reason,
                filename_suggestion=f"PREVIEW_{code}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf",
            )

        if mode == "DISPATCH":
            entries.append(_entry("MAN"))
            entries.append(_entry("ADSP"))
            if payload.get("requires_seal", False):
                entries.append(_entry("CPR"))

        elif mode == "TRANSPORT_HANDOFF":
            entries.append(_entry("MAN"))
            entries.append(_entry("ADSP"))
            if payload.get("requires_seal", True):
                entries.append(_entry("CPR"))
            else:
                entries.append(_entry("CPR", required=False, reason="Precinto no requerido según política"))

        if any(e.document_type_code in PROPOSED_DISPATCH_CODES and e.included for e in entries):
            warnings.append(
                "Este paquete incluye el código propuesto CPR (Control de precinto) "
                "pendiente de aprobación formal en el catálogo documental."
            )

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
            dispatch_reference=payload.get("dispatch_reference"),
            manifest_reference=payload.get("manifest_reference"),
            document_entries=entries,
            preview_mode=True,
            generated_at=generated_at,
            warnings=warnings,
            correlation_id=payload.get("correlation_id"),
        )
