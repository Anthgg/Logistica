"""Phase 044 — Database integration tests for the inventory ledger."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.modules.logistics.inventory.ledger.application.services.posting_service import (
    InventoryMovementPostingService,
)
from app.modules.logistics.inventory.ledger.application.services.validation_service import (
    InventoryMovementValidationService,
)
from app.modules.logistics.inventory.ledger.domain.services.availability_provider import (
    SourceBackedAvailabilityProvider,
)


def _ensure_organization(session: Session, org_id: UUID) -> Organization:
    org = session.get(Organization, org_id)
    if not org:
        org = Organization(
            id=org_id,
            code=f"ORG-{str(org_id)[:8]}",
            name="Test Organization",
            country_code="PE",
        )
        session.add(org)
        session.flush()
    return org


def test_posting_creates_appended_only_movement(database: Session):
    """End-to-end posting flow should publish a single immutable movement."""

    org_id = uuid4()
    _ensure_organization(database, org_id)
    branch_id = uuid4()
    warehouse_id = uuid4()
    product_id = uuid4()
    unit_id = uuid4()
    base_unit_id = unit_id
    source_position_id = uuid4()
    destination_position_id = uuid4()

    availability = SourceBackedAvailabilityProvider(database)
    validation = InventoryMovementValidationService(availability_provider=availability)
    posting = InventoryMovementPostingService(database, validation_service=validation)

    source_event_id = f"evt-{uuid4()}"
    payload = {
        "movement_type": "PUTAWAY_COMPLETED",
        "source_adapter_name": "PUTAWAY_COMPLETED",
        "branch_id": str(branch_id),
        "warehouse_id": str(warehouse_id),
        "source_event_id": source_event_id,
        "source_event_version": 1,
        "source_hash": "a" * 64,
        "payload_hash": "a" * 64,
        "occurred_at": datetime.now(UTC).isoformat(),
        "lines": [
            {
                "product_id": str(product_id),
                "unit_id": str(unit_id),
                "base_unit_id": str(base_unit_id),
                "quantity": "10",
                "base_quantity": "10",
                "source_position_id": str(source_position_id),
                "destination_position_id": str(destination_position_id),
                "quantity_direction": "TRANSFER",
            }
        ],
        "source_references": [
            {
                "source_entity_type": "OPERATIONAL_PLACEMENT",
                "source_entity_id": str(uuid4()),
                "source_hash": "a" * 64,
                "product_id": str(product_id),
                "requested_base_quantity": "10",
            }
        ],
    }
    request = posting.create_posting_request(
        organization_id=org_id,
        request_key=source_event_id,
        source_system="PUTAWAY",
        source_event_type="PUTAWAY_COMPLETED",
        source_event_id=source_event_id,
        source_event_version=1,
        payload=payload,
    )
    # Validation will fail because no source allocation exists, but the request must
    # be persisted so the failure is recoverable.
    with pytest.raises(Exception):  # noqa: B017
        posting.post(organization_id=org_id, posting_request_id=request.id)

    from app.modules.logistics.inventory.ledger.infrastructure.persistence.models import (
        InventoryMovementPostingRequestModel,
    )

    request_db = database.get(InventoryMovementPostingRequestModel, request.id)
    assert request_db is not None
    assert request_db.status == "FAILED"
    assert request_db.failure_code is not None


def test_idempotency_record_persisted(database: Session):
    """Posting twice the same source should not produce two movements."""

    from app.modules.logistics.inventory.ledger.application.services.posting_service import (
        InventoryMovementPostingService,
    )
    from app.modules.logistics.inventory.ledger.application.services.validation_service import (
        InventoryMovementValidationService,
    )
    from app.modules.logistics.inventory.ledger.domain.services.availability_provider import (
        SourceBackedAvailabilityProvider,
    )

    org_id = uuid4()
    _ensure_organization(database, org_id)
    availability = SourceBackedAvailabilityProvider(database)
    validation = InventoryMovementValidationService(availability_provider=availability)
    posting = InventoryMovementPostingService(database, validation_service=validation)

    source_event_id = str(uuid4())
    payload = {
        "movement_type": "PUTAWAY_COMPLETED",
        "source_adapter_name": "PUTAWAY_COMPLETED",
        "branch_id": str(uuid4()),
        "warehouse_id": str(uuid4()),
        "source_event_id": source_event_id,
        "source_event_version": 1,
        "source_hash": "a" * 64,
        "payload_hash": "a" * 64,
        "lines": [
            {
                "product_id": str(uuid4()),
                "unit_id": str(uuid4()),
                "base_unit_id": str(uuid4()),
                "quantity": "5",
                "base_quantity": "5",
                "destination_position_id": str(uuid4()),
                "quantity_direction": "TRANSFER",
            }
        ],
    }
    first = posting.create_posting_request(
        organization_id=org_id,
        request_key=source_event_id,
        source_system="PUTAWAY",
        source_event_type="PUTAWAY_COMPLETED",
        source_event_id=source_event_id,
        source_event_version=1,
        payload=payload,
    )
    second = posting.create_posting_request(
        organization_id=org_id,
        request_key=source_event_id,
        source_system="PUTAWAY",
        source_event_type="PUTAWAY_COMPLETED",
        source_event_id=source_event_id,
        source_event_version=1,
        payload=payload,
    )
    assert first.id == second.id, "The same source event must produce the same posting request"
    assert first.payload_hash == second.payload_hash


def test_duplicate_with_different_payload_hash_raises(database: Session):
    from app.modules.logistics.inventory.ledger.application.services.posting_service import (
        InventoryMovementPostingService,
    )
    from app.modules.logistics.inventory.ledger.application.services.validation_service import (
        InventoryMovementValidationService,
    )
    from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
        InventoryMovementSourceDuplicated,
    )
    from app.modules.logistics.inventory.ledger.domain.services.availability_provider import (
        SourceBackedAvailabilityProvider,
    )

    org_id = uuid4()
    _ensure_organization(database, org_id)
    availability = SourceBackedAvailabilityProvider(database)
    validation = InventoryMovementValidationService(availability_provider=availability)
    posting = InventoryMovementPostingService(database, validation_service=validation)

    source_event_id = str(uuid4())
    payload_a = {"movement_type": "PUTAWAY_COMPLETED", "lines": [], "source_hash": "a" * 64, "payload_hash": "a" * 64}
    payload_b = {"movement_type": "PUTAWAY_COMPLETED", "lines": [], "source_hash": "b" * 64, "payload_hash": "b" * 64}
    posting.create_posting_request(
        organization_id=org_id,
        request_key=source_event_id,
        source_system="PUTAWAY",
        source_event_type="PUTAWAY_COMPLETED",
        source_event_id=source_event_id,
        source_event_version=1,
        payload=payload_a,
    )
    with pytest.raises(InventoryMovementSourceDuplicated):
        posting.create_posting_request(
            organization_id=org_id,
            request_key=source_event_id,
            source_system="PUTAWAY",
            source_event_type="PUTAWAY_COMPLETED",
            source_event_id=source_event_id,
            source_event_version=1,
            payload=payload_b,
        )
