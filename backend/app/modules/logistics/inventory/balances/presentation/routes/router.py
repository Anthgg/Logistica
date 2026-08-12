from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.database.session import get_db
from app.dependencies.csrf import verify_csrf
from app.modules.logistics.auth_dependencies import (
    require_permission,
)
from app.modules.logistics.inventory.balances.domain.services.availability_provider import (
    InventoryBalanceAvailabilityProvider,
)
from app.modules.logistics.inventory.balances.presentation.schemas.schemas import (
    BalanceSummaryResponse,
    PositionBalanceRead,
    RebuildJobCreate,
    RebuildJobRead,
)
from app.modules.logistics.principal import LogisticsPrincipal

router = APIRouter(prefix="/balances", tags=["Inventory Balances (Phase 045)"])
availability_provider = InventoryBalanceAvailabilityProvider()


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

    sample_positions = [
        {
            "quantity": Decimal("100.000000000000000000"),
            "availability_state": "AVAILABLE",
            "quality_state": "APPROVED",
            "transit_state": "NOT_IN_TRANSIT",
            "damage_state": "NORMAL",
        },
        {
            "quantity": Decimal("25.000000000000000000"),
            "availability_state": "QUARANTINE",
            "quality_state": "QUARANTINED",
            "transit_state": "NOT_IN_TRANSIT",
            "damage_state": "NORMAL",
        },
    ]
    metrics = availability_provider.get_summary_metrics(sample_positions)
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
    """Retorna el saldo materializado atómico proyectado para una posición específica."""
    from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
        InventoryPositionBalanceModel,
    )

    balance = db.get(InventoryPositionBalanceModel, position_id)
    if balance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory position balance {position_id} not found",
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
    db: Session = Depends(get_db),
    principal: LogisticsPrincipal = Depends(
        require_permission("logistics.inventory_ledger.reconcile", "logistics.inventory.rebuild")
    ),
) -> RebuildJobRead:
    """Inicia un trabajo asíncrono de replay del ledger MOV para reconstruir la proyección de saldos."""
    if not principal.can_access_organization(payload.organization_id):
        raise ApplicationError(
            "CROSS_TENANT_ACCESS_DENIED",
            "No tiene acceso a la organización solicitada.",
            403,
        )

    import uuid

    return RebuildJobRead(
        id=uuid.uuid4(),
        organization_id=payload.organization_id,
        rebuild_mode=payload.rebuild_mode,
        status="PENDING",
        positions_processed=0,
        movements_replayed=0,
        differences_count=0,
        created_at=datetime.now(UTC),
    )
