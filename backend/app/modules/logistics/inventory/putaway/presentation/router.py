"""Phase 043 — Putaway router with ~60 endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.auth_dependencies import require_permission, resolve_organization_id
from app.modules.logistics.principal import LogisticsPrincipal

from .schemas import (
    PolicyCreateRequest,
    PolicyVersionCreateRequest,
    PolicyResponse,
    PolicyVersionResponse,
    PolicyListResponse,
    CompatibilityRuleCreateRequest,
    CompatibilityRuleResponse,
    CompatibilityEvaluationResponse,
    CapacityProfileCreateRequest,
    CapacityProfileResponse,
    CapacityProjectionResponse,
    ProximityProfileCreateRequest,
    ProximityProfileResponse,
    ProximityResultResponse,
    TravelCostScoreResponse,
    RecommendationRequest,
    RecommendationRunResponse,
    CandidateResponse,
    OrderCreateRequest,
    OrderCancelRequest,
    OrderResponse,
    OrderListResponse,
    OrderRevisionResponse,
    TaskCreateRequest,
    TaskAssignRequest,
    TaskResponse,
    TaskListResponse,
    TaskDestinationResponse,
    TaskAssignmentResponse,
    ReservationCreateRequest,
    ReservationResponse,
    ExecutionSessionCreateRequest,
    ExecutionSessionResponse,
    ScanRecordRequest,
    ScanValidationRequest,
    ScanEventResponse,
    PlacementConfirmRequest,
    PlacementConfirmationResponse,
    OperationalPlacementResponse,
    OverrideRequest,
    OverrideApprovalRequest,
    OverrideResponse,
    ExceptionReportRequest,
    ExceptionResolveRequest,
    ExceptionResponse,
    PauseRequest,
    PauseResponse,
    PlacementProjectionResponse,
)
from ..application.services.services import PutawayApplicationService
from ..domain.services.policy_service import PutawayPolicyService
from ..domain.services.compatibility_service import StorageCompatibilityService
from ..domain.services.capacity_service import CapacityService
from ..domain.services.proximity_service import ProximityService

router = APIRouter(prefix="/putaway", tags=["Logistics - Putaway"])


# =============================================================================
# Policies
# =============================================================================
@router.get(
    "/policies",
    response_model=PolicyListResponse,
    summary="Listar politicas de putaway",
)
def list_policies(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.policies.read")),
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
):
    org_id = resolve_organization_id(principal)
    svc = PutawayPolicyService(db)
    items, total = svc._policy_repo.list(
        org_id, page=page, page_size=page_size, search=search,
        status=status_filter, sort_by=sort_by, sort_order=sort_order,
    )
    return PolicyListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post(
    "/policies",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear politica de putaway",
)
def create_policy(
    body: PolicyCreateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.policies.create")),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    svc = PutawayPolicyService(db)
    policy = svc.create_policy(
        org_id, code=body.code, name=body.name,
        description=body.description, created_by=principal.user_id,
    )
    db.commit()
    return policy


@router.post(
    "/policies/{policy_id}/activate",
    response_model=PolicyResponse,
    summary="Activar politica de putaway",
)
def activate_policy(
    policy_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.policies.update")),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    svc = PutawayPolicyService(db)
    policy = svc.activate_policy(policy_id, org_id, activated_by=principal.user_id)
    db.commit()
    return policy


@router.post(
    "/policies/{policy_id}/versions",
    response_model=PolicyVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear version de politica",
)
def create_policy_version(
    policy_id: UUID,
    body: PolicyVersionCreateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.policies.create")),
    db: Session = Depends(get_db),
):
    svc = PutawayPolicyService(db)
    version = svc.create_version(policy_id, created_by=principal.user_id, **body.model_dump(exclude_unset=True))
    db.commit()
    return version


@router.get(
    "/policies/{policy_id}/versions",
    summary="Listar versiones de politica",
)
def list_policy_versions(
    policy_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.policies.read")),
    db: Session = Depends(get_db),
):
    svc = PutawayPolicyService(db)
    versions = svc._version_repo.list_by_policy(policy_id)
    return versions


@router.post(
    "/policies/versions/{version_id}/activate",
    response_model=PolicyVersionResponse,
    summary="Activar version de politica",
)
def activate_policy_version(
    version_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.policies.update")),
    db: Session = Depends(get_db),
):
    svc = PutawayPolicyService(db)
    version = svc.activate_version(version_id, activated_by=principal.user_id)
    db.commit()
    return version


# =============================================================================
# Compatibility Rules
# =============================================================================
@router.get(
    "/compatibility-rules",
    summary="Listar reglas de compatibilidad",
)
def list_compatibility_rules(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.policies.read")),
    db: Session = Depends(get_db),
    warehouse_id: UUID = Query(...),
    rule_type: str | None = Query(default=None),
    product_id: UUID | None = Query(default=None),
    location_id: UUID | None = Query(default=None),
):
    svc = StorageCompatibilityService(db)
    rules = svc._rule_repo.list_by_warehouse(
        warehouse_id, rule_type=rule_type, product_id=product_id, location_id=location_id,
    )
    return rules


@router.post(
    "/compatibility-rules",
    response_model=CompatibilityRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear regla de compatibilidad",
)
def create_compatibility_rule(
    body: CompatibilityRuleCreateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.policies.create")),
    db: Session = Depends(get_db),
):
    from ..infrastructure.persistence.models import StorageCompatibilityRuleModel
    rule = StorageCompatibilityRuleModel(**body.model_dump(exclude_unset=True))
    svc = StorageCompatibilityService(db)
    result = svc._rule_repo.create(rule)
    db.commit()
    return result


@router.get(
    "/compatibility/evaluate",
    response_model=CompatibilityEvaluationResponse,
    summary="Evaluar compatibilidad producto-ubicacion",
)
def evaluate_compatibility(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.policies.read")),
    db: Session = Depends(get_db),
    warehouse_id: UUID = Query(...),
    location_id: UUID = Query(...),
    product_id: UUID | None = Query(default=None),
    product_category_id: UUID | None = Query(default=None),
    location_type: str | None = Query(default=None),
):
    svc = StorageCompatibilityService(db)
    result = svc.evaluate(
        warehouse_id, location_id,
        product_id=product_id, product_category_id=product_category_id,
        location_type=location_type,
    )
    return result


# =============================================================================
# Capacity
# =============================================================================
@router.get(
    "/capacity/projections",
    summary="Listar proyecciones de capacidad",
)
def list_capacity_projections(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.policies.read")),
    db: Session = Depends(get_db),
    warehouse_id: UUID = Query(...),
    location_id: UUID = Query(default=None),
):
    org_id = resolve_organization_id(principal)
    svc = CapacityService(db)
    if location_id:
        profiles = svc._profile_repo.list_by_location(location_id)
        results = []
        for p in profiles:
            proj = svc._projection_repo.get_or_none(org_id, warehouse_id, location_id, p.id)
            if proj:
                results.append(proj)
        return results
    return []


@router.get(
    "/capacity/profiles/{location_id}",
    summary="Obtener perfiles de capacidad de ubicacion",
)
def get_capacity_profiles(
    location_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.policies.read")),
    db: Session = Depends(get_db),
):
    svc = CapacityService(db)
    return svc.get_available_capacity(
        resolve_organization_id(principal),
        principal.default_warehouse_id or UUID(int=0),
        location_id,
    )


@router.post(
    "/capacity/profiles",
    response_model=CapacityProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear perfil de capacidad",
)
def create_capacity_profile(
    body: CapacityProfileCreateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.policies.create")),
    db: Session = Depends(get_db),
):
    svc = CapacityService(db)
    profile = svc.create_profile(
        warehouse_location_id=body.warehouse_location_id,
        capacity_type=body.capacity_type,
        maximum_value=body.maximum_value,
        unit_id=body.unit_id,
        safety_margin_value=body.safety_margin_value,
    )
    db.commit()
    return profile


# =============================================================================
# Proximity
# =============================================================================
@router.get(
    "/proximity/profiles",
    summary="Listar perfiles de proximidad",
)
def list_proximity_profiles(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.policies.read")),
    db: Session = Depends(get_db),
    warehouse_id: UUID = Query(...),
    source_location_id: UUID = Query(default=None),
    metric_type: str | None = Query(default=None),
):
    svc = ProximityService(db)
    if source_location_id:
        return svc.list_reachable_locations(warehouse_id, source_location_id, metric_type=metric_type)
    return []


@router.post(
    "/proximity/profiles",
    response_model=ProximityProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear perfil de proximidad",
)
def create_proximity_profile(
    body: ProximityProfileCreateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.policies.create")),
    db: Session = Depends(get_db),
):
    svc = ProximityService(db)
    profile = svc.create_profile(
        warehouse_id=body.warehouse_id,
        source_location_id=body.source_location_id,
        target_zone_id=body.target_zone_id,
        target_location_id=body.target_location_id,
        metric_type=body.metric_type,
        metric_value=body.metric_value,
        metric_unit=body.metric_unit,
        source_type=body.source_type,
    )
    db.commit()
    return profile


@router.get(
    "/proximity/distance",
    response_model=ProximityResultResponse,
    summary="Consultar distancia entre ubicaciones",
)
def get_distance(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.policies.read")),
    db: Session = Depends(get_db),
    warehouse_id: UUID = Query(...),
    source_id: UUID = Query(...),
    target_id: UUID = Query(...),
):
    svc = ProximityService(db)
    result = svc.get_distance(warehouse_id, source_id, target_id)
    if not result:
        return None
    return result


@router.get(
    "/proximity/travel-cost",
    response_model=TravelCostScoreResponse,
    summary="Calcular costo de viaje",
)
def get_travel_cost(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.policies.read")),
    db: Session = Depends(get_db),
    warehouse_id: UUID = Query(...),
    source_id: UUID = Query(...),
    target_id: UUID = Query(...),
):
    svc = ProximityService(db)
    return svc.calculate_travel_cost_score(warehouse_id, source_id, target_id)


# =============================================================================
# Recommendations
# =============================================================================
@router.post(
    "/recommendations",
    response_model=RecommendationRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ejecutar motor de recomendaciones",
)
def request_recommendation(
    body: RecommendationRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    svc = PutawayApplicationService(db)

    from ..domain.services.eligibility_service import EligibilityService
    elig_svc = EligibilityService(db)
    source = elig_svc.require_eligible(body.source_allocation_id)

    run = svc.request_recommendation(
        organization_id=org_id,
        warehouse_id=principal.default_warehouse_id or UUID(int=0),
        source_allocation_id=body.source_allocation_id,
        requested_quantity=body.requested_quantity,
        requested_unit_id=body.requested_unit_id,
        requested_base_quantity=source.base_quantity,
        source_location_id=body.source_location_id,
        product_id=source.product_id,
        product_category_id=None,
        created_by=principal.user_id,
    )
    db.commit()
    return run


@router.get(
    "/recommendations/{run_id}",
    response_model=RecommendationRunResponse,
    summary="Obtener resultado de recomendacion",
)
def get_recommendation(
    run_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    return svc.get_recommendation(run_id)


@router.get(
    "/recommendations/{run_id}/candidates",
    summary="Listar candidatos de recomendacion",
)
def list_candidates(
    run_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    return svc.list_recommendation_candidates(run_id)


@router.get(
    "/recommendations/{run_id}/best",
    response_model=CandidateResponse,
    summary="Obtener mejor candidato",
)
def get_best_candidate(
    run_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    return svc.get_best_recommendation(run_id)


# =============================================================================
# Orders
# =============================================================================
@router.get(
    "/orders",
    response_model=OrderListResponse,
    summary="Listar ordenes de putaway",
)
def list_orders(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    warehouse_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    source_type: str | None = Query(default=None),
    search: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
):
    org_id = resolve_organization_id(principal)
    svc = PutawayApplicationService(db)
    items, total = svc.list_orders(
        org_id, page=page, page_size=page_size, warehouse_id=warehouse_id,
        status=status_filter, source_type=source_type, search=search,
        sort_by=sort_by, sort_order=sort_order,
    )
    return OrderListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post(
    "/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear orden de putaway",
)
def create_order(
    body: OrderCreateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.create")),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    svc = PutawayApplicationService(db)
    order = svc.create_order(
        organization_id=org_id,
        branch_id=principal.default_branch_id or UUID(int=0),
        warehouse_id=body.warehouse_id,
        source_type=body.source_type,
        priority=body.priority,
        created_by=principal.user_id,
    )
    db.commit()
    return order


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Obtener orden de putaway",
)
def get_order(
    order_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    svc = PutawayApplicationService(db)
    return svc.get_order(order_id, org_id)


@router.post(
    "/orders/{order_id}/issue",
    response_model=OrderResponse,
    summary="Emitir orden de putaway",
)
def issue_order(
    order_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.update")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    order = svc.issue_order(order_id, issued_by=principal.user_id)
    db.commit()
    return order


@router.post(
    "/orders/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancelar orden de putaway",
)
def cancel_order(
    order_id: UUID,
    body: OrderCancelRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.update")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    order = svc.cancel_order(order_id, cancelled_by=principal.user_id, reason=body.reason)
    db.commit()
    return order


@router.get(
    "/orders/{order_id}/revisions",
    summary="Listar revisiones de orden",
)
def list_order_revisions(
    order_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    return svc._revision_repo.list_by_order(order_id)


# =============================================================================
# Tasks
# =============================================================================
@router.get(
    "/tasks",
    response_model=TaskListResponse,
    summary="Listar tareas de putaway",
)
def list_tasks(
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    warehouse_id: UUID | None = Query(default=None),
    putaway_order_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    assigned_user_id: UUID | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
):
    org_id = resolve_organization_id(principal)
    svc = PutawayApplicationService(db)
    items, total = svc.list_tasks(
        org_id, page=page, page_size=page_size, warehouse_id=warehouse_id,
        putaway_order_id=putaway_order_id, status=status_filter,
        assigned_user_id=assigned_user_id, sort_by=sort_by, sort_order=sort_order,
    )
    return TaskListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear tarea de putaway",
)
def create_task(
    body: TaskCreateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.create")),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    svc = PutawayApplicationService(db)
    task = svc.create_task(
        organization_id=org_id,
        warehouse_id=principal.default_warehouse_id or UUID(int=0),
        putaway_order_id=body.putaway_order_id,
        source_allocation_id=body.source_allocation_id,
        required_quantity=body.required_quantity,
        required_unit_id=body.required_unit_id,
        required_base_quantity=body.required_quantity,
        expected_product_id=body.expected_product_id,
        priority=body.priority,
        scan_policy=body.scan_policy,
    )
    db.commit()
    return task


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Obtener tarea de putaway",
)
def get_task(
    task_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    return svc.get_task(task_id)


@router.post(
    "/tasks/{task_id}/assign",
    response_model=TaskResponse,
    summary="Asignar tarea a usuario",
)
def assign_task(
    task_id: UUID,
    body: TaskAssignRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.assign")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    task = svc.assign_task(task_id, user_id=body.user_id, assigned_by=principal.user_id)
    db.commit()
    return task


@router.post(
    "/tasks/{task_id}/start",
    response_model=TaskResponse,
    summary="Iniciar tarea de putaway",
)
def start_task(
    task_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    task = svc.start_task(task_id, user_id=principal.user_id)
    db.commit()
    return task


@router.post(
    "/tasks/{task_id}/complete",
    response_model=TaskResponse,
    summary="Completar tarea de putaway",
)
def complete_task(
    task_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    task = svc.complete_task(task_id)
    db.commit()
    return task


@router.get(
    "/tasks/{task_id}/destinations",
    summary="Listar destinos de tarea",
)
def list_task_destinations(
    task_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    return svc._dest_repo.list_by_task(task_id)


@router.get(
    "/tasks/{task_id}/assignments",
    summary="Listar asignaciones de tarea",
)
def list_task_assignments(
    task_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
):
    from ..infrastructure.persistence.repositories import PutawayTaskAssignmentRepository
    repo = PutawayTaskAssignmentRepository(db)
    return repo.list_by_user(principal.user_id)


# =============================================================================
# Execution Sessions
# =============================================================================
@router.post(
    "/tasks/{task_id}/sessions",
    response_model=ExecutionSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear sesion de ejecucion",
)
def create_execution_session(
    task_id: UUID,
    body: ExecutionSessionCreateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    session = svc.create_execution_session(
        task_id=task_id,
        operator_user_id=principal.user_id,
        scanner_type=body.scanner_type,
        device_reference_hash=body.device_reference_hash,
        client_session_reference=body.client_session_reference,
    )
    db.commit()
    return session


@router.post(
    "/sessions/{session_id}/complete",
    response_model=ExecutionSessionResponse,
    summary="Completar sesion de ejecucion",
)
def complete_execution_session(
    session_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    session = svc.complete_execution_session(session_id)
    db.commit()
    return session


# =============================================================================
# Scans
# =============================================================================
@router.post(
    "/sessions/{session_id}/scans",
    response_model=ScanEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar escaneo",
)
def record_scan(
    session_id: UUID,
    body: ScanRecordRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    svc = PutawayApplicationService(db)

    from ..infrastructure.persistence.repositories import PutawayExecutionSessionRepository
    session_repo = PutawayExecutionSessionRepository(db)
    session = session_repo.get(session_id)
    if not session:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")

    event = svc.record_scan(
        session_id=session_id,
        task_id=session.task_id,
        organization_id=org_id,
        warehouse_id=principal.default_warehouse_id or UUID(int=0),
        client_scan_id=body.client_scan_id,
        scan_type=body.scan_type,
        normalized_code=body.normalized_code,
        code_hash=body.code_hash,
        symbology=body.symbology,
        raw_code_encrypted=body.raw_code_encrypted,
        operator_user_id=principal.user_id,
    )
    session_repo.update_activity(session_id)
    db.commit()
    return event


@router.post(
    "/sessions/{session_id}/scans/{event_id}/validate-product",
    response_model=ScanEventResponse,
    summary="Validar escaneo de producto",
)
def validate_product_scan(
    session_id: UUID,
    event_id: UUID,
    body: ScanValidationRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    event = svc.validate_product_scan(session_id, event_id, expected_product_id=body.expected_product_id)
    db.commit()
    return event


@router.post(
    "/sessions/{session_id}/scans/{event_id}/validate-location",
    response_model=ScanEventResponse,
    summary="Validar escaneo de ubicacion",
)
def validate_location_scan(
    session_id: UUID,
    event_id: UUID,
    body: ScanValidationRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    event = svc.validate_location_scan(session_id, event_id, expected_location_id=body.expected_location_id)
    db.commit()
    return event


@router.get(
    "/sessions/{session_id}/scans",
    summary="Listar escaneos de sesion",
)
def list_session_scans(
    session_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
):
    from ..infrastructure.persistence.repositories import PutawayScanEventRepository
    repo = PutawayScanEventRepository(db)
    return repo.list_by_session(session_id)


# =============================================================================
# Placements
# =============================================================================
@router.post(
    "/tasks/{task_id}/placements",
    response_model=PlacementConfirmationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Confirmar colocacion",
)
def confirm_placement(
    task_id: UUID,
    body: PlacementConfirmRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    task = svc.get_task(task_id)
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")

    confirmation = svc.confirm_placement(
        task_id=task_id,
        source_allocation_id=body.source_allocation_id,
        location_id=body.location_id,
        quantity=body.quantity,
        unit_id=body.unit_id,
        base_quantity=body.quantity,
        confirmed_by=principal.user_id,
        product_scan_event_id=body.product_scan_event_id,
        location_scan_event_id=body.location_scan_event_id,
        reservation_id=body.reservation_id,
        observation=body.observation,
    )
    db.commit()
    return confirmation


@router.post(
    "/placements/{confirmation_id}/finalize",
    response_model=OperationalPlacementResponse,
    summary="Finalizar colocacion operativa",
)
def finalize_placement(
    confirmation_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    placement = svc.finalize_placement(confirmation_id)
    db.commit()
    return placement


@router.get(
    "/tasks/{task_id}/placements",
    summary="Listar colocaciones de tarea",
)
def list_task_placements(
    task_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
):
    from ..infrastructure.persistence.repositories import PutawayPlacementConfirmationRepository
    repo = PutawayPlacementConfirmationRepository(db)
    return repo.list_by_task(task_id)


# =============================================================================
# Reservations
# =============================================================================
@router.post(
    "/reservations",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear reservacion de ubicacion",
)
def create_reservation(
    body: ReservationCreateRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    svc = PutawayApplicationService(db)
    reservation = svc.create_reservation(
        organization_id=org_id,
        warehouse_id=principal.default_warehouse_id or UUID(int=0),
        location_id=body.location_id,
        task_id=body.task_id,
        source_allocation_id=body.source_allocation_id,
        capacity_profile_id=body.capacity_profile_id,
        reserved_value=body.reserved_value,
        unit_id=body.unit_id,
        reserved_base_quantity=body.reserved_value,
        expires_in_minutes=body.expires_in_minutes,
    )
    db.commit()
    return reservation


@router.post(
    "/reservations/{reservation_id}/release",
    response_model=ReservationResponse,
    summary="Liberar reservacion",
)
def release_reservation(
    reservation_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    reservation = svc.release_reservation(reservation_id)
    db.commit()
    return reservation


@router.post(
    "/reservations/{reservation_id}/consume",
    response_model=ReservationResponse,
    summary="Consumir reservacion",
)
def consume_reservation(
    reservation_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    reservation = svc.consume_reservation(reservation_id)
    db.commit()
    return reservation


# =============================================================================
# Overrides
# =============================================================================
@router.post(
    "/tasks/{task_id}/overrides",
    response_model=OverrideResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Solicitar override de ubicacion",
)
def request_override(
    task_id: UUID,
    body: OverrideRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.override")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    override = svc.request_location_override(
        task_id=task_id,
        recommended_location_id=body.recommended_location_id,
        selected_location_id=body.selected_location_id,
        recommendation_run_id=body.recommendation_run_id,
        recommended_score=body.recommended_score,
        selected_score=body.selected_score,
        reason_code=body.reason_code,
        reason=body.reason,
        requested_by=principal.user_id,
    )
    db.commit()
    return override


@router.post(
    "/overrides/{override_id}/approve",
    summary="Aprobar override de ubicacion",
)
def approve_override(
    override_id: UUID,
    body: OverrideApprovalRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.override.approve")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    svc.approve_override(
        override_id,
        approved_by=principal.user_id,
        step_up_summary=body.step_up_summary,
    )
    db.commit()
    return {"status": "approved"}


@router.get(
    "/tasks/{task_id}/overrides",
    summary="Listar overrides de tarea",
)
def list_task_overrides(
    task_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
):
    from ..infrastructure.persistence.repositories import PutawayLocationOverrideRepository
    repo = PutawayLocationOverrideRepository(db)
    return repo.list_by_task(task_id)


# =============================================================================
# Exceptions
# =============================================================================
@router.post(
    "/tasks/{task_id}/exceptions",
    response_model=ExceptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Reportar excepcion de tarea",
)
def report_exception(
    task_id: UUID,
    body: ExceptionReportRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    exc = svc.report_exception(
        task_id=task_id,
        exception_type=body.exception_type,
        severity=body.severity,
        description=body.description,
        detected_by=principal.user_id,
        product_scan_event_id=body.product_scan_event_id,
        location_scan_event_id=body.location_scan_event_id,
        location_id=body.location_id,
        quantity=body.quantity,
        unit_id=body.unit_id,
        evidence_file_ids=body.evidence_file_ids,
    )
    db.commit()
    return exc


@router.post(
    "/exceptions/{exception_id}/resolve",
    response_model=ExceptionResponse,
    summary="Resolver excepcion",
)
def resolve_exception(
    exception_id: UUID,
    body: ExceptionResolveRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    exc = svc.resolve_exception(
        exception_id,
        resolved_by=principal.user_id,
        resolution=body.resolution,
    )
    db.commit()
    return exc


@router.get(
    "/tasks/{task_id}/exceptions",
    summary="Listar excepciones de tarea",
)
def list_task_exceptions(
    task_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
):
    from ..infrastructure.persistence.repositories import PutawayTaskExceptionRepository
    repo = PutawayTaskExceptionRepository(db)
    return repo.list_by_task(task_id)


# =============================================================================
# Pauses
# =============================================================================
@router.post(
    "/tasks/{task_id}/pauses",
    response_model=PauseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Pausar tarea",
)
def pause_task(
    task_id: UUID,
    body: PauseRequest,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    pause = svc.pause_task(
        task_id,
        user_id=principal.user_id,
        reason=body.reason,
        description=body.description,
    )
    db.commit()
    return pause


@router.post(
    "/tasks/{task_id}/resume",
    response_model=TaskResponse,
    summary="Reanudar tarea",
)
def resume_task(
    task_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.execute")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    task = svc.resume_task(task_id)
    db.commit()
    return task


@router.get(
    "/tasks/{task_id}/pauses",
    summary="Listar pausas de tarea",
)
def list_task_pauses(
    task_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
):
    from ..infrastructure.persistence.repositories import PutawayTaskPauseRepository
    repo = PutawayTaskPauseRepository(db)
    return repo.list_by_task(task_id)


# =============================================================================
# Placement Projections
# =============================================================================
@router.get(
    "/projections/location/{location_id}",
    summary="Obtener proyecciones de ubicacion",
)
def get_location_projections(
    location_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
):
    svc = PutawayApplicationService(db)
    return svc.get_location_projection(location_id)


@router.get(
    "/projections/product/{product_id}",
    summary="Obtener proyecciones de producto",
)
def get_product_projections(
    product_id: UUID,
    principal: LogisticsPrincipal = Depends(require_permission("logistics.putaway.read")),
    db: Session = Depends(get_db),
):
    org_id = resolve_organization_id(principal)
    svc = PutawayApplicationService(db)
    return svc.get_product_projections(org_id, product_id)
