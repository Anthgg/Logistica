"""Phase 041. Quality inspection plan presentation router."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import (
    get_logistics_principal,
    require_permission,
    resolve_organization_id,
    verify_csrf,
)
from app.modules.logistics.principal import LogisticsPrincipal

from app.modules.logistics.inbound.reception_differences.presentation.quality_plan_schemas import (
    QualityPlanCreate,
    QualityPlanUpdate,
    QualityPlanResponse,
    QualityPlanSummary,
    QualityPlanVersionCreate,
    QualityPlanVersionResponse,
    QualityPlanScopeCreate,
    QualityPlanScopeResponse,
    QualityControlCreate,
    QualityControlUpdate,
    QualityControlResponse,
    QualityToleranceCreate,
    QualityToleranceResponse,
    QualitySamplingCreate,
    QualitySamplingResponse,
    QualityCertificateCreate,
    QualityCertificateResponse,
    QualityConditionCreate,
    QualityConditionResponse,
    QualityPlanReferenceFileCreate,
    QualityPlanReferenceFileResponse,
    QualityPlanConflictResponse,
    QualityPlanResolutionResponse,
    QualityPlanValidationResponse,
    QualityPlanIntegrityResponse,
    QualityPlanMetricsResponse,
    QualityPlanSnapshotResponse,
    QualityPlanUsageProjectionResponse,
    QualityPlanFutureTemplateCreate,
    QualityPlanFutureTemplateResponse,
)

from app.modules.logistics.inbound.reception_differences.application.services.quality_plan_service import (
    QualityInspectionPlanService,
)
from app.modules.logistics.inbound.reception_differences.application.services.quality_version_service import (
    QualityPlanVersionService,
)
from app.modules.logistics.inbound.reception_differences.application.services.quality_scope_service import (
    QualityPlanScopeService,
)
from app.modules.logistics.inbound.reception_differences.application.services.quality_control_service import (
    QualityControlService,
)
from app.modules.logistics.inbound.reception_differences.application.services.quality_tolerance_sampling_service import (
    QualityToleranceService,
    QualitySamplingService,
)
from app.modules.logistics.inbound.reception_differences.application.services.quality_certificate_condition_service import (
    QualityCertificateService,
    QualityConditionService,
)
from app.modules.logistics.inbound.reception_differences.application.services.quality_conflict_service import (
    QualityConflictDetectionService,
)
from app.modules.logistics.inbound.reception_differences.application.services.quality_validation_service import (
    QualityPlanValidationService,
)
from app.modules.logistics.inbound.reception_differences.application.services.quality_snapshot_service import (
    QualityPlanSnapshotProvider,
)
from app.modules.logistics.inbound.reception_differences.application.services.quality_integrity_service import (
    QualityPlanIntegrityService,
)
from app.modules.logistics.inbound.reception_differences.application.services.quality_metrics_service import (
    QualityPlanMetricsProjectionService,
)
from app.modules.logistics.inbound.reception_differences.application.services.quality_reference_file_service import (
    QualityPlanReferenceFileService,
)

from app.modules.logistics.inbound.arrival_notices.application.services.idempotency import (
    get_idempotent_response,
    save_idempotent_response,
)


router = APIRouter(tags=["Quality Inspection Plans (Phase 041)"])

IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)]


def org(principal: LogisticsPrincipal) -> UUID:
    return resolve_organization_id(principal)


def _idempotent(
    db: Session,
    organization_id: UUID,
    idempotency_key: str,
    operation: str,
    payload: dict,
    execute_fn,
):
    existing = get_idempotent_response(db, organization_id, operation, idempotency_key, payload)
    if existing:
        return existing
    result = execute_fn()
    save_idempotent_response(db, organization_id, None, operation, idempotency_key, payload, result)
    return result


# ─── Plan CRUD ──────────────────────────────────────────────────────────────


@router.get(
    "/quality-inspection-plans",
    response_model=dict,
)
def list_quality_plans(
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
    status_filter: str | None = Query(None, alias="status"),
    family: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = "created_at",
    sort_direction: str = "desc",
):
    organization_id = org(principal)
    rows, total = QualityInspectionPlanService(db).list_plans(
        organization_id,
        status=status_filter,
        family=family,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )
    return {
        "items": [QualityPlanSummary.model_validate(r).model_dump() for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/quality-inspection-plans/{plan_id}",
    response_model=QualityPlanResponse,
)
def get_quality_plan(
    plan_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
):
    return QualityInspectionPlanService(db).get_plan(plan_id, org(principal))


@router.post(
    "/quality-inspection-plans",
    response_model=QualityPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quality_plan(
    body: QualityPlanCreate,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.create"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityInspectionPlanService(db).create_plan(org(principal), body.model_dump(), principal)
    return _idempotent(db, org(principal), idempotency_key, "quality_plan.create", body.model_dump(), execute)


@router.patch(
    "/quality-inspection-plans/{plan_id}",
    response_model=QualityPlanResponse,
)
def update_quality_plan(
    plan_id: UUID,
    body: QualityPlanUpdate,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.update"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityInspectionPlanService(db).update_plan(plan_id, org(principal), body.model_dump(exclude_none=True), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.update:{plan_id}", body.model_dump(), execute)


@router.post(
    "/quality-inspection-plans/{plan_id}/activate",
    response_model=QualityPlanResponse,
)
def activate_quality_plan(
    plan_id: UUID,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.activate"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityInspectionPlanService(db).transition_plan(plan_id, org(principal), "ACTIVE", principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.activate:{plan_id}", {}, execute)


@router.post(
    "/quality-inspection-plans/{plan_id}/deactivate",
    response_model=QualityPlanResponse,
)
def deactivate_quality_plan(
    plan_id: UUID,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.deactivate"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityInspectionPlanService(db).transition_plan(plan_id, org(principal), "INACTIVE", principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.deactivate:{plan_id}", {}, execute)


@router.post(
    "/quality-inspection-plans/{plan_id}/archive",
    response_model=QualityPlanResponse,
)
def archive_quality_plan(
    plan_id: UUID,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.archive"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityInspectionPlanService(db).transition_plan(plan_id, org(principal), "ARCHIVED", principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.archive:{plan_id}", {}, execute)


@router.delete(
    "/quality-inspection-plans/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_quality_plan(
    plan_id: UUID,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.delete"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        QualityInspectionPlanService(db).delete_plan(plan_id, org(principal), principal)
        return None
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.delete:{plan_id}", {}, execute)


# ─── Versions ───────────────────────────────────────────────────────────────


@router.get(
    "/quality-inspection-plans/{plan_id}/versions",
    response_model=dict,
)
def list_quality_plan_versions(
    plan_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    rows, total = QualityPlanVersionService(db).list_versions(plan_id, org(principal), page=page, page_size=page_size)
    return {
        "items": [QualityPlanVersionResponse.model_validate(r).model_dump() for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/quality-inspection-plans/versions/{version_id}",
    response_model=QualityPlanVersionResponse,
)
def get_quality_plan_version(
    version_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
):
    return QualityPlanVersionService(db).get_version(version_id, org(principal))


@router.post(
    "/quality-inspection-plans/{plan_id}/versions",
    response_model=QualityPlanVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quality_plan_version(
    plan_id: UUID,
    body: QualityPlanVersionCreate,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.create_version"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityPlanVersionService(db).create_version(plan_id, org(principal), body.model_dump(), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.create_version:{plan_id}", body.model_dump(), execute)


@router.post(
    "/quality-inspection-plans/versions/{version_id}/activate",
    response_model=QualityPlanVersionResponse,
)
def activate_quality_plan_version(
    version_id: UUID,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.activate_version"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityPlanVersionService(db).activate_version(version_id, org(principal), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.activate_version:{version_id}", {}, execute)


@router.post(
    "/quality-inspection-plans/versions/{version_id}/retire",
    response_model=QualityPlanVersionResponse,
)
def retire_quality_plan_version(
    version_id: UUID,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.retire_version"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityPlanVersionService(db).retire_version(version_id, org(principal), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.retire_version:{version_id}", {}, execute)


@router.post(
    "/quality-inspection-plans/versions/{version_id}/hash",
    response_model=dict,
)
def compute_version_hash(
    version_id: UUID,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.update"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        h = QualityPlanVersionService(db).compute_content_hash(version_id, org(principal))
        return {"version_id": str(version_id), "content_hash": h}
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.hash_version:{version_id}", {}, execute)


# ─── Scopes ─────────────────────────────────────────────────────────────────


@router.get(
    "/quality-inspection-plans/{plan_id}/scopes",
    response_model=list[QualityPlanScopeResponse],
)
def list_quality_plan_scopes(
    plan_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
):
    rows = QualityPlanScopeService(db).list_scopes(plan_id, org(principal))
    return [QualityPlanScopeResponse.model_validate(r).model_dump() for r in rows]


@router.get(
    "/quality-inspection-plans/scopes/{scope_id}",
    response_model=QualityPlanScopeResponse,
)
def get_quality_plan_scope(
    scope_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
):
    return QualityPlanScopeService(db).get_scope(scope_id, org(principal))


@router.post(
    "/quality-inspection-plans/{plan_id}/scopes",
    response_model=QualityPlanScopeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quality_plan_scope(
    plan_id: UUID,
    body: QualityPlanScopeCreate,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.create_scope"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityPlanScopeService(db).create_scope(plan_id, org(principal), body.model_dump(), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.create_scope:{plan_id}", body.model_dump(), execute)


@router.patch(
    "/quality-inspection-plans/scopes/{scope_id}",
    response_model=QualityPlanScopeResponse,
)
def update_quality_plan_scope(
    scope_id: UUID,
    body: QualityPlanScopeCreate,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.update_scope"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityPlanScopeService(db).update_scope(scope_id, org(principal), body.model_dump(exclude_none=True), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.update_scope:{scope_id}", body.model_dump(), execute)


@router.delete(
    "/quality-inspection-plans/scopes/{scope_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_quality_plan_scope(
    scope_id: UUID,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.delete_scope"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        QualityPlanScopeService(db).delete_scope(scope_id, org(principal), principal)
        return None
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.delete_scope:{scope_id}", {}, execute)


# ─── Controls ───────────────────────────────────────────────────────────────


@router.get(
    "/quality-inspection-plans/{plan_id}/controls",
    response_model=dict,
)
def list_quality_plan_controls(
    plan_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
    scope_id: UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    rows, total = QualityControlService(db).list_controls(plan_id, org(principal), scope_id=scope_id, page=page, page_size=page_size)
    return {
        "items": [QualityControlResponse.model_validate(r).model_dump() for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/quality-inspection-plans/controls/{control_id}",
    response_model=QualityControlResponse,
)
def get_quality_plan_control(
    control_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
):
    return QualityControlService(db).get_control(control_id, org(principal))


@router.post(
    "/quality-inspection-plans/{plan_id}/controls",
    response_model=QualityControlResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quality_plan_control(
    plan_id: UUID,
    body: QualityControlCreate,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.create_control"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityControlService(db).create_control(plan_id, org(principal), body.model_dump(), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.create_control:{plan_id}", body.model_dump(), execute)


@router.patch(
    "/quality-inspection-plans/controls/{control_id}",
    response_model=QualityControlResponse,
)
def update_quality_plan_control(
    control_id: UUID,
    body: QualityControlUpdate,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.update_control"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityControlService(db).update_control(control_id, org(principal), body.model_dump(exclude_none=True), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.update_control:{control_id}", body.model_dump(), execute)


@router.delete(
    "/quality-inspection-plans/controls/{control_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_quality_plan_control(
    control_id: UUID,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.delete_control"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        QualityControlService(db).delete_control(control_id, org(principal), principal)
        return None
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.delete_control:{control_id}", {}, execute)


# ─── Tolerances ─────────────────────────────────────────────────────────────


@router.get(
    "/quality-inspection-plans/controls/{control_id}/tolerances",
    response_model=list[QualityToleranceResponse],
)
def list_quality_plan_tolerances(
    control_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
):
    rows = QualityToleranceService(db).list_tolerances(control_id)
    return [QualityToleranceResponse.model_validate(r).model_dump() for r in rows]


@router.get(
    "/quality-inspection-plans/tolerances/{tolerance_id}",
    response_model=QualityToleranceResponse,
)
def get_quality_plan_tolerance(
    tolerance_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
):
    return QualityToleranceService(db).get_tolerance(tolerance_id, org(principal))


@router.post(
    "/quality-inspection-plans/controls/{control_id}/tolerances",
    response_model=QualityToleranceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quality_plan_tolerance(
    control_id: UUID,
    body: QualityToleranceCreate,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.create_tolerance"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityToleranceService(db).create_tolerance(control_id, body.model_dump(), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.create_tolerance:{control_id}", body.model_dump(), execute)


@router.patch(
    "/quality-inspection-plans/tolerances/{tolerance_id}",
    response_model=QualityToleranceResponse,
)
def update_quality_plan_tolerance(
    tolerance_id: UUID,
    body: QualityToleranceCreate,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.update_tolerance"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityToleranceService(db).update_tolerance(tolerance_id, body.model_dump(exclude_none=True), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.update_tolerance:{tolerance_id}", body.model_dump(), execute)


@router.delete(
    "/quality-inspection-plans/tolerances/{tolerance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_quality_plan_tolerance(
    tolerance_id: UUID,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.delete_tolerance"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        QualityToleranceService(db).delete_tolerance(tolerance_id, principal)
        return None
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.delete_tolerance:{tolerance_id}", {}, execute)


# ─── Sampling ───────────────────────────────────────────────────────────────


@router.get(
    "/quality-inspection-plans/controls/{control_id}/samplings",
    response_model=list[QualitySamplingResponse],
)
def list_quality_plan_samplings(
    control_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
):
    rows = QualitySamplingService(db).list_samplings(control_id)
    return [QualitySamplingResponse.model_validate(r).model_dump() for r in rows]


@router.post(
    "/quality-inspection-plans/controls/{control_id}/samplings",
    response_model=QualitySamplingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quality_plan_sampling(
    control_id: UUID,
    body: QualitySamplingCreate,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.create_sampling"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualitySamplingService(db).create_sampling(control_id, body.model_dump(), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.create_sampling:{control_id}", body.model_dump(), execute)


@router.patch(
    "/quality-inspection-plans/samplings/{sampling_id}",
    response_model=QualitySamplingResponse,
)
def update_quality_plan_sampling(
    sampling_id: UUID,
    body: QualitySamplingCreate,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.update_sampling"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualitySamplingService(db).update_sampling(sampling_id, body.model_dump(exclude_none=True), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.update_sampling:{sampling_id}", body.model_dump(), execute)


@router.delete(
    "/quality-inspection-plans/samplings/{sampling_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_quality_plan_sampling(
    sampling_id: UUID,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.delete_sampling"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        QualitySamplingService(db).delete_sampling(sampling_id, principal)
        return None
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.delete_sampling:{sampling_id}", {}, execute)


# ─── Certificates ───────────────────────────────────────────────────────────


@router.get(
    "/quality-inspection-plans/controls/{control_id}/certificates",
    response_model=list[QualityCertificateResponse],
)
def list_quality_plan_certificates(
    control_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
):
    rows = QualityCertificateService(db).list_certificates(control_id)
    return [QualityCertificateResponse.model_validate(r).model_dump() for r in rows]


@router.post(
    "/quality-inspection-plans/controls/{control_id}/certificates",
    response_model=QualityCertificateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quality_plan_certificate(
    control_id: UUID,
    body: QualityCertificateCreate,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.create_certificate"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityCertificateService(db).create_certificate(control_id, body.model_dump(), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.create_certificate:{control_id}", body.model_dump(), execute)


@router.patch(
    "/quality-inspection-plans/certificates/{certificate_id}",
    response_model=QualityCertificateResponse,
)
def update_quality_plan_certificate(
    certificate_id: UUID,
    body: QualityCertificateCreate,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.update_certificate"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityCertificateService(db).update_certificate(certificate_id, body.model_dump(exclude_none=True), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.update_certificate:{certificate_id}", body.model_dump(), execute)


@router.delete(
    "/quality-inspection-plans/certificates/{certificate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_quality_plan_certificate(
    certificate_id: UUID,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.delete_certificate"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        QualityCertificateService(db).delete_certificate(certificate_id, principal)
        return None
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.delete_certificate:{certificate_id}", {}, execute)


# ─── Conditions ─────────────────────────────────────────────────────────────


@router.get(
    "/quality-inspection-plans/controls/{control_id}/conditions",
    response_model=list[QualityConditionResponse],
)
def list_quality_plan_conditions(
    control_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
):
    rows = QualityConditionService(db).list_conditions(control_id)
    return [QualityConditionResponse.model_validate(r).model_dump() for r in rows]


@router.post(
    "/quality-inspection-plans/controls/{control_id}/conditions",
    response_model=QualityConditionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quality_plan_condition(
    control_id: UUID,
    body: QualityConditionCreate,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.create_condition"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityConditionService(db).create_condition(control_id, body.model_dump(), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.create_condition:{control_id}", body.model_dump(), execute)


@router.patch(
    "/quality-inspection-plans/conditions/{condition_id}",
    response_model=QualityConditionResponse,
)
def update_quality_plan_condition(
    condition_id: UUID,
    body: QualityConditionCreate,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.update_condition"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityConditionService(db).update_condition(condition_id, body.model_dump(exclude_none=True), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.update_condition:{condition_id}", body.model_dump(), execute)


@router.delete(
    "/quality-inspection-plans/conditions/{condition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_quality_plan_condition(
    condition_id: UUID,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.delete_condition"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        QualityConditionService(db).delete_condition(condition_id, principal)
        return None
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.delete_condition:{condition_id}", {}, execute)


# ─── Reference Files ────────────────────────────────────────────────────────


@router.get(
    "/quality-inspection-plans/{plan_id}/reference-files",
    response_model=list[QualityPlanReferenceFileResponse],
)
def list_quality_plan_reference_files(
    plan_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
):
    rows = QualityPlanReferenceFileService(db).list_reference_files(plan_id, org(principal))
    return [QualityPlanReferenceFileResponse.model_validate(r).model_dump() for r in rows]


@router.post(
    "/quality-inspection-plans/{plan_id}/reference-files",
    response_model=QualityPlanReferenceFileResponse,
    status_code=status.HTTP_201_CREATED,
)
def link_quality_plan_reference_file(
    plan_id: UUID,
    body: QualityPlanReferenceFileCreate,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.link_reference_file"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        return QualityPlanReferenceFileService(db).link_reference_file(plan_id, org(principal), body.model_dump(), principal)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.link_ref:{plan_id}", body.model_dump(), execute)


@router.delete(
    "/quality-inspection-plans/reference-files/{reference_file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unlink_quality_plan_reference_file(
    reference_file_id: UUID,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.unlink_reference_file"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        QualityPlanReferenceFileService(db).unlink_reference_file(reference_file_id, org(principal), principal)
        return None
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.unlink_ref:{reference_file_id}", {}, execute)


# ─── Conflict Detection ────────────────────────────────────────────────────


@router.get(
    "/quality-inspection-plans/conflicts",
    response_model=list[QualityPlanConflictResponse],
)
def detect_quality_plan_conflicts(
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
    product_id: UUID | None = None,
    product_category_id: UUID | None = None,
    warehouse_id: UUID | None = None,
    branch_id: UUID | None = None,
):
    conflicts = QualityConflictDetectionService(db).detect_conflicts(
        org(principal),
        product_id=product_id,
        product_category_id=product_category_id,
        warehouse_id=warehouse_id,
        branch_id=branch_id,
    )
    return conflicts


# ─── Resolution ─────────────────────────────────────────────────────────────


@router.get(
    "/quality-inspection-plans/resolve",
    response_model=QualityPlanResolutionResponse,
)
def resolve_quality_plan(
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
    product_id: UUID | None = None,
    product_category_id: UUID | None = None,
    warehouse_id: UUID | None = None,
    branch_id: UUID | None = None,
):
    result = QualityConflictDetectionService(db).resolve_for_context(
        org(principal),
        product_id=product_id,
        product_category_id=product_category_id,
        warehouse_id=warehouse_id,
        branch_id=branch_id,
    )
    return QualityPlanResolutionResponse(**result)


# ─── Validation ─────────────────────────────────────────────────────────────


@router.get(
    "/quality-inspection-plans/{plan_id}/validate",
    response_model=QualityPlanValidationResponse,
)
def validate_quality_plan(
    plan_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
):
    result = QualityPlanValidationService(db).validate_plan(plan_id, org(principal))
    return QualityPlanValidationResponse(**result)


# ─── Snapshot ───────────────────────────────────────────────────────────────


@router.get(
    "/quality-inspection-plans/{plan_id}/snapshot",
    response_model=QualityPlanSnapshotResponse,
)
def get_quality_plan_snapshot(
    plan_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
):
    snapshot = QualityPlanSnapshotProvider(db).capture(plan_id, org(principal))
    return QualityPlanSnapshotResponse(**snapshot)


# ─── Integrity ──────────────────────────────────────────────────────────────


@router.get(
    "/quality-inspection-plans/{plan_id}/integrity",
    response_model=QualityPlanIntegrityResponse,
)
def verify_quality_plan_integrity(
    plan_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
):
    result = QualityPlanIntegrityService(db).verify(plan_id, org(principal))
    return QualityPlanIntegrityResponse(**result)


# ─── Metrics ────────────────────────────────────────────────────────────────


@router.get(
    "/quality-inspection-plans/{plan_id}/metrics",
    response_model=QualityPlanMetricsResponse,
)
def get_quality_plan_metrics(
    plan_id: UUID,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
):
    result = QualityPlanMetricsProjectionService(db).get_metrics(plan_id)
    if not result:
        result = QualityPlanMetricsProjectionService(db).update_metrics(plan_id, org(principal))
    return QualityPlanMetricsResponse(**result)


@router.post(
    "/quality-inspection-plans/{plan_id}/metrics/recalculate",
    response_model=QualityPlanMetricsResponse,
)
def recalculate_quality_plan_metrics(
    plan_id: UUID,
    idempotency_key: IdempotencyKey,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.update"))],
    db: Session = Depends(get_db),
    _csrf: Any = Depends(verify_csrf),
):
    def execute():
        result = QualityPlanMetricsProjectionService(db).update_metrics(plan_id, org(principal))
        return QualityPlanMetricsResponse(**result)
    return _idempotent(db, org(principal), idempotency_key, f"quality_plan.metrics:{plan_id}", {}, execute)


# ─── Future Template Preview ───────────────────────────────────────────────


@router.post(
    "/quality-inspection-plans/future-template-preview",
    response_model=QualityPlanFutureTemplateResponse,
)
def preview_future_template(
    body: QualityPlanFutureTemplateCreate,
    principal: Annotated[LogisticsPrincipal, Depends(require_permission("logistics.quality_plan.read"))],
    db: Session = Depends(get_db),
):
    from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.quality_plan_models import (
        QualityInspectionPlanModel,
        QualityControlDefinitionModel,
    )
    from sqlalchemy import select

    result = QualityConflictDetectionService(db).resolve_for_context(
        org(principal),
        product_id=body.product_id,
        product_category_id=body.product_category_id,
        warehouse_id=body.warehouse_id,
        branch_id=body.branch_id,
    )

    plan_code = None
    plan_name = None
    control_count = 0
    is_applicable = result.get("resolved_plan_id") is not None

    if result.get("resolved_plan_id"):
        plan = db.scalar(
            select(QualityInspectionPlanModel).where(
                QualityInspectionPlanModel.id == UUID(result["resolved_plan_id"]),
            )
        )
        if plan:
            plan_code = plan.plan_code
            plan_name = plan.plan_name
            control_count = db.scalar(
                select(func.count()).select_from(
                    select(QualityControlDefinitionModel).where(
                        QualityControlDefinitionModel.plan_id == plan.id,
                    ).subquery()
                )
            ) or 0

    return QualityPlanFutureTemplateResponse(
        resolved_plan_id=result.get("resolved_plan_id"),
        resolution_specificity=result.get("resolution_specificity", "NO_PLAN"),
        plan_code=plan_code,
        plan_name=plan_name,
        is_applicable=is_applicable,
        control_count=control_count,
    )
