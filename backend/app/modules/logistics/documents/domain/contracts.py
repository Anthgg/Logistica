"""Documents domain — contracts.

Typed protocols defining the document engine surface without any
implementation.  These contracts allow the application layer to depend
on abstractions rather than concrete renderers or storage backends.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

class DocumentType(StrEnum):
    REMISSION_GUIDE = "remission_guide"
    RECEPTION_ACT = "reception_act"
    DISPATCH_ACT = "dispatch_act"
    MANIFEST = "manifest"
    DELIVERY_PROOF = "delivery_proof"


class DocumentStatus(StrEnum):
    DRAFT = "draft"
    ISSUED = "issued"
    CANCELLED = "cancelled"
    REPRINTED = "reprinted"


@dataclass(frozen=True)
class DocumentNumber:
    """A document's human-readable identifier (serie-correlativo)."""
    serie: str
    correlativo: int

    def __str__(self) -> str:
        return f"{self.serie}-{self.correlativo:06d}"


@dataclass(frozen=True)
class DocumentRequest:
    """Input contract for creating a document from an operation."""
    document_type: DocumentType
    source_resource_id: UUID
    issued_by: UUID
    metadata: dict[str, str] | None = None


@dataclass(frozen=True)
class DocumentSnapshot:
    """Immutable snapshot of a document at a point in time."""
    id: UUID
    number: DocumentNumber
    document_type: DocumentType
    status: DocumentStatus
    issued_at: datetime
    issued_by: UUID
    verification_code: str
    metadata: dict[str, str] | None = None


@dataclass(frozen=True)
class StoredDocument:
    """Result of storing a rendered document."""
    id: UUID
    snapshot: DocumentSnapshot
    storage_key: str
    content_type: str
    size_bytes: int
    sha256: str


# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------

class DocumentRenderer(Protocol):
    """Renders a document into a binary representation (PDF, etc.)."""

    async def render(self, snapshot: DocumentSnapshot) -> bytes: ...


class DocumentStorage(Protocol):
    """Persists rendered document binaries and retrieves them."""

    async def save(self, content: bytes, snapshot: DocumentSnapshot) -> StoredDocument: ...

    async def retrieve(self, document_id: UUID) -> bytes: ...


class DocumentNumberGenerator(Protocol):
    """Generates unique document numbers (serie-correlativo)."""

    def next_number(self, document_type: DocumentType) -> DocumentNumber: ...


class DocumentSnapshotRepository(Protocol):
    """Reads and persists document snapshots."""

    async def save(self, snapshot: DocumentSnapshot) -> DocumentSnapshot: ...

    async def get_by_id(self, document_id: UUID) -> DocumentSnapshot | None: ...

    async def get_by_verification_code(self, code: str) -> DocumentSnapshot | None: ...


class DocumentVerificationService(Protocol):
    """Validates a document's verification code."""

    def verify(self, code: str) -> bool: ...

    def generate_code(self, snapshot: DocumentSnapshot) -> str: ...