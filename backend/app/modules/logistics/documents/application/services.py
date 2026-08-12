"""Documents application — service contracts.

Application-layer use cases that coordinate between domain contracts.
These services orchestrate rendering, numbering, storage and verification
without depending on concrete implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.modules.logistics.documents.domain.contracts import (
    DocumentRequest,
    DocumentSnapshot,
    DocumentStatus,
    StoredDocument,
)


@dataclass(frozen=True)
class PreviewRequest:
    """Request a preview (not yet issued) of a document."""
    document_type: str
    source_resource_id: UUID
    metadata: dict[str, str] | None = None


class DocumentIssueService(Protocol):
    """Issue a new document from an operation."""

    async def issue(self, request: DocumentRequest) -> DocumentSnapshot: ...


class DocumentPreviewService(Protocol):
    """Generate a preview without persisting or numbering."""

    async def preview(self, request: PreviewRequest) -> bytes: ...


class DocumentReprintService(Protocol):
    """Re-render an already-issued document."""

    async def reprint(self, document_id: UUID) -> StoredDocument: ...


class DocumentCancelService(Protocol):
    """Cancel/annull an issued document."""

    async def cancel(self, document_id: UUID, reason: str) -> DocumentSnapshot: ...


class DocumentDownloadService(Protocol):
    """Retrieve the rendered binary for download."""

    async def download(self, document_id: UUID) -> bytes: ...


class DocumentPackageService(Protocol):
    """Download a package of multiple documents (ZIP)."""

    async def download_package(self, document_ids: list[UUID]) -> bytes: ...


class DocumentMetadataService(Protocol):
    """Retrieve document metadata without the binary."""

    async def get_metadata(self, document_id: UUID) -> DocumentSnapshot | None: ...