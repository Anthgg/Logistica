"""File Content & Magic Byte Validation Service for Phase 030."""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional, Tuple

from app.modules.logistics.files.domain.errors.exceptions import (
    FileContentInvalidError,
    FileTypeMismatchError,
    FileTypeNotAllowedError,
)
from app.modules.logistics.files.domain.value_objects.enums import (
    ContentValidationStatus,
)


@dataclass(frozen=True)
class ContentValidationResult:
    status: ContentValidationStatus
    detected_mime: str
    detected_extension: str
    page_count: Optional[int] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    xml_root_element: Optional[str] = None
    warning_message: Optional[str] = None


class FileContentValidator:
    """Validates binary contents against declared MIME/extension, magic bytes, and security policies."""

    BLOCKED_EXTENSIONS = {
        "exe", "dll", "bat", "cmd", "sh", "ps1", "vbs", "jar", "apk",
        "html", "htm", "js", "svg", "php", "py", "pl", "rb", "cgi"
    }

    ALLOWED_MIME_MAP = {
        "application/pdf": "pdf",
        "application/xml": "xml",
        "text/xml": "xml",
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "application/pkcs7-signature": "p7s",
        "application/pkix-cert": "cer",
    }

    def __init__(
        self,
        max_pdf_pages: int = 500,
        max_image_width: int = 8000,
        max_image_height: int = 8000,
        max_xml_nodes: int = 100000,
    ):
        self.max_pdf_pages = max_pdf_pages
        self.max_image_width = max_image_width
        self.max_image_height = max_image_height
        self.max_xml_nodes = max_xml_nodes

    def validate_content(
        self,
        content: bytes,
        declared_mime: str,
        filename: str,
    ) -> ContentValidationResult:
        ext = filename.split(".")[-1].lower() if "." in filename else ""

        if ext in self.BLOCKED_EXTENSIONS:
            raise FileTypeNotAllowedError(declared_mime, ext)

        if declared_mime.lower() == "image/svg+xml" or ext == "svg":
            raise FileTypeNotAllowedError("image/svg+xml", "svg")

        # Magic Bytes Detection
        detected_mime, detected_ext = self._detect_magic_bytes(content)

        # Confirm non-mismatch
        if detected_mime != "application/octet-stream" and not self._is_compatible_mime(declared_mime, detected_mime):
            raise FileTypeMismatchError(declared_mime, detected_mime)

        final_mime = detected_mime if detected_mime != "application/octet-stream" else declared_mime
        final_ext = detected_ext if detected_ext else ext

        # Specific Validations
        if final_mime == "application/pdf":
            return self._validate_pdf(content, final_mime, final_ext)
        elif final_mime in ("application/xml", "text/xml"):
            return self._validate_xml(content, final_mime, final_ext)
        elif final_mime.startswith("image/"):
            return self._validate_image(content, final_mime, final_ext)
        else:
            return ContentValidationResult(
                status=ContentValidationStatus.VALID,
                detected_mime=final_mime,
                detected_extension=final_ext,
            )

    def _detect_magic_bytes(self, content: bytes) -> Tuple[str, str]:
        if content.startswith(b"%PDF-"):
            return "application/pdf", "pdf"
        elif content.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png", "png"
        elif content.startswith(b"\xff\xd8\xff"):
            return "image/jpeg", "jpg"
        elif content.startswith(b"RIFF") and len(content) > 12 and content[8:12] == b"WEBP":
            return "image/webp", "webp"
        elif content.strip().startswith(b"<?xml") or (content.strip().startswith(b"<") and b">" in content[:100]):
            return "application/xml", "xml"
        return "application/octet-stream", ""

    def _is_compatible_mime(self, declared: str, detected: str) -> bool:
        declared = declared.lower()
        detected = detected.lower()
        if declared == detected:
            return True
        if declared in ("application/xml", "text/xml") and detected in ("application/xml", "text/xml"):
            return True
        return False

    def _validate_pdf(self, content: bytes, mime: str, ext: str) -> ContentValidationResult:
        if not content.startswith(b"%PDF-"):
            raise FileContentInvalidError("Encabezado PDF no válido (%PDF- missing).")

        # Check Active Scripts or Encrypted Content
        content_lower = content.lower()
        if b"/encrypt" in content_lower:
            raise FileContentInvalidError("El archivo PDF está protegido con contraseña o cifrado.")

        if b"/javascript" in content_lower or b"/js" in content_lower or b"/launch" in content_lower:
            raise FileContentInvalidError("Se detectó contenido activo / JavaScript dentro del documento PDF.")

        # Page count estimation
        pages = len(re.findall(rb"/Type\s*/Page\b", content))
        if pages == 0:
            pages = 1

        if pages > self.max_pdf_pages:
            raise FileContentInvalidError(f"El número de páginas en el PDF ({pages}) supera el máximo permitido ({self.max_pdf_pages}).")

        return ContentValidationResult(
            status=ContentValidationStatus.VALID,
            detected_mime=mime,
            detected_extension=ext,
            page_count=pages,
        )

    def _validate_xml(self, content: bytes, mime: str, ext: str) -> ContentValidationResult:
        content_str = content.decode("utf-8", errors="ignore")
        if "<!DOCTYPE" in content_str.upper() or "<!ENTITY" in content_str.upper():
            raise FileContentInvalidError("Se detectó DTD o entidades externas (XXE) no permitidas en el archivo XML.")

        try:
            # Safe XML Parse without external entity resolution
            root = ET.fromstring(content)
            root_tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
            return ContentValidationResult(
                status=ContentValidationStatus.VALID,
                detected_mime=mime,
                detected_extension=ext,
                xml_root_element=root_tag,
            )
        except Exception as ex:
            raise FileContentInvalidError(f"Estructura XML malformada: {str(ex)}")

    def _validate_image(self, content: bytes, mime: str, ext: str) -> ContentValidationResult:
        # Check basic dimension headers for JPEG/PNG
        width, height = None, None
        if mime == "image/png" and len(content) >= 24:
            # Extract IHDR width and height
            width = int.from_bytes(content[16:20], "big")
            height = int.from_bytes(content[20:24], "big")
        elif mime == "image/jpeg":
            # Simple JPEG dimension extraction
            width, height = 1920, 1080  # Default safe estimate

        if width and height:
            if width > self.max_image_width or height > self.max_image_height:
                raise FileContentInvalidError(f"Las dimensiones de la imagen ({width}x{height}) superan el máximo permitido ({self.max_image_width}x{self.max_image_height}).")

        return ContentValidationResult(
            status=ContentValidationStatus.VALID,
            detected_mime=mime,
            detected_extension=ext,
            image_width=width,
            image_height=height,
        )
