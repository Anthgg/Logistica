from decimal import Decimal
from typing import Any

from app.modules.logistics.inventory.balances.domain.value_objects.states import (
    AvailabilityState,
    DamageState,
    ExpirationState,
    QualityState,
    TransitState,
)


class InventoryBalanceFormulaService:
    """Motor de cálculo de 8 métricas de saldos de inventario de alta precisión."""

    @staticmethod
    def calculate_physical_on_hand(position_balances: list[dict[str, Any]]) -> Decimal:
        """1. Physical Stock on Hand.
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
        """2. Available to Promise (ATP) Operativo.
        Stock físico apto para promesa/venta/despacho:
        - Availability = AVAILABLE
        - Quality = APPROVED
        - Transit = NOT_IN_TRANSIT
        - Damage = NORMAL
        - Expiration = FRESH or NOT_APPLICABLE
        """
        total = Decimal("0.000000000000000000")
        for pos in position_balances:
            avail = pos.get("availability_state", AvailabilityState.AVAILABLE)
            quality = pos.get("quality_state", QualityState.APPROVED)
            transit = pos.get("transit_state", TransitState.NOT_IN_TRANSIT)
            damage = pos.get("damage_state", DamageState.NORMAL)
            expiration = pos.get("expiration_state", ExpirationState.NOT_APPLICABLE)

            if (
                avail == AvailabilityState.AVAILABLE
                and quality == QualityState.APPROVED
                and transit == TransitState.NOT_IN_TRANSIT
                and damage == DamageState.NORMAL
                and expiration in (ExpirationState.FRESH, ExpirationState.NOT_APPLICABLE)
            ):
                total += Decimal(str(pos.get("quantity", "0")))
        return total

    @staticmethod
    def calculate_reserved_stock(position_balances: list[dict[str, Any]]) -> Decimal:
        """3. Stock Reservado.
        Suma de saldos asignados o reservados para pedidos o compromisos comerciales.
        """
        total = Decimal("0.000000000000000000")
        for pos in position_balances:
            avail = pos.get("availability_state")
            if avail == AvailabilityState.RESERVED:
                total += Decimal(str(pos.get("quantity", "0")))
        return total

    @staticmethod
    def calculate_blocked_stock(position_balances: list[dict[str, Any]]) -> Decimal:
        """4. Stock Bloqueado.
        Suma de saldos bloqueados explícitamente para operaciones o rechazados.
        """
        total = Decimal("0.000000000000000000")
        for pos in position_balances:
            avail = pos.get("availability_state")
            quality = pos.get("quality_state")
            damage = pos.get("damage_state")
            if (
                avail in (AvailabilityState.BLOCKED, "BLOCKED")
                or quality == QualityState.REJECTED
                or damage == DamageState.SCRAPPED
            ):
                total += Decimal(str(pos.get("quantity", "0")))
        return total

    @staticmethod
    def calculate_quarantine_stock(position_balances: list[dict[str, Any]]) -> Decimal:
        """5. Stock en Cuarentena.
        Suma de saldos retenidos por control de calidad o inspección pendiente.
        """
        total = Decimal("0.000000000000000000")
        for pos in position_balances:
            avail = pos.get("availability_state")
            quality = pos.get("quality_state")
            if avail == AvailabilityState.QUARANTINE or quality in (QualityState.QUARANTINED, QualityState.INSPECTION_PENDING):
                total += Decimal(str(pos.get("quantity", "0")))
        return total

    @staticmethod
    def calculate_in_transit_stock(position_balances: list[dict[str, Any]]) -> Decimal:
        """6. Stock en Tránsito.
        Suma de saldos en tránsito entre almacenes o compras en curso.
        """
        total = Decimal("0.000000000000000000")
        for pos in position_balances:
            transit = pos.get("transit_state")
            avail = pos.get("availability_state")
            if (transit and transit != TransitState.NOT_IN_TRANSIT) or avail == AvailabilityState.IN_TRANSIT:
                total += Decimal(str(pos.get("quantity", "0")))
        return total

    @staticmethod
    def calculate_damaged_stock(position_balances: list[dict[str, Any]]) -> Decimal:
        """7. Stock Dañado.
        Suma de saldos clasificados como dañados.
        """
        total = Decimal("0.000000000000000000")
        for pos in position_balances:
            damage = pos.get("damage_state")
            avail = pos.get("availability_state")
            if damage == DamageState.DAMAGED or avail == AvailabilityState.DAMAGED:
                total += Decimal(str(pos.get("quantity", "0")))
        return total

    @staticmethod
    def calculate_expired_stock(position_balances: list[dict[str, Any]]) -> Decimal:
        """8. Stock Vencido.
        Suma de saldos cuya fecha de caducidad ha expirado.
        """
        total = Decimal("0.000000000000000000")
        for pos in position_balances:
            expiration = pos.get("expiration_state")
            avail = pos.get("availability_state")
            if expiration == ExpirationState.EXPIRED or avail == AvailabilityState.EXPIRED:
                total += Decimal(str(pos.get("quantity", "0")))
        return total

