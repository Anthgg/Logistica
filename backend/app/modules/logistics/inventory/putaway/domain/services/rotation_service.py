"""Phase 043 — Rotation score calculation service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..enums import RotationStrategy
from ...infrastructure.persistence.models import PutawayLocationPlacementProjectionModel


@dataclass
class RotationEvaluation:
    location_id: UUID
    last_putaway_at: datetime | None
    placement_count: int
    days_since_last_putaway: int | None
    rotation_strategy: str
    score: Decimal


class RotationService:
    """Calculates rotation scores based on placement frequency and recency."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def evaluate(
        self,
        location_id: UUID,
        *,
        strategy: str = RotationStrategy.FIFO.value,
        lookback_days: int = 90,
    ) -> RotationEvaluation:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=lookback_days)

        projection = self._db.execute(
            select(PutawayLocationPlacementProjectionModel).where(
                PutawayLocationPlacementProjectionModel.location_id == location_id,
                PutawayLocationPlacementProjectionModel.calculated_at >= cutoff,
            )
        ).scalar_one_or_none()

        if projection is None:
            return RotationEvaluation(
                location_id=location_id,
                last_putaway_at=None,
                placement_count=0,
                days_since_last_putaway=None,
                rotation_strategy=strategy,
                score=Decimal("100"),
            )

        last_putaway = projection.last_putaway_at
        placement_count = projection.placement_count

        if last_putaway:
            days_since = (now - last_putaway).days
        else:
            days_since = None

        score = self._calculate_score(
            strategy=strategy,
            placement_count=placement_count,
            days_since_last=days_since,
            lookback_days=lookback_days,
        )

        return RotationEvaluation(
            location_id=location_id,
            last_putaway_at=last_putaway,
            placement_count=placement_count,
            days_since_last_putaway=days_since,
            rotation_strategy=strategy,
            score=score,
        )

    def _calculate_score(
        self,
        *,
        strategy: str,
        placement_count: int,
        days_since_last: int | None,
        lookback_days: int,
    ) -> Decimal:
        if strategy == RotationStrategy.FIFO.value:
            return self._fifo_score(placement_count, days_since_last, lookback_days)
        elif strategy == RotationStrategy.LIFO.value:
            return self._lifo_score(placement_count, days_since_last, lookback_days)
        elif strategy == RotationStrategy.FEFO.value:
            return self._fefo_score(placement_count, days_since_last, lookback_days)
        else:
            return self._fifo_score(placement_count, days_since_last, lookback_days)

    def _fifo_score(
        self, placement_count: int, days_since_last: int | None, lookback_days: int
    ) -> Decimal:
        if placement_count == 0:
            return Decimal("100")

        if days_since_last is None:
            return Decimal("90")

        recency_factor = Decimal(str(max(0, lookback_days - days_since_last))) / Decimal(str(lookback_days))
        frequency_factor = Decimal(str(min(placement_count, 50))) / Decimal("50")

        score = (recency_factor * Decimal("60") + frequency_factor * Decimal("40"))
        return score.quantize(Decimal("0.01"))

    def _lifo_score(
        self, placement_count: int, days_since_last: int | None, lookback_days: int
    ) -> Decimal:
        if placement_count == 0:
            return Decimal("100")

        if days_since_last is None:
            return Decimal("50")

        recency_factor = Decimal(str(days_since_last)) / Decimal(str(lookback_days))
        frequency_factor = Decimal(str(min(placement_count, 50))) / Decimal("50")

        score = (recency_factor * Decimal("60") + frequency_factor * Decimal("40"))
        return score.quantize(Decimal("0.01"))

    def _fefo_score(
        self, placement_count: int, days_since_last: int | None, lookback_days: int
    ) -> Decimal:
        return self._fifo_score(placement_count, days_since_last, lookback_days)

    def get_placement_history(
        self,
        location_id: UUID,
        *,
        limit: int = 50,
    ) -> list[dict]:
        projections = list(self._db.scalars(
            select(PutawayLocationPlacementProjectionModel).where(
                PutawayLocationPlacementProjectionModel.location_id == location_id
            ).order_by(PutawayLocationPlacementProjectionModel.last_putaway_at.desc())
            .limit(limit)
        ))

        return [
            {
                "product_id": str(p.product_id),
                "quantity": str(p.quantity),
                "base_quantity": str(p.base_quantity),
                "placement_count": p.placement_count,
                "last_putaway_at": p.last_putaway_at.isoformat() if p.last_putaway_at else None,
            }
            for p in projections
        ]
