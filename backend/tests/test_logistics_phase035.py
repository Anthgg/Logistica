"""Unit and Integration Tests for Phase 035 — Procurement Approvals Engine."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.modules.logistics.procurement.approvals.application.services.approval_engine import (
    ProcurementApprovalEngine,
)
from app.modules.logistics.procurement.approvals.domain.entities.subject_registry import (
    ApprovalSubjectRegistry,
)
from app.modules.logistics.procurement.approvals.domain.errors.exceptions import (
    ApprovalPolicyConflict,
    ApprovalSelfApprovalDenied,
    ApprovalSeparationOfDutiesViolation,
)
from app.modules.logistics.procurement.approvals.domain.services.audit_seal_service import (
    ApprovalAuditSealService,
)
from app.modules.logistics.procurement.approvals.domain.services.chain_compiler import (
    ApprovalChainCompiler,
)
from app.modules.logistics.procurement.approvals.domain.services.conflict_detector import (
    ApprovalPolicyConflictDetector,
)
from app.modules.logistics.procurement.approvals.domain.services.match_service import (
    ApprovalPolicyMatchService,
)
from app.modules.logistics.procurement.approvals.domain.services.separation_of_duties import (
    ApprovalSeparationOfDutiesService,
)
from app.modules.logistics.procurement.purchase_orders.domain.policies.approval_gate import (
    get_approval_policy,
)


from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """In-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    target_tables = [
        t for name, t in Base.metadata.tables.items()
        if name.startswith(("procurement_approval_", "approval_"))
    ]
    Base.metadata.create_all(engine, tables=target_tables)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()




def test_subject_registry() -> None:
    """Verify registered purchasing subject types."""
    assert ApprovalSubjectRegistry.is_registered("PURCHASE_ORDER")
    assert ApprovalSubjectRegistry.is_registered("PURCHASE_ORDER_REVISION")
    assert ApprovalSubjectRegistry.is_registered("PURCHASE_ORDER_AMENDMENT")
    assert ApprovalSubjectRegistry.is_registered("PURCHASE_ORDER_VARIANCE")
    assert ApprovalSubjectRegistry.is_registered("SINGLE_SOURCE_EXCEPTION")

    po_def = ApprovalSubjectRegistry.get("PURCHASE_ORDER")
    assert po_def.code == "PURCHASE_ORDER"
    assert po_def.default_approval_permission == "logistics.purchase_orders.approve"


def test_deterministic_policy_matching() -> None:
    """Verify policy matching logic with Decimal amount boundaries."""
    policies = [
        {
            "policy": {"id": "p1", "subject_type": "PURCHASE_ORDER", "priority": 100, "is_fallback": False},
            "version": {"id": "v1", "version_number": 1},
            "conditions": [
                {
                    "field_code": "TOTAL_AMOUNT",
                    "operator": "BETWEEN",
                    "value_data": {"min": "0.00", "max": "5000.00"},
                }
            ],
            "steps": [{"step_code": "S1", "order_index": 1}],
        },
        {
            "policy": {"id": "p2", "subject_type": "PURCHASE_ORDER", "priority": 200, "is_fallback": False},
            "version": {"id": "v2", "version_number": 1},
            "conditions": [
                {
                    "field_code": "TOTAL_AMOUNT",
                    "operator": "GREATER_THAN",
                    "value_data": {"value": "5000.00"},
                }
            ],
            "steps": [{"step_code": "S1", "order_index": 1}, {"step_code": "S2", "order_index": 2}],
        },
    ]

    ctx_low = {
        "subject_type": "PURCHASE_ORDER",
        "organization_id": "org1",
        "amount": Decimal("2500.00"),
        "currency_code": "PEN",
    }
    match_low = ApprovalPolicyMatchService.match_policies(policies, ctx_low)
    assert len(match_low) == 1
    assert match_low[0]["policy"]["id"] == "p1"

    ctx_high = {
        "subject_type": "PURCHASE_ORDER",
        "organization_id": "org1",
        "amount": Decimal("15000.00"),
        "currency_code": "PEN",
    }
    match_high = ApprovalPolicyMatchService.match_policies(policies, ctx_high)
    assert len(match_high) == 1
    assert match_high[0]["policy"]["id"] == "p2"


def test_chain_compilation_and_hash() -> None:
    """Verify compiling step definitions into a frozen approval chain with SHA-256 hash."""
    matched = [
        {
            "policy": {"id": "p1", "subject_type": "PURCHASE_ORDER", "priority": 100},
            "version": {"id": "v1", "version_number": 1},
            "steps": [
                {
                    "id": "s1",
                    "step_code": "DEPT_MGR",
                    "name": "Department Approval",
                    "order_index": 1,
                    "execution_mode": "SEQUENTIAL",
                    "completion_mode": "ALL",
                    "approver_source_type": "FIXED_USER",
                    "approver_source_config": {"user_id": str(uuid.uuid4()), "user_name": "Dept Manager"},
                }
            ],
        }
    ]
    ctx = {"subject_type": "PURCHASE_ORDER", "amount": Decimal("1000.00"), "currency_code": "PEN"}

    compiled = ApprovalChainCompiler.compile_chain(matched, ctx)
    assert "chain_hash" in compiled
    assert len(compiled["chain_hash"]) == 64
    assert len(compiled["steps"]) == 1
    assert compiled["steps"][0]["step_code"] == "DEPT_MGR"


def test_separation_of_duties_enforcement() -> None:
    """Verify anti-self-approval and multi-level separation rules."""
    creator_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    step = {"sequence_number": 1, "distinct_from_creator": True}

    # 1. Creator acting as sole approver in 1-step chain raises error
    with pytest.raises(ApprovalSelfApprovalDenied):
        ApprovalSeparationOfDutiesService.validate_decision_acting_user(
            acting_user_id=creator_id,
            creator_user_id=creator_id,
            requester_user_id=creator_id,
            step_instance=step,
            total_steps_in_chain=1,
            previous_decisions=[],
        )

    # 2. Distinct user is permitted
    ApprovalSeparationOfDutiesService.validate_decision_acting_user(
        acting_user_id=other_user_id,
        creator_user_id=creator_id,
        requester_user_id=creator_id,
        step_instance=step,
        total_steps_in_chain=1,
        previous_decisions=[],
    )

    # 3. Same user approving twice in a 2-step chain raises SoD error
    prev_decs = [{"decided_by_user_id": str(other_user_id), "step_sequence_number": 1}]
    step2 = {"sequence_number": 2, "distinct_from_creator": True}
    with pytest.raises(ApprovalSeparationOfDutiesViolation):
        ApprovalSeparationOfDutiesService.validate_decision_acting_user(
            acting_user_id=other_user_id,
            creator_user_id=creator_id,
            requester_user_id=creator_id,
            step_instance=step2,
            total_steps_in_chain=2,
            previous_decisions=prev_decs,
        )


def test_conflict_detector() -> None:
    """Verify policy version conflict detection before activation."""
    version = {"id": str(uuid.uuid4())}
    conditions: list[dict] = []
    empty_steps: list[dict] = []

    with pytest.raises(ApprovalPolicyConflict):
        ApprovalPolicyConflictDetector.validate_version_for_activation(version, conditions, empty_steps)


def test_audit_seal_creation_and_verification() -> None:
    """Verify creating and verifying SHA-256 audit seal."""
    org_id = uuid.uuid4()
    req_id = uuid.uuid4()
    subj_id = uuid.uuid4()

    seal = ApprovalAuditSealService.create_seal(
        organization_id=org_id,
        approval_request_id=req_id,
        subject_type="PURCHASE_ORDER",
        subject_id=subj_id,
        subject_revision_id=None,
        subject_snapshot={"code": "OC-LIM-2026-000001", "total": "5000.00"},
        policy_versions=[{"version_id": "v1"}],
        compiled_chain={"chain_hash": "a" * 64},
        decisions=[{"id": "d1", "type": "APPROVE"}],
        integrity_events=[{"seq": 1, "hash": "b" * 64}],
        final_status="APPROVED",
        final_decision="APPROVED",
    )

    assert "seal_hash" in seal
    assert seal["hash_algorithm"] == "SHA-256"

    # Verification against matching live data
    live_data = {
        "subject_snapshot": {"code": "OC-LIM-2026-000001", "total": "5000.00"},
        "policy_versions": [{"version_id": "v1"}],
        "compiled_chain": {"chain_hash": "a" * 64},
        "decisions": [{"id": "d1", "type": "APPROVE"}],
        "integrity_events": [{"seq": 1, "hash": "b" * 64}],
    }

    res = ApprovalAuditSealService.verify_seal(seal, live_data)
    assert res["valid"] is True


def test_full_approval_engine_e2e(db_session: Session) -> None:
    """End-to-End integration test for ProcurementApprovalEngine."""
    engine = ProcurementApprovalEngine(db_session)
    org_id = uuid.uuid4()
    creator_id = uuid.uuid4()
    approver1_id = uuid.uuid4()
    approver2_id = uuid.uuid4()

    # 1. Create policy
    policy = engine.create_policy(
        organization_id=org_id,
        code="PO_STANDARD_APPROVAL",
        name="Standard PO Approval Policy",
        subject_type="PURCHASE_ORDER",
        created_by=creator_id,
        priority=100,
    )
    v_id = policy.versions[0].id

    # 2. Add Condition: TOTAL_AMOUNT >= 0
    engine.add_condition(
        version_id=v_id,
        field_code="TOTAL_AMOUNT",
        operator="GREATER_THAN_OR_EQUAL",
        value_data={"value": "0.00"},
    )

    # 3. Add Step 1 Definition
    engine.add_step_definition(
        version_id=v_id,
        step_code="LEVEL_1_APPROVAL",
        name="Direct Supervisor Approval",
        approver_source_type="FIXED_USER",
        approver_source_config={"user_id": str(approver1_id), "user_name": "Supervisor"},
        order_index=1,
    )

    # 4. Activate Version
    engine.activate_policy_version(v_id, activated_by=creator_id)

    # 5. Submit PO for approval
    po_id = uuid.uuid4()
    req = engine.submit_for_approval(
        organization_id=org_id,
        subject_type="PURCHASE_ORDER",
        subject_id=po_id,
        subject_revision_id=None,
        subject_code="OC-LIM-2026-000001",
        subject_snapshot={"po_number": "OC-LIM-2026-000001", "total": "1200.00"},
        amount="1200.00",
        currency_code="PEN",
        creator_user_id=creator_id,
        requester_user_id=creator_id,
        submitted_by=creator_id,
    )

    assert req.status == "IN_PROGRESS"
    assert len(req.steps) == 1
    assert len(req.assignments) == 1

    # 6. Approver 1 records APPROVE decision
    assignment = req.assignments[0]
    decision = engine.record_decision(
        assignment_id=assignment.id,
        acting_user_id=approver1_id,
        decision_type="APPROVE",
        reason="Approved within budget limits.",
    )

    assert decision.decision_type == "APPROVE"
    assert req.status == "APPROVED"
    assert req.audit_seal_id is not None


def test_purchase_order_approval_adapter() -> None:
    """Verify PurchaseOrderApprovalGate adapter interface in Phase 035."""
    gate = get_approval_policy()
    req = gate.resolve_requirements("DRAFT", "5000.00")
    assert req.policy_code == "PROCUREMENT_APPROVAL_ENGINE_035"
    assert req.requires_step_up is True
    assert req.step_up_factor == "COMBINED_FACE_PAD"

    # Test submission
    po_id = uuid.uuid4()
    rev_id = uuid.uuid4()
    sub_status = gate.submit_for_approval(po_id, rev_id, uuid.uuid4(), uuid.uuid4(), "NOT_SUBMITTED", "DRAFT")
    assert sub_status == "PENDING"

    # Test approval
    appr_res = gate.approve(po_id, rev_id, uuid.uuid4(), uuid.uuid4(), "PENDING", "Approved successfully.")
    assert appr_res.new_approval_status == "APPROVED"
    assert appr_res.new_po_status == "APPROVED"
