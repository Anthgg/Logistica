"""Application service for the purchase-order lifecycle."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ApplicationError
from app.database.base import utc_now
from app.modules.logistics.partners.models import (
    BusinessPartnerModel,
    BusinessPartnerRoleModel,
)
from app.modules.logistics.products.models import ProductModel
from app.modules.logistics.purchase_orders.models import (
    PurchaseOrderLineModel,
    PurchaseOrderModel,
)
from app.modules.logistics.purchase_orders.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
)
from app.services.audit_service import AuditService


_MONEY_QUANTUM = Decimal("0.0001")


class PurchaseOrderService:
    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        organization_id: UUID,
        *,
        order_status: str | None = None,
        supplier_id: UUID | None = None,
    ) -> list[PurchaseOrderModel]:
        statement = (
            select(PurchaseOrderModel)
            .where(PurchaseOrderModel.organization_id == organization_id)
            .options(
                selectinload(PurchaseOrderModel.supplier),
                selectinload(PurchaseOrderModel.lines),
            )
            .order_by(PurchaseOrderModel.created_at.desc())
        )
        if order_status:
            statement = statement.where(
                PurchaseOrderModel.status == order_status.strip().upper()
            )
        if supplier_id:
            statement = statement.where(PurchaseOrderModel.supplier_id == supplier_id)
        return list(self.db.scalars(statement).unique().all())

    def get(self, purchase_order_id: UUID, organization_id: UUID) -> PurchaseOrderModel:
        order = self.db.scalar(
            select(PurchaseOrderModel)
            .where(
                and_(
                    PurchaseOrderModel.id == purchase_order_id,
                    PurchaseOrderModel.organization_id == organization_id,
                )
            )
            .options(
                selectinload(PurchaseOrderModel.supplier),
                selectinload(PurchaseOrderModel.lines),
            )
        )
        if not order:
            raise ApplicationError(
                "PURCHASE_ORDER_NOT_FOUND",
                "La orden de compra no existe.",
                404,
            )
        return order

    def create(
        self,
        organization_id: UUID,
        payload: PurchaseOrderCreate,
        actor_id: UUID,
    ) -> PurchaseOrderModel:
        self._require_supplier(organization_id, payload.supplier_id)
        products = self._load_products(
            organization_id,
            [line.product_id for line in payload.lines],
        )
        order = PurchaseOrderModel(
            organization_id=organization_id,
            supplier_id=payload.supplier_id,
            order_number=self._next_order_number(organization_id),
            currency_code=payload.currency_code,
            expected_delivery_date=payload.expected_delivery_date,
            notes=payload.notes,
            status="DRAFT",
            created_by=actor_id,
        )
        self.db.add(order)
        self.db.flush()

        subtotal = Decimal("0")
        tax = Decimal("0")
        for line_number, line_payload in enumerate(payload.lines, start=1):
            product = products[line_payload.product_id]
            line_subtotal = (line_payload.quantity * line_payload.unit_price).quantize(
                _MONEY_QUANTUM,
                rounding=ROUND_HALF_UP,
            )
            line_tax = (
                line_subtotal * line_payload.tax_rate / Decimal("100")
            ).quantize(_MONEY_QUANTUM, rounding=ROUND_HALF_UP)
            self.db.add(
                PurchaseOrderLineModel(
                    purchase_order_id=order.id,
                    line_number=line_number,
                    product_id=product.id,
                    description=line_payload.description or product.name,
                    unit_code=(line_payload.unit_code or product.base_unit_code).upper(),
                    quantity=line_payload.quantity,
                    unit_price=line_payload.unit_price,
                    tax_rate=line_payload.tax_rate,
                    subtotal_amount=line_subtotal,
                    tax_amount=line_tax,
                    total_amount=line_subtotal + line_tax,
                )
            )
            subtotal += line_subtotal
            tax += line_tax

        order.subtotal_amount = subtotal
        order.tax_amount = tax
        order.total_amount = subtotal + tax
        self._audit(order, "logistics.purchase_order.created", actor_id)
        self.db.commit()
        return self.get(order.id, organization_id)

    def update(
        self,
        purchase_order_id: UUID,
        organization_id: UUID,
        payload: PurchaseOrderUpdate,
        actor_id: UUID,
    ) -> PurchaseOrderModel:
        order = self.get(purchase_order_id, organization_id)
        self._require_status(order, {"DRAFT", "APPROVED"}, "actualizar")
        changes = payload.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(order, field, value)
        order.row_version += 1
        self._audit(order, "logistics.purchase_order.updated", actor_id)
        self.db.commit()
        return self.get(order.id, organization_id)

    def approve(
        self,
        purchase_order_id: UUID,
        organization_id: UUID,
        actor_id: UUID,
    ) -> PurchaseOrderModel:
        order = self.get(purchase_order_id, organization_id)
        self._require_status(order, {"DRAFT"}, "aprobar")
        order.status = "APPROVED"
        order.approved_by = actor_id
        order.approved_at = utc_now()
        order.row_version += 1
        self._audit(order, "logistics.purchase_order.approved", actor_id)
        self.db.commit()
        return self.get(order.id, organization_id)

    def issue(
        self,
        purchase_order_id: UUID,
        organization_id: UUID,
        actor_id: UUID,
    ) -> PurchaseOrderModel:
        order = self.get(purchase_order_id, organization_id)
        self._require_status(order, {"DRAFT", "APPROVED"}, "emitir")
        order.status = "ISSUED"
        order.issued_by = actor_id
        order.issued_at = utc_now()
        order.row_version += 1
        self._audit(order, "logistics.purchase_order.issued", actor_id)
        self.db.commit()
        return self.get(order.id, organization_id)

    def cancel(
        self,
        purchase_order_id: UUID,
        organization_id: UUID,
        reason: str,
        actor_id: UUID,
    ) -> PurchaseOrderModel:
        order = self.get(purchase_order_id, organization_id)
        self._require_status(order, {"DRAFT", "APPROVED", "ISSUED"}, "anular")
        order.status = "ANNULLED"
        order.annulled_by = actor_id
        order.annulled_at = utc_now()
        order.annulment_reason = reason
        order.row_version += 1
        self._audit(
            order,
            "logistics.purchase_order.annulled",
            actor_id,
            {"reason": reason},
        )
        self.db.commit()
        return self.get(order.id, organization_id)

    def _next_order_number(self, organization_id: UUID) -> str:
        year = utc_now().year
        prefix = f"OC-{year}-"
        count = self.db.scalar(
            select(func.count(PurchaseOrderModel.id)).where(
                PurchaseOrderModel.organization_id == organization_id,
                PurchaseOrderModel.order_number.like(f"{prefix}%"),
            )
        )
        return f"{prefix}{int(count or 0) + 1:06d}"

    def _require_supplier(self, organization_id: UUID, supplier_id: UUID) -> None:
        supplier = self.db.scalar(
            select(BusinessPartnerModel)
            .join(
                BusinessPartnerRoleModel,
                BusinessPartnerRoleModel.business_partner_id == BusinessPartnerModel.id,
            )
            .where(
                BusinessPartnerModel.id == supplier_id,
                BusinessPartnerModel.organization_id == organization_id,
                BusinessPartnerModel.status == "ACTIVE",
                BusinessPartnerRoleModel.role_type == "SUPPLIER",
                BusinessPartnerRoleModel.status == "ACTIVE",
            )
        )
        if not supplier:
            raise ApplicationError(
                "PURCHASE_ORDER_SUPPLIER_INVALID",
                "El proveedor no existe, no está activo o no tiene el rol SUPPLIER.",
                400,
            )

    def _load_products(
        self,
        organization_id: UUID,
        product_ids: list[UUID],
    ) -> dict[UUID, ProductModel]:
        products = list(
            self.db.scalars(
                select(ProductModel).where(
                    ProductModel.organization_id == organization_id,
                    ProductModel.id.in_(set(product_ids)),
                    ProductModel.status == "ACTIVE",
                )
            ).all()
        )
        by_id = {product.id: product for product in products}
        missing = set(product_ids) - set(by_id)
        if missing:
            raise ApplicationError(
                "PURCHASE_ORDER_PRODUCT_INVALID",
                "La orden contiene productos inexistentes o inactivos.",
                400,
            )
        return by_id

    @staticmethod
    def _require_status(
        order: PurchaseOrderModel,
        allowed: set[str],
        action: str,
    ) -> None:
        if order.status not in allowed:
            raise ApplicationError(
                "PURCHASE_ORDER_INVALID_STATUS",
                f"No se puede {action} una orden en estado {order.status}.",
                409,
            )

    def _audit(
        self,
        order: PurchaseOrderModel,
        event_type: str,
        actor_id: UUID,
        metadata: dict[str, object] | None = None,
    ) -> None:
        AuditService().record(
            self.db,
            event_type,
            user_id=actor_id,
            resource_type="purchase_order",
            resource_id=str(order.id),
            event_metadata={
                "order_number": order.order_number,
                "status": order.status,
                **(metadata or {}),
            },
        )
