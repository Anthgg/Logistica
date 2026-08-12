"""FastAPI Router for Phase 023 — Product Catalog Master Data."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.audit_service import AuditService
from app.modules.logistics.auth_dependencies import require_permission, resolve_organization_id
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.products.brand_service import ProductBrandService
from app.modules.logistics.products.category_service import ProductCategoryService
from app.modules.logistics.products.compatibility_evaluator import EvaluateProductLocationCompatibility
from app.modules.logistics.products.identifier_service import ProductIdentifierService
from app.modules.logistics.products.models import ProductModel
from app.modules.logistics.products.product_service import ProductService
from app.modules.logistics.products.profile_policy_service import ProductProfileAndPolicyService
from app.modules.logistics.products.schemas import (
    ProductBrandCreate,
    ProductBrandResponse,
    ProductCategoryCreate,
    ProductCategoryResponse,
    ProductCreate,
    ProductDetailResponse,
    ProductIdentifierCreate,
    ProductIdentifierResponse,
    ProductListResponse,
    ProductLocationCompatibilityRequest,
    ProductLocationCompatibilityResponse,
    ProductPhysicalProfileResponse,
    ProductPhysicalProfileUpdate,
    ProductResponse,
    ProductSKUChangeRequest,
    ProductStatusChangeRequest,
    ProductStorageConditionCreate,
    ProductStorageConditionResponse,
    ProductTrackingPolicyResponse,
    ProductTrackingPolicyUpdate,
    ProductVersionResponse,
)
from app.modules.logistics.products.version_service import ProductVersionService
from app.modules.logistics.warehouses.models import WarehouseLocationModel, WarehouseLocationRestrictionModel

products_router = APIRouter(prefix="/products", tags=["Product Catalog"])
categories_router = APIRouter(prefix="/product-categories", tags=["Product Categories"])
brands_router = APIRouter(prefix="/product-brands", tags=["Product Brands"])


# --- CATEGORIES ENDPOINTS ---
@categories_router.post("", response_model=ProductCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: ProductCategoryCreate,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.product_categories.create")
    ),
):
    service = ProductCategoryService(db)
    cat = service.create_category(
        organization_id=resolve_organization_id(principal),
        code=payload.code,
        name=payload.name,
        description=payload.description,
        parent_category_id=payload.parent_category_id,
        user_id=principal.user_id,
    )
    AuditService().record(
        database=db,
        event_type="logistics.product_category.created",
        user_id=principal.user_id,
        resource_type="product_category",
        resource_id=str(cat.id),
        event_metadata={"code": cat.code, "name": cat.name, "path": cat.hierarchy_path},
    )
    return cat


@categories_router.get("/tree")
def get_category_tree(
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.product_categories.read")
    ),
):
    service = ProductCategoryService(db)
    return service.get_category_tree(resolve_organization_id(principal))


@categories_router.get("", response_model=List[ProductCategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.product_categories.read")
    ),
):
    service = ProductCategoryService(db)
    return service.list_categories(resolve_organization_id(principal))


# --- BRANDS ENDPOINTS ---
@brands_router.post("", response_model=ProductBrandResponse, status_code=status.HTTP_201_CREATED)
def create_brand(
    payload: ProductBrandCreate,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.product_brands.create")),
):
    service = ProductBrandService(db)
    brand = service.create_brand(
        organization_id=resolve_organization_id(principal),
        code=payload.code,
        name=payload.name,
        description=payload.description,
        manufacturer_name=payload.manufacturer_name,
        country_code=payload.country_code,
        user_id=principal.user_id,
    )
    AuditService().record(
        database=db,
        event_type="logistics.product_brand.created",
        user_id=principal.user_id,
        resource_type="product_brand",
        resource_id=str(brand.id),
        event_metadata={"code": brand.code, "name": brand.name},
    )
    return brand


@brands_router.get("", response_model=List[ProductBrandResponse])
def list_brands(
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.product_brands.read")),
):
    service = ProductBrandService(db)
    return service.list_brands(resolve_organization_id(principal))


# --- PRODUCTS ENDPOINTS ---
@products_router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.products.create")),
):
    service = ProductService(db)
    product = service.create_product(
        organization_id=resolve_organization_id(principal),
        sku=payload.sku,
        name=payload.name,
        category_id=payload.category_id,
        brand_id=payload.brand_id,
        product_type=payload.product_type,
        base_unit_code=payload.base_unit_code,
        short_name=payload.short_name,
        description=payload.description,
        user_id=principal.user_id,
    )
    AuditService().record(
        database=db,
        event_type="logistics.product.created",
        user_id=principal.user_id,
        resource_type="product",
        resource_id=str(product.id),
        event_metadata={"sku": product.sku, "name": product.name},
    )
    return product


@products_router.get("", response_model=ProductListResponse)
def list_products(
    search: Optional[str] = Query(None),
    category_id: Optional[UUID] = Query(None),
    brand_id: Optional[UUID] = Query(None),
    product_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.products.read")),
):
    service = ProductService(db)
    items, total = service.search_products(
        organization_id=resolve_organization_id(principal),
        search=search,
        category_id=category_id,
        brand_id=brand_id,
        product_type=product_type,
        status=status,
        page=page,
        page_size=page_size,
    )
    return ProductListResponse(items=items, total=total, page=page, page_size=page_size)


@products_router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product_detail(
    product_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.products.read")),
):
    return _get_product_for_organization(
        db,
        product_id,
        resolve_organization_id(principal),
    )


@products_router.post("/{product_id}/sku", response_model=ProductResponse)
def change_product_sku(
    product_id: UUID,
    payload: ProductSKUChangeRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.products.update")),
):
    _get_product_for_organization(db, product_id, resolve_organization_id(principal))
    service = ProductService(db)
    product = service.change_sku(
        product_id,
        payload.new_sku,
        payload.reason,
        user_id=principal.user_id,
    )
    AuditService().record(
        database=db,
        event_type="logistics.product.SKU_changed",
        user_id=principal.user_id,
        resource_type="product",
        resource_id=str(product.id),
        event_metadata={"new_sku": product.sku, "reason": payload.reason},
    )
    return product


@products_router.post("/{product_id}/status", response_model=ProductResponse)
def change_product_status(
    product_id: UUID,
    payload: ProductStatusChangeRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.products.activate")),
):
    _get_product_for_organization(db, product_id, resolve_organization_id(principal))
    service = ProductService(db)
    product = service.change_status(
        product_id,
        payload.target_status,
        payload.reason,
        user_id=principal.user_id,
    )
    AuditService().record(
        database=db,
        event_type="logistics.product.activated" if payload.target_status == "ACTIVE" else "logistics.product.updated",
        user_id=principal.user_id,
        resource_type="product",
        resource_id=str(product.id),
        event_metadata={"target_status": payload.target_status, "reason": payload.reason},
    )
    return product


@products_router.get("/{product_id}/versions", response_model=List[ProductVersionResponse])
def list_product_versions(
    product_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.products.read")),
):
    _get_product_for_organization(db, product_id, resolve_organization_id(principal))
    service = ProductVersionService(db)
    return service.list_versions(product_id)


# --- IDENTIFIERS ---
@products_router.post("/{product_id}/identifiers", response_model=ProductIdentifierResponse, status_code=status.HTTP_201_CREATED)
def add_product_identifier(
    product_id: UUID,
    payload: ProductIdentifierCreate,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.product_identifiers.create")
    ),
):
    organization_id = resolve_organization_id(principal)
    _get_product_for_organization(db, product_id, organization_id)
    service = ProductIdentifierService(db)
    ident = service.add_identifier(
        organization_id=organization_id,
        product_id=product_id,
        identifier_type=payload.identifier_type,
        value=payload.value,
        is_primary=payload.is_primary,
        symbology=payload.symbology,
        issuer=payload.issuer,
        user_id=principal.user_id,
    )
    AuditService().record(
        database=db,
        event_type="logistics.product_identifier.created",
        user_id=principal.user_id,
        resource_type="product_identifier",
        resource_id=str(ident.id),
        event_metadata={"type": ident.identifier_type, "value": ident.normalized_value},
    )
    return ident


@products_router.get("/identifiers/{identifier_id}/barcode")
def get_barcode_png(
    identifier_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.product_identifiers.read")
    ),
):
    from app.modules.logistics.products.models import ProductIdentifierModel

    organization_id = resolve_organization_id(principal)
    identifier = db.get(ProductIdentifierModel, identifier_id)
    if not identifier or identifier.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Identifier not found.")
    service = ProductIdentifierService(db)
    return service.render_barcode_png(identifier_id)


# --- PHYSICAL PROFILE & POLICIES ---
@products_router.put("/{product_id}/physical-profile", response_model=ProductPhysicalProfileResponse)
def update_physical_profile(
    product_id: UUID,
    payload: ProductPhysicalProfileUpdate,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.products.update")),
):
    _get_product_for_organization(db, product_id, resolve_organization_id(principal))
    service = ProductProfileAndPolicyService(db)
    prof = service.update_physical_profile(
        product_id=product_id,
        net_weight_value=payload.net_weight_value,
        net_weight_unit=payload.net_weight_unit,
        gross_weight_value=payload.gross_weight_value,
        gross_weight_unit=payload.gross_weight_unit,
        length_value=payload.length_value,
        width_value=payload.width_value,
        height_value=payload.height_value,
        dimension_unit=payload.dimension_unit,
        reported_volume_value=payload.reported_volume_value,
        volume_unit=payload.volume_unit,
        measurement_source=payload.measurement_source,
        user_id=principal.user_id,
    )
    return prof


@products_router.put("/{product_id}/tracking-policy", response_model=ProductTrackingPolicyResponse)
def update_tracking_policy(
    product_id: UUID,
    payload: ProductTrackingPolicyUpdate,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.product_tracking_policies.manage")
    ),
):
    _get_product_for_organization(db, product_id, resolve_organization_id(principal))
    service = ProductProfileAndPolicyService(db)
    pol = service.update_tracking_policy(
        product_id=product_id,
        tracking_type=payload.tracking_type,
        lot_control=payload.lot_control,
        serial_control=payload.serial_control,
        expiration_control=payload.expiration_control,
        manufacturing_date_control=payload.manufacturing_date_control,
        best_before_control=payload.best_before_control,
        minimum_shelf_life_days=payload.minimum_shelf_life_days,
        total_shelf_life_days=payload.total_shelf_life_days,
        user_id=principal.user_id,
    )
    return pol


@products_router.post("/{product_id}/storage-conditions", response_model=ProductStorageConditionResponse, status_code=status.HTTP_201_CREATED)
def add_storage_condition(
    product_id: UUID,
    payload: ProductStorageConditionCreate,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.product_storage_conditions.manage")
    ),
):
    _get_product_for_organization(db, product_id, resolve_organization_id(principal))
    service = ProductProfileAndPolicyService(db)
    cond = service.add_storage_condition(
        product_id=product_id,
        condition_type=payload.condition_type,
        minimum_value=payload.minimum_value,
        maximum_value=payload.maximum_value,
        unit_code=payload.unit_code,
        severity=payload.severity,
        handling_instruction=payload.handling_instruction,
        user_id=principal.user_id,
    )
    return cond


@products_router.post("/{product_id}/location-compatibility", response_model=ProductLocationCompatibilityResponse)
def evaluate_location_compatibility(
    product_id: UUID,
    payload: ProductLocationCompatibilityRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.products.read")),
):
    organization_id = resolve_organization_id(principal)
    product = _get_product_for_organization(db, product_id, organization_id)

    loc = db.get(WarehouseLocationModel, payload.warehouse_location_id)
    if not loc or loc.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse location not found.")

    # Fetch conditions & restrictions
    storage_conds = [
        {"condition_type": sc.condition_type, "severity": sc.severity}
        for sc in product.storage_conditions
    ]
    handling_conds = [
        {"condition_type": hc.condition_type}
        for hc in product.handling_conditions
    ]

    loc_dict = {
        "location_type": loc.location_type,
        "status": loc.status,
    }

    restrictions = list(db.scalars(
        select(WarehouseLocationRestrictionModel).where(WarehouseLocationRestrictionModel.location_id == loc.id)
    ).all())
    loc_restr = [
        {"restriction_type": r.restriction_type, "severity": r.severity}
        for r in restrictions
    ]

    res = EvaluateProductLocationCompatibility.evaluate(
        product_dict={"id": str(product.id)},
        storage_conditions=storage_conds,
        handling_conditions=handling_conds,
        location_dict=loc_dict,
        location_restrictions=loc_restr,
    )
    return res


def _get_product_for_organization(
    db: Session,
    product_id: UUID,
    organization_id: UUID,
) -> ProductModel:
    product = db.get(ProductModel, product_id)
    if not product or product.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product
