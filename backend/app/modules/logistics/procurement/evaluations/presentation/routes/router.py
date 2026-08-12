"""FastAPI REST Router for Supplier Evaluation (Phase 033)."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import (
    require_permission,
    resolve_organization_id,
)
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.procurement.evaluations.application.dto.schemas import (
    EvaluationDecisionCreate,
    EvaluationDecisionResponse,
    EvaluationTemplateCreate,
    EvaluationTemplateResponse,
    ManualScoreCreate,
    QuotationEvaluationCreate,
    QuotationEvaluationResponse,
    TemplateVersionCreate,
    TemplateVersionResponse,
)
from app.modules.logistics.procurement.evaluations.infrastructure.persistence.models import (
    SupplierEvaluationTemplateModel,
)
from app.modules.logistics.procurement.evaluations.application.services.service import evaluation_service

router = APIRouter(
    prefix="/supplier-evaluations",
    tags=["Logistics - Supplier Evaluations"],
)


# ---------------------------------------------------------------------------
# Templates & Versions
# ---------------------------------------------------------------------------
@router.get(
    "/templates",
    response_model=List[EvaluationTemplateResponse],
    summary="List supplier evaluation templates for organization",
)
def list_templates(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.supplier_evaluation_templates.read")),
    db: Session = Depends(get_db),
) -> List[EvaluationTemplateResponse]:
    org_id = resolve_organization_id(principal)
    templates = (
        db.query(SupplierEvaluationTemplateModel)
        .filter(SupplierEvaluationTemplateModel.organization_id == org_id)
        .all()
    )
    return [EvaluationTemplateResponse.model_validate(t) for t in templates]


@router.post(
    "/templates",
    response_model=EvaluationTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new supplier evaluation template",
)
def create_template(
    data: EvaluationTemplateCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.supplier_evaluation_templates.manage")),
    db: Session = Depends(get_db),
) -> EvaluationTemplateResponse:
    org_id = resolve_organization_id(principal)
    init_v = data.initial_version.model_dump() if data.initial_version else None
    template = evaluation_service.create_template(
        db=db,
        org_id=org_id,
        user_id=principal.user_id,
        code=data.code,
        name=data.name,
        description=data.description,
        scope_type=data.scope_type,
        currency_policy=data.currency_policy,
        award_policy=data.award_policy,
        initial_version_data=init_v,
    )
    db.commit()
    db.refresh(template)
    return EvaluationTemplateResponse.model_validate(template)


@router.post(
    "/templates/{template_id}/versions",
    response_model=TemplateVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new template version with criteria weights summing 100%",
)
def create_template_version(
    template_id: UUID,
    data: TemplateVersionCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.supplier_evaluation_templates.manage")),
    db: Session = Depends(get_db),
) -> TemplateVersionResponse:
    v_num = 1
    version = evaluation_service.create_template_version(
        db=db,
        template_id=template_id,
        user_id=principal.user_id,
        version_number=v_num,
        score_scale_min=data.score_scale_min,
        score_scale_max=data.score_scale_max,
        missing_data_policy=data.missing_data_policy,
        tie_policy=data.tie_policy,
        award_policy=data.award_policy,
        criteria_data=[c.model_dump() for c in data.criteria],
    )
    db.commit()
    db.refresh(version)
    return TemplateVersionResponse.model_validate(version)


@router.post(
    "/versions/{version_id}/activate",
    response_model=TemplateVersionResponse,
    summary="Activate a template version (immutable)",
)
def activate_version(
    version_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.supplier_evaluation_templates.activate")),
    db: Session = Depends(get_db),
) -> TemplateVersionResponse:
    version = evaluation_service.activate_template_version(db=db, version_id=version_id, user_id=principal.user_id)
    db.commit()
    db.refresh(version)
    return TemplateVersionResponse.model_validate(version)


# ---------------------------------------------------------------------------
# Quotation Evaluations
# ---------------------------------------------------------------------------
@router.post(
    "/evaluations",
    response_model=QuotationEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an evaluation for a closed quotation round",
)
def create_evaluation(
    data: QuotationEvaluationCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.quotation_evaluations.create")),
    db: Session = Depends(get_db),
) -> QuotationEvaluationResponse:
    org_id = resolve_organization_id(principal)
    eval_obj = evaluation_service.create_quotation_evaluation(
        db=db,
        org_id=org_id,
        user_id=principal.user_id,
        quotation_round_id=data.quotation_round_id,
        template_id=data.template_id,
        evaluation_scope=data.evaluation_scope,
        comparison_currency_code=data.comparison_currency_code,
        currency_conversion_policy=data.currency_conversion_policy,
    )
    db.commit()
    db.refresh(eval_obj)
    return QuotationEvaluationResponse.model_validate(eval_obj)


@router.post(
    "/evaluations/{evaluation_id}/calculate",
    summary="Run deterministic scoring engine for candidates",
)
def calculate_evaluation(
    evaluation_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.quotation_evaluations.calculate")),
    db: Session = Depends(get_db),
) -> dict:
    run = evaluation_service.calculate_evaluation(db=db, evaluation_id=evaluation_id, user_id=principal.user_id)
    db.commit()
    return {
        "status": "ok",
        "run_id": str(run.id),
        "run_number": run.run_number,
        "ranked_candidate_count": run.ranked_candidate_count,
    }


@router.post(
    "/evaluations/{evaluation_id}/manual-scores",
    summary="Submit evidenced manual score entry",
)
def submit_manual_score(
    evaluation_id: UUID,
    data: ManualScoreCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.quotation_evaluation_scores.manual_create")),
    db: Session = Depends(get_db),
) -> dict:
    entry = evaluation_service.submit_manual_score(
        db=db,
        evaluation_id=evaluation_id,
        candidate_id=data.candidate_id,
        criterion_id=data.criterion_id,
        user_id=principal.user_id,
        raw_score=data.raw_score,
        reason=data.reason,
        rubric_level_id=data.rubric_level_id,
        evidence_file_id=data.evidence_file_id,
    )
    db.commit()
    return {"status": "ok", "manual_score_id": str(entry.id)}


@router.post(
    "/evaluations/{evaluation_id}/decisions",
    response_model=EvaluationDecisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record award decision (DECISION_RECORDED - immutable, pending Phase 035 approval)",
)
def record_decision(
    evaluation_id: UUID,
    data: EvaluationDecisionCreate,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.quotation_evaluation_decisions.record")),
    db: Session = Depends(get_db),
) -> EvaluationDecisionResponse:
    lines = [l.model_dump() for l in data.decision_lines] if data.decision_lines else None
    decision = evaluation_service.record_decision(
        db=db,
        evaluation_id=evaluation_id,
        user_id=principal.user_id,
        decision_type=data.decision_type,
        rationale=data.rationale,
        selected_candidate_id=data.selected_candidate_id,
        selected_response_id=data.selected_response_id,
        tie_resolution_reason=data.tie_resolution_reason,
        decision_lines=lines,
    )
    db.commit()
    db.refresh(decision)
    return EvaluationDecisionResponse.model_validate(decision)
