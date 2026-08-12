"""Phase 034 — Purchase Orders Comprehensive Test Suite.

Tests:
1. Value Objects & MoneyService exact Decimal arithmetic (zero float).
2. Atomic PO code formatting and normalization (OC-LIM-2026-000001).
3. PurchaseOrderApprovalGate transitional policy & self-approval prohibition.
4. PurchaseOrderGenerationPlanner grouping, validation, and blocking issues.
5. PurchaseOrderSnapshotProvider deterministic SHA-256 revision content hash.
6. PurchaseOrderService full lifecycle unit test with Mock Session.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.modules.logistics.procurement.purchase_orders.domain.errors.exceptions import (
    PurchaseOrderApprovalRequired,
    PurchaseOrderDiscountInvalid,
    PurchaseOrderNotFound,
    PurchaseOrderSelfApprovalDenied,
    PurchaseOrderStatusInvalid,
)
from app.modules.logistics.procurement.purchase_orders.domain.policies.approval_gate import (
    TransitionalSingleStepPurchaseOrderApprovalPolicy,
)
from app.modules.logistics.procurement.purchase_orders.domain.services.generation_planner import (
    PurchaseOrderGenerationPlanner,
)
from app.modules.logistics.procurement.purchase_orders.domain.services.money_service import (
    LineInput,
    PurchaseOrderMoneyService,
)
from app.modules.logistics.procurement.purchase_orders.domain.services.snapshot_provider import (
    PurchaseOrderSnapshotProvider,
)
from app.modules.logistics.procurement.purchase_orders.domain.value_objects.money import (
    Money,
    PurchaseOrderCode,
    QuantityAmount,
)


# ---------------------------------------------------------------------------
# Test 1: Value Objects & MoneyService
# ---------------------------------------------------------------------------
def test_value_objects_and_money_service_exact_decimals() -> None:
    # 1. Money Value Object
    m1 = Money("100.50", "PEN")
    m2 = Money("49.50", "PEN")
    assert m1.amount == Decimal("100.50")
    assert m1.add(m2) == Money("150.00", "PEN")

    with pytest.raises(TypeError):
        Money(100.50, "PEN")  # type: ignore[arg-type] # Float must be rejected

    # 2. Quantity Value Object
    q = QuantityAmount("10.500", "KG")
    assert q.value == Decimal("10.500")

    with pytest.raises(TypeError):
        QuantityAmount(10.5, "KG")  # type: ignore[arg-type] # Float rejected

    # 3. Money Service Calculations
    svc = PurchaseOrderMoneyService(scale=2)
    line1 = LineInput(
        line_number=1,
        ordered_quantity=Decimal("10"),
        unit_price=Decimal("50.00"),
        currency_code="PEN",
        discount_type="PERCENTAGE",
        discount_value=Decimal("10"),  # 10% of 500 = 50
        tax_rate=Decimal("18"),         # 18% of 450 = 81
        freight_amount=Decimal("20.00"),
        other_charges_amount=Decimal("5.00"),
    )
    summary = svc.calculate_line(line1)
    assert summary.line_subtotal == Decimal("500.00")
    assert summary.discount_amount == Decimal("50.00")
    assert summary.line_net == Decimal("450.00")
    assert summary.tax_amount == Decimal("81.00")
    assert summary.line_total == Decimal("556.00")  # 450 + 81 + 20 + 5

    # 4. Summary calculation across multiple lines
    line2 = LineInput(
        line_number=2,
        ordered_quantity=Decimal("5"),
        unit_price=Decimal("100.00"),
        currency_code="PEN",
        discount_type="NONE",
        tax_rate=Decimal("18"),         # 18% of 500 = 90
    )
    total_summary = svc.calculate_summary([line1, line2])
    assert total_summary.subtotal == Decimal("1000.00")
    assert total_summary.discount_total == Decimal("50.00")
    assert total_summary.net_subtotal == Decimal("950.00")
    assert total_summary.tax_total == Decimal("171.00")  # 81 + 90
    assert total_summary.grand_total == Decimal("1146.00")


# ---------------------------------------------------------------------------
# Test 2: PO Code Generation & Validation
# ---------------------------------------------------------------------------
def test_purchase_order_code_generation() -> None:
    code_vo = PurchaseOrderCode.build("LIM", 2026, 42)
    assert str(code_vo) == "OC-LIM-2026-000042"
    assert code_vo.value == "OC-LIM-2026-000042"

    parsed = PurchaseOrderCode("OC-LIM-2026-000042")
    assert parsed.value == "OC-LIM-2026-000042"

    with pytest.raises(ValueError):
        PurchaseOrderCode("INVALID-CODE-FORMAT")


# ---------------------------------------------------------------------------
# Test 3: Approval Gate & Self-Approval Prohibition
# ---------------------------------------------------------------------------
def test_approval_gate_transitional_policy(monkeypatch) -> None:
    monkeypatch.setenv("PURCHASE_ORDER_TRANSITIONAL_APPROVAL_ENABLED", "true")
    policy = TransitionalSingleStepPurchaseOrderApprovalPolicy()

    po_id = uuid4()
    rev_id = uuid4()
    user_creator = uuid4()
    user_approver = uuid4()

    # 1. Resolve requirements
    req = policy.resolve_requirements("PENDING_APPROVAL", "1000.00")
    assert req.requires_step_up is True
    assert req.step_up_factor == "COMBINED_FACE_PAD"
    assert req.allow_self_approval is False

    # 2. Self-approval must be DENIED
    with pytest.raises(PurchaseOrderSelfApprovalDenied):
        policy.approve(
            purchase_order_id=po_id,
            revision_id=rev_id,
            approver_user_id=user_creator,  # Same user!
            creator_user_id=user_creator,
            current_approval_status="PENDING",
            reason=None,
        )

    # 3. Successful approval by a different user
    res = policy.approve(
        purchase_order_id=po_id,
        revision_id=rev_id,
        approver_user_id=user_approver,
        creator_user_id=user_creator,
        current_approval_status="PENDING",
        reason="Approved after budget verification",
    )
    assert res.new_approval_status == "APPROVED"
    assert res.new_po_status == "APPROVED"

    # 4. Rejection requires reason >= 20 chars
    with pytest.raises(PurchaseOrderApprovalRequired):
        policy.reject(
            purchase_order_id=po_id,
            revision_id=rev_id,
            approver_user_id=user_approver,
            creator_user_id=user_creator,
            current_approval_status="PENDING",
            reason="Short reason",  # Too short!
        )

    res_rej = policy.reject(
        purchase_order_id=po_id,
        revision_id=rev_id,
        approver_user_id=user_approver,
        creator_user_id=user_creator,
        current_approval_status="PENDING",
        reason="This quotation is rejected because the pricing exceeds budget threshold.",
    )
    assert res_rej.new_approval_status == "REJECTED"


# ---------------------------------------------------------------------------
# Test 4: Generation Planner (CCO -> PO)
# ---------------------------------------------------------------------------
def test_generation_planner_from_cco_decision() -> None:
    planner = PurchaseOrderGenerationPlanner()
    decision_id = uuid4()
    supplier1_id = uuid4()
    cand1_id = uuid4()

    decision_data = {
        "id": str(decision_id),
        "status": "RECORDED",
        "procurement_approval_status": "PENDING_PHASE_035",
    }

    line1_id = uuid4()
    decision_lines = [
        {
            "id": str(line1_id),
            "selected_candidate_id": str(cand1_id),
            "selected_quantity": Decimal("100"),
            "selected_unit_price": Decimal("25.50"),
            "selected_line_total": Decimal("2550.00"),
            "selected_currency_code": "PEN",
            "selected_unit_code": "UND",
            "product_snapshot": {"id": str(uuid4()), "name": "Laptop Pro 15"},
        }
    ]

    candidates_by_id = {
        cand1_id: {
            "supplier_business_partner_id": str(supplier1_id),
            "supplier_snapshot": {"legal_name": "Tech Supplier Peru SAC"},
        }
    }

    plan = planner.build_plan(decision_data, decision_lines, candidates_by_id)
    assert plan.is_executable is True
    assert plan.total_orders_to_create == 1
    assert plan.entries[0].supplier_business_partner_id == supplier1_id
    assert plan.entries[0].estimated_subtotal == Decimal("2550.00")

    # Non-RECORDED decision must fail planning
    decision_data["status"] = "DRAFT"
    plan_invalid = planner.build_plan(decision_data, decision_lines, candidates_by_id)
    assert plan_invalid.is_executable is False
    assert "RECORDED" in plan_invalid.blocking_issues[0]


# ---------------------------------------------------------------------------
# Test 5: Snapshot Provider & Content Hash
# ---------------------------------------------------------------------------
def test_snapshot_provider_and_content_hash() -> None:
    supplier_snap = PurchaseOrderSnapshotProvider.build_supplier_snapshot(
        partner_data={"id": str(uuid4()), "legal_name": "Acme Industrial Corp", "tax_id": "20999999999"}
    )
    assert supplier_snap["legal_name"] == "Acme Industrial Corp"
    assert "captured_at" in supplier_snap

    lines_data = [
        {"line_number": 1, "product_name": "Motor 500W", "quantity": "2", "unit_price": "1500.00"}
    ]
    monetary_snap = PurchaseOrderSnapshotProvider.build_monetary_snapshot(
        {"grand_total": "3000.00", "currency_code": "PEN"}
    )

    hash1 = PurchaseOrderSnapshotProvider.compute_revision_hash(
        supplier_snap, lines_data, monetary_snap, "PEN"
    )
    hash2 = PurchaseOrderSnapshotProvider.compute_revision_hash(
        supplier_snap, lines_data, monetary_snap, "PEN"
    )
    assert len(hash1) == 64
    assert hash1 == hash2  # Deterministic!


# ---------------------------------------------------------------------------
# Test 6: Application Service Lifecycle Unit Test (Mocked DB)
# ---------------------------------------------------------------------------
def test_purchase_order_service_lifecycle_mock_db(monkeypatch) -> None:
    monkeypatch.setenv("PURCHASE_ORDER_TRANSITIONAL_APPROVAL_ENABLED", "true")

    db_mock = MagicMock()
    org_id = uuid4()
    branch_id = uuid4()
    buyer_id = uuid4()
    approver_id = uuid4()
    supplier_id = uuid4()
    decision_id = uuid4()
    cand_id = uuid4()
    line_id = uuid4()

    decision_data = {
        "id": str(decision_id),
        "status": "RECORDED",
        "procurement_approval_status": "PENDING_PHASE_035",
    }
    decision_lines = [
        {
            "id": str(line_id),
            "selected_candidate_id": str(cand_id),
            "selected_quantity": Decimal("10"),
            "selected_unit_price": Decimal("100.00"),
            "selected_line_total": Decimal("1000.00"),
            "selected_currency_code": "PEN",
            "selected_unit_code": "UND",
            "product_snapshot": {"id": str(uuid4()), "name": "Servidor Rack 1U"},
        }
    ]
    candidates = {
        cand_id: {
            "supplier_business_partner_id": str(supplier_id),
            "supplier_snapshot": {"legal_name": "Tech Corp Peru SAC"},
        }
    }

    from app.modules.logistics.procurement.purchase_orders.application.services.purchase_order_service import (
        PurchaseOrderService,
    )

    service = PurchaseOrderService(db_mock)
    service._repo.check_allocation_conflicts = MagicMock(return_value=[])  # No conflicts
    service._repo.generate_next_code = MagicMock(return_value=("OC-LIM-2026-000001", "OC-LIM-2026-000001", 1))

    # 1. Generate POs
    created_orders = service.generate_orders_from_decision(
        organization_id=org_id,
        branch_id=branch_id,
        creator_user_id=buyer_id,
        decision_data=decision_data,
        decision_lines_data=decision_lines,
        candidates_by_id=candidates,
        site_code="LIM",
    )
    assert len(created_orders) == 1
    po = created_orders[0]
    assert po.status == "DRAFT"
    assert po.approval_status == "NOT_SUBMITTED"
    assert po.grand_total == Decimal("1000.00")

    # Mock repo.get_by_id_or_raise to return our generated PO
    service._repo.get_by_id_or_raise = MagicMock(return_value=po)

    # 2. Submit for approval
    po_submitted = service.submit_for_approval(
        po_id=po.id,
        organization_id=org_id,
        submitter_user_id=buyer_id,
    )
    assert po_submitted.status == "PENDING_APPROVAL"
    assert po_submitted.approval_status == "PENDING"

    # 3. Self-approval by buyer must fail
    with pytest.raises(PurchaseOrderSelfApprovalDenied):
        service.approve_order(
            po_id=po.id,
            organization_id=org_id,
            approver_user_id=buyer_id,
        )

    # 4. Approval by approver_id succeeds
    po_approved = service.approve_order(
        po_id=po.id,
        organization_id=org_id,
        approver_user_id=approver_id,
        reason="Approved after verification",
    )
    assert po_approved.status == "APPROVED"
    assert po_approved.approval_status == "APPROVED"
    assert po_approved.approved_by == approver_id
    assert po_approved.approved_at is not None
