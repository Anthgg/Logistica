"""Phase 041. Quality inspection plan schema tests."""

import pytest
from pydantic import ValidationError
from decimal import Decimal
from uuid import uuid4

from app.modules.logistics.inbound.reception_differences.presentation.quality_plan_schemas import (
    QualityPlanCreate,
    QualityPlanUpdate,
    QualityControlCreate,
    QualityToleranceCreate,
    QualitySamplingCreate,
    QualityPlanScopeCreate,
    QualityCertificateCreate,
    QualityConditionCreate,
    QualityPlanReferenceFileCreate,
)


class TestPlanCreateSchema:
    def test_valid_plan_create(self):
        plan = QualityPlanCreate(
            plan_code="QP-001",
            plan_name="Test Quality Plan",
            plan_family="GENERAL_QUALITY",
        )
        assert plan.plan_code == "QP-001"
        assert plan.plan_family == "GENERAL_QUALITY"

    def test_plan_create_with_optional_fields(self):
        plan = QualityPlanCreate(
            plan_code="QP-002",
            plan_name="Test Plan",
            description="A test plan",
            plan_family="INBOUND_RECEIVING",
            is_global=True,
            priority=5,
        )
        assert plan.is_global is True
        assert plan.priority == 5

    def test_plan_create_rejects_float(self):
        with pytest.raises(ValidationError):
            QualityPlanCreate(
                plan_code="QP-003",
                plan_name="Test Plan",
                priority=1.5,
            )


class TestPlanUpdateSchema:
    def test_valid_plan_update(self):
        update = QualityPlanUpdate(plan_name="Updated Plan")
        assert update.plan_name == "Updated Plan"
        assert update.description is None

    def test_plan_update_all_none(self):
        update = QualityPlanUpdate()
        d = update.model_dump(exclude_none=True)
        assert len(d) == 0


class TestControlCreateSchema:
    def test_valid_control_create(self):
        ctrl = QualityControlCreate(
            control_type="WEIGHT_MEASUREMENT",
            control_code="CTRL-W-001",
            control_name="Weight Check",
        )
        assert ctrl.control_type == "WEIGHT_MEASUREMENT"
        assert ctrl.is_mandatory is True

    def test_control_create_with_optional(self):
        ctrl = QualityControlCreate(
            control_type="PACKAGING_CONDITION",
            control_code="CTRL-P-001",
            control_name="Packaging Check",
            display_order=1,
            is_mandatory=False,
            is_blocking=True,
        )
        assert ctrl.is_blocking is True
        assert ctrl.is_mandatory is False


class TestToleranceCreateSchema:
    def test_valid_tolerance_create(self):
        tol = QualityToleranceCreate(
            tolerance_type="ABSOLUTE_RANGE",
            min_value=Decimal("10"),
            max_value=Decimal("20"),
        )
        assert tol.tolerance_type == "ABSOLUTE_RANGE"

    def test_tolerance_rejects_float(self):
        with pytest.raises(ValidationError):
            QualityToleranceCreate(
                tolerance_type="ABSOLUTE_RANGE",
                min_value=10.5,
            )


class TestSamplingCreateSchema:
    def test_valid_sampling_create(self):
        sp = QualitySamplingCreate(
            sampling_type="FIXED_COUNT",
            fixed_count=5,
        )
        assert sp.sampling_type == "FIXED_COUNT"
        assert sp.fixed_count == 5


class TestScopeCreateSchema:
    def test_valid_scope_create(self):
        scope = QualityPlanScopeCreate(
            scope_type="PRODUCT",
            scope_product_id=uuid4(),
        )
        assert scope.scope_type == "PRODUCT"
        assert scope.is_active is True

    def test_scope_create_category(self):
        scope = QualityPlanScopeCreate(
            scope_type="PRODUCT_CATEGORY",
            scope_category_id=uuid4(),
        )
        assert scope.scope_type == "PRODUCT_CATEGORY"


class TestCertificateCreateSchema:
    def test_valid_certificate_create(self):
        cert = QualityCertificateCreate(
            certificate_type="COA",
            is_mandatory=True,
            validity_days=365,
        )
        assert cert.certificate_type == "COA"


class TestConditionCreateSchema:
    def test_valid_condition_create(self):
        cond = QualityConditionCreate(
            condition_type="ATTRIBUTE",
            condition_field="product.weight_kg",
            condition_operator="GTE",
            condition_value={"value": 10},
        )
        assert cond.condition_field == "product.weight_kg"


class TestReferenceFileCreateSchema:
    def test_valid_reference_file_create(self):
        rf = QualityPlanReferenceFileCreate(
            file_asset_id=uuid4(),
            reference_type="MANUAL",
        )
        assert rf.reference_type == "MANUAL"
