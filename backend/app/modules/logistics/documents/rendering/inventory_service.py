"""Application service for Inventory Document Previews and Package Manifests (Phase 017).

Covers: EUB, PUT, MOV, AJI, CNT, ADI, TRA, CRT
Phase boundaries:
  - No real inventory movements, stock balances, adjustments, counts, or transfers.
  - No official document emission or correlative reservation.
  - No reprint, void, or ZIP.
  - No frontend modifications.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.modules.logistics.documents.rendering.inventory_schemas import (
    InventoryAjiContext,
    InventoryCntContext,
    InventoryCrtContext,
    InventoryDocumentPackageManifest,
    InventoryDocumentEntry,
    InventoryTraContext,
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
# Template registry for INVENTORY family
# ---------------------------------------------------------------------------

INVENTORY_TEMPLATES: dict[str, tuple[str, str, str]] = {
    # code: (template_key, family, display_name)
    "EUB": ("inventory.location_label", "INVENTORY", "ETIQUETA DE UBICACIÓN"),
    "PUT": ("inventory.putaway_order", "INVENTORY", "ORDEN DE UBICACIÓN"),
    "MOV": ("inventory.movement", "INVENTORY", "MOVIMIENTO DE ALMACÉN"),
    "AJI": ("inventory.adjustment", "INVENTORY", "ACTA DE AJUSTE DE INVENTARIO"),
    "CNT": ("inventory.count", "INVENTORY", "ACTA DE CONTEO FÍSICO"),
    "ADI": ("inventory.difference", "INVENTORY", "ACTA DE DIFERENCIA DE INVENTARIO"),
    "TRA": ("inventory.transfer", "INVENTORY", "ORDEN DE TRANSFERENCIA"),
    "CRT": ("inventory.transfer_receipt", "INVENTORY", "CONSTANCIA DE RECEPCIÓN DE TRANSFERENCIA"),
}

# HTML paths within templates/ directory
_TEMPLATE_HTML_PATHS: dict[str, str] = {
    "EUB": "inventory/location_label/eub_v1.html",
    "PUT": "inventory/putaway_order/put_v1.html",
    "MOV": "inventory/movement/mov_v1.html",
    "AJI": "inventory/adjustment/aji_v1.html",
    "CNT": "inventory/count/cnt_v1.html",
    "ADI": "inventory/difference/adi_v1.html",
    "TRA": "inventory/transfer/tra_v1.html",
    "CRT": "inventory/transfer_receipt/crt_v1.html",
}

# Codes that are PROPOSED (ACTIVE_FOR_PREVIEW) — not yet formally approved
PROPOSED_CODES = {"EUB", "ADI", "CRT"}


class InventoryRenderingService:
    """Service for rendering inventory document previews and package manifests.

    Phase 017 — preview only. No real inventory operations.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.template_repo = DocumentTemplateRepository(db)
        self.version_repo = DocumentTemplateVersionRepository(db)
        self.engine = DocumentRendererEngine()

    def seed_inventory_templates(self) -> None:
        """Seeds catalog with INVENTORY family templates if missing. Idempotent."""
        for doc_type, (t_key, family, t_name) in INVENTORY_TEMPLATES.items():
            tpl = self.template_repo.get_by_key(t_key)
            if not tpl:
                status = "ACTIVE_FOR_PREVIEW" if doc_type in PROPOSED_CODES else "ACTIVE"
                tpl = DocumentTemplateModel(
                    template_key=t_key,
                    document_family_code=family,
                    document_type_code=doc_type,
                    name=t_name,
                    description=f"Plantilla de inventario para {doc_type} (Fase 017)",
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
                        "inventory": "inventory/shared/inventory.css",
                    },
                    content_hash=f"inventory_{doc_type.lower()}_v1_hash",
                    status="ACTIVE",
                )
                self.version_repo.save(ver)
        self.db.commit()

    def render_inventory_preview(
        self,
        document_type_code: str,
        data: dict[str, Any],
        user_id: str | None = None,
        blind_count_mode: bool = False,
        sensitive_read: bool = False,
    ) -> PdfRenderResult:
        """Render a preview PDF for the given inventory document type.

        Args:
            document_type_code: EUB | PUT | MOV | AJI | CNT | ADI | TRA | CRT
            data: Unvalidated payload from the request body.
            user_id: Authenticated user ID for audit correlation.
            blind_count_mode: If True and doc_type==CNT, hides expected quantities.
            sensitive_read: If True, economic impact data may be shown in AJI/ADI.

        Returns:
            PdfRenderResult with preview PDF bytes and metadata.
        """
        doc_type = document_type_code.upper()

        if doc_type not in INVENTORY_TEMPLATES:
            t_key = "base.document"
            t_name = f"DOCUMENTO INVENTARIO {doc_type}"
        else:
            t_key, _family, t_name = INVENTORY_TEMPLATES[doc_type]

        self.seed_inventory_templates()

        render_data = data.copy()

        # Schema-level validation and context transformation
        render_data = self._prepare_render_data(doc_type, render_data, blind_count_mode, sensitive_read)

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
        blind_count_mode: bool,
        sensitive_read: bool,
    ) -> dict[str, Any]:
        """Validate and transform payload per document type."""

        if doc_type == "AJI":
            # Validate and hide economic impact unless permitted
            try:
                ctx = InventoryAjiContext(**data)
                out = ctx.model_dump()
                if not sensitive_read:
                    out["show_economic_impact"] = False
                return out
            except Exception:
                pass  # Fall through to raw render in preview mode

        elif doc_type == "CNT":
            # Apply blind count protection
            try:
                ctx = InventoryCntContext(**data)
                if blind_count_mode:
                    ctx = InventoryCntContext(**{**data, "blind_count_mode": True})
                return ctx.get_safe_context()
            except Exception:
                pass

        elif doc_type == "TRA":
            try:
                ctx = InventoryTraContext(**data)
                return ctx.model_dump()
            except Exception:
                pass

        elif doc_type == "CRT":
            try:
                ctx = InventoryCrtContext(**data)
                return ctx.model_dump()
            except Exception:
                pass

        elif doc_type == "ADI":
            out = data.copy()
            if not sensitive_read:
                out["show_economic_impact"] = False
            return out

        return data

    def build_inventory_package_manifest(
        self, payload: dict[str, Any]
    ) -> InventoryDocumentPackageManifest:
        """Build a package manifest based on package_mode and event flags.

        Phase 017 — PREVIEW mode. No correlativos, no real operations.
        """
        mode = payload.get("package_mode", "MOVEMENT").upper()
        generated_at = datetime.now(timezone.utc).isoformat()
        warnings: list[str] = []
        entries: list[InventoryDocumentEntry] = []

        def _entry(code: str, required: bool = True, reason: str | None = None) -> InventoryDocumentEntry:
            t_key = INVENTORY_TEMPLATES.get(code, (f"inventory.{code.lower()}", "INVENTORY", ""))[0]
            return InventoryDocumentEntry(
                document_type_code=code,
                template_key=t_key,
                required=required,
                included=reason is None,
                reason_if_missing=reason,
                filename_suggestion=f"PREVIEW_{code}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf",
            )

        if mode == "LOCATION":
            entries.append(_entry("EUB"))
            if payload.get("include_putaway"):
                entries.append(_entry("PUT", required=False))

        elif mode == "PUTAWAY":
            entries.append(_entry("PUT"))
            entries.append(_entry("EUB", required=False))

        elif mode == "MOVEMENT":
            entries.append(_entry("MOV"))

        elif mode == "ADJUSTMENT":
            entries.append(_entry("AJI"))
            if payload.get("originated_from_count"):
                entries.append(_entry("ADI", required=False))
            if payload.get("has_compensatory_movement"):
                entries.append(_entry("MOV", required=False))

        elif mode == "COUNT":
            entries.append(_entry("CNT"))
            if payload.get("has_differences"):
                entries.append(_entry("ADI"))
                warnings.append("Conteo con diferencias detectadas — Se requiere investigación (ADI).")
            if payload.get("has_approved_adjustment"):
                entries.append(_entry("AJI", required=False))

        elif mode == "TRANSFER":
            entries.append(_entry("TRA"))
            if payload.get("has_dispatched"):
                entries.append(_entry("MOV", required=False, reason="MOV origen — PENDING_PHASE_049"))

        elif mode == "TRANSFER_RECEIPT":
            entries.append(_entry("CRT"))
            if payload.get("has_internal_differences"):
                entries.append(_entry("ADI", required=False))
                warnings.append("Diferencias detectadas en recepción de transferencia.")

        if any(e.document_type_code in PROPOSED_CODES and e.included for e in entries):
            warnings.append(
                "Este paquete incluye uno o más códigos documentales PROPUESTOS "
                "(EUB, ADI o CRT) pendientes de aprobación formal en el catálogo."
            )

        package_status = "READY_FOR_PREVIEW" if all(
            e.included for e in entries if e.required
        ) else "INCOMPLETE"

        return InventoryDocumentPackageManifest(
            manifest_version="1.0.0",
            package_mode=mode,
            package_status=package_status,
            package_status_detail=package_status,
            organization_name=payload.get("organization_name", "PROYECTO T1 LOGÍSTICA S.A.C."),
            branch_name=payload.get("branch_name", "SEDE LIMA PRINCIPAL"),
            warehouse_name=payload.get("warehouse_name", "Almacén Principal"),
            source_warehouse_name=payload.get("source_warehouse_name"),
            destination_warehouse_name=payload.get("destination_warehouse_name"),
            related_operation_reference=payload.get("related_operation_reference"),
            document_entries=entries,
            preview_mode=True,
            generated_at=generated_at,
            generated_by=payload.get("generated_by"),
            warnings=warnings,
            correlation_id=payload.get("correlation_id"),
        )
