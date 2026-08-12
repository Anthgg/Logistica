"""Document Artifact Storage implementation (Phase 020).

Handles local filesystem and potentially GCS/S3 storage backends.
"""

from __future__ import annotations

import os
import hashlib
from pathlib import Path
from typing import Literal

from app.core.config import settings

# Determine base path for local storage
BACKEND_DIR = Path(__file__).resolve().parents[5]
LOCAL_STORAGE_DIR = BACKEND_DIR / "data" / "documents"


class DocumentArtifactStorage:
    """Concrete storage adapter for document files (Phase 020)."""

    def __init__(self, provider: Literal["local", "gcs", "s3"] | None = None) -> None:
        self.provider = provider or settings.STORAGE_PROVIDER
        if self.provider == "local":
            os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)

    def _resolve_local_path(self, storage_key: str) -> Path:
        # Prevent Directory Traversal / ZIP Slip by cleaning the path
        clean_key = storage_key.lstrip("/")
        # Resolve path
        target_path = (LOCAL_STORAGE_DIR / clean_key).resolve()
        # Verify it remains within LOCAL_STORAGE_DIR to prevent directory traversal
        if not str(target_path).startswith(str(LOCAL_STORAGE_DIR.resolve())):
            raise ValueError(f"Path traversal attempt detected: {storage_key}")
        return target_path

    def put(self, storage_key: str, content: bytes) -> str:
        """Stores the binary content under the given storage key.

        Returns:
            The final resolved storage key.
        """
        if self.provider == "local":
            target_path = self._resolve_local_path(storage_key)
            os.makedirs(target_path.parent, exist_ok=True)
            with open(target_path, "wb") as f:
                f.write(content)
            return storage_key
        else:
            # Simulate or raise not implemented for other providers in tests
            raise NotImplementedError(f"Storage provider '{self.provider}' not implemented.")

    def get(self, storage_key: str) -> bytes:
        """Retrieves binary content by key."""
        if self.provider == "local":
            target_path = self._resolve_local_path(storage_key)
            if not target_path.exists():
                raise FileNotFoundError(f"Artifact not found under storage key: {storage_key}")
            with open(target_path, "rb") as f:
                return f.read()
        else:
            raise NotImplementedError(f"Storage provider '{self.provider}' not implemented.")

    def exists(self, storage_key: str) -> bool:
        """Checks if key exists in storage."""
        if self.provider == "local":
            try:
                target_path = self._resolve_local_path(storage_key)
                return target_path.exists()
            except ValueError:
                return False
        return False

    def verify_hash(self, storage_key: str, expected_hash: str) -> bool:
        """Verifies if the stored file matches the expected SHA-256 hash."""
        try:
            content = self.get(storage_key)
            actual_hash = hashlib.sha256(content).hexdigest()
            return actual_hash == expected_hash
        except Exception:
            return False

    def delete_temporary(self, storage_key: str) -> None:
        """Permanently deletes temporary storage artifacts (e.g. export ZIPs).

        Does NOT allow deleting issued/official document artifacts.
        """
        if "temporary" in storage_key or "exports" in storage_key:
            if self.provider == "local":
                target_path = self._resolve_local_path(storage_key)
                if target_path.exists():
                    os.remove(target_path)
            else:
                raise NotImplementedError()
        else:
            raise PermissionError("Deleting permanent document artifacts is strictly prohibited.")
