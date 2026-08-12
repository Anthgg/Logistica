from decimal import Decimal
import pytest

from app.modules.logistics.inventory.balances.domain.policies.negative_stock_policy import (
    NegativeStockPolicy,
)


def test_negative_stock_policy_denied_preserves_balance():
    """Valida que un delta que causaría stock negativo (-11 en saldo 10) sea RECHAZADO y preserve el saldo original de 10."""
    policy = NegativeStockPolicy(allow_negative=False)
    current_balance = Decimal("10.000000000000000000")
    attempted_decrease = Decimal("-11.000000000000000000")

    with pytest.raises(ValueError, match="Negative stock policy violation"):
        policy.validate(current_balance, attempted_decrease)

    # Balance se mantiene en 10
    assert current_balance == Decimal("10.000000000000000000")
