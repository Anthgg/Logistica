"""Integration coverage for the purchase-order lifecycle."""

from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.exceptions import ApplicationError
from app.models.organization import Organization
from app.models.user import User
from app.modules.logistics.partners.models import (
    BusinessPartnerModel,
    BusinessPartnerRoleModel,
)
from app.modules.logistics.products.models import ProductCategoryModel, ProductModel
from app.modules.logistics.purchase_orders.schemas import (
    PurchaseOrderCancel,
    PurchaseOrderCreate,
    PurchaseOrderLineCreate,
)
from app.modules.logistics.purchase_orders.service import PurchaseOrderService


def test_purchase_order_create_approve_issue_and_cancel(database):
    actor = User(
        id=uuid4(),
        email=f"buyer-{uuid4().hex[:8]}@example.com",
        password_hash="not-used-in-this-test",
        full_name="Comprador de prueba",
        role="admin",
        is_active=True,
    )
    organization = Organization(
        id=uuid4(),
        code=f"ORG-{uuid4().hex[:6].upper()}",
        name="Organización compras",
        country_code="PE",
        status="active",
    )
    supplier = BusinessPartnerModel(
        id=uuid4(),
        organization_id=organization.id,
        partner_code=f"SUP-{uuid4().hex[:6].upper()}",
        normalized_partner_code=f"SUP-{uuid4().hex[:6].upper()}",
        legal_name="Proveedor de prueba S.A.C.",
        person_type="LEGAL_ENTITY",
        country_code="PE",
        status="ACTIVE",
    )
    supplier_role = BusinessPartnerRoleModel(
        id=uuid4(),
        business_partner_id=supplier.id,
        role_type="SUPPLIER",
        status="ACTIVE",
    )
    category = ProductCategoryModel(
        id=uuid4(),
        organization_id=organization.id,
        code=f"CAT-{uuid4().hex[:4].upper()}",
        name="Categoría de prueba",
        hierarchy_path=f"CAT-{uuid4().hex[:4].upper()}",
    )
    product = ProductModel(
        id=uuid4(),
        organization_id=organization.id,
        sku=f"SKU-{uuid4().hex[:6].upper()}",
        normalized_sku=f"SKU-{uuid4().hex[:6].upper()}",
        name="Producto de prueba",
        category_id=category.id,
        product_type="PHYSICAL_GOOD",
        base_unit_code="UND",
        status="ACTIVE",
    )
    database.add_all(
        [actor, organization, supplier, supplier_role, category, product]
    )
    database.commit()

    service = PurchaseOrderService(database)
    order = service.create(
        organization.id,
        PurchaseOrderCreate(
            supplier_id=supplier.id,
            lines=[
                PurchaseOrderLineCreate(
                    product_id=product.id,
                    quantity=Decimal("2"),
                    unit_price=Decimal("50"),
                    tax_rate=Decimal("18"),
                )
            ],
        ),
        actor.id,
    )

    assert order.status == "DRAFT"
    assert order.subtotal_amount == Decimal("100.0000")
    assert order.tax_amount == Decimal("18.0000")
    assert order.total_amount == Decimal("118.0000")
    assert len(order.lines) == 1

    approved = service.approve(order.id, organization.id, actor.id)
    assert approved.status == "APPROVED"
    issued = service.issue(order.id, organization.id, actor.id)
    assert issued.status == "ISSUED"
    cancelled = service.cancel(
        order.id,
        organization.id,
        PurchaseOrderCancel(reason="Proveedor no podrá cumplir la fecha.").reason,
        actor.id,
    )
    assert cancelled.status == "ANNULLED"

    with pytest.raises(ApplicationError) as exc_info:
        service.approve(order.id, organization.id, actor.id)
    assert exc_info.value.code == "PURCHASE_ORDER_INVALID_STATUS"
