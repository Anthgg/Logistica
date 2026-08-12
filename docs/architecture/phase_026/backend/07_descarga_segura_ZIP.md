# 07 — Descarga Segura de Archivos y Protección contra ZIP Bombs

## 1. Descarga Segura (`SafeZipDownloader`)

El componente `SafeZipDownloader` implementa controles estrictos de seguridad de red antes y durante la descarga de padrones ZIP oficiales:

```python
class SafeZipDownloader:
    ALLOWED_HOSTS = {
        "e-consultaruc.sunat.gob.pe",
        "www.sunat.gob.pe",
        "padron.sunat.gob.pe"
    }

    def __init__(self, allowed_hosts: set = None):
        self.allowed_hosts = allowed_hosts or self.ALLOWED_HOSTS

    def validate_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise RucImportUrlNotAllowedError("Solo se permiten conexiones HTTPS seguras.")
        if parsed.hostname not in self.allowed_hosts:
            raise RucImportUrlNotAllowedError(f"Host no autorizado: {parsed.hostname}")
        return True
```

---

## 2. Extracción Segura y Protección Anti ZIP-Bomb (`SafeZipExtractor`)

Los ataques ZIP Bomb intentan agotar el espacio en disco o memoria del servidor mediante archivos comprimidos altamente eficientes. `SafeZipExtractor` aplica límites de protección en tiempo de extracción:

```python
class SafeZipExtractor:
    MAX_COMPRESSION_RATIO = 100.0  # Máxima relación de compresión permitida (1:100)
    MAX_UNCOMPRESSED_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB
    MAX_FILE_COUNT = 1000

    @classmethod
    def extract_safely(cls, zip_bytes: bytes) -> bytes:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            infos = zf.infolist()
            if len(infos) > cls.MAX_FILE_COUNT:
                raise RucImportZipBombError("Exceso de archivos dentro del archivo ZIP.")

            total_uncompressed = 0
            for info in infos:
                if ".." in info.filename or info.filename.startswith("/"):
                    raise RucImportZipBombError(f"Intento de Path Traversal detectado: {info.filename}")
                
                total_uncompressed += info.file_size
                if total_uncompressed > cls.MAX_UNCOMPRESSED_SIZE_BYTES:
                    raise RucImportZipBombError("El tamaño descomprimido supera el límite de seguridad de 2 GB.")

                if info.compress_size > 0:
                    ratio = info.file_size / info.compress_size
                    if ratio > cls.MAX_COMPRESSION_RATIO:
                        raise RucImportZipBombError(f"Ratio de compresión anómalo detectado ({ratio:.2f}:1).")

            return zf.read(infos[0].filename)
```
