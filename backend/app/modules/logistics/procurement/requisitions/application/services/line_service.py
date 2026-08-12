"""Line service for purchase requisitions — adds, updates, removes lines (Phase 031)."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.logistics.procurement.requisitions.domain.errors.exceptions import (
    PurchaseRequisitionLineNotFound,
    PurchaseRequisitionLineInvalid,
    PurchaseRequisitionConversionMissing,
    PurchaseRequisitionProductInactive,
    PurchaseRequisitionQuantityInvalid,
    PurchaseRequisitionUnitInvalid,
)
from app.modules.logistics.procurement.requisitions.domain.services.services import normalize_quantity
from app.modules.logistics.procurement.requisitions.domain.value_objects.enums import (
    LineStatus,
    RevisionStatus,
)
from app.modules.logistics.procurement.requisitions.infrastructure.persistence.models import (
    PurchaseRequisitionLineModel,
    PurchaseRequisitionRevisionModel,
)
from app.modules.logistics.units.conversion_engine import UnitConversionEngine


class PurchaseRequisitionLineService:
    """Manages product lines within an editable revision.
    
    - Quantities always as Decimal (string input)
    - Units always via FK to units_of_measure (never free text)
    - Conversion always via UnitConversionEngine (no free factors)
    - Snapshots captured at creation time
    """

    def _get_revision_or_404(self, db: Session, revision_id: UUID) -> PurchaseRequisitionRevisionModel:
        rev = db.get(PurchaseRequisitionRevisionModel, revision_id)
        if rev is None:
            raise HTTPException(status_code=404, detail={"code": "REVISION_NOT_FOUND", "revision_id": str(revision_id)})
        return rev

    def _require_editable(self, rev: PurchaseRequisitionRevisionModel) -> None:
        if rev.status != RevisionStatus.EDITABLE:
            raise PurchaseRequisitionLineInvalid(
                f"Revision {rev.id} is not editable (status={rev.status}). "
                "Cannot modify lines of a frozen revision."
            )

    def _resolve_conversion(
        self,
        db: Session,
        product,
        requested_unit_id: UUID,
        requested_qty: Decimal,
    ) -> tuple[Decimal, UUID, UUID | None, Decimal | None]:
        """Returns (base_qty, base_unit_id, rule_id, factor_snapshot)."""
        from app.modules.logistics.units.models import UnitOfMeasureModel, UnitConversionRuleModel

        # Resolve base unit from product.base_unit_code
        base_unit = (
            db.query(UnitOfMeasureModel)
            .filter(UnitOfMeasureModel.code == product.base_unit_code)
            .first()
        )
        if base_unit is None:
            raise PurchaseRequisitionUnitInvalid(f"base_unit_code={product.base_unit_code}")

        # Resolve requested unit
        req_unit = db.get(UnitOfMeasureModel, requested_unit_id)
        if req_unit is None or req_unit.status != "ACTIVE":
            raise PurchaseRequisitionUnitInvalid(requested_unit_id)

        # Same unit — no conversion needed
        if requested_unit_id == base_unit.id:
            return requested_qty, base_unit.id, None, None

        # Look for direct conversion rule
        rule = (
            db.query(UnitConversionRuleModel)
            .filter(
                UnitConversionRuleModel.from_unit_id == requested_unit_id,
                UnitConversionRuleModel.to_unit_id == base_unit.id,
                UnitConversionRuleModel.status == "ACTIVE",
            )
            .first()
        )
        if rule is None:
            raise PurchaseRequisitionConversionMissing(req_unit.code, base_unit.code)

        result = UnitConversionEngine.convert(
            quantity=requested_qty,
            source_code=req_unit.code,
            target_code=base_unit.code,
            effective_factor=Decimal(str(rule.multiplier)),
            path=[req_unit.code, base_unit.code],
        )
        return (
            Decimal(result["rounded_result"]),
            base_unit.id,
            rule.id,
            Decimal(str(rule.multiplier)),
        )

    # ------------------------------------------------------------------ #
    # Add line                                                             #
    # ------------------------------------------------------------------ #

    def add_line(
        self,
        db: Session,
        revision_id: UUID,
        org_id: UUID,
        user_id: UUID,
        product_id: UUID,
        requested_quantity_str: str,
        requested_unit_id: UUID,
        line_justification: str | None = None,
        notes: str | None = None,
        manufacturer_reference: str | None = None,
        preferred_brand_reference: str | None = None,
        required_date: object = None,
        destination_warehouse_id: UUID | None = None,
        specifications: dict | None = None,
        priority_override: str | None = None,
    ) -> PurchaseRequisitionLineModel:
        from app.modules.logistics.products.models import ProductModel

        rev = self._get_revision_or_404(db, revision_id)
        self._require_editable(rev)

        # Validate product — must be ACTIVE and belong to same org
        product = (
            db.query(ProductModel)
            .filter(ProductModel.id == product_id)
            .first()
        )
        if product is None:
            raise HTTPException(status_code=404, detail={"code": "PRODUCT_NOT_FOUND"})
        if product.status not in ("ACTIVE",) or product.lifecycle_status != "ACTIVE":
            raise PurchaseRequisitionProductInactive(product_id)
        if str(product.organization_id) != str(org_id):
            raise HTTPException(
                status_code=403,
                detail={"code": "PRODUCT_ORG_MISMATCH", "product_id": str(product_id)},
            )

        # Parse quantity
        try:
            qty = normalize_quantity(requested_quantity_str)
        except ValueError as e:
            raise PurchaseRequisitionQuantityInvalid(requested_quantity_str, str(e))

        # Resolve conversion
        base_qty, base_unit_id, rule_id, factor = self._resolve_conversion(
            db, product, requested_unit_id, qty
        )

        # Compute next line number
        max_line = (
            db.query(PurchaseRequisitionLineModel.line_number)
            .filter(
                PurchaseRequisitionLineModel.requisition_revision_id == revision_id,
                PurchaseRequisitionLineModel.status == LineStatus.ACTIVE,
            )
            .order_by(PurchaseRequisitionLineModel.line_number.desc())
            .first()
        )
        next_line_number = (max_line[0] + 1) if max_line else 1

        line = PurchaseRequisitionLineModel(
            requisition_revision_id=revision_id,
            line_number=next_line_number,
            product_id=product_id,
            product_version_id=product.active_version_id,
            sku_snapshot=product.sku,
            product_name_snapshot=product.name,
            product_description_snapshot=product.description,
            requested_quantity=qty,
            requested_unit_id=requested_unit_id,
            base_quantity=base_qty,
            base_unit_id=base_unit_id,
            conversion_rule_id=rule_id,
            conversion_factor_snapshot=factor,
            required_date=required_date,
            destination_warehouse_id=destination_warehouse_id,
            line_justification=line_justification,
            specifications=specifications,
            manufacturer_reference=manufacturer_reference,
            preferred_brand_reference=preferred_brand_reference,
            priority_override=priority_override,
            notes=notes,
            status=LineStatus.ACTIVE,
            created_by=user_id,
        )
        db.add(line)
        db.flush()

        # Update line count in revision
        rev.line_count = (
            db.query(PurchaseRequisitionLineModel)
            .filter(
                PurchaseRequisitionLineModel.requisition_revision_id == revision_id,
                PurchaseRequisitionLineModel.status == LineStatus.ACTIVE,
            )
            .count()
        )

        return line

    # ------------------------------------------------------------------ #
    # Update line                                                          #
    # ------------------------------------------------------------------ #

    def update_line(
        self,
        db: Session,
        line_id: UUID,
        org_id: UUID,
        user_id: UUID,
        **fields,
    ) -> PurchaseRequisitionLineModel:
        line = db.get(PurchaseRequisitionLineModel, line_id)
        if line is None:
            raise PurchaseRequisitionLineNotFound(line_id)
        rev = self._get_revision_or_404(db, line.requisition_revision_id)
        self._require_editable(rev)

        if "requested_quantity_str" in fields or "requested_unit_id" in fields:
            from app.modules.logistics.products.models import ProductModel
            product = db.get(ProductModel, line.product_id)
            qty_str = fields.pop("requested_quantity_str", str(line.requested_quantity))
            unit_id = fields.pop("requested_unit_id", line.requested_unit_id)
            try:
                qty = normalize_quantity(qty_str)
            except ValueError as e:
                raise PurchaseRequisitionQuantityInvalid(qty_str, str(e))
            base_qty, base_unit_id, rule_id, factor = self._resolve_conversion(db, product, unit_id, qty)
            line.requested_quantity = qty
            line.requested_unit_id = unit_id
            line.base_quantity = base_qty
            line.base_unit_id = base_unit_id
            line.conversion_rule_id = rule_id
            line.conversion_factor_snapshot = factor

        for field, value in fields.items():
            if hasattr(line, field):
                setattr(line, field, value)
        line.row_version += 1
        return line

    # ------------------------------------------------------------------ #
    # Remove (soft delete)                                                 #
    # ------------------------------------------------------------------ #

    def remove_line(self, db: Session, line_id: UUID, org_id: UUID, user_id: UUID) -> PurchaseRequisitionLineModel:
        line = db.get(PurchaseRequisitionLineModel, line_id)
        if line is None:
            raise PurchaseRequisitionLineNotFound(line_id)
        rev = self._get_revision_or_404(db, line.requisition_revision_id)
        self._require_editable(rev)

        line.status = LineStatus.REMOVED
        # Update line count
        rev.line_count = max(0, (rev.line_count or 1) - 1)
        return line

    # ------------------------------------------------------------------ #
    # List                                                                 #
    # ------------------------------------------------------------------ #

    def get_lines(self, db: Session, revision_id: UUID) -> list[PurchaseRequisitionLineModel]:
        return (
            db.query(PurchaseRequisitionLineModel)
            .filter(
                PurchaseRequisitionLineModel.requisition_revision_id == revision_id,
                PurchaseRequisitionLineModel.status == LineStatus.ACTIVE,
            )
            .order_by(PurchaseRequisitionLineModel.line_number)
            .all()
        )

    # ------------------------------------------------------------------ #
    # Reorder                                                              #
    # ------------------------------------------------------------------ #

    def reorder_lines(
        self, db: Session, revision_id: UUID, line_ids: list[UUID], user_id: UUID
    ) -> list[PurchaseRequisitionLineModel]:
        rev = self._get_revision_or_404(db, revision_id)
        self._require_editable(rev)

        lines = {
            str(line.id): line
            for line in self.get_lines(db, revision_id)
        }
        updated = []
        for new_number, lid in enumerate(line_ids, start=1):
            line = lines.get(str(lid))
            if line is None:
                raise PurchaseRequisitionLineNotFound(lid)
            line.line_number = new_number
            updated.append(line)
        return updated


purchase_requisition_line_service = PurchaseRequisitionLineService()
