from decimal import Decimal
import pytest

from app.modules.logistics.inventory.balances.domain.policies.negative_stock_policy import (
    NegativeStockPolicy,
)


def test_negative_stock_policy_deny_default():
    policy = NegativeStockPolicy(allow_negative=False)

    # Valid adjustment (10 - 5 = 5 >= 0)
    policy.validate(Decimal("10.000000000000000000"), Decimal("-5.000000000000000000"))

    # Violation adjustment (10 - 15 = -5 < 0)
    with pytest.raises(ValueError, match="Negative stock policy violation"):
        policy.validate(Decimal("10.000000000000000000"), Decimal("-15.000000000000000000"))
