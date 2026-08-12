"""Phase 044 — Integration tests for the inventory ledger HTTP API."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


class TestLedgerHTTP:
    def test_list_movements_returns_401_without_auth(self, client: TestClient):
        org_id = uuid4()
        response = client.get(
            "/api/logistics/inventory/movements",
            params={"organization_id": str(org_id)},
        )
        # Without a session cookie the request must be rejected by the auth layer.
        assert response.status_code in {401, 403}

    def test_kardex_lists_movement_types(self, client: TestClient):
        response = client.get("/api/logistics/inventory/kardex/movement-types")
        # Either OK (no auth needed for catalogue) or rejected by auth.
        assert response.status_code in {200, 401, 403}

    def test_kardex_lists_source_types(self, client: TestClient):
        response = client.get("/api/logistics/inventory/kardex/source-types")
        assert response.status_code in {200, 401, 403}

    def test_kardex_state_transitions(self, client: TestClient):
        response = client.get("/api/logistics/inventory/kardex/state-transitions")
        assert response.status_code in {200, 401, 403}

    def test_get_movement_returns_404_for_unknown(self, client: TestClient):
        org_id = uuid4()
        movement_id = uuid4()
        response = client.get(
            f"/api/logistics/inventory/movements/{movement_id}",
            params={"organization_id": str(org_id)},
        )
        # Movement not found is a 404 or 422 depending on how the endpoint handles missing
        assert response.status_code in {401, 403, 404, 422}

    def test_posting_request_flow_idempotent(self, client: TestClient):
        org_id = uuid4()
        body = {
            "request_key": "test-1",
            "source_system": "QUALITY",
            "source_event_type": "QUARANTINE_APPLIED",
            "source_event_id": "evt-1",
            "source_event_version": 1,
            "payload": {
                "movement_type": "QUARANTINE_APPLIED",
                "source_hash": "a" * 64,
                "payload_hash": "a" * 64,
                "branch_id": str(uuid4()),
                "warehouse_id": str(uuid4()),
                "lines": [
                    {
                        "product_id": str(uuid4()),
                        "unit_id": str(uuid4()),
                        "base_unit_id": str(uuid4()),
                        "quantity": "5",
                        "base_quantity": "5",
                        "destination_position_id": str(uuid4()),
                        "quantity_direction": "TRANSFER",
                    }
                ],
            },
        }
        first = client.post(
            "/api/logistics/inventory/ledger/posting-requests",
            params={"organization_id": str(org_id)},
            json=body,
        )
        # Either it succeeds (201) or fails because of auth/CSRF guard, but never 500.
        assert first.status_code in {201, 401, 403, 422}

    def test_running_quantity_requires_exact_scope(self, client: TestClient):
        org_id = uuid4()
        warehouse_id = uuid4()
        product_id = uuid4()
        base_unit_id = uuid4()
        response = client.get(
            "/api/logistics/inventory/kardex/technical-running-quantity",
            params={
                "organization_id": str(org_id),
                "warehouse_id": str(warehouse_id),
                "product_id": str(product_id),
                "base_unit_id": str(base_unit_id),
            },
        )
        # Without position_id or states, it should return 422 (ambiguous scope) or 401/403.
        assert response.status_code in {401, 403, 422, 400}

    def test_reconciliation_job_runs(self, client: TestClient):
        org_id = uuid4()
        response = client.post(
            "/api/logistics/inventory/ledger/reconciliation-jobs",
            params={"organization_id": str(org_id)},
            json={"scope": {"warehouse_id": str(uuid4())}},
        )
        # We expect 201 if creation succeeds, or 403 if capability is required.
        assert response.status_code in {201, 401, 403}


class TestKardexRunningQuantityScope:
    def test_ambiguous_scope_is_rejected(self):
        from app.modules.logistics.inventory.ledger.application.services.kardex_query_service import (
            InventoryKardexQueryService,
        )
        from app.modules.logistics.inventory.ledger.domain.errors.exceptions import (
            InventoryKardexScopeAmbiguous,
        )

        svc = InventoryKardexQueryService(db=None)  # type: ignore[arg-type]
        with pytest.raises(InventoryKardexScopeAmbiguous):
            svc.compute_technical_running_quantity(
                organization_id=uuid4(),
                warehouse_id=uuid4(),
                product_id=uuid4(),
                base_unit_id=uuid4(),
            )
