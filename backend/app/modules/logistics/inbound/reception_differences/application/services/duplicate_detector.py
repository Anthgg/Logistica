from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.errors import reception_difference_error
from ...infrastructure.persistence.models import (
    ReceptionDifferenceCaseModel,
    ReceptionDifferenceItemModel,
)


class ReceptionDifferenceDuplicateDetector:
    EXACT = "EXACT_DUPLICATE"
    POSSIBLE = "POSSIBLE_DUPLICATE"
    NONE = "NO_DUPLICATE"

    def __init__(self, db: Session):
        self.db = db

    def detect(self, case_id: UUID, item_data: dict, organization_id: UUID) -> str:
        case = self.db.scalar(select(ReceptionDifferenceCaseModel).where(
            ReceptionDifferenceCaseModel.id == case_id,
            ReceptionDifferenceCaseModel.organization_id == organization_id,
        ))
        if not case:
            raise reception_difference_error("ReceptionDifferenceCaseNotFound", "Caso de diferencia no encontrado.", 404)

        difference_type = item_data.get("difference_type")
        product_id = item_data.get("product_id")
        expected_quantity = item_data.get("expected_quantity")
        observed_quantity = item_data.get("observed_quantity")

        existing_items = list(self.db.scalars(
            select(ReceptionDifferenceItemModel).where(
                ReceptionDifferenceItemModel.difference_case_id == case_id,
                ReceptionDifferenceItemModel.status.notin_(["SUPERSEDED", "CLOSED"]),
            )
        ))

        for item in existing_items:
            type_match = item.difference_type == difference_type
            product_match = True
            if product_id is not None:
                item_pid = str(item.product_id) if item.product_id else None
                product_match = item_pid == str(product_id)
            expected_match = True
            if expected_quantity is not None and item.expected_quantity is not None:
                expected_match = Decimal(str(expected_quantity)) == Decimal(str(item.expected_quantity))
            observed_match = True
            if observed_quantity is not None and item.observed_quantity is not None:
                observed_match = Decimal(str(observed_quantity)) == Decimal(str(item.observed_quantity))

            if type_match and product_match and expected_match and observed_match:
                return self.EXACT

        for item in existing_items:
            type_match = item.difference_type == difference_type
            product_match = True
            if product_id is not None:
                item_pid = str(item.product_id) if item.product_id else None
                product_match = item_pid == str(product_id)
            if type_match and product_match:
                return self.POSSIBLE

        return self.NONE
