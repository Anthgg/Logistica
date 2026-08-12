"""FastAPI REST endpoints for Phase 024 UOM Engine."""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission, resolve_organization_id
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.products.models import ProductModel
from app.modules.logistics.units.comparison_service import QuantityComparisonService
from app.modules.logistics.units.conversion_engine import UnitConversionEngine
from app.modules.logistics.units.decomposition_service import QuantityDecompositionService
from app.modules.logistics.units.path_resolver import ConversionPathResolver
from app.modules.logistics.units.schemas import (
    MeasurementDimensionResponse,
    ProductPackagingDefinitionRequest,
    ProductPackagingDefinitionResponse,
    ProductUnitConfigurationRequest,
    ProductUnitConfigurationResponse,
    UnitCompareRequest,
    UnitCompareResponse,
    UnitConversionEvaluateRequest,
    UnitConversionEvaluateResponse,
    UnitConversionRuleCreateRequest,
    UnitConversionRuleResponse,
    UnitCreateRequest,
    UnitDecomposeRequest,
    UnitDecomposeResponse,
    UnitResponse,
)
from app.modules.logistics.units.unit_service import UnitCatalogService
from app.services.audit_service import AuditService

dimensions_router = APIRouter(prefix="/measurement-dimensions", tags=["Measurement Dimensions"])
units_router = APIRouter(prefix="/units", tags=["Units of Measure"])
conversion_rules_router = APIRouter(prefix="/unit-conversion-rules", tags=["Unit Conversion Rules"])
conversion_engine_router = APIRouter(prefix="/unit-conversions", tags=["Unit Conversion Engine"])
product_units_router = APIRouter(prefix="/products", tags=["Product Unit Configurations"])


# --- Measurement Dimensions ---

@dimensions_router.get("", response_model=List[MeasurementDimensionResponse])
def list_dimensions(
    db: Session = Depends(get_db),
    _principal: LogisticsPrincipal = Depends(require_permission("logistics.units.read")),
):
    service = UnitCatalogService(db)
    return service.list_dimensions()


# --- Units of Measure ---

@units_router.get("", response_model=List[UnitResponse])
def list_units(
    dimension_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.units.read")),
):
    service = UnitCatalogService(db)
    return service.list_units(
        dimension_id=dimension_id,
        organization_id=resolve_organization_id(principal),
    )


@units_router.post("", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
def create_unit(
    req: UnitCreateRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.units.create")),
):
    service = UnitCatalogService(db)

    unit = service.create_unit(
        dimension_id=req.dimension_id,
        code=req.code,
        name=req.name,
        symbol=req.symbol,
        unit_kind=req.unit_kind,
        organization_id=resolve_organization_id(principal),
        plural_name=req.plural_name,
        decimal_precision=req.decimal_precision,
        integer_only=req.integer_only,
        user_id=principal.user_id,
    )

    AuditService().record(
        database=db,
        event_type="logistics.unit.created",
        user_id=principal.user_id,
        resource_type="unit_of_measure",
        resource_id=str(unit.id),
        event_metadata={"code": unit.code, "dimension_id": str(unit.dimension_id)},
    )
    return unit


# --- Conversion Rules ---

@conversion_rules_router.post("", response_model=UnitConversionRuleResponse, status_code=status.HTTP_201_CREATED)
def create_conversion_rule(
    req: UnitConversionRuleCreateRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.unit_conversions.create")
    ),
):
    service = UnitCatalogService(db)

    mult = Decimal(req.multiplier)
    rule = service.create_conversion_rule(
        source_unit_id=req.source_unit_id,
        target_unit_id=req.target_unit_id,
        multiplier=mult,
        organization_id=resolve_organization_id(principal),
        product_id=req.product_id,
        allows_inverse=req.allows_inverse,
        rounding_policy=req.rounding_policy,
        user_id=principal.user_id,
    )

    AuditService().record(
        database=db,
        event_type="logistics.unit_conversion_rule.activated",
        user_id=principal.user_id,
        resource_type="unit_conversion_rule",
        resource_id=str(rule.id),
        event_metadata={"multiplier": str(mult), "scope": rule.conversion_scope},
    )
    return rule


# --- Product Unit Configurations & Packaging ---

@product_units_router.get("/{product_id}/unit-configuration", response_model=ProductUnitConfigurationResponse)
def get_product_unit_configuration(
    product_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.product_units.read")),
):
    from app.modules.logistics.units.models import ProductUnitConfigurationModel

    _require_product(db, product_id, resolve_organization_id(principal))
    cfg = db.scalar(
        select(ProductUnitConfigurationModel).where(
            ProductUnitConfigurationModel.product_id == product_id
        )
    )
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit configuration for product not found.")
    return cfg


@product_units_router.put("/{product_id}/unit-configuration", response_model=ProductUnitConfigurationResponse)
def configure_product_units(
    product_id: UUID,
    req: ProductUnitConfigurationRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.product_units.manage")),
):
    _require_product(db, product_id, resolve_organization_id(principal))
    service = UnitCatalogService(db)

    config = service.configure_product_units(
        product_id=product_id,
        base_unit_id=req.base_unit_id,
        purchase_unit_id=req.purchase_unit_id,
        reception_unit_id=req.reception_unit_id,
        storage_unit_id=req.storage_unit_id,
        picking_unit_id=req.picking_unit_id,
        dispatch_unit_id=req.dispatch_unit_id,
        user_id=principal.user_id,
    )

    AuditService().record(
        database=db,
        event_type="logistics.product_unit_configuration.updated",
        user_id=principal.user_id,
        resource_type="product_unit_configuration",
        resource_id=str(config.id),
        event_metadata={"product_id": str(product_id), "base_unit_id": str(req.base_unit_id)},
    )
    return config


@product_units_router.post("/{product_id}/packaging-definitions", response_model=ProductPackagingDefinitionResponse, status_code=status.HTTP_201_CREATED)
def add_product_packaging(
    product_id: UUID,
    req: ProductPackagingDefinitionRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.product_packaging.manage")
    ),
):
    _require_product(db, product_id, resolve_organization_id(principal))
    service = UnitCatalogService(db)
    qty = Decimal(req.contained_quantity)
    g_weight = Decimal(req.gross_weight) if req.gross_weight else None

    pkg = service.add_product_packaging(
        product_id=product_id,
        packaging_unit_id=req.packaging_unit_id,
        contained_unit_id=req.contained_unit_id,
        contained_quantity=qty,
        level_order=req.level_order,
        package_type=req.package_type,
        gross_weight=g_weight,
        user_id=principal.user_id,
    )

    AuditService().record(
        database=db,
        event_type="logistics.product_packaging.activated",
        user_id=principal.user_id,
        resource_type="product_packaging_definition",
        resource_id=str(pkg.id),
        event_metadata={"product_id": str(product_id), "contained_quantity": str(qty)},
    )
    return pkg


# --- Conversion Engine & Evaluation ---

@conversion_engine_router.post("/evaluate", response_model=UnitConversionEvaluateResponse)
def evaluate_conversion(
    req: UnitConversionEvaluateRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.unit_conversions.evaluate")
    ),
):
    qty = Decimal(req.quantity)
    organization_id = resolve_organization_id(principal)

    # Resolve unit codes to IDs
    from app.modules.logistics.units.models import UnitOfMeasureModel

    visible_unit = or_(
        UnitOfMeasureModel.organization_id.is_(None),
        UnitOfMeasureModel.organization_id == organization_id,
    )
    stmt_src = select(UnitOfMeasureModel).where(
        UnitOfMeasureModel.normalized_code == req.source_unit_code.upper(),
        visible_unit,
    )
    stmt_tgt = select(UnitOfMeasureModel).where(
        UnitOfMeasureModel.normalized_code == req.target_unit_code.upper(),
        visible_unit,
    )

    src_unit = db.scalar(stmt_src)
    tgt_unit = db.scalar(stmt_tgt)

    if not src_unit or not tgt_unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source or target unit of measure not found.")

    resolver = ConversionPathResolver(db)
    factor, path, rules = resolver.resolve_path(
        source_unit_id=src_unit.id,
        target_unit_id=tgt_unit.id,
        organization_id=organization_id,
        product_id=req.product_id,
    )

    res = UnitConversionEngine.convert(
        quantity=qty,
        source_code=req.source_unit_code.upper(),
        target_code=req.target_unit_code.upper(),
        effective_factor=factor,
        path=path,
        precision=tgt_unit.decimal_precision,
        rounding_policy=req.rounding_policy,
        integer_only_target=tgt_unit.integer_only,
    )

    AuditService().record(
        database=db,
        event_type="logistics.unit_conversion.evaluated",
        user_id=principal.user_id,
        resource_type="unit_conversion",
        resource_id=f"{req.source_unit_code}->{req.target_unit_code}",
        event_metadata={"quantity": str(qty), "exact_result": res["exact_result"]},
    )
    return res


@product_units_router.post("/{product_id}/unit-conversions/decompose", response_model=UnitDecomposeResponse)
def decompose_quantity(
    product_id: UUID,
    req: UnitDecomposeRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.unit_conversions.evaluate")
    ),
):
    _require_product(db, product_id, resolve_organization_id(principal))
    qty = Decimal(req.quantity)
    service = QuantityDecompositionService(db)
    res = service.decompose(
        product_id=product_id,
        quantity=qty,
        source_unit_code=req.source_unit_code,
        strategy=req.strategy,
    )

    AuditService().record(
        database=db,
        event_type="logistics.unit_conversion.decomposed",
        user_id=principal.user_id,
        resource_type="product_packaging_decomposition",
        resource_id=str(product_id),
        event_metadata={"quantity": str(qty), "normalized_base_quantity": res["normalized_base_quantity"]},
    )
    return res


@conversion_engine_router.post("/compare", response_model=UnitCompareResponse)
def compare_quantities(
    req: UnitCompareRequest,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.unit_conversions.evaluate")
    ),
):
    l_qty = Decimal(req.left_quantity)
    r_qty = Decimal(req.right_quantity)
    service = QuantityComparisonService(db)
    return service.compare(
        left_quantity=l_qty,
        left_unit_code=req.left_unit_code,
        right_quantity=r_qty,
        right_unit_code=req.right_unit_code,
        product_id=req.product_id,
        organization_id=resolve_organization_id(principal),
    )


def _require_product(db: Session, product_id: UUID, organization_id: UUID) -> ProductModel:
    product = db.get(ProductModel, product_id)
    if not product or product.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product
