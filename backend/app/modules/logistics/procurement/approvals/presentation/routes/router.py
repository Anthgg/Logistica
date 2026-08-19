"""FastAPI Router for Phase 035 — Procurement Approvals Engine."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import (
    current_actor_id,
    require_permission,
)
from app.modules.logistics.procurement.approvals.application.services.approval_engine import (
    ProcurementApprovalEngine,
)
from app.modules.logistics.procurement.approvals.domain.errors.exceptions import (
    ProcurementApprovalDomainError,
)
from app.modules.logistics.procurement.approvals.infrastructure.persistence.models import (
    ApprovalAssignmentModel,
    ApprovalAuditSealModel,
    ProcurementApprovalPolicyModel,
    ProcurementApprovalRequestModel,
)
from app.modules.logistics.procurement.approvals.presentation.schemas.schemas import (
    ApprovalRequestResponseSchema,
    ApprovalSubmitSchema,
    AuditSealVerificationSchema,
    DecisionRecordSchema,
    PolicyConditionCreateSchema,
    PolicyCreateSchema,
    PolicyResponseSchema,
    StepDefinitionCreateSchema,
)

router = APIRouter(
    prefix="/procurement-approvals",
    tags=["Procurement Approvals Engine"],
)


@router.post(
    "/policies",
    dependencies=[Depends(require_permission("logistics.procurement_approval_policies.create"))],
    response_model=PolicyResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new procurement approval policy",
)
def create_policy(
    payload: PolicyCreateSchema,
    user_id: UUID = Depends(current_actor_id),
    db: Session = Depends(get_db),
) -> Any:
    """Create a new policy aggregate root."""
    engine = ProcurementApprovalEngine(db)
    try:
        policy = engine.create_policy(
            organization_id=payload.organization_id,
            code=payload.code,
            name=payload.name,
            subject_type=payload.subject_type,
            created_by=user_id,
            description=payload.description,
            priority=payload.priority,
            effective_scope=payload.effective_scope,
            is_fallback=payload.is_fallback,
        )
        db.commit()
        return policy
    except ProcurementApprovalDomainError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/policies",
    dependencies=[Depends(require_permission("logistics.procurement_approval_policies.read"))],
    response_model=list[PolicyResponseSchema],
    summary="List procurement approval policies",
)
def list_policies(
    organization_id: UUID = Query(...),
    subject_type: str | None = Query(None),
    db: Session = Depends(get_db),
) -> Any:
    query = db.query(ProcurementApprovalPolicyModel).filter_by(organization_id=organization_id)
    if subject_type:
        query = query.filter_by(subject_type=subject_type.upper().strip())
    return query.all()


@router.get(
    "/policies/{policy_id}",
    dependencies=[Depends(require_permission("logistics.procurement_approval_policies.read"))],
    response_model=PolicyResponseSchema,
    summary="Get policy details",
)
def get_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    policy = db.query(ProcurementApprovalPolicyModel).filter_by(id=policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found.")
    return policy


@router.post(
    "/policy-versions/{version_id}/conditions",
    dependencies=[Depends(require_permission("logistics.procurement_approval_policies.update"))],
    status_code=status.HTTP_201_CREATED,
    summary="Add condition to policy version",
)
def add_condition(
    version_id: UUID,
    payload: PolicyConditionCreateSchema,
    db: Session = Depends(get_db),
) -> Any:
    engine = ProcurementApprovalEngine(db)
    try:
        cond = engine.add_condition(
            version_id=version_id,
            field_code=payload.field_code,
            operator=payload.operator,
            value_data=payload.value_data,
            condition_group=payload.condition_group,
            order_index=payload.order_index,
        )
        db.commit()
        return {"id": str(cond.id), "status": "ADDED"}
    except ProcurementApprovalDomainError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.post(
    "/policy-versions/{version_id}/steps",
    dependencies=[Depends(require_permission("logistics.procurement_approval_policies.update"))],
    status_code=status.HTTP_201_CREATED,
    summary="Add step definition to policy version",
)
def add_step_definition(
    version_id: UUID,
    payload: StepDefinitionCreateSchema,
    db: Session = Depends(get_db),
) -> Any:
    engine = ProcurementApprovalEngine(db)
    try:
        step = engine.add_step_definition(
            version_id=version_id,
            step_code=payload.step_code,
            name=payload.name,
            approver_source_type=payload.approver_source_type,
            approver_source_config=payload.approver_source_config,
            order_index=payload.order_index,
            execution_mode=payload.execution_mode,
            completion_mode=payload.completion_mode,
            minimum_approvals=payload.minimum_approvals,
            required_approvals=payload.required_approvals,
            step_up_level=payload.step_up_level,
            distinct_from_creator=payload.distinct_from_creator,
        )
        db.commit()
        return {"id": str(step.id), "step_code": step.step_code, "status": "ADDED"}
    except ProcurementApprovalDomainError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.post(
    "/policy-versions/{version_id}/activate",
    dependencies=[Depends(require_permission("logistics.procurement_approval_policies.activate"))],
    summary="Activate policy version",
)
def activate_policy_version(
    version_id: UUID,
    user_id: UUID = Depends(current_actor_id),
    db: Session = Depends(get_db),
) -> Any:
    engine = ProcurementApprovalEngine(db)
    try:
        v = engine.activate_policy_version(version_id=version_id, activated_by=user_id)
        db.commit()
        return {"version_id": str(v.id), "status": v.status, "activated_at": v.activated_at}
    except ProcurementApprovalDomainError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.post(
    "/requests",
    dependencies=[Depends(require_permission("logistics.procurement_approvals.read"))],
    response_model=ApprovalRequestResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a purchasing resource for approval",
)
def submit_request(
    payload: ApprovalSubmitSchema,
    user_id: UUID = Depends(current_actor_id),
    db: Session = Depends(get_db),
) -> Any:
    engine = ProcurementApprovalEngine(db)
    try:
        req = engine.submit_for_approval(
            organization_id=payload.organization_id,
            subject_type=payload.subject_type,
            subject_id=payload.subject_id,
            subject_revision_id=payload.subject_revision_id,
            subject_code=payload.subject_code,
            subject_snapshot=payload.subject_snapshot,
            amount=payload.amount,
            currency_code=payload.currency_code,
            creator_user_id=payload.creator_user_id,
            requester_user_id=payload.requester_user_id,
            submitted_by=user_id,
            cost_center_snapshot=payload.cost_center_snapshot,
            category_snapshots=payload.category_snapshots,
            branch_snapshot=payload.branch_snapshot,
        )
        db.commit()
        return req
    except ProcurementApprovalDomainError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/requests/{request_id}",
    dependencies=[Depends(require_permission("logistics.procurement_approvals.read"))],
    response_model=ApprovalRequestResponseSchema,
    summary="Get approval request status details",
)
def get_request(
    request_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    req = db.query(ProcurementApprovalRequestModel).filter_by(id=request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    return req


@router.get(
    "/assignments/my-pending",
    dependencies=[Depends(require_permission("logistics.procurement_approvals.read"))],
    summary="Get pending assignments for active user",
)
def get_my_pending_assignments(
    user_id: UUID = Depends(current_actor_id),
    db: Session = Depends(get_db),
) -> Any:
    assignments = (
        db.query(ApprovalAssignmentModel)
        .filter_by(effective_approver_user_id=user_id, status="ASSIGNED")
        .all()
    )
    return [
        {
            "assignment_id": str(a.id),
            "approval_request_id": str(a.approval_request_id),
            "step_instance_id": str(a.step_instance_id),
            "source_type": a.assignment_source_type,
            "assigned_at": a.assigned_at,
        }
        for a in assignments
    ]


@router.post(
    "/assignments/{assignment_id}/decision",
    dependencies=[Depends(require_permission("logistics.procurement_approvals.decide"))],
    summary="Record an approval decision (APPROVE / REJECT / RETURN)",
)
def record_decision(
    assignment_id: UUID,
    payload: DecisionRecordSchema,
    user_id: UUID = Depends(current_actor_id),
    db: Session = Depends(get_db),
) -> Any:
    engine = ProcurementApprovalEngine(db)
    try:
        decision = engine.record_decision(
            assignment_id=assignment_id,
            acting_user_id=user_id,
            decision_type=payload.decision_type,
            reason=payload.reason,
            conditions=payload.conditions,
            step_up_assurance_level=payload.step_up_assurance_level,
        )
        db.commit()
        return {
            "decision_id": str(decision.id),
            "decision_type": decision.decision_type,
            "status": decision.status,
            "decision_at": decision.decision_at,
        }
    except ProcurementApprovalDomainError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.http_status, detail=exc.message)


@router.get(
    "/requests/{request_id}/audit-seal",
    dependencies=[Depends(require_permission("logistics.procurement_approvals.read"))],
    summary="Get approval request audit seal",
)
def get_audit_seal(
    request_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    seal = db.query(ApprovalAuditSealModel).filter_by(approval_request_id=request_id).first()
    if not seal:
        raise HTTPException(status_code=404, detail="Audit seal not found for request.")
    return {
        "seal_id": str(seal.id),
        "approval_request_id": str(seal.approval_request_id),
        "seal_hash": seal.seal_hash,
        "signature_algorithm": seal.signature_algorithm,
        "verification_status": seal.verification_status,
        "sealed_at": seal.sealed_at,
    }
