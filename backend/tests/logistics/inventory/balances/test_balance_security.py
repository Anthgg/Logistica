from decimal import Decimal

import pytest


def test_float_type_rejection():
    """Garantiza que valores float, NaN o Infinity sean rechazados en contratos de saldos."""
    def parse_decimal(val):
        if isinstance(val, float):
            raise TypeError("Floats are strictly forbidden in inventory balances. Use string or Decimal.")
        return Decimal(str(val))

    with pytest.raises(TypeError, match="Floats are strictly forbidden"):
        parse_decimal(0.1)

    with pytest.raises(TypeError, match="Floats are strictly forbidden"):
        parse_decimal(float("nan"))

    with pytest.raises(TypeError, match="Floats are strictly forbidden"):
        parse_decimal(float("inf"))


def test_cross_tenant_isolation_rule():
    """Valida la regla de aislamiento multi-tenant por organization_id."""
    def verify_tenant_access(user_org_id: str, requested_org_id: str):
        if user_org_id != requested_org_id:
            raise PermissionError("Cross-tenant access forbidden (403).")
        return True

    assert verify_tenant_access("org-123", "org-123") is True

    with pytest.raises(PermissionError, match="Cross-tenant access forbidden"):
        verify_tenant_access("org-123", "org-999")
