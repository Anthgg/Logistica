"""Deterministic filenames for rendered logistics documents."""

from __future__ import annotations

from datetime import UTC, date, datetime


def preview_pdf_filename(document_type_code: str, *, today: date | None = None) -> str:
    """Filename for a preview-mode render, e.g. ``PREVIEW-CIT-20260813.pdf``.

    Keeps the ``PREVIEW`` marker so an unissued render is never mistaken for the
    authoritative document, while still being human-readable and dated.
    """
    stamp = (today or datetime.now(tz=UTC).date()).strftime("%Y%m%d")
    return f"PREVIEW-{(document_type_code or 'DOCUMENTO').upper()}-{stamp}.pdf"
