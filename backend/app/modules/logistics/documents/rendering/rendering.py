"""Core Document Rendering Engine, Contracts, and QR Generator (Phase 014, Phase 015, Phase 016 & Phase 021)."""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import io
import os
import re
from typing import Any

# Jinja2 Template Engine
try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False

# QR Code Generator
try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

# WeasyPrint PDF Renderer
try:
    import weasyprint
    HAS_WEASYPRINT = True
except (ImportError, Exception):
    HAS_WEASYPRINT = False

# ReportLab PDF Renderer
try:
    import reportlab
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except (ImportError, Exception):
    HAS_REPORTLAB = False


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class DocumentRenderCommand:
    document_type_code: str
    template_key: str = "base.document"
    template_version: str = "1.0.0"
    catalog_version: str = "1.0.0"
    code_standard_version: str = "1.0.0"
    document_code: str | None = None
    document_status: str = "PREVIEW"
    document_title: str = "VISTA PREVIA DE DOCUMENTO"
    organization_name: str = "PROYECTO T1 LOGÍSTICA S.A.C."
    branch_name: str = "SEDE PRINCIPAL"
    document_data: dict[str, Any] = field(default_factory=dict)
    header_data: dict[str, Any] = field(default_factory=dict)
    footer_data: dict[str, Any] = field(default_factory=dict)
    qr_data: str | None = None
    signature_data: dict[str, Any] | None = None
    watermark_text: str | None = "VISTA PREVIA"
    preview_mode: bool = True
    requested_by: str | None = None


@dataclass(frozen=True)
class HtmlRenderResult:
    html: str
    template_key: str
    template_version: str
    rendered_at: datetime
    content_hash: str
    warnings: list[str]
    renderer_version: str = "1.0.0"


@dataclass(frozen=True)
class PdfRenderResult:
    pdf_bytes: bytes
    mime_type: str = "application/pdf"
    filename_suggestion: str = "document_preview.pdf"
    size_bytes: int = 0
    page_count: int = 1
    file_hash: str = ""
    content_hash: str = ""
    template_key: str = "base.document"
    template_version: str = "1.0.0"
    renderer_name: str = "ReportLab"
    renderer_version: str = "1.0.0"
    rendered_at: datetime = field(default_factory=utc_now)
    warnings: list[str] = field(default_factory=list)
    rendering_duration_ms: float = 0.0


class DocumentQRGenerator:
    """Generates PNG/SVG QR code representations as Base64 data URIs."""

    @staticmethod
    def generate_qr_base64(data: str, preview_mode: bool = True) -> str:
        payload = f"PREVIEW:{data}" if preview_mode else data
        if HAS_QRCODE:
            qr = qrcode.QRCode(version=1, box_size=4, border=2)
            qr.add_data(payload)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{b64_str}"
        else:
            svg = (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
                f'<rect width="100" height="100" fill="#f0f0f0"/>'
                f'<text x="50" y="55" font-size="10" text-anchor="middle">QR:{payload[:10]}</text>'
                f'</svg>'
            )
            b64_str = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
            return f"data:image/svg+xml;base64,{b64_str}"


DOCUMENT_METADATA_REGISTRY: dict[str, dict[str, Any]] = {
    "AREC": {
        "title": "ACTA DE RECEPCIÓN DE BIENES E INSUMOS",
        "short_title": "ACTA DE RECEPCIÓN",
        "family": "INBOUND",
        "counterparty_label": "Proveedor / Remitente",
        "default_counterparty": "DISTRIBUIDORA LOGÍSTICA DEL PERÚ S.A.C. (RUC 20512345678)",
        "reference_label": "N° O/C / Guía Remisión",
        "default_reference": "OC-LIM-2026-000412 / GR-001-008921",
        "transport_label": "Muelle / Transporte",
        "default_transport": "Muelle 03 | Placa: ABC-789 (Carlos Mendoza)",
        "notes": "Documento emitido conforme al procedimiento de control de calidad y recepción en almacén. La firma acredita la verificación física y conformidad de los ítems recibidos.",
        "headers": ["#", "Código / SKU", "Descripción del Bien / Insumo", "U.M.", "Cant. Esp.", "Cant. Rec.", "Estado"],
        "widths": [25, 65, 203, 35, 55, 55, 85],
        "aligns": ["CENTER", "LEFT", "LEFT", "CENTER", "RIGHT", "RIGHT", "CENTER"],
        "default_items": [
            ["1", "SKU-1001", "Aceite Industrial Sintético 5W-30 Alto Rendimiento", "GLN", "150.00", "150.00", "CONFORME"],
            ["2", "SKU-1002", "Filtros de Aire Heavy Duty para Maquinaria Pesada", "UND", "80.00", "80.00", "CONFORME"],
            ["3", "SKU-1003", "Grasa Lubricante Multipropósito EP-2 Balde 16kg", "BLD", "25.00", "25.00", "CONFORME"],
            ["4", "SKU-1004", "Kit de Sellos y Empaquetaduras Hidráulicas 2 pulg", "JGO", "10.00", "10.00", "CONFORME"],
        ],
    },
    "CIT": {
        "title": "CITACIÓN Y TURNO PROGRAMADO DE DESCARGA",
        "short_title": "CITACIÓN DE DESCARGA",
        "family": "INBOUND",
        "counterparty_label": "Transportista / Proveedor",
        "default_counterparty": "TRANSPORTES LOGÍSTICOS DEL SUR S.A. (RUC 20489123841)",
        "reference_label": "N° Cita / Slot Asignado",
        "default_reference": "SLOT-2026-0802-0930 | Ventana: 09:00 - 11:00",
        "transport_label": "Unidad / Conductor",
        "default_transport": "Placa Tracto: F3B-890 | Manuel Salazar (Lic. Q-45892134)",
        "notes": "La unidad debe presentarse 15 minutos antes de la hora programada con EPP completo, SCTR vigente y precintos intactos para su inspección en garita.",
        "headers": ["#", "Código Ref.", "Tipo Carga / Descripción", "U.M.", "Pallets", "Peso Est. (KG)", "Estado"],
        "widths": [25, 65, 203, 35, 55, 55, 85],
        "aligns": ["CENTER", "LEFT", "LEFT", "CENTER", "RIGHT", "RIGHT", "CENTER"],
        "default_items": [
            ["1", "CARGA-01", "Palletizado de Repuestos y Componentes Mecánicos", "PLT", "12", "4,800.00", "CONFIRMADO"],
            ["2", "CARGA-02", "Bobinas de Embalaje Industrial Termocontraíble", "PLT", "8", "2,400.00", "CONFIRMADO"],
        ],
    },
    "CPV": {
        "title": "CONSTANCIA DE PESO Y CONTROL VOLUMÉTRICO",
        "short_title": "CONSTANCIA DE PESO (CPV)",
        "family": "INBOUND",
        "counterparty_label": "Empresa Transportista",
        "default_counterparty": "EXPRESS CARGO PERÚ S.A.C. (RUC 20600123984)",
        "reference_label": "N° Ticket de Báscula",
        "default_reference": "TICK-BASC-2026-00912 / Báscula Puente 01",
        "transport_label": "Vehículo / Precintos",
        "default_transport": "Tracto: T9A-812 | Carreta: C3B-981 | Precinto: SN-9988123",
        "notes": "Pesaje certificado en báscula electrónica calibrada con certificado INACAL vigente. Medición conforme a tolerancias reglamentarias de pesos y medidas MTC.",
        "headers": ["#", "Concepto de Pesaje / Registro", "Detalle de Medición", "U.M.", "Peso Bruto", "Peso Neto", "Resultado"],
        "widths": [25, 110, 160, 35, 60, 60, 73],
        "aligns": ["CENTER", "LEFT", "LEFT", "CENTER", "RIGHT", "RIGHT", "CENTER"],
        "default_items": [
            ["1", "PESAJE INICIAL (LLENO)", "Entrada de unidad con carga completa", "KG", "32,450.00", "-", "REGISTRADO"],
            ["2", "PESAJE TARA (VACÍO)", "Salida de unidad posterior a descarga", "KG", "14,200.00", "-", "REGISTRADO"],
            ["3", "CARGA NETA CALCULADA", "Diferencia neta de material ingresado", "KG", "-", "18,250.00", "CONFORME"],
        ],
    },
    "DIF": {
        "title": "ACTA DE DISCREPANCIAS E INCIDENCIAS EN RECEPCIÓN",
        "short_title": "ACTA DE DISCREPANCIAS",
        "family": "INBOUND",
        "counterparty_label": "Proveedor Observado",
        "default_counterparty": "IMPORTACIONES Y SUMINISTROS DEL PACÍFICO S.A.",
        "reference_label": "Documento Origen / GR",
        "default_reference": "AREC-LIM-2026-000142 / Guía: GR-002-44120",
        "transport_label": "Inspector / Área",
        "default_transport": "Ing. Roberto Gómez (Control Calidad e Inbound)",
        "notes": "Las unidades discrepantes u observadas quedan retenidas en zona de cuarentena hasta la emisión de la Nota de Crédito o reposición física por el proveedor.",
        "headers": ["#", "SKU / Código", "Descripción del Bien", "U.M.", "Facturado", "Recibido", "Discrepancia"],
        "widths": [25, 65, 203, 35, 55, 55, 85],
        "aligns": ["CENTER", "LEFT", "LEFT", "CENTER", "RIGHT", "RIGHT", "CENTER"],
        "default_items": [
            ["1", "SKU-2041", "Rodamientos de Precisión SKF 6205-2RSH", "UND", "100.00", "92.00", "-8 FALTANTE"],
            ["2", "SKU-2045", "Válvulas Reguladoras de Presión 1/2 pulg", "UND", "50.00", "50.00", "3 DAÑADOS"],
        ],
    },
    "NC": {
        "title": "INFORME DE NO CONFORMIDAD DE CALIDAD",
        "short_title": "REPORTE NO CONFORMIDAD",
        "family": "QUALITY",
        "counterparty_label": "Área / Proveedor Origen",
        "default_counterparty": "FABRICACIONES METALMECÁNICAS LIMA S.A.C.",
        "reference_label": "N° Lote / Reporte QA",
        "default_reference": "LOT-2026-X09 / Severidad: MAYOR",
        "transport_label": "Responsable Aseguramiento",
        "default_transport": "Lic. Patricia Flores (Jefatura de Calidad)",
        "notes": "Lote no apto para liberación operativa. Se dispone el bloqueo preventivo en sistema WMS y traslado inmediato al almacén de cuarentena.",
        "headers": ["#", "Muestra / Ítem", "Parámetro Inspeccionado", "Norma", "Esperado", "Hallado", "Veredicto"],
        "widths": [25, 75, 170, 45, 60, 65, 83],
        "aligns": ["CENTER", "LEFT", "LEFT", "CENTER", "LEFT", "LEFT", "CENTER"],
        "default_items": [
            ["1", "M-01: Eje Rotor", "Tolerancia Dimensional y Alabeo", "ISO 286", "+/- 0.05 mm", "+0.18 mm", "NO CONFORME"],
            ["2", "M-02: Empaque", "Hermeticidad y Sellado de Seguridad", "NTP 399", "Sellado 100%", "Rasgadura", "NO CONFORME"],
        ],
    },
    "APC": {
        "title": "ACTA DE PASE DE CONTROL DE ACCESO Y VIGILANCIA",
        "short_title": "PASE DE CONTROL (APC)",
        "family": "INBOUND",
        "counterparty_label": "Empresa / Conductor",
        "default_counterparty": "TRANSPORTES INTEGRALES DEL PERÚ S.A.C.",
        "reference_label": "Garita / Control",
        "default_reference": "Garita 01 - Acceso Vehicular Pesado | Turno A",
        "transport_label": "Vehículo / Conductor",
        "default_transport": "Placa: AYZ-654 | Conductor: Víctor Huamán (DNI 41209384)",
        "notes": "Ingreso autorizado con revisión de seguridad, checklist vehicular y verificación de póliza SCTR completa. Salida registrada conforme.",
        "headers": ["#", "Documento Presentado", "N° Registro / Ref.", "U.M.", "Personal", "Horario", "Estado"],
        "widths": [25, 110, 150, 35, 70, 60, 73],
        "aligns": ["CENTER", "LEFT", "LEFT", "CENTER", "LEFT", "CENTER", "CENTER"],
        "default_items": [
            ["1", "Guía de Remisión Remitente", "GR-003-88210", "DOC", "Conductor", "07:45 - In", "APROBADO"],
            ["2", "Póliza de Seguro SCTR", "POL-992104-MAPFRE", "DOC", "Conductor/Aux", "Vigente", "APROBADO"],
        ],
    },
    "CEP": {
        "title": "CERTIFICADO DE EVALUACIÓN Y HOMOLOGACIÓN DE PROVEEDORES",
        "short_title": "CERTIFICADO EVALUACIÓN",
        "family": "PURCHASING",
        "counterparty_label": "Proveedor Evaluado",
        "default_counterparty": "TECNOLOGÍA Y SUMINISTROS INDUSTRIALES S.A.C. (RUC 20459871234)",
        "reference_label": "Período / Calificación",
        "default_reference": "Semestre 2026-I | Calificación Global: 96.5 / 100",
        "transport_label": "Comité Evaluador",
        "default_transport": "Gerencia de Compras y Aseguramiento de Cadena de Suministro",
        "notes": "Proveedor homologado en Categoría A (Excelente). Cumplimiento sobresaliente en calidad de producto, puntualidad en entregas (OTIF) y gestión documental.",
        "headers": ["#", "Criterio de Evaluación", "Descripción del Indicador", "Peso", "Puntaje", "Nivel", "Estado"],
        "widths": [25, 110, 160, 35, 55, 65, 73],
        "aligns": ["CENTER", "LEFT", "LEFT", "CENTER", "RIGHT", "CENTER", "CENTER"],
        "default_items": [
            ["1", "Calidad y Cero Defectos", "Índice de rechazos e incidencias en recepción", "40%", "39.0 / 40", "97.5%", "EXCELENTE"],
            ["2", "Puntualidad en Entregas (OTIF)", "Cumplimiento de ventanas y plazos de entrega", "35%", "34.0 / 35", "97.1%", "EXCELENTE"],
            ["3", "Gestión Documental y SST", "Trazabilidad, guías electrónicas y protocolos SST", "25%", "23.5 / 25", "94.0%", "CUMPLE"],
        ],
    },
    "PED": {
        "title": "SOLICITUD DE PEDIDO Y REQUERIMIENTO DE MATERIALES",
        "short_title": "REQUERIMIENTO PEDIDO",
        "family": "OUTBOUND",
        "counterparty_label": "Área Solicitante",
        "default_counterparty": "DEPARTAMENTO DE OPERACIONES Y MANTENIMIENTO PLANTA",
        "reference_label": "N° Centro de Costos",
        "default_reference": "CC-4010 - Mantenimiento Mecánico | Prioridad: ALTA",
        "transport_label": "Destino / Entrega",
        "default_transport": "Taller Central - Muelle de Despacho Bloque 4",
        "notes": "Requerimiento aprobado para abastecimiento operativo. Despacho programado con cargo a la cuenta de centro de costos indicada.",
        "headers": ["#", "Código Material", "Descripción del Bien / Suministro", "U.M.", "Cant. Sol.", "Cant. Aprob.", "Disponibilidad"],
        "widths": [25, 75, 193, 35, 55, 55, 85],
        "aligns": ["CENTER", "LEFT", "LEFT", "CENTER", "RIGHT", "RIGHT", "CENTER"],
        "default_items": [
            ["1", "MAT-301", "Cable Eléctrico Vulcanizado 3x10 AWG Libre de Halógenos", "MTR", "250.00", "250.00", "EN STOCK"],
            ["2", "MAT-302", "Interruptor Termomagnético Industrial Trifásico 63A", "UND", "6.00", "6.00", "EN STOCK"],
            ["3", "MAT-303", "Cinta Aislante Autofundente de Alta Tensión 3M", "ROL", "20.00", "20.00", "EN STOCK"],
        ],
    },
    "MAN": {
        "title": "MANIFIESTO DE CARGA DE TRANSPORTE TERRESTRE",
        "short_title": "MANIFIESTO DE CARGA",
        "family": "DISPATCH",
        "counterparty_label": "Consignatario / Destino",
        "default_counterparty": "MINERA SUR PERÚ S.A. - SEDE AREQUIPA (RUC 20109847123)",
        "reference_label": "Ruta / Trayecto",
        "default_reference": "Lima Central -> Arequipa Terminal | Modalidad: Terrestre",
        "transport_label": "Unidad de Transporte",
        "default_transport": "Tracto VOLVO FH-500: F3B-890 | Semirremolque: R9A-120 (Jorge Vargas)",
        "notes": "Manifiesto oficial de carga emitido en conformidad con el Reglamento Nacional de Transporte Terrestre. Precintos verificados al cierre de furgón.",
        "headers": ["#", "N° Guía Remisión", "Destinatario / Cliente", "Ciudad", "Bultos", "Peso (KG)", "Precinto"],
        "widths": [25, 80, 160, 55, 45, 65, 93],
        "aligns": ["CENTER", "LEFT", "LEFT", "CENTER", "RIGHT", "RIGHT", "CENTER"],
        "default_items": [
            ["1", "GR-001-00981", "MINERA SUR PERÚ S.A.", "Arequipa", "18", "8,500.00", "PR-10091"],
            ["2", "GR-001-00982", "CONSORCIO VIAL ANDINO S.A.", "Moquegua", "20", "10,100.00", "PR-10092"],
            ["3", "GR-001-00983", "MAQUINARIAS Y SERVICIOS S.A.", "Tacna", "10", "4,200.00", "PR-10093"],
        ],
    },
    "POD": {
        "title": "PRUEBA DE ENTREGA Y CONFORMIDAD DE RECEPCIÓN (POD)",
        "short_title": "PRUEBA DE ENTREGA (POD)",
        "family": "DELIVERY",
        "counterparty_label": "Cliente / Receptor",
        "default_counterparty": "MINERA SUR PERÚ S.A. (Carretera Variante Km 14.5, Arequipa)",
        "reference_label": "N° Despacho / Manifiesto",
        "default_reference": "MAN-2026-000523 / GR-001-00981",
        "transport_label": "Transportista / Entrega",
        "default_transport": "TRANSPORTES ANDINOS S.A. | Entregado: 02/08/2026 16:30",
        "notes": "La mercadería fue entregada íntegra, con precintos de seguridad conformes y empaques en óptimas condiciones. Recepción firmada por el encargado en destino.",
        "headers": ["#", "Guía Ref.", "Descripción de la Carga", "U.M.", "Bultos", "Peso (KG)", "Conformidad"],
        "widths": [25, 75, 193, 35, 45, 65, 85],
        "aligns": ["CENTER", "LEFT", "LEFT", "CENTER", "RIGHT", "RIGHT", "CENTER"],
        "default_items": [
            ["1", "GR-001-00981", "Componentes Mecánicos y Repuestos Industriales", "CJ", "18", "8,500.00", "CONFORME"],
            ["2", "GR-001-00982", "Equipos de Bombeo y Válvulas de Presión", "PLT", "20", "10,100.00", "CONFORME"],
        ],
    },
    "OC": {
        "title": "ORDEN DE COMPRA INSTITUCIONAL",
        "short_title": "ORDEN DE COMPRA",
        "family": "PURCHASING",
        "counterparty_label": "Proveedor Seleccionado",
        "default_counterparty": "DISTRIBUIDORA INDUSTRIAL S.A.C. (RUC 20512345678)",
        "reference_label": "Cotización / Solicitud",
        "default_reference": "COT-2026-00941 / Requerimiento: REQ-00124",
        "transport_label": "Condición de Pago / Entrega",
        "default_transport": "Crédito 30 Días | Entrega en Almacén Lurín",
        "notes": "Orden de compra aprobada. Toda entrega debe acompañarse con la Guía de Remisión Remitente indicando el presente número de orden.",
        "headers": ["#", "Código SKU", "Descripción del Bien / Servicio", "U.M.", "Cantidad", "P. Unit (S/)", "Total (S/)"],
        "widths": [25, 70, 198, 35, 50, 65, 80],
        "aligns": ["CENTER", "LEFT", "LEFT", "CENTER", "RIGHT", "RIGHT", "RIGHT"],
        "default_items": [
            ["1", "SKU-1001", "Aceite Industrial Sintético 5W-30 Alto Rendimiento", "GLN", "150.00", "45.00", "6,750.00"],
            ["2", "SKU-1002", "Filtros de Aire Heavy Duty para Maquinaria Pesada", "UND", "80.00", "120.00", "9,600.00"],
        ],
    },
}


class DocumentRendererEngine:
    """Central Document Rendering Engine using Jinja2 and ReportLab PDF Generator (Phase 021)."""

    TEMPLATE_MAP = {
        "base.document": "base/base_v1.html",
        # PURCHASING family (Phase 015)
        "purchasing.req": "purchasing/request/req_v1.html",
        "purchasing.scot": "purchasing/quotation_request/scot_v1.html",
        "purchasing.cco": "purchasing/comparison/cco_v1.html",
        "purchasing.oc": "purchasing/purchase_order/oc_v1.html",
        "purchasing.apc": "purchasing/approval/apc_v1.html",
        "purchasing.cep": "purchasing/supplier_dispatch/cep_v1.html",
        # INBOUND family (Phase 016)
        "inbound.cit": "inbound/appointment/cit_v1.html",
        "inbound.cpv": "inbound/gate_control/cpv_v1.html",
        "inbound.arec": "inbound/reception_act/arec_v1.html",
        "inbound.ni": "inbound/inbound_note/ni_v1.html",
        "inbound.dif": "inbound/differences/dif_v1.html",
        # QUALITY family (Phase 016)
        "quality.nc": "quality/non_conformity/nc_v1.html",
        # INVENTORY family (Phase 017)
        "inventory.location_label": "inventory/location_label/eub_v1.html",
        "inventory.putaway_order": "inventory/putaway_order/put_v1.html",
        "inventory.movement": "inventory/movement/mov_v1.html",
        "inventory.adjustment": "inventory/adjustment/aji_v1.html",
        "inventory.count": "inventory/count/cnt_v1.html",
        "inventory.difference": "inventory/difference/adi_v1.html",
        "inventory.transfer": "inventory/transfer/tra_v1.html",
        "inventory.transfer_receipt": "inventory/transfer_receipt/crt_v1.html",
        # OUTBOUND family (Phase 018)
        "outbound.ped": "outbound/request/ped_v1.html",
        "outbound.ods": "outbound/outbound_order/ods_v1.html",
        "outbound.picking_list": "outbound/picking/pick_v1.html",
        "outbound.packing_list": "outbound/packing/pack_v1.html",
        # DISPATCH family (Phase 018)
        "dispatch.load_manifest": "dispatch/load_manifest/man_v1.html",
        "dispatch.dispatch_act": "dispatch/dispatch_act/adsp_v1.html",
        "dispatch.seal_control": "dispatch/seal_control/cpr_v1.html",
        # TRANSPORT family (Phase 019)
        "transport.trip_sheet": "transport/trip_sheet/hv_v1.html",
        "transport.route_sheet": "transport/route_sheet/hr_v1.html",
        "transport.vehicle_control": "transport/vehicle_control/cvt_v1.html",
        "transport.stop_record": "transport/stop_record/par_v1.html",
        "transport.incident_report": "transport/incident/inc_v1.html",
        # DELIVERY family (Phase 019)
        "delivery.proof_of_delivery": "delivery/proof_of_delivery/pod_v1.html",
        "delivery.partial_delivery": "delivery/partial_delivery/ep_v1.html",
        "delivery.rejection_act": "delivery/rejection/rech_v1.html",
    }

    def __init__(self, templates_dir: str | None = None) -> None:
        if not templates_dir:
            templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.templates_dir = templates_dir

        if HAS_JINJA2:
            self.env = Environment(
                loader=FileSystemLoader(self.templates_dir),
                autoescape=select_autoescape(["html", "xml"]),
                undefined=StrictUndefined,
            )
        else:
            self.env = None

    def render_html(self, command: DocumentRenderCommand) -> HtmlRenderResult:
        qr_b64 = None
        if command.qr_data:
            qr_b64 = DocumentQRGenerator.generate_qr_base64(command.qr_data, preview_mode=command.preview_mode)

        template_path = self.TEMPLATE_MAP.get(command.template_key, "base/base_v1.html")

        # Resolve document metadata
        code = (command.document_type_code or "AREC").upper()
        meta = DOCUMENT_METADATA_REGISTRY.get(code, {
            "title": command.document_title or f"DOCUMENTO INSTITUCIONAL {code}",
            "short_title": f"DOCUMENTO {code}",
            "family": "GENERAL",
            "counterparty_label": "Contraparte / Tercero",
            "default_counterparty": "ENTIDAD DE CONTROL / TERCERO",
            "reference_label": "N° Referencia",
            "default_reference": f"REF-{code}-2026-0001",
            "transport_label": "Muelle / Transporte",
            "default_transport": "Sede Principal",
            "notes": "Documento emitido en conformidad con los procedimientos institucionales de la organización.",
            "headers": ["#", "Código", "Descripción", "U.M.", "Cant. Esperada", "Cant. Recibida", "Estado"],
            "default_items": [
                ["1", f"{code}-001", "Registro Operativo de Bienes y Materiales", "UND", "100.00", "100.00", "CONFORME"],
                ["2", f"{code}-002", "Suministro e Insumos Complementarios", "UND", "50.00", "50.00", "CONFORME"],
            ],
        })

        if HAS_JINJA2 and self.env:
            try:
                template = self.env.get_template(template_path)
            except Exception:
                template = self.env.get_template("base/base_v1.html")

            ctx = {
                "cmd": command,
                "meta": meta,
                "qr_b64": qr_b64,
                "now": utc_now(),
            }
            rendered_html = template.render(**ctx)
        else:
            rendered_html = (
                f"<html><head><title>{command.document_title}</title></head><body>"
                f"<h1>{command.organization_name}</h1>"
                f"<h2>{command.document_title} - {command.document_code or 'PREVIEW'}</h2>"
                f"<p>Status: {command.document_status}</p>"
                f"<p>Watermark: {command.watermark_text or 'VISTA PREVIA'}</p>"
                f"</body></html>"
            )

        content_hash = hashlib.sha256(rendered_html.encode("utf-8")).hexdigest()

        return HtmlRenderResult(
            html=rendered_html,
            template_key=command.template_key,
            template_version=command.template_version,
            rendered_at=utc_now(),
            content_hash=content_hash,
            warnings=["Engine running in preview mode"] if command.preview_mode else [],
        )

    def render_pdf(self, command: DocumentRenderCommand) -> PdfRenderResult:
        start_time = datetime.now()
        html_res = self.render_html(command)

        pdf_bytes: bytes
        renderer_name = "ReportLab"

        if HAS_REPORTLAB:
            try:
                pdf_bytes = self._render_reportlab_pdf(command)
                renderer_name = "ReportLab"
            except Exception:
                if HAS_WEASYPRINT:
                    try:
                        wp_doc = weasyprint.HTML(string=html_res.html, base_url=self.templates_dir)
                        pdf_bytes = wp_doc.write_pdf()
                        renderer_name = "WeasyPrint"
                    except Exception:
                        pdf_bytes = self._generate_fallback_pdf(html_res.html, command)
                        renderer_name = "FallbackPdfEngine"
                else:
                    pdf_bytes = self._generate_fallback_pdf(html_res.html, command)
                    renderer_name = "FallbackPdfEngine"
        elif HAS_WEASYPRINT:
            try:
                wp_doc = weasyprint.HTML(string=html_res.html, base_url=self.templates_dir)
                pdf_bytes = wp_doc.write_pdf()
                renderer_name = "WeasyPrint"
            except Exception:
                pdf_bytes = self._generate_fallback_pdf(html_res.html, command)
                renderer_name = "FallbackPdfEngine"
        else:
            pdf_bytes = self._generate_fallback_pdf(html_res.html, command)
            renderer_name = "FallbackPdfEngine"

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000.0
        file_hash = hashlib.sha256(pdf_bytes).hexdigest()
        filename = f"PREVIEW_{command.document_type_code}.pdf"

        return PdfRenderResult(
            pdf_bytes=pdf_bytes,
            mime_type="application/pdf",
            filename_suggestion=filename,
            size_bytes=len(pdf_bytes),
            page_count=1,
            file_hash=file_hash,
            content_hash=html_res.content_hash,
            template_key=command.template_key,
            template_version=command.template_version,
            renderer_name=renderer_name,
            rendered_at=utc_now(),
            warnings=html_res.warnings,
            rendering_duration_ms=duration_ms,
        )

    def _render_reportlab_pdf(self, command: DocumentRenderCommand) -> bytes:
        """High-fidelity ReportLab Platypus PDF Generator with full institutional branding."""
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=45
        )

        styles = getSampleStyleSheet()

        # Custom typography styles
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=10.2,
            textColor=colors.HexColor("#334155"),
        )
        body_bold = ParagraphStyle(
            "DocBodyBold",
            parent=body_style,
            fontName="Helvetica-Bold",
        )
        body_center = ParagraphStyle(
            "DocBodyCenter",
            parent=body_style,
            alignment=1,
        )
        body_right = ParagraphStyle(
            "DocBodyRight",
            parent=body_style,
            alignment=2,
        )
        title_box_style = ParagraphStyle(
            "DocTitleBox",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            alignment=1,
            textColor=colors.HexColor("#0f172a"),
        )

        # 1. Resolve Document Type Metadata
        doc_code = (command.document_type_code or "AREC").upper()
        meta = DOCUMENT_METADATA_REGISTRY.get(doc_code, {
            "title": command.document_title or f"DOCUMENTO INSTITUCIONAL {doc_code}",
            "short_title": f"DOCUMENTO {doc_code}",
            "family": "GENERAL",
            "counterparty_label": "Contraparte / Tercero",
            "default_counterparty": "ENTIDAD DE CONTROL / TERCERO",
            "reference_label": "N° Referencia",
            "default_reference": f"REF-{doc_code}-2026-0001",
            "transport_label": "Muelle / Transporte",
            "default_transport": "Sede Principal",
            "notes": "Documento emitido en conformidad con los procedimientos institucionales de la organización.",
            "headers": ["#", "Código", "Descripción", "U.M.", "Cant. Esperada", "Cant. Recibida", "Estado"],
            "widths": [25, 75, 193, 35, 55, 55, 85],
            "aligns": ["CENTER", "LEFT", "LEFT", "CENTER", "RIGHT", "RIGHT", "CENTER"],
            "default_items": [
                ["1", f"{doc_code}-001", "Registro Operativo de Bienes y Materiales", "UND", "100.00", "100.00", "CONFORME"],
                ["2", f"{doc_code}-002", "Suministro e Insumos Complementarios", "UND", "50.00", "50.00", "CONFORME"],
            ],
        })

        # 2. Extract Company and Header Data
        header_data = command.header_data or {}
        legal_name = header_data.get("legal_name") or command.organization_name or "ANDESLOG OPERACIONES S.A.C."
        trade_name = header_data.get("trade_name") or "AndesLog Operaciones"
        ruc = header_data.get("ruc") or "20601234567"
        fiscal_addr = header_data.get("fiscal_address") or "Av. Industrial 456, Parque Industrial Lurín, Lima"
        branch_name = header_data.get("branch_name") or command.branch_name or "Sede Principal Lima"
        email = header_data.get("email") or "operaciones@andeslog.pe"
        phone = header_data.get("phone") or "(01) 710-8800"

        # 3. Extract Signer Data
        sig_data = command.signature_data or {}
        signer_name = sig_data.get("signer_name") or "CARLOS ALBERTO MENDOZA"
        signer_role = sig_data.get("signer_role") or "Representante Legal / Apoderado"
        signer_dni = sig_data.get("signer_dni") or "****5678"

        # 4. Extract Custom Data or use Defaults
        custom_data = command.document_data or {}
        if "custom_data" in custom_data and isinstance(custom_data["custom_data"], dict):
            custom_data = {**custom_data, **custom_data["custom_data"]}

        doc_number = command.document_code or custom_data.get("document_code") or f"PREV-{doc_code}-2026-000142"
        now_dt = utc_now()
        emission_date = custom_data.get("date") or custom_data.get("emission_date") or now_dt.strftime("%d/%m/%Y %H:%M UTC")
        counterparty_name = custom_data.get("counterparty_name") or custom_data.get("supplier_name") or custom_data.get("client_name") or meta["default_counterparty"]
        doc_reference = custom_data.get("reference") or custom_data.get("waybill_reference") or custom_data.get("order_reference") or meta["default_reference"]
        transport_info = custom_data.get("transport_info") or custom_data.get("dock") or meta["default_transport"]
        notes_text = custom_data.get("notes") or custom_data.get("observations") or meta["notes"]

        story = []

        # ----------------------------------------------------
        # 1. Header Table: [Logo/Brand, Company Info, SUNAT Box]
        # ----------------------------------------------------
        logo_flowable = None
        logo_bytes = header_data.get("logo_bytes")
        if logo_bytes and isinstance(logo_bytes, bytes):
            try:
                logo_flowable = RLImage(io.BytesIO(logo_bytes), width=105, height=45, kind="proportional")
            except Exception:
                logo_flowable = None

        if not logo_flowable:
            logo_flowable = Paragraph(
                '<b><font size=13 color="#0f172a">ANDESLOG</font></b><br/>'
                '<font size=8 color="#0284c7">OPERACIONES LOGÍSTICAS</font>',
                body_style
            )

        center_header = Paragraph(
            f'<b><font size=9.5 color="#0f172a">{legal_name}</font></b><br/>'
            f'<font size=7.5 color="#475569"><b>{trade_name}</b> | RUC: {ruc}<br/>'
            f'Dir: {fiscal_addr}<br/>'
            f'Sede: {branch_name} | Email: {email} | Tel: {phone}</font>',
            body_style
        )

        doc_short_title = meta.get("short_title", meta["title"])
        right_box = Paragraph(
            f'<font size=8.5 color="#0f172a"><b>R.U.C. N° {ruc}</b></font><br/>'
            f'<b><font size=9 color="#0369a1">{doc_short_title}</font></b><br/>'
            f'<b><font size=9.5 color="#b91c1c">{doc_number}</font></b><br/>'
            f'<font size=7 color="#dc2626"><b>VISTA PREVIA INSTITUCIONAL</b></font>',
            title_box_style
        )

        header_table = Table([[logo_flowable, center_header, right_box]], colWidths=[110, 250, 163])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (2, 0), (2, 0), 1.2, colors.HexColor("#0f172a")),
            ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#f8fafc")),
            ("ALIGN", (2, 0), (2, 0), "CENTER"),
            ("TOPPADDING", (2, 0), (2, 0), 5),
            ("BOTTOMPADDING", (2, 0), (2, 0), 5),
            ("LEFTPADDING", (2, 0), (2, 0), 6),
            ("RIGHTPADDING", (2, 0), (2, 0), 6),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 8))

        # ----------------------------------------------------
        # 2. Metadata Grid Table (2x3 key-value matrix)
        # ----------------------------------------------------
        meta_data = [
            [
                Paragraph('<b>Fecha y Hora de Emisión:</b>', body_style),
                Paragraph(str(emission_date), body_style),
                Paragraph('<b>Sede Operativa / Almacén:</b>', body_style),
                Paragraph(str(branch_name), body_style),
            ],
            [
                Paragraph('<b>Responsable / Solicitante:</b>', body_style),
                Paragraph(f'{signer_name} ({signer_role})', body_style),
                Paragraph(f'<b>{meta["counterparty_label"]}:</b>', body_style),
                Paragraph(str(counterparty_name), body_style),
            ],
            [
                Paragraph(f'<b>{meta["reference_label"]}:</b>', body_style),
                Paragraph(str(doc_reference), body_style),
                Paragraph(f'<b>{meta["transport_label"]}:</b>', body_style),
                Paragraph(str(transport_info), body_style),
            ],
        ]
        meta_table = Table(meta_data, colWidths=[120, 140, 120, 143])
        meta_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
            ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f1f5f9")),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 9))

        # ----------------------------------------------------
        # 3. Section Title
        # ----------------------------------------------------
        story.append(Paragraph('<b><font size=8.5 color="#0f172a">DETALLE DE ÍTEMS / REGISTROS OPERATIVOS</font></b>', body_style))
        story.append(Spacer(1, 3))

        # ----------------------------------------------------
        # 4. Items Table (Custom Columns & Rows)
        # ----------------------------------------------------
        headers = meta.get("headers", ["#", "Código", "Descripción", "U.M.", "Cant. Esp.", "Cant. Rec.", "Estado"])
        col_widths = meta.get("widths", [25, 75, 193, 35, 55, 55, 85])
        col_aligns = meta.get("aligns", ["CENTER", "LEFT", "LEFT", "CENTER", "RIGHT", "RIGHT", "CENTER"])

        # Determine items list
        raw_items = custom_data.get("items") or custom_data.get("received_items") or custom_data.get("lines")
        items_list = []
        if raw_items and isinstance(raw_items, list):
            for idx, item in enumerate(raw_items, start=1):
                if isinstance(item, dict):
                    code_val = item.get("code") or item.get("sku") or f"ITM-{idx:03d}"
                    desc_val = item.get("description") or item.get("name") or "Ítem registrado"
                    um_val = item.get("unit") or item.get("um") or "UND"
                    exp_val = str(item.get("expected_quantity") or item.get("quantity") or "0.00")
                    rec_val = str(item.get("received_quantity") or item.get("accepted_quantity") or exp_val)
                    st_val = str(item.get("status") or item.get("state") or "CONFORME")
                    items_list.append([str(idx), code_val, desc_val, um_val, exp_val, rec_val, st_val])
                elif isinstance(item, list):
                    items_list.append([str(x) for x in item])
        if not items_list:
            items_list = meta.get("default_items", [
                ["1", f"{doc_code}-001", "Registro Operativo de Bienes y Materiales", "UND", "100.00", "100.00", "CONFORME"],
                ["2", f"{doc_code}-002", "Suministro e Insumos Complementarios", "UND", "50.00", "50.00", "CONFORME"],
            ])

        table_rows = []
        header_cells = [Paragraph(f'<b><font color="white" size=7.5>{h}</font></b>', title_box_style) for h in headers]
        table_rows.append(header_cells)

        for row in items_list:
            row_cells = []
            for col_idx, cell_value in enumerate(row):
                if col_idx < len(col_aligns):
                    align = col_aligns[col_idx]
                else:
                    align = "LEFT"

                if align == "CENTER":
                    style_to_use = body_center
                elif align == "RIGHT":
                    style_to_use = body_right
                else:
                    style_to_use = body_style

                # Highlight status column if last
                if col_idx == len(row) - 1 and any(kw in str(cell_value).upper() for kw in ["CONFORME", "APROBADO", "EXCELENTE", "CONFIRMADO", "EN STOCK"]):
                    row_cells.append(Paragraph(f'<b><font size=7.5 color="#15803d">{cell_value}</font></b>', style_to_use))
                elif col_idx == len(row) - 1 and any(kw in str(cell_value).upper() for kw in ["RECHAZADO", "FALTANTE", "DAÑADO", "NO CONFORME"]):
                    row_cells.append(Paragraph(f'<b><font size=7.5 color="#dc2626">{cell_value}</font></b>', style_to_use))
                else:
                    row_cells.append(Paragraph(f'<font size=7.5>{cell_value}</font>', style_to_use))

            table_rows.append(row_cells)

        items_table = Table(table_rows, colWidths=col_widths)
        items_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 9))

        # ----------------------------------------------------
        # 5. Observations & General Conditions Box
        # ----------------------------------------------------
        obs_content = [
            [
                Paragraph(
                    f'<b><font size=7.5 color="#334155">OBSERVACIONES Y CONDICIONES GENERALES:</font></b><br/>'
                    f'<font size=7 color="#475569">{notes_text}</font>',
                    body_style
                )
            ]
        ]
        obs_table = Table(obs_content, colWidths=[523])
        obs_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(obs_table)
        story.append(Spacer(1, 16))

        # ----------------------------------------------------
        # 6. Signatures Block (KeepTogether)
        # ----------------------------------------------------
        sig_1 = Paragraph(
            '________________________________________<br/>'
            f'<b><font size=8 color="#0f172a">{signer_name}</font></b><br/>'
            f'<font size=7 color="#475569">{signer_role}<br/>'
            f'Doc. Identidad: {signer_dni}<br/>'
            f'<b><font color="#0369a1">FIRMANTE INSTITUCIONAL AUTORIZADO</font></b></font>',
            title_box_style
        )
        sig_2 = Paragraph(
            '________________________________________<br/>'
            f'<b><font size=8 color="#0f172a">RESPONSABLE OPERATIVO / RECEPCIÓN</font></b><br/>'
            f'<font size=7 color="#475569">Control y Fiscalización de Procesos<br/>'
            f'Sello y Firma de Conformidad<br/>'
            f'<b><font color="#64748b">CONFORMIDAD OPERATIVA</font></b></font>',
            title_box_style
        )

        sig_table = Table([[sig_1, sig_2]], colWidths=[261, 262])
        sig_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(KeepTogether([sig_table]))

        # ----------------------------------------------------
        # 7. Canvas Background Callback (Watermark + Footer)
        # ----------------------------------------------------
        def on_page(canvas_obj, doc_obj):
            # 1. Subtle Diagonal Watermark
            canvas_obj.saveState()
            canvas_obj.setFont("Helvetica-Bold", 30)
            canvas_obj.setFillColor(colors.Color(0.85, 0.15, 0.15, alpha=0.08))
            canvas_obj.translate(A4[0] / 2.0, A4[1] / 2.0)
            canvas_obj.rotate(-35)
            canvas_obj.drawCentredString(0, 0, "VISTA PREVIA INSTITUCIONAL — SIN VALOR LEGAL")
            canvas_obj.restoreState()

            # 2. Bottom Footer Rule and Text
            canvas_obj.saveState()
            canvas_obj.setFont("Helvetica", 7.5)
            canvas_obj.setFillColor(colors.HexColor("#64748b"))
            canvas_obj.setStrokeColor(colors.HexColor("#cbd5e1"))
            canvas_obj.setLineWidth(0.5)
            canvas_obj.line(36, 32, A4[0] - 36, 32)
            canvas_obj.drawString(36, 20, f"AndesLog Operaciones — {trade_name} | {meta['title']}")
            canvas_obj.drawRightString(A4[0] - 36, 20, f"Página 1 de 1 | Emitido: {now_dt.strftime('%d/%m/%Y %H:%M UTC')}")
            canvas_obj.restoreState()

        doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
        return buf.getvalue()

    def _generate_fallback_pdf(self, html_content: str, command: DocumentRenderCommand) -> bytes:
        """Minimal valid PDF 1.4 binary generator when third-party libraries are unavailable."""
        safe_title = (command.document_title or "DOCUMENTO LOGISTICO").replace("(", "").replace(")", "")
        safe_status = (command.document_status or "PREVIEW").replace("(", "").replace(")", "")
        safe_wm = (command.watermark_text or "VISTA PREVIA").replace("(", "").replace(")", "")
        safe_org = (command.organization_name or "ANDESLOG").replace("(", "").replace(")", "")
        safe_code = (command.document_code or "PREVIEW-001").replace("(", "").replace(")", "")

        content_stream = (
            f"BT\n"
            f"/F1 14 Tf\n"
            f"50 780 Td\n"
            f"({safe_org}) Tj\n"
            f"/F1 12 Tf\n"
            f"0 -25 Td\n"
            f"({safe_title} - {safe_code}) Tj\n"
            f"/F1 10 Tf\n"
            f"0 -20 Td\n"
            f"(Estado: {safe_status} | Modo: {safe_wm}) Tj\n"
            f"ET\n"
        )
        stream_bytes = content_stream.encode("latin1")
        stream_len = len(stream_bytes)

        obj4 = f"4 0 obj <</Length {stream_len}>> stream\n{content_stream}endstream\nendobj\n"

        pdf_parts = [
            "%PDF-1.4\n",
            "1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n",
            "2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n",
            "3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>>>> endobj\n",
            obj4,
            "5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n",
        ]

        body = "".join(pdf_parts)
        header_len = len("%PDF-1.4\n")
        pos = header_len
        xref_entries = ["0000000000 65535 f \n"]
        for part in pdf_parts[1:]:
            xref_entries.append(f"{pos:010d} 00000 n \n")
            pos += len(part)

        xref_pos = pos
        xref_table = f"xref\n0 {len(xref_entries)}\n" + "".join(xref_entries)
        trailer = f"trailer <</Size {len(xref_entries)} /Root 1 0 R>>\nstartxref\n{xref_pos}\n%%EOF\n"

        full_pdf = body + xref_table + trailer
        return full_pdf.encode("latin1")
