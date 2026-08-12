"""Reusable Phase 020 idempotency record adapter for Phase 036 commands."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.documents.series.series_models import IdempotencyRecordModel
from app.modules.logistics.inbound.arrival_notices.domain.errors.exceptions import (
    IdempotencyConflict,
)


def request_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def get_idempotent_response(
    db: Session,
    organization_id: UUID,
    operation: str,
    idempotency_key: str | None,
    payload: dict,
) -> dict | None:
    if not idempotency_key:
        return None
    record = db.scalar(
        select(IdempotencyRecordModel)
        .where(
            IdempotencyRecordModel.organization_id == organization_id,
            IdempotencyRecordModel.operation == operation,
            IdempotencyRecordModel.idempotency_key == idempotency_key,
        )
        .with_for_update()
    )
    if record is None:
        return None
    if record.request_hash != request_hash(payload):
        raise IdempotencyConflict(
            "La clave de idempotencia ya fue usada con una solicitud diferente."
        )
    return record.response_payload


def save_idempotent_response(
    db: Session,
    organization_id: UUID,
    user_id: UUID | None,
    operation: str,
    idempotency_key: str | None,
    payload: dict,
    response: dict,
) -> None:
    if not idempotency_key:
        return
    db.add(
        IdempotencyRecordModel(
            organization_id=organization_id,
            user_id=user_id,
            operation=operation,
            idempotency_key=idempotency_key,
            request_hash=request_hash(payload),
            response_payload=json.loads(json.dumps(response, default=str)),
            status="COMPLETED",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
    )
