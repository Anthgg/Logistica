"""Unit tests for the shared PDF download/preview response helper."""

import pytest
from fastapi import HTTPException

from app.core.pdf_response import (
    PDF_MEDIA_TYPE,
    assert_pdf_bytes,
    build_content_disposition,
    build_pdf_download_response,
    build_pdf_preview_response,
    sanitize_pdf_filename,
)

MINIMAL_PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


class TestSanitizeFilename:
    def test_keeps_a_normal_name(self):
        assert sanitize_pdf_filename("guia-remision-T001-00001234.pdf") == (
            "guia-remision-T001-00001234.pdf"
        )

    def test_appends_pdf_extension(self):
        assert sanitize_pdf_filename("orden-compra-OC-000234") == "orden-compra-OC-000234.pdf"

    def test_empty_falls_back(self):
        assert sanitize_pdf_filename("") == "documento.pdf"
        assert sanitize_pdf_filename(None) == "documento.pdf"

    @pytest.mark.parametrize("raw", ["a\r\nb.pdf", "a\rb.pdf", "a\nb.pdf", "a\tb.pdf"])
    def test_strips_crlf_and_control_chars(self, raw):
        cleaned = sanitize_pdf_filename(raw)
        assert "\r" not in cleaned
        assert "\n" not in cleaned
        assert "\t" not in cleaned

    def test_strips_null_byte(self):
        assert "\x00" not in sanitize_pdf_filename("gu\x00ia.pdf")

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("../../etc/passwd.pdf", "passwd.pdf"),
            ("..\\..\\windows\\system32\\evil.pdf", "evil.pdf"),
            ("/absolute/path/doc.pdf", "doc.pdf"),
            ("....//....//doc.pdf", "doc.pdf"),
        ],
    )
    def test_path_traversal_reduced_to_a_name(self, raw, expected):
        cleaned = sanitize_pdf_filename(raw)
        assert cleaned == expected
        assert "/" not in cleaned
        assert "\\" not in cleaned
        assert ".." not in cleaned

    def test_strips_quotes(self):
        assert '"' not in sanitize_pdf_filename('foo".pdf')

    def test_long_name_is_truncated_but_keeps_extension(self):
        cleaned = sanitize_pdf_filename("x" * 500 + ".pdf")
        assert len(cleaned) <= 120
        assert cleaned.endswith(".pdf")

    def test_unicode_is_preserved(self):
        assert sanitize_pdf_filename("guía-remisión.pdf") == "guía-remisión.pdf"


class TestContentDisposition:
    def test_ascii_name_has_no_utf8_parameter(self):
        header = build_content_disposition("reporte.pdf", disposition="attachment")
        assert header == 'attachment; filename="reporte.pdf"'
        assert "filename*" not in header

    def test_unicode_name_gets_ascii_fallback_and_utf8(self):
        header = build_content_disposition("guía-remisión.pdf", disposition="attachment")
        assert header.startswith("attachment; ")
        assert 'filename="guia-remision.pdf"' in header
        assert "filename*=UTF-8''" in header
        assert "gu%C3%ADa" in header

    def test_name_with_spaces_is_quoted_and_readable(self):
        header = build_content_disposition("orden de compra.pdf")
        # A quoted string keeps the space legible instead of truncating the name.
        assert 'filename="orden-de-compra.pdf"' in header

    def test_inline_disposition_supported(self):
        assert build_content_disposition("a.pdf", disposition="inline").startswith("inline;")

    def test_rejects_unknown_disposition(self):
        with pytest.raises(ValueError):
            build_content_disposition("a.pdf", disposition="form-data")

    def test_header_injection_cannot_create_a_second_header(self):
        header = build_content_disposition('foo.pdf"\r\nX-Evil: yes')
        assert "\r" not in header
        assert "\n" not in header
        # No header separator and no extra parameter separator survive, so the
        # payload can only ever be inert filename text.
        assert ":" not in header
        assert header.startswith("attachment;")
        assert header.count(";") == 1


class TestPdfValidation:
    def test_accepts_real_pdf(self):
        assert assert_pdf_bytes(MINIMAL_PDF) == MINIMAL_PDF

    @pytest.mark.parametrize(
        "payload",
        [b"", b"<html><body>error</body></html>", b'{"detail":"boom"}', b"not a pdf", None, "str"],
    )
    def test_rejects_non_pdf_payloads(self, payload):
        with pytest.raises(HTTPException) as exc:
            assert_pdf_bytes(payload)
        assert exc.value.status_code == 500


class TestResponses:
    def test_download_response_contract(self):
        response = build_pdf_download_response(MINIMAL_PDF, "guía-remisión.pdf")
        assert response.status_code == 200
        assert response.media_type == PDF_MEDIA_TYPE
        assert response.headers["content-type"].startswith("application/pdf")
        assert response.headers["content-disposition"].startswith("attachment;")
        assert "filename*=UTF-8''" in response.headers["content-disposition"]
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["cache-control"] == "private, no-store"
        assert response.headers["content-length"] == str(len(MINIMAL_PDF))
        assert response.body == MINIMAL_PDF
        assert response.body.startswith(b"%PDF-")

    def test_preview_response_is_inline_but_otherwise_identical(self):
        preview = build_pdf_preview_response(MINIMAL_PDF, "doc.pdf")
        download = build_pdf_download_response(MINIMAL_PDF, "doc.pdf")
        assert preview.headers["content-disposition"].startswith("inline;")
        assert download.headers["content-disposition"].startswith("attachment;")
        # Only delivery differs: identical bytes, identical media type.
        assert preview.body == download.body
        assert preview.media_type == download.media_type

    def test_extra_headers_cannot_override_security_headers(self):
        response = build_pdf_download_response(
            MINIMAL_PDF,
            "doc.pdf",
            extra_headers={
                "Content-Disposition": "inline; filename=hack.pdf",
                "X-Content-Type-Options": "",
                "X-Document-Mode": "FINAL",
            },
        )
        assert response.headers["content-disposition"].startswith("attachment;")
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-document-mode"] == "FINAL"

    def test_extra_header_values_are_stripped_of_crlf(self):
        response = build_pdf_download_response(
            MINIMAL_PDF, "doc.pdf", extra_headers={"X-Document-Type": "CIT\r\nX-Evil: yes"}
        )
        assert "\r" not in response.headers["x-document-type"]
        assert "\n" not in response.headers["x-document-type"]
        assert "x-evil" not in response.headers

    def test_invalid_pdf_never_returns_200(self):
        with pytest.raises(HTTPException) as exc:
            build_pdf_download_response(b"<html>error</html>", "doc.pdf")
        assert exc.value.status_code == 500
