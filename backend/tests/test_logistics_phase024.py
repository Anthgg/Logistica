"""Comprehensive test suite for Phase 024 — Units and Conversions Engine."""

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.main import app
from app.models.organization import Organization
from app.modules.logistics.products.models import ProductModel, ProductCategoryModel, ProductBrandModel
from app.modules.logistics.units.comparison_service import QuantityComparisonService
from app.modules.logistics.units.conversion_engine import UnitConversionEngine
from app.modules.logistics.units.decomposition_service import QuantityDecompositionService
from app.modules.logistics.units.models import (
    MeasurementDimensionModel,
    ProductPackagingDefinitionModel,
    ProductUnitConfigurationModel,
    UnitConversionRuleModel,
    UnitOfMeasureModel,
)
from app.modules.logistics.units.path_resolver import ConversionPathResolver
from app.modules.logistics.units.seed import seed_units_and_conversions
from app.modules.logistics.units.unit_service import UnitCatalogService


from app.database.session import SessionLocal


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def run_seed_before_tests(db_session: Session):
    """Ensures UOM seed data is present in database before each test."""
    seed_units_and_conversions(db_session)


class TestUOMSeedAndCatalog:
    def test_seed_execution(self, db_session: Session):
        dims = db_session.query(MeasurementDimensionModel).all()
        assert len(dims) >= 5
        codes = [d.code for d in dims]
        assert "COUNT" in codes
        assert "MASS" in codes
        assert "LENGTH" in codes
        assert "AREA" in codes
        assert "VOLUME" in codes

        units = db_session.query(UnitOfMeasureModel).filter_by(organization_id=None).all()
        assert len(units) >= 20
        u_codes = [u.code for u in units]
        assert "UND" in u_codes
        assert "KG" in u_codes
        assert "M" in u_codes
        assert "M2" in u_codes
        assert "M3" in u_codes

    def test_create_custom_organization_unit(self, db_session: Session):
        org = Organization(code=f"ORG-{uuid4().hex[:6]}", name="Test UOM Org", country_code="PE")
        db_session.add(org)
        db_session.flush()

        dim = db_session.query(MeasurementDimensionModel).filter_by(code="MASS").first()
        service = UnitCatalogService(db_session)
        custom_u = service.create_unit(
            dimension_id=dim.id,
            code="LIBRA",
            name="Libra Personalizada",
            symbol="lb",
            organization_id=org.id,
        )

        assert custom_u.normalized_code == "LIBRA"
        assert custom_u.unit_scope == "ORGANIZATION"
        assert custom_u.organization_id == org.id


class TestMathematicalDecimalConversions:
    def test_physical_mass_conversions(self, db_session: Session):
        resolver = ConversionPathResolver(db_session)
        kg_u = db_session.query(UnitOfMeasureModel).filter_by(code="KG").first()
        g_u = db_session.query(UnitOfMeasureModel).filter_by(code="G").first()

        factor, path, _ = resolver.resolve_path(source_unit_id=kg_u.id, target_unit_id=g_u.id)
        assert factor == Decimal("1000")
        assert path == ["KG", "G"]

        res = UnitConversionEngine.convert(
            quantity=Decimal("2.5"),
            source_code="KG",
            target_code="G",
            effective_factor=factor,
            path=path,
        )
        assert res["exact_result"] == "2500.000000000000000000"
        assert res["rounded_result"] == "2500.0000"

        # Inverse conversion: 2500 G to KG
        inv_factor, inv_path, _ = resolver.resolve_path(source_unit_id=g_u.id, target_unit_id=kg_u.id)
        assert inv_factor == Decimal("0.001")
        res_inv = UnitConversionEngine.convert(
            quantity=Decimal("2500"),
            source_code="G",
            target_code="KG",
            effective_factor=inv_factor,
            path=inv_path,
        )
        assert res_inv["rounded_result"] == "2.5000"

    def test_physical_length_area_volume(self, db_session: Session):
        resolver = ConversionPathResolver(db_session)
        m_u = db_session.query(UnitOfMeasureModel).filter_by(code="M").first()
        cm_u = db_session.query(UnitOfMeasureModel).filter_by(code="CM").first()
        factor, _, _ = resolver.resolve_path(source_unit_id=m_u.id, target_unit_id=cm_u.id)
        assert factor == Decimal("100")

        # 3.75 M to CM
        res = UnitConversionEngine.convert(quantity=Decimal("3.75"), source_code="M", target_code="CM", effective_factor=factor, path=["M", "CM"])
        assert res["rounded_result"] == "375.0000"

        # Volume: M3 to L
        m3_u = db_session.query(UnitOfMeasureModel).filter_by(code="M3").first()
        l_u = db_session.query(UnitOfMeasureModel).filter_by(code="L").first()
        vol_factor, _, _ = resolver.resolve_path(source_unit_id=m3_u.id, target_unit_id=l_u.id)
        assert vol_factor == Decimal("1000")


class TestProductPackagingConversionsAndDecomposition:
    def test_product_specific_packaging_hierarchy(self, db_session: Session):
        org = Organization(code=f"ORG-{uuid4().hex[:6]}", name="Packaging Org", country_code="PE")
        db_session.add(org)
        db_session.flush()

        from app.modules.logistics.products.models import ProductCategoryModel, ProductBrandModel

        cat = ProductCategoryModel(organization_id=org.id, code=f"CAT-{uuid4().hex[:4]}", name="Cat General", hierarchy_path=f"CAT-{uuid4().hex[:4]}")
        brand = ProductBrandModel(organization_id=org.id, code=f"BR-{uuid4().hex[:4]}", name="Marca General", normalized_name=f"MARCA-{uuid4().hex[:4]}")
        db_session.add_all([cat, brand])
        db_session.flush()

        prod_a = ProductModel(organization_id=org.id, sku=f"SKU-A-{uuid4().hex[:4]}", normalized_sku=f"SKU-A-{uuid4().hex[:4]}", name="Producto A", category_id=cat.id, brand_id=brand.id, base_unit_code="UND")
        prod_b = ProductModel(organization_id=org.id, sku=f"SKU-B-{uuid4().hex[:4]}", normalized_sku=f"SKU-B-{uuid4().hex[:4]}", name="Producto B", category_id=cat.id, brand_id=brand.id, base_unit_code="UND")
        db_session.add_all([prod_a, prod_b])
        db_session.flush()

        und_u = db_session.query(UnitOfMeasureModel).filter_by(code="UND").first()
        pqt_u = db_session.query(UnitOfMeasureModel).filter_by(code="PAQUETE").first()
        cja_u = db_session.query(UnitOfMeasureModel).filter_by(code="CAJA").first()
        plt_u = db_session.query(UnitOfMeasureModel).filter_by(code="PALLET").first()

        service = UnitCatalogService(db_session)
        # Prod A: 1 PAQUETE = 6 UND, 1 CAJA = 4 PAQUETES (24 UND), 1 PALLET = 40 CAJAS (960 UND)
        service.add_product_packaging(product_id=prod_a.id, packaging_unit_id=pqt_u.id, contained_unit_id=und_u.id, contained_quantity=Decimal("6"), level_order=1)
        service.add_product_packaging(product_id=prod_a.id, packaging_unit_id=cja_u.id, contained_unit_id=pqt_u.id, contained_quantity=Decimal("4"), level_order=2)
        service.add_product_packaging(product_id=prod_a.id, packaging_unit_id=plt_u.id, contained_unit_id=cja_u.id, contained_quantity=Decimal("40"), level_order=3)

        # Prod B: 1 CAJA = 10 UND
        service.add_product_packaging(product_id=prod_b.id, packaging_unit_id=cja_u.id, contained_unit_id=und_u.id, contained_quantity=Decimal("10"), level_order=1)

        resolver = ConversionPathResolver(db_session)

        # Test Prod A: 1 CAJA -> UND = 24
        f_a_box, path_a, _ = resolver.resolve_path(source_unit_id=cja_u.id, target_unit_id=und_u.id, product_id=prod_a.id)
        assert f_a_box == Decimal("24")

        # Test Prod A: 1 PALLET -> UND = 960
        f_a_plt, _, _ = resolver.resolve_path(source_unit_id=plt_u.id, target_unit_id=und_u.id, product_id=prod_a.id)
        assert f_a_plt == Decimal("960")

        # Test Prod B: 1 CAJA -> UND = 10
        f_b_box, _, _ = resolver.resolve_path(source_unit_id=cja_u.id, target_unit_id=und_u.id, product_id=prod_b.id)
        assert f_b_box == Decimal("10")

    def test_quantity_decomposition_service(self, db_session: Session):
        org = Organization(code=f"ORG-{uuid4().hex[:6]}", name="Decomp Org", country_code="PE")
        db_session.add(org)
        db_session.flush()

        cat = ProductCategoryModel(organization_id=org.id, code=f"CAT-{uuid4().hex[:4]}", name="Cat General", hierarchy_path=f"CAT-{uuid4().hex[:4]}")
        brand = ProductBrandModel(organization_id=org.id, code=f"BR-{uuid4().hex[:4]}", name="Marca General", normalized_name=f"MARCA-{uuid4().hex[:4]}")
        db_session.add_all([cat, brand])
        db_session.flush()

        prod = ProductModel(organization_id=org.id, sku=f"SKU-DEC-{uuid4().hex[:4]}", normalized_sku=f"SKU-DEC-{uuid4().hex[:4]}", name="Producto Decomp", category_id=cat.id, brand_id=brand.id, base_unit_code="UND")
        db_session.add(prod)
        db_session.flush()

        und_u = db_session.query(UnitOfMeasureModel).filter_by(code="UND").first()
        pqt_u = db_session.query(UnitOfMeasureModel).filter_by(code="PAQUETE").first()
        cja_u = db_session.query(UnitOfMeasureModel).filter_by(code="CAJA").first()
        plt_u = db_session.query(UnitOfMeasureModel).filter_by(code="PALLET").first()

        service = UnitCatalogService(db_session)
        service.add_product_packaging(product_id=prod.id, packaging_unit_id=pqt_u.id, contained_unit_id=und_u.id, contained_quantity=Decimal("6"), level_order=1)
        service.add_product_packaging(product_id=prod.id, packaging_unit_id=cja_u.id, contained_unit_id=pqt_u.id, contained_quantity=Decimal("4"), level_order=2)
        service.add_product_packaging(product_id=prod.id, packaging_unit_id=plt_u.id, contained_unit_id=cja_u.id, contained_quantity=Decimal("40"), level_order=3)

        decomp_service = QuantityDecompositionService(db_session)
        res = decomp_service.decompose(product_id=prod.id, quantity=Decimal("985"), source_unit_code="UND")

        assert Decimal(res["normalized_base_quantity"]) == Decimal("985")
        components = res["components"]
        assert len(components) == 3

        # 985 UND = 1 PALLET (960 UND) + 1 CAJA (24 UND) + 1 UND
        assert components[0]["unit_code"] == "PALLET"
        assert components[0]["quantity"] == "1"

        assert components[1]["unit_code"] == "CAJA"
        assert components[1]["quantity"] == "1"

        assert components[2]["unit_code"] == "UND"
        assert components[2]["quantity"] == "1"


class TestQuantityComparisonService:
    def test_compare_quantities_equal_and_different(self, db_session: Session):
        comp_service = QuantityComparisonService(db_session)
        res_eq = comp_service.compare(left_quantity=Decimal("2.5"), left_unit_code="KG", right_quantity=Decimal("2500"), right_unit_code="G")
        assert res_eq["comparison"] == "EQUAL"
        assert res_eq["equivalent"] is True

        res_diff = comp_service.compare(left_quantity=Decimal("3"), left_unit_code="KG", right_quantity=Decimal("2500"), right_unit_code="G")
        assert res_diff["comparison"] == "GREATER_THAN"
        assert res_diff["equivalent"] is False


class TestSecurityAndApiEndpoints:
    def test_unauthenticated_requests_return_401(self):
        client = TestClient(app)
        res = client.get("/api/logistics/units")
        assert res.status_code == 401

        res_eval = client.post("/api/logistics/unit-conversions/evaluate", json={
            "quantity": "2.5",
            "source_unit_code": "KG",
            "target_unit_code": "G",
        })
        assert res_eval.status_code == 401
