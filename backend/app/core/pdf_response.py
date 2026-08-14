"""Helpers for delivering PDF documents over HTTP.

Centralises the rules every PDF response in the backend must follow so that a
document can always be retrieved, regardless of whether the browser is able to
render PDFs inline:

* ``application/pdf`` media type;
* an RFC 6266 ``Content-Disposition`` with an ASCII ``filename`` fallback and a
  percent-encoded ``filename*`` for names carrying non-ASCII characters;
* filenames sanitised against header injection and path traversal;
* ``X-Content-Type-Options: nosniff`` so the payload is never re-interpreted;
* a guard that refuses to emit ``200`` for something that is not a real PDF.

``preview`` (``inline``) and ``download`` (``attachment``) share the same
builder: only the disposition differs, never the bytes.
"""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import quote

from fastapi import HTTPException, Response, status

PDF_MEDIA_TYPE = "application/pdf"
PDF_MAGIC = b"%PDF-"
DEFAULT_PDF_FILENAME = "documento.pdf"
DEFAULT_CACHE_CONTROL = "private, no-store"

# Declared on every PDF route so OpenAPI advertises the real payload instead of
# defaulting to application/json.
PDF_RESPONSE_SCHEMA: dict = {
    200: {"content": {PDF_MEDIA_TYPE: {}}, "description": "Documento PDF"}
}

# Longest filename we are willing to put in a header; keeps the encoded
# ``filename*`` well inside the limits proxies impose on a single header line.
_MAX_FILENAME_LENGTH = 120

# Anything that could terminate the header, start a new one, separate a
# parameter, or turn the value into a path rather than a name. ``;`` and ``:``
# are dropped as defence in depth: both are invalid in Windows filenames and
# neither should ever appear inside a header parameter value.
_FORBIDDEN_CHARS = re.compile(r'[\r\n\t"\\/;:]+')
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_COLLAPSE_SEPARATORS = re.compile(r"[\s_]+")
_REPEATED_DOTS = re.compile(r"\.{2,}")


def sanitize_pdf_filename(raw: str | None, *, fallback: str = DEFAULT_PDF_FILENAME) -> str:
    """Return a safe, single-segment ``*.pdf`` filename.

    Strips CR/LF and control characters (header injection), path separators and
    ``..`` sequences (path traversal), and guarantees a non-empty name ending in
    ``.pdf``. Never raises: an unusable input degrades to ``fallback``.
    """
    candidate = (raw or "").strip()

    # Keep only the last path segment before removing separators, so that
    # "../../etc/passwd.pdf" degrades to "passwd.pdf" rather than "etcpasswd.pdf".
    candidate = candidate.replace("\\", "/").split("/")[-1]

    candidate = _CONTROL_CHARS.sub("", candidate)
    candidate = _FORBIDDEN_CHARS.sub("", candidate)
    candidate = _REPEATED_DOTS.sub(".", candidate)
    candidate = _COLLAPSE_SEPARATORS.sub("-", candidate)
    candidate = candidate.strip(" .-")

    if not candidate:
        candidate = fallback

    if not candidate.lower().endswith(".pdf"):
        candidate = f"{candidate}.pdf"

    if len(candidate) > _MAX_FILENAME_LENGTH:
        candidate = candidate[: _MAX_FILENAME_LENGTH - len(".pdf")].strip(" .-") + ".pdf"

    return candidate or fallback


def _ascii_fallback(filename: str, *, fallback: str = DEFAULT_PDF_FILENAME) -> str:
    """Best-effort ASCII rendering of ``filename`` for legacy ``filename=``."""
    decomposed = unicodedata.normalize("NFKD", filename)
    stripped = decomposed.encode("ascii", "ignore").decode("ascii")
    stripped = _FORBIDDEN_CHARS.sub("", stripped).strip(" .-")

    if not stripped or stripped.lower() == ".pdf":
        return fallback
    if not stripped.lower().endswith(".pdf"):
        stripped = f"{stripped}.pdf"
    return stripped


def build_content_disposition(filename: str, *, disposition: str = "attachment") -> str:
    """Build an RFC 6266 ``Content-Disposition`` value.

    Always emits a quoted ASCII ``filename``; adds ``filename*=UTF-8''`` only
    when the sanitised name actually needs it, keeping the header minimal for
    plain ASCII documents.
    """
    if disposition not in ("attachment", "inline"):
        raise ValueError(f"Unsupported content disposition: {disposition!r}")

    safe = sanitize_pdf_filename(filename)
    ascii_name = _ascii_fallback(safe)

    header = f'{disposition}; filename="{ascii_name}"'
    if safe != ascii_name:
        header += f"; filename*=UTF-8''{quote(safe, safe='')}"
    return header


def assert_pdf_bytes(pdf_bytes: bytes | None) -> bytes:
    """Validate that ``pdf_bytes`` really is a non-empty PDF payload.

    Prevents the two failure modes that are worse than an error: an empty body
    served as ``200``, and an HTML/JSON error page labelled ``application/pdf``.
    """
    if not isinstance(pdf_bytes, (bytes, bytearray, memoryview)):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El documento generado no es un archivo PDF válido.",
        )

    payload = bytes(pdf_bytes)
    if not payload or not payload.startswith(PDF_MAGIC):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El documento generado no es un archivo PDF válido.",
        )
    return payload


def build_pdf_response(
    pdf_bytes: bytes,
    filename: str,
    *,
    disposition: str = "attachment",
    extra_headers: dict[str, str] | None = None,
    cache_control: str | None = DEFAULT_CACHE_CONTROL,
) -> Response:
    """Return a validated ``application/pdf`` response.

    ``Content-Length`` is left to Starlette, which derives it from the body.
    """
    payload = assert_pdf_bytes(pdf_bytes)

    headers = {
        "Content-Disposition": build_content_disposition(filename, disposition=disposition),
        "X-Content-Type-Options": "nosniff",
    }
    if cache_control:
        headers["Cache-Control"] = cache_control
    if extra_headers:
        # Caller-supplied metadata (X-Document-Mode, hashes, ...) must never be
        # able to override the security-relevant headers set above.
        for key, value in extra_headers.items():
            if key.lower() in ("content-disposition", "x-content-type-options", "content-type"):
                continue
            headers[key] = _sanitize_header_value(value)

    return Response(content=payload, media_type=PDF_MEDIA_TYPE, headers=headers)


def build_pdf_download_response(
    pdf_bytes: bytes,
    filename: str,
    *,
    extra_headers: dict[str, str] | None = None,
    cache_control: str | None = DEFAULT_CACHE_CONTROL,
) -> Response:
    """Browser-independent download: ``Content-Disposition: attachment``."""
    return build_pdf_response(
        pdf_bytes,
        filename,
        disposition="attachment",
        extra_headers=extra_headers,
        cache_control=cache_control,
    )


def build_pdf_preview_response(
    pdf_bytes: bytes,
    filename: str,
    *,
    extra_headers: dict[str, str] | None = None,
    cache_control: str | None = DEFAULT_CACHE_CONTROL,
) -> Response:
    """In-browser preview: ``Content-Disposition: inline``.

    A preview is always optional; every previewable document must also be
    reachable through an ``attachment`` download.
    """
    return build_pdf_response(
        pdf_bytes,
        filename,
        disposition="inline",
        extra_headers=extra_headers,
        cache_control=cache_control,
    )


def _sanitize_header_value(value: str) -> str:
    """Strip CR/LF from an arbitrary header value to prevent response splitting."""
    return _CONTROL_CHARS.sub("", str(value)).strip()
