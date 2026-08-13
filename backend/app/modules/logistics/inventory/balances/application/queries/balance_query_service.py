"""Phase 045 — Balance Query Service.

Provides real read queries for active materialized position balances (is_active_projection = TRUE).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.balances.domain.services.availability_provider import (
    InventoryBalanceAvailabilityProvider,
)
from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
    InventoryPositionBalanceModel,
)


class BalanceQueryService:
    """Read query service for inventory position balances (Phase 045)."""

    def __init__(
        self,
        availability_provider: InventoryBalanceAvailabilityProvider | None = None,
    ) -> None:
        self.availability_provider = (
            availability_provider or InventoryBalanceAvailabilityProvider()
        )

    def get_active_balances_summary(
        self,
        db: Session,
        organization_id: UUID,
        warehouse_id: UUID | None = None,
        product_id: UUID | None = None,
    ) -> dict[str, Decimal]:
        """Queries active materialized position balances (is_active_projection=True) and computes metrics."""
        query = (
            select(InventoryPositionBalanceModel)
            .where(InventoryPositionBalanceModel.organization_id == organization_id)
            .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
        )
        if warehouse_id:
            query = query.where(InventoryPositionBalanceModel.warehouse_id == warehouse_id)
        if product_id:
            query = query.where(InventoryPositionBalanceModel.product_id == product_id)

        rows = list(db.scalars(query))
        position_dicts: list[dict[str, Any]] = [
            {
                "quantity": row.quantity,
                "availability_state": row.availability_state,
                "quality_state": row.quality_state,
                "transit_state": row.transit_state,
                "damage_state": row.damage_state,
                "expiration_state": row.expiration_state,
            }
            for row in rows
        ]
        return self.availability_provider.get_summary_metrics(position_dicts)

    def get_active_position_balance_by_position_id(
        self,
        db: Session,
        organization_id: UUID,
        inventory_position_id: UUID,
    ) -> InventoryPositionBalanceModel | None:
        """Finds the active position balance for a given inventory_position_id."""
        query = (
            select(InventoryPositionBalanceModel)
            .where(
                InventoryPositionBalanceModel.inventory_position_id == inventory_position_id
            )
            .where(InventoryPositionBalanceModel.organization_id == organization_id)
            .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
        )
        return db.scalars(query).first()
