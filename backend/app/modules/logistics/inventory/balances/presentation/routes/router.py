from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.database.session import get_db
from app.dependencies.csrf import verify_csrf
from app.modules.logistics.auth_dependencies import (
    require_permission,
)
from app.modules.logistics.inventory.balances.application.queries.balance_query_service import (
    BalanceQueryService,
)
from app.modules.logistics.inventory.balances.application.services.rebuild_application_service import (
    BalanceRebuildApplicationService,
)
from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
    InventoryBalanceRebuildJobModel,
    InventoryPositionBalanceModel,
)
from app.modules.logistics.inventory.balances.presentation.schemas.schemas import (
    BalanceSummaryResponse,
    PositionBalanceRead,
    RebuildJobCreate,
    RebuildJobRead,
)
from app.modules.logistics.principal import LogisticsPrincipal

router = APIRouter(prefix="/balances", tags=["Inventory Balances (Phase 045)"])
query_service = BalanceQueryService()


@router.get(
    "/summary",
    response_model=BalanceSummaryResponse,
    summary="Obtener resumen consolidado de saldos por warehouse y producto",
)
def get_balance_summary(
    organization_id: UUID = Query(..., description="ID de la organización"),
    warehouse_id: UUID | None = Query(None, description="ID del almacén opcional"),
    product_id: UUID | None = Query(None, description="ID del producto opcional"),
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.inventory.read")),
) -> BalanceSummaryResponse:
    """Retorna el resumen consolidado de métricas (Physical, ATP, Quarantine, Blocked, In Transit)."""
    if not principal.can_access_organization(organization_id):
        raise ApplicationError(
            "CROSS_TENANT_ACCESS_DENIED",
            "No tiene acceso a la organización solicitada.",
            403,
        )

    metrics = query_service.get_active_balances_summary(
        db,
        organization_id=organization_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
    )
    return BalanceSummaryResponse(**metrics)


@router.get(
    "/positions/{position_id}",
    response_model=PositionBalanceRead,
    summary="Consultar saldo atómico de una posición de inventario",
)
def get_position_balance(
    position_id: UUID,
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(require_permission("logistics.inventory.read")),
) -> PositionBalanceRead:
    """Retorna el saldo materializado atómico proyectado para una posición específica (InventoryPosition.id)."""
    query = (
        select(InventoryPositionBalanceModel)
        .where(InventoryPositionBalanceModel.inventory_position_id == position_id)
        .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
    )
    balance = db.scalars(query).first()

    if balance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory position balance for position {position_id} not found",
        )

    if not principal.can_access_organization(balance.organization_id):
        raise ApplicationError(
            "CROSS_TENANT_ACCESS_DENIED",
            "No tiene acceso a la organización solicitada.",
            403,
        )

    return PositionBalanceRead.model_validate(balance)


@router.post(
    "/rebuild",
    response_model=RebuildJobRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Solicitar trabajo de reconstrucción (rebuild) total o parcial de saldos",
    dependencies=[Depends(verify_csrf)],
)
def trigger_balance_rebuild(
    payload: RebuildJobCreate,
    x_step_up_proof_id: str | None = Header(None, alias="X-Step-Up-Proof-ID"),
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.inventory_ledger.reconcile", "logistics.inventory.rebuild")
    ),
) -> RebuildJobRead:
    """Inicia un trabajo de replay del ledger MOV para reconstruir la proyección de saldos."""
    if not principal.can_access_organization(payload.organization_id):
        raise ApplicationError(
            "CROSS_TENANT_ACCESS_DENIED",
            "No tiene acceso a la organización solicitada.",
            403,
        )

    step_up_verified = bool(x_step_up_proof_id) or not any(
        code in principal.step_up_permissions
        for code in ("logistics.inventory_ledger.reconcile", "logistics.inventory.rebuild")
    )

    rebuild_service = BalanceRebuildApplicationService(db)
    job = rebuild_service.create_rebuild_job(
        organization_id=payload.organization_id,
        initiated_by_user_id=principal.user_id,
        rebuild_mode=payload.rebuild_mode.value,
        target_warehouse_id=payload.target_warehouse_id,
        target_product_id=payload.target_product_id,
        step_up_verified=step_up_verified,
    )

    try:
        rebuild_service.execute_rebuild_from_ledger(job.id)
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        rebuild_service.rollback_rebuild(job.id, str(exc))
        db.commit()

    job_record = db.get(InventoryBalanceRebuildJobModel, job.id) or job
    return RebuildJobRead.model_validate(job_record)
