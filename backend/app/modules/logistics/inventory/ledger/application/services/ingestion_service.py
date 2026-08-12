"""Ingestion boundary for source-backed prepared inventory events."""

from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from app.modules.logistics.inventory.ledger.application.services.posting_service import (
    InventoryMovementPostingService,
    PostingResult,
    assert_no_server_derived_fields,
)
from app.modules.logistics.inventory.ledger.domain.services.source_registry import (
    InventoryMovementSourceRegistry,
    PreparedMovement,
)


class PreparedInventoryEventIngestionService:
    """Authorize an adapter, canonicalize its output, then post idempotently."""

    def __init__(
        self,
        *,
        registry: InventoryMovementSourceRegistry,
        posting_service: InventoryMovementPostingService,
    ) -> None:
        self._registry = registry
        self._posting = posting_service

    def prepare(
        self,
        *,
        organization_id: UUID,
        adapter_name: str,
        source_payload: Mapping[str, Any],
    ) -> PreparedMovement:
        assert_no_server_derived_fields(source_payload)
        return self._registry.prepare(
            adapter_name=adapter_name,
            organization_id=organization_id,
            payload=source_payload,
        )

    def ingest_and_post(
        self,
        *,
        organization_id: UUID,
        adapter_name: str,
        source_system: str,
        source_event_type: str,
        source_event_id: str,
        source_event_version: int,
        source_payload: Mapping[str, Any],
        actor_user_id: UUID | None,
    ) -> PostingResult:
        enriched = {
            **dict(source_payload),
            "source_event_id": source_event_id,
            "source_event_version": source_event_version,
        }
        prepared = self.prepare(
            organization_id=organization_id,
            adapter_name=adapter_name,
            source_payload=enriched,
        )
        payload = {
            "movement_type": prepared.movement_type,
            "movement_family": prepared.movement_family,
            "source_adapter_name": adapter_name,
            "branch_id": source_payload.get("branch_id"),
            "warehouse_id": source_payload.get("warehouse_id"),
            "site_code": source_payload.get("site_code", "GLB"),
            "occurred_at": prepared.occurred_at or source_payload.get("occurred_at"),
            "reason_code": prepared.reason_code,
            "source_hash": str(source_payload.get("source_hash", "")),
            "payload_hash": prepared.payload_hash,
            "source_references": [dict(item) for item in prepared.source_references],
            "lines": [dict(item) for item in prepared.lines],
        }
        record = self._posting.create_posting_request(
            organization_id=organization_id,
            request_key=prepared.idempotency_key,
            source_system=source_system,
            source_event_type=source_event_type,
            source_event_id=source_event_id,
            source_event_version=source_event_version,
            payload=payload,
            requested_by_user_id=actor_user_id,
            requested_by_service="prepared-event-api",
        )
        return self._posting.post(
            organization_id=organization_id,
            posting_request_id=record.id,
            actor_user_id=actor_user_id,
        )
