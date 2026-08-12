"""Safe HTTPS Downloader & ZIP extractor with anti-ZIP bomb and traversal protection."""

import hashlib
import io
import os
import re
import urllib.parse
import urllib.request
import zipfile
from typing import List, Tuple

from app.modules.logistics.ruc.domain.errors.exceptions import (
    RucImportArchiveInvalidError,
    RucImportZipBombError,
)


class SafeZipDownloader:
    """Downloads ZIP archive securely from allowed HTTPS hosts."""

    MAX_COMPRESSED_MB = 200
    MAX_UNCOMPRESSED_MB = 1000
    MAX_COMPRESSION_RATIO = 20.0
    DOWNLOAD_TIMEOUT_SECONDS = 120
    ALLOWED_HOSTS = ["e-consultaruc.sunat.gob.pe", "www.sunat.gob.pe", "sunat.gob.pe", "github.com", "raw.githubusercontent.com"]

    @classmethod
    def validate_url(cls, url: str) -> bool:
        if not url.startswith("https://"):
            return False
        parsed = urllib.parse.urlparse(url)
        return parsed.hostname in cls.ALLOWED_HOSTS or any(parsed.hostname.endswith("." + h) for h in cls.ALLOWED_HOSTS) if parsed.hostname else False

    @classmethod
    def download_and_verify(cls, url: str) -> Tuple[bytes, str, int]:
        """Downloads bytes from URL and returns (content_bytes, sha256_hex, size_bytes)."""
        if not cls.validate_url(url):
            raise RucImportArchiveInvalidError(f"URL de descarga '{url}' no está en la lista de hosts autorizados.")

        req = urllib.request.Request(url, headers={"User-Agent": "ProyectoT1-RucImporter/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=cls.DOWNLOAD_TIMEOUT_SECONDS) as resp:
                content = resp.read()
        except Exception as e:
            raise RucImportArchiveInvalidError(f"Error descargando padrón RUC desde {url}: {str(e)}")

        size = len(content)
        if size > cls.MAX_COMPRESSED_MB * 1024 * 1024:
            raise RucImportArchiveInvalidError(f"Tamaño comprimido ({size} bytes) excede el máximo permitido ({cls.MAX_COMPRESSED_MB} MB).")

        sha256_hash = hashlib.sha256(content).hexdigest()
        return content, sha256_hash, size


class SafeZipExtractor:
    """Safely inspects and extracts text streams from ZIP archives."""

    @classmethod
    def inspect_and_extract_file(cls, zip_bytes: bytes, target_filename_pattern: str | None = None) -> Tuple[str, bytes]:
        """Returns (filename, uncompressed_bytes) safely."""
        try:
            zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        except zipfile.BadZipFile:
            raise RucImportArchiveInvalidError("El contenido descargado no es un archivo ZIP válido.")

        total_uncompressed = sum(zinfo.file_size for zinfo in zf.infolist())
        total_compressed = len(zip_bytes)

        if total_compressed > 0 and (total_uncompressed / total_compressed) > SafeZipDownloader.MAX_COMPRESSION_RATIO:
            raise RucImportZipBombError(f"Ratio de compresión Sospechoso ({total_uncompressed / total_compressed:.1f}x > {SafeZipDownloader.MAX_COMPRESSION_RATIO}x). Posible ZIP Bomb.")

        if total_uncompressed > SafeZipDownloader.MAX_UNCOMPRESSED_MB * 1024 * 1024:
            raise RucImportZipBombError(f"Tamaño descomprimido ({total_uncompressed} bytes) excede el máximo permitido ({SafeZipDownloader.MAX_UNCOMPRESSED_MB} MB).")

        selected_info = None
        for zinfo in zf.infolist():
            # Security checks against path traversal
            filename = zinfo.filename
            if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
                raise RucImportZipBombError(f"Ruta de archivo maliciosa detectada en ZIP: {filename}")

            if zinfo.is_dir():
                continue

            ext = os.path.splitext(filename)[1].lower()
            if ext in [".exe", ".bat", ".sh", ".cmd", ".dll", ".so", ".elf"]:
                raise RucImportZipBombError(f"Tipo de archivo no permitido en ZIP: {filename}")

            if target_filename_pattern:
                if re.search(target_filename_pattern, filename, re.IGNORECASE):
                    selected_info = zinfo
                    break
            else:
                if ext in [".txt", ".csv", ".dat"]:
                    selected_info = zinfo
                    break

        if not selected_info:
            if len(zf.infolist()) > 0:
                selected_info = [z for z in zf.infolist() if not z.is_dir()][0]
            else:
                raise RucImportArchiveInvalidError("El archivo ZIP no contiene ficheros válidos.")

        data = zf.read(selected_info.filename)
        return selected_info.filename, data
