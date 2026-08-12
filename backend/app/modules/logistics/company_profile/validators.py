"""Validation utilities for Company Profile (Phase 021).

Includes:
- Peruvian RUC syntax and checksum (modulo 11) validator
- Numbering pattern token parser & validator
- Image security, magic byte validation, dimensions & EXIF metadata sanitizer
"""

import hashlib
import io
import re
from typing import Any

from PIL import Image

ALLOWED_NUMBERING_TOKENS = {
    "{TYPE}",
    "{SITE}",
    "{YEAR}",
    "{SEQUENCE}",
    "{EXTERNAL_SERIES}",
    "{EXTERNAL_NUMBER}",
}

ALLOWED_IMAGE_MIMES = {
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/webp": [b"RIFF"],  # WebP starts with RIFF ... WEBP
}


def validate_peruvian_ruc(ruc: str) -> tuple[bool, str]:
    """Validates Peruvian RUC format and Modulo 11 check digit algorithm.

    Peruvian RUCs must:
    1. Be exactly 11 numeric digits.
    2. Start with valid 2-digit prefixes: 10 (Person), 15, 17, 20 (Company).
    3. Satisfy Modulo 11 check digit on the 11th digit.
    """
    if not ruc or not isinstance(ruc, str):
        return False, "El RUC no puede estar vacío."

    ruc = ruc.strip()
    if not ruc.isdigit() or len(ruc) != 11:
        return False, "El RUC debe tener exactamente 11 dígitos numéricos."

    prefix = ruc[:2]
    if prefix not in {"10", "15", "17", "20"}:
        return False, f"Prefijo de RUC inválido '{prefix}'. Debe iniciar con 10, 15, 17 o 20."

    # Modulo 11 verification algorithm
    multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    sum_product = sum(int(ruc[i]) * multipliers[i] for i in range(10))
    remainder = sum_product % 11
    expected_check_digit = 11 - remainder

    if expected_check_digit == 10:
        expected_check_digit = 0
    elif expected_check_digit == 11:
        expected_check_digit = 1

    actual_check_digit = int(ruc[10])
    if actual_check_digit != expected_check_digit:
        return False, f"El RUC '{ruc}' tiene un dígito de verificación inválido."

    return True, "RUC válido."


def generate_valid_ruc(seed: int | str = 0) -> str:
    """Generates a valid 11-digit Peruvian company RUC (prefix 20) with correct Modulo 11 check digit."""
    if isinstance(seed, str):
        seed_num = int(hashlib.md5(seed.encode()).hexdigest(), 16) % 100000000
    else:
        seed_num = abs(int(seed)) % 100000000
    base_digits = f"20{seed_num:08d}"
    multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    sum_product = sum(int(base_digits[i]) * multipliers[i] for i in range(10))
    remainder = sum_product % 11
    check_digit = 11 - remainder
    if check_digit == 10:
        check_digit = 0
    elif check_digit == 11:
        check_digit = 1
    return f"{base_digits}{check_digit}"


def validate_numbering_display_pattern(pattern: str, sequence_padding: int = 6) -> tuple[bool, str]:
    """Validates a display pattern for document numbering.

    Allowed tokens: {TYPE}, {SITE}, {YEAR}, {SEQUENCE}, {EXTERNAL_SERIES}, {EXTERNAL_NUMBER}
    Mandatory token: {SEQUENCE}
    """
    if not pattern or not isinstance(pattern, str):
        return False, "El patrón de presentación no puede estar vacío."

    if "{SEQUENCE}" not in pattern:
        return False, "El patrón de presentación debe incluir obligatoriamente el token {SEQUENCE}."

    if sequence_padding < 4 or sequence_padding > 10:
        return False, "El padding del correlativo debe estar entre 4 y 10 dígitos."

    # Find all tokens in curly braces
    found_tokens = re.findall(r"\{[^}]*\}", pattern)
    for token in found_tokens:
        if token not in ALLOWED_NUMBERING_TOKENS:
            return False, f"Token no permitido '{token}'. Tokens válidos: {', '.join(sorted(ALLOWED_NUMBERING_TOKENS))}."

    # Prevent malicious characters / expressions
    for char in ["<", ">", ";", "$", "eval", "exec", "import", "script"]:
        if char in pattern.lower():
            return False, "El patrón de presentación contiene caracteres o expresiones no permitidas."

    return True, "Patrón de presentación válido."


def validate_and_sanitize_image(
    image_bytes: bytes,
    filename: str,
    asset_type: str,
    max_mb: float = 5.0,
    max_width: int = 4096,
    max_height: int = 4096,
) -> dict[str, Any]:
    """Validates binary headers, dimensions, size limits, and strips EXIF metadata from image.

    Returns sanitized image bytes, file hash, width, height, mime_type, size_bytes.
    """
    if not image_bytes:
        raise ValueError("El archivo de imagen está vacío.")

    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > max_mb:
        raise ValueError(f"El archivo excede el tamaño máximo permitido de {max_mb} MB (tamaño actual: {size_mb:.2f} MB).")

    # SVG check: Explicitly reject SVG unless allowed
    lower_filename = filename.lower()
    if lower_filename.endswith(".svg") or b"<svg" in image_bytes[:512].lower():
        raise ValueError("El formato SVG no está permitido por razones de seguridad de renderizado.")

    # Check magic bytes
    detected_mime = None
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        detected_mime = "image/png"
    elif image_bytes.startswith(b"\xff\xd8\xff"):
        detected_mime = "image/jpeg"
    elif image_bytes.startswith(b"RIFF") and b"WEBP" in image_bytes[8:16]:
        detected_mime = "image/webp"

    if not detected_mime:
        raise ValueError("Formato de imagen no soportado o firma binaria corrupta. Solo se permiten PNG, JPEG y WebP.")

    # Validate Pillow readable image & strip EXIF
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img.verify()
    except Exception as exc:
        raise ValueError("La imagen está corrupta o no es un archivo de imagen válido.") from exc

    # Re-open for metadata stripping & metric extraction
    with Image.open(io.BytesIO(image_bytes)) as img:
        width, height = img.size
        img_format = img.format

        if width > max_width or height > max_height:
            raise ValueError(f"Las dimensiones de la imagen ({width}x{height}) exceden el máximo permitido de {max_width}x{max_height} píxeles.")

        # Re-save to in-memory buffer without EXIF metadata
        output_io = io.BytesIO()
        # Preserve alpha channel for PNG/WebP
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            save_format = "PNG" if detected_mime == "image/png" else "WEBP"
        else:
            save_format = img_format if img_format in ("PNG", "JPEG", "WEBP") else ("PNG" if detected_mime == "image/png" else "JPEG")

        # Convert palette images to RGBA if needed
        if img.mode == "P" and save_format in ("PNG", "WEBP"):
            img = img.convert("RGBA")

        img.save(output_io, format=save_format)
        sanitized_bytes = output_io.getvalue()

    file_hash = hashlib.sha256(sanitized_bytes).hexdigest()

    return {
        "sanitized_bytes": sanitized_bytes,
        "filename": filename,
        "mime_type": detected_mime,
        "size_bytes": len(sanitized_bytes),
        "width": width,
        "height": height,
        "file_hash": file_hash,
    }
