from decimal import Decimal
from typing import Any

from app.modules.logistics.inventory.balances.domain.value_objects.states import (
    AvailabilityState,
    DamageState,
    QualityState,
    TransitState,
)


class InventoryBalanceFormulaService:
    """Motor de cálculo de métricas de saldos de inventario para Casos A, B, C, D, E."""

    @staticmethod
    def calculate_physical_on_hand(position_balances: list[dict[str, Any]]) -> Decimal:
        """Caso A: Physical Stock on Hand.
        Suma de saldos presentes físicamente en el almacén (excluyendo únicamente mercadería en tránsito).
        """
        total = Decimal("0.000000000000000000")
        for pos in position_balances:
            transit = pos.get("transit_state", TransitState.NOT_IN_TRANSIT)
            if transit == TransitState.NOT_IN_TRANSIT:
                total += Decimal(str(pos.get("quantity", "0")))
        return total

    @staticmethod
    def calculate_available_to_promise(position_balances: list[dict[str, Any]]) -> Decimal:
        """Caso B: Available to Promise (ATP) Operativo.
        Stock físico apto para venta/despacho:
        - Availability = AVAILABLE
        - Quality = APPROVED
        - Transit = NOT_IN_TRANSIT
        - Damage = NORMAL
        """
        total = Decimal("0.000000000000000000")
        for pos in position_balances:
            avail = pos.get("availability_state", AvailabilityState.AVAILABLE)
            quality = pos.get("quality_state", QualityState.APPROVED)
            transit = pos.get("transit_state", TransitState.NOT_IN_TRANSIT)
            damage = pos.get("damage_state", DamageState.NORMAL)

            if (
                avail == AvailabilityState.AVAILABLE
                and quality == QualityState.APPROVED
                and transit == TransitState.NOT_IN_TRANSIT
                and damage == DamageState.NORMAL
            ):
                total += Decimal(str(pos.get("quantity", "0")))
        return total

    @staticmethod
    def calculate_quarantine_stock(position_balances: list[dict[str, Any]]) -> Decimal:
        """Caso C: Stock en Cuarentena.
        Suma de saldos retenidos por control de calidad.
        """
        total = Decimal("0.000000000000000000")
        for pos in position_balances:
            avail = pos.get("availability_state")
            quality = pos.get("quality_state")
            if avail == AvailabilityState.QUARANTINE or quality == QualityState.QUARANTINED:
                total += Decimal(str(pos.get("quantity", "0")))
        return total

    @staticmethod
    def calculate_blocked_stock(position_balances: list[dict[str, Any]]) -> Decimal:
        """Caso D: Stock Bloqueado / Reservado / Dañado.
        Suma de saldos retenidos o dañados que no están disponibles para promesa.
        """
        total = Decimal("0.000000000000000000")
        for pos in position_balances:
            avail = pos.get("availability_state")
            damage = pos.get("damage_state")
            if avail in (AvailabilityState.RESERVED, AvailabilityState.DAMAGED) or damage == DamageState.DAMAGED:
                total += Decimal(str(pos.get("quantity", "0")))
        return total

    @staticmethod
    def calculate_in_transit_stock(position_balances: list[dict[str, Any]]) -> Decimal:
        """Caso E: Stock en Tránsito.
        Suma de saldos en tránsito entre almacenes o compras en curso.
        """
        total = Decimal("0.000000000000000000")
        for pos in position_balances:
            transit = pos.get("transit_state")
            if transit != TransitState.NOT_IN_TRANSIT:
                total += Decimal(str(pos.get("quantity", "0")))
        return total
