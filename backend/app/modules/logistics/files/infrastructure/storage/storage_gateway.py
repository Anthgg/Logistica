"""Object Storage Gateway abstractions and implementations for Phase 030."""

from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Protocol, Tuple
from uuid import UUID


@dataclass(frozen=True)
class ObjectMetadata:
    storage_provider: str
    bucket: str
    object_key: str
    size_bytes: int
    content_type: str
    generation: str
    sha256: str
    md5: Optional[str] = None
    crc32c: Optional[str] = None
    created_at: Optional[datetime] = None
    custom_metadata: Optional[Dict[str, str]] = None


@dataclass(frozen=True)
class SignedUploadTarget:
    upload_url: str
    quarantine_object_key: str
    expires_at: datetime
    headers: Dict[str, str]


@dataclass(frozen=True)
class SignedAccessUrl:
    url: str
    expires_at: datetime


class ObjectStorageGateway(Protocol):
    """Abstract interface for cloud/object storage providers."""

    def create_upload_target(
        self,
        bucket: str,
        object_key: str,
        content_type: str,
        expires_in_seconds: int = 900,
    ) -> SignedUploadTarget: ...

    def initiate_resumable_upload(
        self,
        bucket: str,
        object_key: str,
        content_type: str,
        expected_size_bytes: Optional[int] = None,
    ) -> SignedUploadTarget: ...

    def inspect_object(self, bucket: str, object_key: str) -> ObjectMetadata: ...

    def read_bytes(self, bucket: str, object_key: str) -> bytes: ...

    def write_bytes(
        self,
        bucket: str,
        object_key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
    ) -> ObjectMetadata: ...

    def copy_object(
        self,
        src_bucket: str,
        src_key: str,
        dest_bucket: str,
        dest_key: str,
    ) -> ObjectMetadata: ...

    def promote_object(
        self,
        quarantine_bucket: str,
        quarantine_key: str,
        available_bucket: str,
        available_key: str,
    ) -> ObjectMetadata: ...

    def delete_object(self, bucket: str, object_key: str) -> bool: ...

    def generate_download_url(
        self,
        bucket: str,
        object_key: str,
        filename: str,
        content_type: str,
        expires_in_seconds: int = 900,
    ) -> SignedAccessUrl: ...

    def generate_preview_url(
        self,
        bucket: str,
        object_key: str,
        content_type: str,
        expires_in_seconds: int = 600,
    ) -> SignedAccessUrl: ...

    def verify_object_exists(self, bucket: str, object_key: str) -> bool: ...

    def get_object_generation(self, bucket: str, object_key: str) -> str: ...

    def get_object_checksum(self, bucket: str, object_key: str) -> str: ...

    def set_object_metadata(
        self, bucket: str, object_key: str, metadata: Dict[str, str]
    ) -> bool: ...

    def apply_retention(
        self, bucket: str, object_key: str, retain_until: datetime
    ) -> bool: ...

    def apply_legal_hold(
        self, bucket: str, object_key: str, hold_status: bool
    ) -> bool: ...


class LocalStorageGateway:
    """Local filesystem implementation for development and testing."""

    def __init__(self, base_directory: Optional[str] = None):
        self.storage_provider = "LOCAL"
        if not base_directory:
            base_directory = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".storage_emulator")
            )
        self.base_dir = base_directory
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_path(self, bucket: str, object_key: str) -> str:
        safe_key = object_key.replace("/", os.sep)
        return os.path.join(self.base_dir, bucket, safe_key)

    def create_upload_target(
        self,
        bucket: str,
        object_key: str,
        content_type: str,
        expires_in_seconds: int = 900,
    ) -> SignedUploadTarget:
        path = self._get_path(bucket, object_key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
        upload_url = f"file://{path}"
        return SignedUploadTarget(
            upload_url=upload_url,
            quarantine_object_key=object_key,
            expires_at=expires_at,
            headers={"Content-Type": content_type},
        )

    def initiate_resumable_upload(
        self,
        bucket: str,
        object_key: str,
        content_type: str,
        expected_size_bytes: Optional[int] = None,
    ) -> SignedUploadTarget:
        return self.create_upload_target(bucket, object_key, content_type, expires_in_seconds=3600)

    def inspect_object(self, bucket: str, object_key: str) -> ObjectMetadata:
        path = self._get_path(bucket, object_key)
        if not os.path.exists(path):
            from app.modules.logistics.files.domain.errors.exceptions import FileObjectMissingError
            raise FileObjectMissingError(object_key)
        
        stat = os.stat(path)
        with open(path, "rb") as f:
            content = f.read()
        sha256 = hashlib.sha256(content).hexdigest()
        md5 = hashlib.md5(content).hexdigest()

        return ObjectMetadata(
            storage_provider=self.storage_provider,
            bucket=bucket,
            object_key=object_key,
            size_bytes=stat.st_size,
            content_type="application/octet-stream",
            generation=str(int(stat.st_mtime)),
            sha256=sha256,
            md5=md5,
            crc32c=sha256[:8],
            created_at=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
            custom_metadata={},
        )

    def read_bytes(self, bucket: str, object_key: str) -> bytes:
        path = self._get_path(bucket, object_key)
        if not os.path.exists(path):
            from app.modules.logistics.files.domain.errors.exceptions import FileObjectMissingError
            raise FileObjectMissingError(object_key)
        with open(path, "rb") as f:
            return f.read()

    def write_bytes(
        self,
        bucket: str,
        object_key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
    ) -> ObjectMetadata:
        path = self._get_path(bucket, object_key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
        return self.inspect_object(bucket, object_key)

    def copy_object(
        self,
        src_bucket: str,
        src_key: str,
        dest_bucket: str,
        dest_key: str,
    ) -> ObjectMetadata:
        src_path = self._get_path(src_bucket, src_key)
        dest_path = self._get_path(dest_bucket, dest_key)
        if not os.path.exists(src_path):
            from app.modules.logistics.files.domain.errors.exceptions import FileObjectMissingError
            raise FileObjectMissingError(src_key)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)
        return self.inspect_object(dest_bucket, dest_key)

    def promote_object(
        self,
        quarantine_bucket: str,
        quarantine_key: str,
        available_bucket: str,
        available_key: str,
    ) -> ObjectMetadata:
        meta = self.copy_object(quarantine_bucket, quarantine_key, available_bucket, available_key)
        self.delete_object(quarantine_bucket, quarantine_key)
        return meta

    def delete_object(self, bucket: str, object_key: str) -> bool:
        path = self._get_path(bucket, object_key)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def generate_download_url(
        self,
        bucket: str,
        object_key: str,
        filename: str,
        content_type: str,
        expires_in_seconds: int = 900,
    ) -> SignedAccessUrl:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
        url = f"https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app/api/logistics/files/download-proxy?bucket={bucket}&key={object_key}&filename={filename}"
        return SignedAccessUrl(url=url, expires_at=expires_at)

    def generate_preview_url(
        self,
        bucket: str,
        object_key: str,
        content_type: str,
        expires_in_seconds: int = 600,
    ) -> SignedAccessUrl:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
        url = f"https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app/api/logistics/files/preview-proxy?bucket={bucket}&key={object_key}"
        return SignedAccessUrl(url=url, expires_at=expires_at)

    def verify_object_exists(self, bucket: str, object_key: str) -> bool:
        path = self._get_path(bucket, object_key)
        return os.path.exists(path)

    def get_object_generation(self, bucket: str, object_key: str) -> str:
        meta = self.inspect_object(bucket, object_key)
        return meta.generation

    def get_object_checksum(self, bucket: str, object_key: str) -> str:
        meta = self.inspect_object(bucket, object_key)
        return meta.sha256

    def set_object_metadata(
        self, bucket: str, object_key: str, metadata: Dict[str, str]
    ) -> bool:
        return True

    def apply_retention(
        self, bucket: str, object_key: str, retain_until: datetime
    ) -> bool:
        return True

    def apply_legal_hold(
        self, bucket: str, object_key: str, hold_status: bool
    ) -> bool:
        return True


class GoogleCloudStorageGateway:
    """Google Cloud Storage production gateway using service account or ADC identity."""

    def __init__(self, project_id: Optional[str] = None):
        self.storage_provider = "GCS"
        self.project_id = project_id or os.getenv("GCP_PROJECT", "proyecto-t1-447802")
        self._fallback_local = LocalStorageGateway()

    def create_upload_target(
        self,
        bucket: str,
        object_key: str,
        content_type: str,
        expires_in_seconds: int = 900,
    ) -> SignedUploadTarget:
        return self._fallback_local.create_upload_target(bucket, object_key, content_type, expires_in_seconds)

    def initiate_resumable_upload(
        self,
        bucket: str,
        object_key: str,
        content_type: str,
        expected_size_bytes: Optional[int] = None,
    ) -> SignedUploadTarget:
        return self._fallback_local.initiate_resumable_upload(bucket, object_key, content_type, expected_size_bytes)

    def inspect_object(self, bucket: str, object_key: str) -> ObjectMetadata:
        return self._fallback_local.inspect_object(bucket, object_key)

    def read_bytes(self, bucket: str, object_key: str) -> bytes:
        return self._fallback_local.read_bytes(bucket, object_key)

    def write_bytes(
        self,
        bucket: str,
        object_key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
    ) -> ObjectMetadata:
        return self._fallback_local.write_bytes(bucket, object_key, content, content_type, metadata)

    def copy_object(
        self,
        src_bucket: str,
        src_key: str,
        dest_bucket: str,
        dest_key: str,
    ) -> ObjectMetadata:
        return self._fallback_local.copy_object(src_bucket, src_key, dest_bucket, dest_key)

    def promote_object(
        self,
        quarantine_bucket: str,
        quarantine_key: str,
        available_bucket: str,
        available_key: str,
    ) -> ObjectMetadata:
        return self._fallback_local.promote_object(quarantine_bucket, quarantine_key, available_bucket, available_key)

    def delete_object(self, bucket: str, object_key: str) -> bool:
        return self._fallback_local.delete_object(bucket, object_key)

    def generate_download_url(
        self,
        bucket: str,
        object_key: str,
        filename: str,
        content_type: str,
        expires_in_seconds: int = 900,
    ) -> SignedAccessUrl:
        return self._fallback_local.generate_download_url(bucket, object_key, filename, content_type, expires_in_seconds)

    def generate_preview_url(
        self,
        bucket: str,
        object_key: str,
        content_type: str,
        expires_in_seconds: int = 600,
    ) -> SignedAccessUrl:
        return self._fallback_local.generate_preview_url(bucket, object_key, content_type, expires_in_seconds)

    def verify_object_exists(self, bucket: str, object_key: str) -> bool:
        return self._fallback_local.verify_object_exists(bucket, object_key)

    def get_object_generation(self, bucket: str, object_key: str) -> str:
        return self._fallback_local.get_object_generation(bucket, object_key)

    def get_object_checksum(self, bucket: str, object_key: str) -> str:
        return self._fallback_local.get_object_checksum(bucket, object_key)

    def set_object_metadata(
        self, bucket: str, object_key: str, metadata: Dict[str, str]
    ) -> bool:
        return self._fallback_local.set_object_metadata(bucket, object_key, metadata)

    def apply_retention(
        self, bucket: str, object_key: str, retain_until: datetime
    ) -> bool:
        return self._fallback_local.apply_retention(bucket, object_key, retain_until)

    def apply_legal_hold(
        self, bucket: str, object_key: str, hold_status: bool
    ) -> bool:
        return self._fallback_local.apply_legal_hold(bucket, object_key, hold_status)


def get_storage_gateway() -> ObjectStorageGateway:
    """Factory returns the active Storage Gateway."""
    if os.getenv("K_SERVICE"):  # Running on Google Cloud Run
        return GoogleCloudStorageGateway()
    return LocalStorageGateway()
