from hashlib import sha256
from pathlib import Path
from typing import Protocol
from uuid import UUID

from app.core.config import BACKEND_DIR, settings
from app.core.exceptions import ApplicationError


class CaptureStorageService(Protocol):
    def save_capture(
        self, session_id: UUID, capture_id: UUID, extension: str, content: bytes
    ) -> str: ...

    def delete_capture(self, storage_path: str) -> None: ...

    def exists(self, storage_path: str) -> bool: ...

    def read_capture(self, storage_path: str) -> bytes: ...

    def calculate_checksum(self, content: bytes) -> str: ...


class LocalCaptureStorageService:
    def __init__(self, root: str | Path | None = None) -> None:
        configured = Path(root or settings.CAPTURE_LOCAL_PATH)
        if not configured.is_absolute():
            configured = BACKEND_DIR / configured
        self.root = configured.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe_target(self, storage_path: str) -> Path:
        relative = Path(storage_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ApplicationError(
                "INVALID_CAPTURE_PATH", "La ruta de captura no es válida.", 400
            )
        target = (self.root / relative).resolve()
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise ApplicationError(
                "INVALID_CAPTURE_PATH", "La ruta de captura no es válida.", 400
            ) from exc
        return target

    def save_capture(
        self, session_id: UUID, capture_id: UUID, extension: str, content: bytes
    ) -> str:
        if extension not in {"jpg", "webp"}:
            raise ApplicationError(
                "CAPTURE_FORMAT_NOT_ALLOWED", "Formato de captura no permitido.", 415
            )
        storage_path = f"{session_id}/{capture_id}.{extension}"
        target = self._safe_target(storage_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(f"{target.suffix}.tmp")
        temporary.write_bytes(content)
        temporary.replace(target)
        return storage_path

    def delete_capture(self, storage_path: str) -> None:
        target = self._safe_target(storage_path)
        if target.exists():
            target.unlink()

    def exists(self, storage_path: str) -> bool:
        return self._safe_target(storage_path).is_file()

    def read_capture(self, storage_path: str) -> bytes:
        target = self._safe_target(storage_path)
        if not target.is_file():
            raise ApplicationError(
                "INVALID_CAPTURE",
                "El archivo de la captura no está disponible.",
                404,
            )
        return target.read_bytes()

    def calculate_checksum(self, content: bytes) -> str:
        return sha256(content).hexdigest()
