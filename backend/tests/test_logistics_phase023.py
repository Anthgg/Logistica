"""Tests for Phase 023 — Product Catalog Master Data."""

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.main import app
from app.models.branch import Branch
from app.models.organization import Organization
from app.modules.logistics.products.brand_service import ProductBrandService
from app.modules.logistics.products.category_service import ProductCategoryService
from app.modules.logistics.products.compatibility_evaluator import EvaluateProductLocationCompatibility
from app.modules.logistics.products.gtin_validator import ProductIdentifierValidator
from app.modules.logistics.products.identifier_service import ProductIdentifierService
from app.modules.logistics.products.models import ProductModel
from app.modules.logistics.products.product_service import ProductService
from app.modules.logistics.products.profile_policy_service import ProductProfileAndPolicyService
from app.modules.logistics.products.sku_validator import ProductSKUValidator
from app.modules.logistics.products.version_service import ProductVersionService
from app.modules.logistics.products.volume_calculator import ProductVolumeCalculator


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def setup_domain(db_session: Session):
    org_code = f"ORG{uuid4().hex[:6].upper()}"
    org = Organization(
        id=uuid4(),
        code=org_code,
        name="Org Test Phase 023",
        status="active",
        country_code="PE",
    )
    db_session.add(org)

    branch = Branch(
        id=uuid4(),
        organization_id=org.id,
        code="SED01",
        name="Sede Principal",
        status="active",
    )
    db_session.add(branch)
    db_session.commit()

    return {"org": org, "branch": branch}


class TestSKUAndGTINValidators:
    def test_sku_validation_and_normalization(self):
        is_valid, norm, err = ProductSKUValidator.validate("  cable-hdmi-2m  ")
        assert is_valid is True
        assert norm == "CABLE-HDMI-2M"

        # Invalid path traversal
        is_valid, norm, err = ProductSKUValidator.validate("../bad-sku")
        assert is_valid is False
        assert "path traversal" in err

    def test_gtin_checksum_validation(self):
        # EAN-13 valid checksum
        # EAN-13 "775012345678" -> Check digit calculated
        val_digits = "775012345678"
        check_digit = ProductIdentifierValidator.calculate_check_digit(val_digits)
        full_ean = f"{val_digits}{check_digit}"

        is_valid, norm, status, err = ProductIdentifierValidator.validate_gtin("EAN_13", full_ean)
        assert is_valid is True
        assert status == "CHECK_DIGIT_VALID"

    def test_internal_barcode_generation(self):
        code = ProductIdentifierValidator.generate_internal_barcode(uuid4().hex)
        assert code.startswith("T1P-")


class TestProductMasterServices:
    def test_category_and_brand_creation(self, db_session: Session, setup_domain: dict):
        org = setup_domain["org"]
        cat_service = ProductCategoryService(db_session)
        brand_service = ProductBrandService(db_session)

        # 1. Create parent category
        cat_parent = cat_service.create_category(org.id, code="ELEC", name="Electrónica")
        assert cat_parent.hierarchy_path == "ELEC"
        assert cat_parent.depth == 1

        # 2. Create subcategory
        cat_child = cat_service.create_category(org.id, code="LAP", name="Laptops", parent_category_id=cat_parent.id)
        assert cat_child.hierarchy_path == "ELEC/LAP"
        assert cat_child.depth == 2

        # 3. Create brand
        brand = brand_service.create_brand(org.id, code="LNV", name="Lenovo")
        assert brand.normalized_name == "LENOVO"

    def test_product_crud_and_sku_alias(self, db_session: Session, setup_domain: dict):
        org = setup_domain["org"]
        cat_service = ProductCategoryService(db_session)
        brand_service = ProductBrandService(db_session)
        product_service = ProductService(db_session)

        cat = cat_service.create_category(org.id, code="COMP", name="Cómputo")
        brand = brand_service.create_brand(org.id, code="DELL", name="Dell")

        sku_initial = f"LAP-DELL-{uuid4().hex[:4].upper()}"
        product = product_service.create_product(
            organization_id=org.id,
            sku=sku_initial,
            name="Laptop Latitude 5420",
            category_id=cat.id,
            brand_id=brand.id,
            base_unit_code="UND",
        )
        assert product.status == "DRAFT"
        assert product.normalized_sku == sku_initial

        # Activate product
        product_service.change_status(product.id, target_status="ACTIVE", reason="Launch product")
        assert product.status == "ACTIVE"

        # Change SKU on ACTIVE product -> creates Alias
        new_sku = f"LAP-DELL-NEW-{uuid4().hex[:4].upper()}"
        updated_product = product_service.change_sku(product.id, new_sku=new_sku, reason="Rebranding SKU")
        assert updated_product.sku == new_sku
        assert len(updated_product.sku_aliases) == 1
        assert updated_product.sku_aliases[0].previous_sku == sku_initial

    def test_volume_calculator_and_physical_profile(self, db_session: Session, setup_domain: dict):
        org = setup_domain["org"]
        cat = ProductCategoryService(db_session).create_category(org.id, code="GEN", name="General")
        product = ProductService(db_session).create_product(org.id, sku=f"PROD-{uuid4().hex[:4]}", name="Box Product", category_id=cat.id)

        # Decimal calculation: 50cm x 40cm x 30cm = 0.06 m3
        calc_res = ProductVolumeCalculator.calculate_volume(Decimal("50"), Decimal("40"), Decimal("30"), "CM")
        assert calc_res["calculated_value"] == Decimal("0.0600")

        profile_service = ProductProfileAndPolicyService(db_session)
        profile = profile_service.update_physical_profile(
            product_id=product.id,
            net_weight_value=Decimal("5.5000"),
            gross_weight_value=Decimal("6.2000"),
            length_value=Decimal("50"),
            width_value=Decimal("40"),
            height_value=Decimal("30"),
            dimension_unit="CM",
        )
        assert profile.volume_value == Decimal("0.0600")
        assert profile.gross_weight_value >= profile.net_weight_value

    def test_compatibility_evaluator(self):
        storage_conds = [{"condition_type": "COLD_CHAIN", "severity": "HARD_BLOCK"}]
        loc_dict = {"location_type": "GENERAL", "temperature_controlled": False, "status": "ACTIVE"}

        res = EvaluateProductLocationCompatibility.evaluate(
            product_dict={},
            storage_conditions=storage_conds,
            handling_conditions=[],
            location_dict=loc_dict,
            location_restrictions=[],
        )
        assert res["status"] == "INCOMPATIBLE"
        assert len(res["blocking_reasons"]) > 0


class TestSecurityAndEndpoints:
    def test_unauthenticated_returns_401(self):
        client = TestClient(app)
        response = client.get("/api/logistics/products")
        assert response.status_code == 401
