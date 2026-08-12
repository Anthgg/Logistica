from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BalanceSummaryResponse(BaseModel):
    """Schema Pydantic v2 para el resumen global de las 8 métricas de saldos de inventario."""
    physical_on_hand: Decimal = Field(..., description="Stock físico total en almacén")
    available_to_promise: Decimal = Field(..., description="Stock disponible operativo (ATP)")
    reserved_stock: Decimal = Field(..., description="Stock reservado para compromisos/pedidos")
    blocked_stock: Decimal = Field(..., description="Stock bloqueado operativamente")
    quarantine_stock: Decimal = Field(..., description="Stock retenido en cuarentena por calidad")
    in_transit_stock: Decimal = Field(..., description="Stock en tránsito entre almacenes/compras")
    damaged_stock: Decimal = Field(..., description="Stock dañado registrado")
    expired_stock: Decimal = Field(..., description="Stock vencido por fecha de caducidad")

    model_config = ConfigDict(from_attributes=True)


class PositionBalanceRead(BaseModel):
    """Schema Pydantic v2 para la consulta detallada de saldo por posición."""
    id: UUID
    organization_id: UUID
    branch_id: UUID
    warehouse_id: UUID | None = None
    warehouse_location_id: UUID | None = None
    inventory_position_id: UUID
    product_id: UUID
    product_version_id: UUID | None = None
    base_unit_id: UUID
    quantity: Decimal

    availability_state: str
    quality_state: str
    transit_state: str
    damage_state: str
    expiration_state: str

    dimension_key: str
    last_applied_ledger_sequence: int
    data_quality_status: str
    reconciliation_status: str
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)


from enum import Enum


class RebuildMode(str, Enum):
    FULL = "FULL"
    TOTAL = "TOTAL"
    PARTIAL_WAREHOUSE = "PARTIAL_WAREHOUSE"
    PARTIAL_PRODUCT = "PARTIAL_PRODUCT"


class RebuildJobCreate(BaseModel):
    """Schema Pydantic v2 para la solicitud de rebuild de saldos."""
    organization_id: UUID
    rebuild_mode: RebuildMode = Field(RebuildMode.FULL, description="FULL, TOTAL, PARTIAL_WAREHOUSE, PARTIAL_PRODUCT")
    target_warehouse_id: UUID | None = None
    target_product_id: UUID | None = None
    as_of_sequence: int | None = None


class RebuildJobRead(BaseModel):
    """Schema Pydantic v2 para el resultado de trabajo de rebuild."""
    id: UUID
    organization_id: UUID
    rebuild_mode: str
    status: str
    positions_processed: int
    movements_replayed: int
    differences_count: int
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
