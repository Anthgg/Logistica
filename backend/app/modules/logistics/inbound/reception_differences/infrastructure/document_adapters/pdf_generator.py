"""PDF generation for Reception Difference Act (DIF) using reportlab."""

from __future__ import annotations

import io
from datetime import datetime
from decimal import Decimal
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="DIFTitle", fontSize=16, leading=20, spaceAfter=6, alignment=1, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="DIFSubtitle", fontSize=11, leading=14, spaceAfter=4, alignment=1, fontName="Helvetica"))
    styles.add(ParagraphStyle(name="DIFSection", fontSize=12, leading=15, spaceBefore=12, spaceAfter=4, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="DIFField", fontSize=9, leading=12, fontName="Helvetica"))
    styles.add(ParagraphStyle(name="DIFValue", fontSize=9, leading=12, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="DIFSmall", fontSize=8, leading=10, fontName="Helvetica"))
    styles.add(ParagraphStyle(name="DIFWatermark", fontSize=40, leading=50, alignment=1, fontName="Helvetica-Bold", textColor=colors.Color(0.85, 0.85, 0.85)))
    styles.add(ParagraphStyle(name="DIFHeader", fontSize=8, leading=10, fontName="Helvetica"))
    styles.add(ParagraphStyle(name="DIFFooter", fontSize=7, leading=9, fontName="Helvetica", textColor=colors.grey))
    return styles


def _header_footer(canvas, doc, styles, snapshot, is_preview):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2 * cm, A4[1] - 1.5 * cm, f"Acta de Diferencias - {snapshot.get('case_code', 'SIN CODIGO')}")
    canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.5 * cm, f"Estado: {snapshot.get('status', 'N/A')}")
    canvas.setFont("Helvetica", 7)
    canvas.drawString(2 * cm, 1.2 * cm, f"Generado: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Hash: {snapshot.get('content_hash', 'N/A')[:16]}...")
    if is_preview:
        canvas.setFont("Helvetica-Bold", 40)
        canvas.setFillColor(colors.Color(0.85, 0.85, 0.85))
        canvas.saveState()
        canvas.translate(A4[0] / 2, A4[1] / 2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "NO OFICIAL")
        canvas.restoreState()
    canvas.restoreState()


def generate_dif_pdf(snapshot: dict, *, is_preview: bool = False) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2.5 * cm, bottomMargin=2 * cm)
    styles = _build_styles()
    elements: list[Any] = []

    org = snapshot.get("organization", {})
    elements.append(Paragraph(org.get("name", "Organizacion"), styles["DIFTitle"]))
    elements.append(Paragraph(f"RUC: {org.get('ruc', 'N/A')}", styles["DIFSubtitle"]))
    elements.append(Paragraph("ACTA DE DIFERENCIAS DE RECEPCION", styles["DIFTitle"]))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    elements.append(Spacer(1, 0.3 * cm))

    info_data = [
        ["Codigo DIF:", snapshot.get("case_code", "PENDIENTE"), "Estado:", snapshot.get("status", "N/A")],
        ["Fecha:", snapshot.get("created_at", "N/A"), "Severidad:", snapshot.get("severity", "N/A")],
        ["Sede:", snapshot.get("branch_name", "N/A"), "Almacen:", snapshot.get("warehouse_name", "N/A")],
        ["Recepcion:", snapshot.get("receipt_code", "N/A"), "Revision:", str(snapshot.get("receipt_revision_number", "N/A"))],
        ["Proveedor:", snapshot.get("supplier_name", "N/A"), "Transportista:", snapshot.get("carrier_name", "N/A")],
        ["CPV:", snapshot.get("cpv_code", "N/A"), "CIT:", snapshot.get("cit_code", "N/A")],
        ["OC:", snapshot.get("purchase_order_code", "N/A"), "", ""],
    ]
    info_table = Table(info_data, colWidths=[3 * cm, 5.5 * cm, 3 * cm, 5.5 * cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.5 * cm))

    items = snapshot.get("items", [])
    if items:
        elements.append(Paragraph("DETALLE DE DIFERENCIAS", styles["DIFSection"]))
        header = ["#", "Tipo", "Severidad", "Producto", "Cant. Esperada", "Cant. Observada", "Diferencia", "Unidad", "Descripcion"]
        table_data = [header]
        for idx, item in enumerate(items, 1):
            table_data.append([
                str(idx),
                item.get("difference_type", "N/A"),
                item.get("severity", "N/A"),
                item.get("product_name", "N/A")[:30],
                str(item.get("expected_quantity", "N/A")),
                str(item.get("observed_quantity", "N/A")),
                str(item.get("difference_quantity", "N/A")),
                item.get("unit_code", "N/A"),
                (item.get("description", "") or "")[:40],
            ])
        items_table = Table(table_data, colWidths=[1 * cm, 2.5 * cm, 1.8 * cm, 3 * cm, 2 * cm, 2 * cm, 2 * cm, 1.5 * cm, 3 * cm])
        items_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.5 * cm))

    evidence = snapshot.get("evidence", [])
    if evidence:
        elements.append(Paragraph("EVIDENCIAS", styles["DIFSection"]))
        for ev in evidence:
            elements.append(Paragraph(
                f"- {ev.get('evidence_type', 'N/A')}: {ev.get('description', 'Sin descripcion')} ({ev.get('file_name', 'N/A')})",
                styles["DIFSmall"],
            ))
        elements.append(Spacer(1, 0.3 * cm))

    responsible = snapshot.get("responsible_parties", [])
    if responsible:
        elements.append(Paragraph("RESPONSABLES PROPUESTOS", styles["DIFSection"]))
        for rp in responsible:
            elements.append(Paragraph(
                f"- {rp.get('party_type', 'N/A')}: {rp.get('party_name', 'N/A')} ({rp.get('responsibility_status', 'N/A')})",
                styles["DIFSmall"],
            ))
        elements.append(Spacer(1, 0.3 * cm))

    reviews = snapshot.get("reviews", [])
    if reviews:
        elements.append(Paragraph("REVISIONES", styles["DIFSection"]))
        for rv in reviews:
            elements.append(Paragraph(
                f"- {rv.get('review_type', 'N/A')}: {rv.get('status', 'N/A')} por {rv.get('reviewer_name', 'N/A')}",
                styles["DIFSmall"],
            ))
        elements.append(Spacer(1, 0.3 * cm))

    approvals = snapshot.get("approvals", [])
    if approvals:
        elements.append(Paragraph("APROBACIONES", styles["DIFSection"]))
        for ap in approvals:
            elements.append(Paragraph(
                f"- Nivel {ap.get('approval_level', 'N/A')}: {ap.get('decision', 'N/A')} por {ap.get('approver_name', 'N/A')}",
                styles["DIFSmall"],
            ))
        elements.append(Spacer(1, 0.3 * cm))

    acknowledgements = snapshot.get("acknowledgements", [])
    if acknowledgements:
        elements.append(Paragraph("RECONOCIMIENTOS", styles["DIFSection"]))
        for ack in acknowledgements:
            elements.append(Paragraph(
                f"- {ack.get('party_type', 'N/A')}: {ack.get('acknowledgement_type', 'N/A')} ({ack.get('status', 'N/A')})",
                styles["DIFSmall"],
            ))
        elements.append(Spacer(1, 0.3 * cm))

    recommendations = snapshot.get("follow_up_recommendations", [])
    if recommendations:
        elements.append(Paragraph("RECOMENDACIONES FUTURAS", styles["DIFSection"]))
        for rec in recommendations:
            elements.append(Paragraph(
                f"- {rec.get('recommendation_type', 'N/A')}: {rec.get('reason', 'N/A')} (Prioridad: {rec.get('priority', 'N/A')})",
                styles["DIFSmall"],
            ))
        elements.append(Spacer(1, 0.3 * cm))

    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("PIE DE AUDITORIA", styles["DIFSection"]))
    elements.append(Paragraph(f"Creado por: {snapshot.get('created_by_name', 'N/A')}", styles["DIFSmall"]))
    elements.append(Paragraph(f"Revisado por: {snapshot.get('reviewed_by_name', 'N/A')}", styles["DIFSmall"]))
    elements.append(Paragraph(f"Aprobado por: {snapshot.get('approved_by_name', 'N/A')}", styles["DIFSmall"]))
    elements.append(Paragraph(f"Emitido: {snapshot.get('issued_at', 'N/A')}", styles["DIFSmall"]))
    elements.append(Paragraph(f"Hash de integridad: {snapshot.get('content_hash', 'N/A')}", styles["DIFSmall"]))
    if is_preview:
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph("*** VISTA PREVIA - NO OFICIAL ***", styles["DIFSubtitle"]))

    doc.build(elements, onFirstPage=lambda c, d: _header_footer(c, d, styles, snapshot, is_preview), onLaterPages=lambda c, d: _header_footer(c, d, styles, snapshot, is_preview))
    return buffer.getvalue()
