from decimal import Decimal
import pytest

from app.modules.logistics.inventory.balances.domain.services.reconciliation_service import (
    ReconciliationService,
)


def test_reconciliation_service_detects_mismatch_without_mutating():
    """Valida que la reconciliación detecte MISMATCH_DETECTED sin mutar el ledger ni forzar el balance."""
    reconciliation_service = ReconciliationService()

    projected = Decimal("100.000000000000000000")
    replayed = Decimal("80.000000000000000000")

    projected_balances = {"pos-100": projected}
    replayed_balances = {"pos-100": replayed}

    differences = reconciliation_service.reconcile(projected_balances, replayed_balances)

    assert len(differences) == 1
    assert differences[0]["status"] == "MISMATCH_DETECTED"
    assert differences[0]["difference_quantity"] == Decimal("20.000000000000000000")
    # Confirmar que el saldo proyectado original no es alterado
    assert projected_balances["pos-100"] == Decimal("100.000000000000000000")
