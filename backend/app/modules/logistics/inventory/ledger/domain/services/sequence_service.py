"""Inventory ledger sequence and MOV code services.

The book is partitioned by ``(organization, warehouse?, fiscal_year)``.
For each partition we maintain ``InventoryLedgerPartitionModel.current_sequence``
which is incremented transactionally under ``SELECT ... FOR UPDATE``.
This avoids ``MAX(seq)+1`` race conditions.

The MOV document code is reserved at posting time and follows the
project standard ``TYPE-SITE-YEAR-CORRELATIVE`` when a matching
``DocumentTypeModel`` with code ``MOV`` is available. Otherwise we
register a ``PENDIENTE_CATÁLOGO_DOCUMENTAL`` decision and use a
deterministic UUID-based technical code (only for development).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
    InventoryLedgerSequenceConflict,
    InventoryMovementCodeConflict,
)
from app.modules.logistics.inventory.ledger.infrastructure.persistence.models import (
    InventoryLedgerPartitionModel,
    InventoryMovementModel,
)


# ---------------------------------------------------------------------------
# Partition service
# ---------------------------------------------------------------------------

class InventoryLedgerSequenceService:
    """Transactional partition sequence allocator."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def build_partition_key(
        self,
        *,
        organization_id: UUID,
        warehouse_id: UUID | None,
        fiscal_year: int | None,
    ) -> str:
        wh = str(warehouse_id) if warehouse_id else "GLOBAL"
        yr = str(fiscal_year) if fiscal_year is not None else "OPEN"
        return f"{organization_id}:{wh}:{yr}"

    def get_or_create_partition(
        self,
        *,
        organization_id: UUID,
        partition_key: str,
        warehouse_id: UUID | None,
        fiscal_year: int | None,
    ) -> InventoryLedgerPartitionModel:
        stmt = select(InventoryLedgerPartitionModel).where(
            InventoryLedgerPartitionModel.organization_id == organization_id,
            InventoryLedgerPartitionModel.partition_key == partition_key,
        )
        partition = self._db.scalars(stmt).first()
        if partition is not None:
            return partition
        partition = InventoryLedgerPartitionModel(
            organization_id=organization_id,
            partition_key=partition_key,
            warehouse_id=warehouse_id,
            fiscal_year=fiscal_year,
            current_sequence=0,
        )
        self._db.add(partition)
        self._db.flush()
        return partition

    def reserve_next_sequence(self, partition: InventoryLedgerPartitionModel) -> int:
        """Atomically increment and return the next sequence value.

        Uses ``SELECT ... FOR UPDATE`` to guarantee no two postings can
        get the same sequence. The caller must already be inside a
        transaction.
        """

        locked = self._db.execute(
            select(InventoryLedgerPartitionModel)
            .where(InventoryLedgerPartitionModel.id == partition.id)
            .with_for_update()
        ).scalar_one()
        next_seq = int(locked.current_sequence) + 1
        if next_seq < 1:
            raise InventoryLedgerSequenceConflict(
                "Computed sequence is not positive for partition.",
            )
        locked.current_sequence = next_seq
        self._db.flush()
        return next_seq

    def bind_last_movement(
        self,
        partition: InventoryLedgerPartitionModel,
        movement: InventoryMovementModel,
    ) -> None:
        partition.last_movement_id = movement.id
        partition.last_movement_hash = movement.movement_hash
        self._db.flush()


# ---------------------------------------------------------------------------
# MOV code service
# ---------------------------------------------------------------------------

_SITE_CODE_RE = re.compile(r"[^A-Z0-9]")


def _normalize_site(site_code: str) -> str:
    cleaned = _SITE_CODE_RE.sub("", site_code.upper())
    return cleaned[:8] or "GLOBAL"


class InventoryMovementCodeService:
    """Reserves MOV document codes for the posting flow."""

    DOCUMENT_TYPE_CODE = "MOV"
    PENDING_CATALOG_DECISION = "PENDIENTE_CATALOGO_DOCUMENTAL"

    def __init__(self, db: Session) -> None:
        self._db = db

    def build_movement_code(
        self,
        *,
        organization_id: UUID,
        site_code: str,
        fiscal_year: int,
        correlative: int,
        site_code_used: bool = True,
    ) -> tuple[str, str]:
        """Return ``(movement_code, normalized_movement_code)``."""

        if site_code_used:
            code = (
                f"{self.DOCUMENT_TYPE_CODE}-{_normalize_site(site_code)}-"
                f"{fiscal_year}-{correlative:06d}"
            )
        else:
            code = (
                f"{self.DOCUMENT_TYPE_CODE}-GLOBAL-{fiscal_year}-{correlative:06d}"
            )
        return code, code

    def build_technical_code(
        self,
        *,
        organization_id: UUID,
        posting_request_id: UUID,
    ) -> tuple[str, str]:
        code = (
            f"MOV-DEV-{organization_id}-{str(posting_request_id).split('-')[0].upper()}"
        )
        return code, code

    def is_code_taken(
        self,
        *,
        organization_id: UUID,
        normalized_movement_code: str,
    ) -> bool:
        stmt = select(InventoryMovementModel.id).where(
            InventoryMovementModel.organization_id == organization_id,
            InventoryMovementModel.normalized_movement_code == normalized_movement_code,
        )
        return self._db.scalars(stmt).first() is not None
