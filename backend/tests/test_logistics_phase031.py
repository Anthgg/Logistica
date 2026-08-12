"""Pytest Test Suite for Phase 031 — Purchase Requisitions & Cost Centers."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
import app.models.registry  # register ORM models

from app.modules.logistics.cost_centers.models import CostCenterModel
from app.modules.logistics.cost_centers.service import cost_center_service
from app.modules.logistics.procurement.requisitions.application.services.decision_service import (
    purchase_requisition_decision_service,
)
from app.modules.logistics.procurement.requisitions.application.services.line_service import (
    purchase_requisition_line_service,
)
from app.modules.logistics.procurement.requisitions.application.services.requisition_service import (
    purchase_requisition_service,
)
from app.modules.logistics.procurement.requisitions.application.services.submission_service import (
    purchase_requisition_submission_service,
)
from app.modules.logistics.procurement.requisitions.domain.errors.exceptions import (
    PurchaseRequisitionCannotBeApproved,
    PurchaseRequisitionNotEditable,
    PurchaseRequisitionSelfApprovalDenied,
)
from app.modules.logistics.procurement.requisitions.domain.policies.approval_policy import (
    ApprovalContext,
    purchase_approval_policy,
)
from app.modules.logistics.procurement.requisitions.domain.services.services import (
    compute_content_hash,
    normalize_quantity,
    validate_justification,
    validate_required_date,
)
from app.modules.logistics.procurement.requisitions.domain.value_objects.enums import (
    RequisitionStatus,
    RevisionStatus,
)
from app.modules.logistics.procurement.requisitions.infrastructure.persistence.models import (
    PurchaseRequisitionLineModel,
    PurchaseRequisitionModel,
    PurchaseRequisitionRevisionModel,
)
from app.modules.logistics.products.models import ProductCategoryModel, ProductModel
from app.modules.logistics.units.models import MeasurementDimensionModel, UnitOfMeasureModel


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    allowed_prefixes = (
        "organizations", "logistics_", "cost_", "purchase_", "products",
        "product_", "units_", "measurement_", "users", "branches",
    )
    for table in Base.metadata.sorted_tables:
        if any(table.name.startswith(p) for p in allowed_prefixes) or table.name in ("cost_centers", "purchase_requisitions", "purchase_requisition_revisions", "purchase_requisition_lines", "purchase_requisition_decisions", "purchase_requisition_comments", "purchase_requisition_duplicate_candidates"):
            try:
                table.create(engine, checkfirst=True)
            except Exception:
                pass
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_cost_center_creation_and_lifecycle(db_session):
    org_id = uuid4()
    user_id = uuid4()

    # Create Cost Center
    cc = cost_center_service.create(
        db=db_session,
        org_id=org_id,
        user_id=user_id,
        code=" CC-LOG-01 ",
        name="Centro Logístico 01",
        description="Centro de costos operacional",
    )
    db_session.commit()

    assert cc.normalized_code == "CC-LOG-01"
    assert cc.status == "DRAFT"

    # Activate
    cc = cost_center_service.activate(db_session, cc.id, org_id, user_id)
    db_session.commit()
    assert cc.status == "ACTIVE"

    # Fetch
    fetched = cost_center_service.get(db_session, cc.id, org_id)
    assert fetched.name == "Centro Logístico 01"


def test_domain_justification_validation():
    # Valid
    val = validate_justification("Se requiere repuesto urgente para la flota vehicular de la sede sur.")
    assert "repuesto urgente" in val

    # Too short
    with pytest.raises(ValueError, match="too short"):
        validate_justification("Demasiado corto")

    # HTML injection
    with pytest.raises(ValueError, match="HTML"):
        validate_justification("<b>Solicitud invalida con html</b> extra de mas de 20 caracteres")


def test_exact_decimal_quantity_parser():
    # Valid string decimal
    qty = normalize_quantity("12.5000")
    assert isinstance(qty, Decimal)
    assert qty == Decimal("12.5")

    # Reject non-string / float directly
    with pytest.raises(ValueError, match="Quantity must be a string decimal"):
        normalize_quantity(12.5)  # type: ignore

    # Reject zero or negative
    with pytest.raises(ValueError, match="greater than zero"):
        normalize_quantity("0.0")


def test_self_approval_policy_denial():
    requester = uuid4()
    approver = requester  # Same user

    ctx = ApprovalContext(
        requisition_id=uuid4(),
        requester_user_id=requester,
        approver_user_id=approver,
        priority="NORMAL",
        organization_id=uuid4(),
    )
    result = purchase_approval_policy.resolve(ctx)
    assert result.can_approve is False
    assert "Self-approval is denied" in result.reason
    assert result.step_up_level == "HIGH"


def test_purchase_requisition_draft_creation(db_session):
    org_id = uuid4()
    branch_id = uuid4()
    user_id = uuid4()

    # Seed Cost Center
    cc = cost_center_service.create(
        db=db_session,
        org_id=org_id,
        user_id=user_id,
        code="CC-OPER-01",
        name="Operaciones",
    )
    cost_center_service.activate(db_session, cc.id, org_id, user_id)
    db_session.commit()

    tomorrow = date.today() + timedelta(days=2)
    pr = purchase_requisition_service.create_draft(
        db=db_session,
        org_id=org_id,
        branch_id=branch_id,
        user_id=user_id,
        user_name="Juan Perez",
        cost_center_id=cc.id,
        priority="NORMAL",
        required_date=tomorrow,
        justification="Requerimiento de insumos de almacén central para operaciones.",
    )
    db_session.commit()

    assert pr.status == RequisitionStatus.DRAFT
    assert pr.current_revision_number == 1
    assert pr.cost_center_snapshot["code"] == "CC-OPER-01"


def test_line_addition_and_submission_workflow(db_session):
    org_id = uuid4()
    branch_id = uuid4()
    user_id = uuid4()
    approver_id = uuid4()  # Different user for approval

    # Seed Cost Center
    cc = cost_center_service.create(
        db=db_session, org_id=org_id, user_id=user_id, code="CC-01", name="General"
    )
    cost_center_service.activate(db_session, cc.id, org_id, user_id)

    # Seed Dimension & Unit
    dim = MeasurementDimensionModel(code="COUNT", name="Count", default_precision=0)
    db_session.add(dim)
    db_session.flush()
    unit = UnitOfMeasureModel(dimension_id=dim.id, code="UND", normalized_code="UND", name="Unidad", symbol="u")
    db_session.add(unit)
    db_session.flush()

    # Seed Product
    cat = ProductCategoryModel(
        organization_id=org_id,
        code="CAT1",
        name="General",
        hierarchy_path="/CAT1",
        depth=1,
    )
    db_session.add(cat)
    db_session.flush()
    prod = ProductModel(
        organization_id=org_id,
        category_id=cat.id,
        sku="SKU-TEST-01",
        normalized_sku="SKU_TEST_01",
        name="Filtro de Aceite Heavy Duty",
        base_unit_code="UND",
        status="ACTIVE",
        lifecycle_status="ACTIVE",
    )
    db_session.add(prod)
    db_session.commit()

    # Create Requisition Draft
    pr = purchase_requisition_service.create_draft(
        db=db_session,
        org_id=org_id,
        branch_id=branch_id,
        user_id=user_id,
        user_name="Ana Gomez",
        cost_center_id=cc.id,
        priority="NORMAL",
        required_date=date.today() + timedelta(days=5),
        justification="Requerimiento de filtros de aceite para mantenimiento preventivo.",
    )
    db_session.commit()

    # Add Line
    line = purchase_requisition_line_service.add_line(
        db=db_session,
        revision_id=pr.active_revision_id,
        org_id=org_id,
        user_id=user_id,
        product_id=prod.id,
        requested_quantity_str="15.0000",
        requested_unit_id=unit.id,
    )
    db_session.commit()
    assert line.requested_quantity == Decimal("15.0000")
    assert line.product_name_snapshot == "Filtro de Aceite Heavy Duty"

    # Submit Requisition
    pr_submitted = purchase_requisition_submission_service.submit(
        db=db_session,
        requisition_id=pr.id,
        org_id=org_id,
        user_id=user_id,
        expected_row_version=pr.row_version,
    )
    db_session.commit()
    assert pr_submitted.status == RequisitionStatus.SUBMITTED
    assert pr_submitted.requisition_code.startswith("REQ-")

    # Approve (by different approver user)
    pr_approved = purchase_requisition_decision_service.approve(
        db=db_session,
        requisition_id=pr.id,
        org_id=org_id,
        user_id=approver_id,
        reason="Aprobado para compra de mantenimiento.",
    )
    db_session.commit()
    assert pr_approved.status == RequisitionStatus.APPROVED
    assert pr_approved.approved_by == approver_id
