from datetime import UTC, datetime
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
    InventoryBalanceDeltaModel,
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
        query = (
            select(InventoryPositionBalanceModel)
            .where(InventoryPositionBalanceModel.organization_id == payload.organization_id)
            .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
        )
        if payload.target_warehouse_id:
            query = query.where(InventoryPositionBalanceModel.warehouse_id == payload.target_warehouse_id)
        if payload.target_product_id:
            query = query.where(InventoryPositionBalanceModel.product_id == payload.target_product_id)

        active_positions = list(db.scalars(query))

        if active_positions:
            positions_to_rebuild = [
                {
                    "inventory_position_id": p.inventory_position_id,
                    "product_id": p.product_id,
                    "base_unit_id": p.base_unit_id,
                    "branch_id": p.branch_id,
                    "warehouse_id": p.warehouse_id,
                    "warehouse_location_id": p.warehouse_location_id,
                    "product_version_id": p.product_version_id,
                    "initial_quantity": p.quantity,
                    "dimension_key": p.dimension_key,
                    "partition_key": p.last_applied_ledger_partition_key,
                }
                for p in active_positions
            ]
            rebuild_service.prepare_staging_projection(job.id, positions_to_rebuild)

            pos_ids = [p.inventory_position_id for p in active_positions]
            deltas = list(
                db.scalars(
                    select(InventoryBalanceDeltaModel)
                    .where(InventoryBalanceDeltaModel.organization_id == payload.organization_id)
                    .where(InventoryBalanceDeltaModel.position_id.in_(pos_ids))
                    .where(InventoryBalanceDeltaModel.applied_status == "PENDING")
                )
            )
            if deltas:
                rebuild_service.replay_deltas_into_staging(job.id, deltas)

            rebuild_service.validate_staging(job.id)
            rebuild_service.execute_atomic_swap(job.id)
        else:
            job.status = "COMPLETED"
            job.completed_at = datetime.now(UTC)

        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        rebuild_service.rollback_rebuild(job.id, str(exc))
        db.commit()

    db.refresh(job)
    return RebuildJobRead.model_validate(job)
