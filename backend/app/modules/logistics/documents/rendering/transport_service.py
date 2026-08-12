"""Application service for Transport Document Previews and Package Manifests (Phase 019).

Covers: HV, HR, CVT, PAR, INC
Phase boundaries:
  - Seed and initialize Jinja2 templates.
  - Driver and vehicle data masking.
  - Rules against fake routes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session

from app.modules.logistics.documents.rendering.transport_schemas import (
    OutboundTripContext,
    OutboundRouteContext,
    VehicleControlContext,
    StopRecordContext,
    IncidentReportContext,
)
from app.modules.logistics.documents.rendering.delivery_schemas import (
    TransportDeliveryDocumentPackageManifest,
    TransportDeliveryDocumentEntry,
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


TRANSPORT_TEMPLATES: dict[str, tuple[str, str, str]] = {
    "HV": ("transport.trip_sheet", "TRANSPORT", "HOJA DE VIAJE"),
    "HR": ("transport.route_sheet", "TRANSPORT", "HOJA DE RUTA"),
    "CVT": ("transport.vehicle_control", "TRANSPORT", "CONTROL VEHICULAR DE TRANSPORTE"),
    "PAR": ("transport.stop_record", "TRANSPORT", "CONSTANCIA DE PARADA"),
    "INC": ("transport.incident_report", "TRANSPORT", "REPORTE DE INCIDENCIA"),
}

_TEMPLATE_HTML_PATHS: dict[str, str] = {
    "HV": "transport/trip_sheet/hv_v1.html",
    "HR": "transport/route_sheet/hr_v1.html",
    "CVT": "transport/vehicle_control/cvt_v1.html",
    "PAR": "transport/stop_record/par_v1.html",
    "INC": "transport/incident/inc_v1.html",
}

PROPOSED_TRANSPORT_CODES = {"CVT", "PAR"}


def mask_sensitive_val(val: str | None, visible_end: int = 2) -> str:
    """Utility to mask DNI or license for privacy protection."""
    if not val:
        return "******"
    val_str = str(val).strip()
    if len(val_str) <= visible_end:
        return "*" * len(val_str)
    return "*" * (len(val_str) - visible_end) + val_str[-visible_end:]


class TransportRenderingService:
    """Service for rendering transport document previews and manifests.

    Phase 019 — preview only. No real operations.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.template_repo = DocumentTemplateRepository(db)
        self.version_repo = DocumentTemplateVersionRepository(db)
        self.engine = DocumentRendererEngine()

    def seed_transport_templates(self) -> None:
        """Seeds catalog with TRANSPORT family templates if missing. Idempotent."""
        for doc_type, (t_key, family, t_name) in TRANSPORT_TEMPLATES.items():
            tpl = self.template_repo.get_by_key(t_key)
            if not tpl:
                status = "ACTIVE_FOR_PREVIEW" if doc_type in PROPOSED_TRANSPORT_CODES else "ACTIVE"
                tpl = DocumentTemplateModel(
                    template_key=t_key,
                    document_family_code=family,
                    document_type_code=doc_type,
                    name=t_name,
                    description=f"Plantilla de transporte para {doc_type} (Fase 019)",
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
                        "transport": "transport/shared/transport.css",
                    },
                    content_hash=f"transport_{doc_type.lower()}_v1_hash",
                    status="ACTIVE",
                )
                self.version_repo.save(ver)
        self.db.commit()

    def render_transport_preview(
        self,
        document_type_code: str,
        data: dict[str, Any],
        user_id: str,
        sensitive_read: bool = False,
    ) -> PdfRenderResult:
        """Validates and renders a transport document preview."""
        dtype = document_type_code.upper()
        if dtype not in TRANSPORT_TEMPLATES:
            raise ValueError(f"Document type {dtype} not supported by Transport service")

        t_key, _, t_name = TRANSPORT_TEMPLATES[dtype]

        # 1. Parse & validate payload
        if dtype == "HV":
            context = OutboundTripContext(**data)
        elif dtype == "HR":
            context = OutboundRouteContext(**data)
        elif dtype == "CVT":
            context = VehicleControlContext(**data)
        elif dtype == "PAR":
            context = StopRecordContext(**data)
        elif dtype == "INC":
            context = IncidentReportContext(**data)
        else:
            raise ValueError(f"Invalid document type: {dtype}")

        ctx_dict = context.model_dump()

        # 2. Apply privacy masking if not authorized
        if not sensitive_read:
            # Mask driver snapshots
            if "driver_snapshot" in ctx_dict and ctx_dict["driver_snapshot"]:
                driver = ctx_dict["driver_snapshot"]
                driver["document_number"] = mask_sensitive_val(driver.get("document_number"))
                driver["license_number"] = mask_sensitive_val(driver.get("license_number"))
            # Mask stops contacts
            if "planned_stops" in ctx_dict:
                for stop in ctx_dict["planned_stops"]:
                    if stop.get("contact"):
                        stop["contact"] = "******"
            if "stops" in ctx_dict:
                for stop in ctx_dict["stops"]:
                    if stop.get("contact"):
                        stop["contact"] = "******"

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

    def build_transport_delivery_package_manifest(
        self, payload: dict[str, Any]
    ) -> TransportDeliveryDocumentPackageManifest:
        """Evaluates inclusion rules and builds the Transport & Delivery package manifest."""
        package_mode = payload.get("package_mode", "COMPLETE_TRIP_PACKAGE")
        organization = payload.get("organization", "PROYECTO T1")
        branch = payload.get("branch", "SEDE CENTRAL")
        warehouse = payload.get("warehouse")
        trip_reference = payload.get("trip_reference", "TRP-PREVIEW")
        route_plan_reference = payload.get("route_plan_reference")
        dispatch_reference = payload.get("dispatch_reference")
        
        vehicle = payload.get("vehicle_snapshot", {"plate": "XYZ-000"})
        driver = payload.get("driver_snapshot", {"full_name": "Chofer Demo", "document_number": "00000000", "license_number": "L00000000"})
        
        # Decide which documents are required/included
        entries: list[TransportDeliveryDocumentEntry] = []
        warnings: list[str] = []
        
        # HV is always included
        entries.append(
            TransportDeliveryDocumentEntry(
                document_type_code="HV",
                family_code="TRANSPORT",
                template_key="transport.trip_sheet",
                required=True,
                included=True,
                filename_suggestion=f"PREVIEW_HV_{trip_reference}.pdf",
            )
        )
        
        # HR: included in ROUTE, VEHICLE_CONTROL, STOP, COMPLETE_TRIP_PACKAGE
        hr_required = package_mode in ("ROUTE", "VEHICLE_CONTROL", "STOP", "COMPLETE_TRIP_PACKAGE")
        hr_included = hr_required or route_plan_reference is not None
        if hr_required and not route_plan_reference:
            warnings.append("Ruta pendiente de cálculo")
        
        entries.append(
            TransportDeliveryDocumentEntry(
                document_type_code="HR",
                family_code="TRANSPORT",
                template_key="transport.route_sheet",
                required=hr_required,
                included=hr_included,
                filename_suggestion=f"PREVIEW_HR_{trip_reference}.pdf",
                render_status="SUCCESS" if route_plan_reference else "SKIPPED",
                reason_if_missing=None if route_plan_reference else "Ruta no calculada",
            )
        )
        
        # CVT: required in VEHICLE_CONTROL, COMPLETE_TRIP_PACKAGE
        cvt_required = package_mode in ("VEHICLE_CONTROL", "COMPLETE_TRIP_PACKAGE")
        cvt_included = cvt_required
        entries.append(
            TransportDeliveryDocumentEntry(
                document_type_code="CVT",
                family_code="TRANSPORT",
                template_key="transport.vehicle_control",
                required=cvt_required,
                included=cvt_included,
                filename_suggestion=f"PREVIEW_CVT_{trip_reference}.pdf",
            )
        )
        
        # PAR: required in STOP, COMPLETE_TRIP_PACKAGE
        par_required = package_mode in ("STOP", "COMPLETE_TRIP_PACKAGE")
        par_included = par_required
        entries.append(
            TransportDeliveryDocumentEntry(
                document_type_code="PAR",
                family_code="TRANSPORT",
                template_key="transport.stop_record",
                required=par_required,
                included=par_included,
                filename_suggestion=f"PREVIEW_PAR_{trip_reference}.pdf",
            )
        )
        
        # INC: required in INCIDENT, COMPLETE_TRIP_PACKAGE
        inc_required = package_mode in ("INCIDENT", "COMPLETE_TRIP_PACKAGE")
        inc_included = inc_required or payload.get("incident_code") is not None
        entries.append(
            TransportDeliveryDocumentEntry(
                document_type_code="INC",
                family_code="TRANSPORT",
                template_key="transport.incident_report",
                required=inc_required,
                included=inc_included,
                filename_suggestion=f"PREVIEW_INC_{trip_reference}.pdf",
            )
        )
        
        # POD: required in DELIVERY, PARTIAL_DELIVERY, REJECTED_DELIVERY, COMPLETE_TRIP_PACKAGE
        pod_required = package_mode in ("DELIVERY", "PARTIAL_DELIVERY", "REJECTED_DELIVERY", "COMPLETE_TRIP_PACKAGE")
        pod_included = pod_required
        entries.append(
            TransportDeliveryDocumentEntry(
                document_type_code="POD",
                family_code="DELIVERY",
                template_key="delivery.proof_of_delivery",
                required=pod_required,
                included=pod_included,
                filename_suggestion=f"PREVIEW_POD_{trip_reference}.pdf",
            )
        )
        
        # EP: required in PARTIAL_DELIVERY, COMPLETE_TRIP_PACKAGE
        ep_required = package_mode in ("PARTIAL_DELIVERY", "COMPLETE_TRIP_PACKAGE")
        ep_included = ep_required
        entries.append(
            TransportDeliveryDocumentEntry(
                document_type_code="EP",
                family_code="DELIVERY",
                template_key="delivery.partial_delivery",
                required=ep_required,
                included=ep_included,
                filename_suggestion=f"PREVIEW_EP_{trip_reference}.pdf",
            )
        )
        
        # RECH: required in REJECTED_DELIVERY, COMPLETE_TRIP_PACKAGE
        rech_required = package_mode in ("REJECTED_DELIVERY", "COMPLETE_TRIP_PACKAGE")
        rech_included = rech_required
        entries.append(
            TransportDeliveryDocumentEntry(
                document_type_code="RECH",
                family_code="DELIVERY",
                template_key="delivery.rejection_act",
                required=rech_required,
                included=rech_included,
                filename_suggestion=f"PREVIEW_RECH_{trip_reference}.pdf",
            )
        )
        
        return TransportDeliveryDocumentPackageManifest(
            package_mode=package_mode,
            organization=organization,
            branch=branch,
            warehouse=warehouse,
            trip_reference=trip_reference,
            route_plan_reference=route_plan_reference,
            dispatch_reference=dispatch_reference,
            vehicle_snapshot=vehicle,
            driver_snapshot=driver,
            document_entries=entries,
            package_status="READY_FOR_PREVIEW" if not warnings else "INCOMPLETE",
            generated_at=datetime.now(timezone.utc).isoformat(),
            generated_by="system",
            preview_mode=True,
            warnings=warnings,
        )

