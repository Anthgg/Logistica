"""Idempotency service for inventory ledger posting requests.

The implementation relies on the existing ``IdempotencyRecordModel``
(Phase 013). It enforces:

* Same (key, payload_hash) → return prior result.
* Same key, different payload_hash → raise IDEMPOTENCY_CONFLICT.
* A new key inserts a fresh idempotency record inside the same
  transaction as the posting request.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.documents.series.series_models import IdempotencyRecordModel
from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
    InventoryMovementIdempotencyConflict,
)


def hash_payload(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class InventoryMovementIdempotencyService:
    """Persist and resolve idempotency records for posting requests."""

    OPERATION = "inventory_ledger.post_movement"

    def __init__(self, db: Session) -> None:
        self._db = db

    def lookup(
        self,
        *,
        organization_id: UUID,
        idempotency_key: str,
    ) -> IdempotencyRecordModel | None:
        stmt = select(IdempotencyRecordModel).where(
            IdempotencyRecordModel.organization_id == organization_id,
            IdempotencyRecordModel.operation == self.OPERATION,
            IdempotencyRecordModel.idempotency_key == idempotency_key,
        )
        return self._db.scalars(stmt).first()

    def register(
        self,
        *,
        organization_id: UUID,
        idempotency_key: str,
        payload_hash: str,
        response_payload: Mapping[str, Any] | None = None,
    ) -> IdempotencyRecordModel:
        existing = self.lookup(
            organization_id=organization_id,
            idempotency_key=idempotency_key,
        )
        if existing is not None:
            if existing.request_hash != payload_hash:
                raise InventoryMovementIdempotencyConflict(
                    "Idempotency key reused with a different payload hash.",
                )
            return existing
        record = IdempotencyRecordModel(
            organization_id=organization_id,
            operation=self.OPERATION,
            idempotency_key=idempotency_key,
            request_hash=payload_hash,
            response_payload=dict(response_payload) if response_payload else None,
            status="COMPLETED",
        )
        self._db.add(record)
        self._db.flush()
        return record
