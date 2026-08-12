from decimal import Decimal
import pytest

from app.modules.logistics.inventory.balances.infrastructure.projections.balance_projection_service import (
    BalanceProjectionService,
)


def test_transactional_rollback_preserves_original_state():
    """Valida la integridad transaccional frente a fallos a mitad de procesamiento de un delta."""
    service = BalanceProjectionService()
    original_balance = Decimal("100.000000000000000000")

    # Intentar aplicar un delta que falla por política de stock negativo
    invalid_delta = {
        "delta_type": "DECREASE",
        "delta_quantity": "150.000000000000000000",
    }

    with pytest.raises(ValueError, match="Negative stock policy violation"):
        service.apply_delta(original_balance, invalid_delta)

    # Confirmar que el saldo original permanece intacto post-excepción
    assert original_balance == Decimal("100.000000000000000000")
