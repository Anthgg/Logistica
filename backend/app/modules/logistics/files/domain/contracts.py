"""Files domain — contracts for file storage and management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class FileCategory(StrEnum):
    PDF = "pdf"
    XML = "xml"
    IMAGE = "image"
    SIGNATURE = "signature"
    EVIDENCE = "evidence"
    CERTIFICATE = "certificate"
    ATTACHMENT = "attachment"


@dataclass(frozen=True)
class SaveFileRequest:
    """Input for saving a file."""
    content: bytes
    filename: str
    content_type: str
    category: FileCategory
    uploaded_by: UUID
    metadata: dict[str, str] | None = None


@dataclass(frozen=True)
class StoredFile:
    """Output of saving a file."""
    id: UUID
    storage_key: str
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    category: FileCategory
    uploaded_by: UUID
    uploaded_at: datetime
    metadata: dict[str, str] | None = None


@dataclass(frozen=True)
class FileMetadata:
    """Metadata for a stored file."""
    id: UUID
    filename: str
    content_type: str
    size_bytes: int
    category: FileCategory
    sha256: str
    uploaded_at: datetime


@dataclass(frozen=True)
class SignedUrl:
    """A temporary URL for downloading a file."""
    url: str
    expires_at: datetime


# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------

class FileStorage(Protocol):
    """Stores and retrieves file binaries."""

    async def save(self, request: SaveFileRequest) -> StoredFile: ...

    async def read(self, file_id: UUID) -> bytes: ...

    async def delete(self, file_id: UUID) -> bool: ...


class FileMetadataRepository(Protocol):
    """Reads and persists file metadata."""

    async def get_by_id(self, file_id: UUID) -> FileMetadata | None: ...

    async def list_by_category(self, category: FileCategory, limit: int = 50) -> list[FileMetadata]: ...


class FileValidator(Protocol):
    """Validates file content, type and size."""

    def validate(self, content: bytes, content_type: str, filename: str) -> bool: ...


class FileHashService(Protocol):
    """Computes cryptographic hashes for file integrity."""

    def compute_sha256(self, content: bytes) -> str: ...

    def verify(self, content: bytes, expected_hash: str) -> bool: ...


class SignedUrlProvider(Protocol):
    """Generates temporary signed URLs for file download."""

    def generate(self, file_id: UUID, expires_in_seconds: int = 3600) -> SignedUrl: ...