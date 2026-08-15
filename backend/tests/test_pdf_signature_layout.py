"""Geometric regression tests for the institutional PDF signature zone."""

from __future__ import annotations

import io
import re
from pathlib import Path

import pdfplumber
import pytest

from app.modules.logistics.documents.rendering.rendering import (
    HAS_REPORTLAB,
    DocumentRenderCommand,
    DocumentRendererEngine,
)

pytestmark = pytest.mark.skipif(not HAS_REPORTLAB, reason="ReportLab is required")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
BASE_TEMPLATE = (
    BACKEND_ROOT / "app/modules/logistics/documents/rendering/templates/base/base_v1.html"
)
PRINT_CSS = BACKEND_ROOT / "app/modules/logistics/documents/rendering/templates/shared/print.css"


def _items(count: int) -> list[dict[str, str]]:
    return [
        {
            "code": f"DIF-{index:03d}",
            "description": f"Producto con discrepancia controlada {index:03d}",
            "unit": "UND",
            "expected_quantity": f"{index + 10}.00",
            "received_quantity": f"{index + 9}.00",
            "status": "FALTANTE",
        }
        for index in range(1, count + 1)
    ]


def _render_dif(item_count: int) -> bytes:
    result = DocumentRendererEngine().render_pdf(
        DocumentRenderCommand(
            document_type_code="DIF",
            document_title="ACTA DE DISCREPANCIAS",
            document_code="PREV-DIF-2026-00000",
            organization_name="ANDESLOG OPERACIONES S.A.C.",
            branch_name="SEDE LIMA",
            document_data={
                "items": _items(item_count),
                "observations": (
                    "Diferencias verificadas durante la recepción; se deja "
                    "constancia para control y regularización institucional."
                ),
            },
            signature_data={
                "signer_name": "CARLOS ALBERTO MENDOZA",
                "signer_role": "Representante Legal / Apoderado",
                "signer_dni": "****5678",
            },
            watermark_text="VISTA PREVIA INSTITUCIONAL — SIN VALOR LEGAL",
            preview_mode=True,
        )
    )
    assert result.renderer_name == "ReportLab"
    assert result.pdf_bytes.startswith(b"%PDF-")
    return result.pdf_bytes


def _matching_words(page: pdfplumber.page.Page, text: str) -> list[dict]:
    return [word for word in page.extract_words() if word["text"] == text]


def _css_block(css: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{(?P<body>[^}}]*)\}}", css)
    assert match, f"Expected CSS selector {selector!r}"
    return match.group("body")


def _top(page: pdfplumber.page.Page, text: str, *, last: bool = False) -> float:
    matches = _matching_words(page, text)
    assert matches, f"Expected word {text!r} on PDF page"
    positions = [float(word["top"]) for word in matches]
    return max(positions) if last else min(positions)


def _bottom(page: pdfplumber.page.Page, text: str, *, last: bool = False) -> float:
    matches = _matching_words(page, text)
    assert matches, f"Expected word {text!r} on PDF page"
    positions = [float(word["bottom"]) for word in matches]
    return max(positions) if last else min(positions)


def _assert_signature_geometry(pdf_bytes: bytes, *, minimum_pages: int) -> dict[str, float]:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as document:
        pages = document.pages
        assert len(pages) >= minimum_pages

        signature_pages = [
            index for index, page in enumerate(pages, start=1) if _matching_words(page, "FIRMANTE")
        ]
        conformity_pages = [
            index
            for index, page in enumerate(pages, start=1)
            if _matching_words(page, "CONFORMIDAD")
        ]
        assert signature_pages == [len(pages)]
        assert conformity_pages == [len(pages)]

        for index, page in enumerate(pages, start=1):
            text = page.extract_text() or ""
            assert f"Página {index} de {len(pages)}" in text

        last_page = pages[-1]
        observations_top = _top(last_page, "OBSERVACIONES")
        signature_top = _top(last_page, "FIRMANTE", last=True)
        signature_bottom = _bottom(last_page, "FIRMANTE", last=True)
        conformity_top = _top(last_page, "CONFORMIDAD", last=True)
        footer_top = _top(last_page, "Página", last=True)

        assert observations_top < signature_top < footer_top
        assert abs(signature_top - conformity_top) <= 1.5
        assert signature_top >= float(last_page.height) * 0.68
        assert 25 <= footer_top - signature_bottom <= 80
        assert "________________________________" not in (last_page.extract_text() or "")

        return {
            "pages": float(len(pages)),
            "observations_top": observations_top,
            "signature_top": signature_top,
            "footer_top": footer_top,
        }


def test_shared_template_uses_flow_layout_and_css_signature_lines() -> None:
    template = BASE_TEMPLATE.read_text(encoding="utf-8")
    css = PRINT_CSS.read_text(encoding="utf-8")

    assert 'class="document-layout"' in template
    assert 'class="document-content"' in template
    assert 'class="document-signature-zone"' in template
    assert template.count('class="sig-signing-space"') == 2
    assert template.count('class="sig-line"') == 2
    assert "________________________________" not in template

    signature_zone = _css_block(css, ".document-signature-zone")
    signatures_wrapper = _css_block(css, ".signatures-wrapper")
    assert "margin-top: auto" in signature_zone
    assert "break-inside: avoid" in signature_zone
    assert "position: fixed" not in signature_zone
    assert "page-break-inside: avoid" in signatures_wrapper
    assert "position: fixed" not in signatures_wrapper


def test_short_dif_places_signatures_in_lower_area_above_footer() -> None:
    metrics = _assert_signature_geometry(_render_dif(2), minimum_pages=1)

    assert metrics["pages"] == 1
    assert metrics["signature_top"] - metrics["observations_top"] >= 250


def test_medium_dif_keeps_signature_block_once_on_final_page() -> None:
    _assert_signature_geometry(_render_dif(12), minimum_pages=1)


def test_signature_block_moves_intact_when_remaining_space_is_insufficient() -> None:
    with pdfplumber.open(io.BytesIO(_render_dif(25))) as document:
        assert len(document.pages) == 2
        first_page, final_page = document.pages

        assert _matching_words(first_page, "OBSERVACIONES")
        assert not _matching_words(first_page, "FIRMANTE")
        assert not _matching_words(first_page, "CONFORMIDAD")

        assert not _matching_words(final_page, "OBSERVACIONES")
        assert len(_matching_words(final_page, "FIRMANTE")) == 1
        assert len(_matching_words(final_page, "CONFORMIDAD")) == 1
        assert "CARLOS ALBERTO MENDOZA" in (final_page.extract_text() or "")
        assert "RESPONSABLE OPERATIVO / RECEPCIÓN" in (final_page.extract_text() or "")

        signature_top = _top(final_page, "FIRMANTE")
        conformity_top = _top(final_page, "CONFORMIDAD")
        footer_top = _top(final_page, "Página", last=True)
        assert abs(signature_top - conformity_top) <= 1.5
        assert signature_top < footer_top
        assert "Página 1 de 2" in (first_page.extract_text() or "")
        assert "Página 2 de 2" in (final_page.extract_text() or "")


def test_long_dif_keeps_signature_block_intact_on_final_page() -> None:
    _assert_signature_geometry(_render_dif(55), minimum_pages=2)
