from tests.support import authenticate, create_client, create_shipment


def test_dashboard_calculates_real_indicators(client, database) -> None:
    _, headers = authenticate(client, database)
    before = client.get("/api/dashboard/summary").json()
    customer = create_client(client, headers)
    shipment = create_shipment(client, headers, customer["id"])
    client.post(
        f"/api/shipments/{shipment['id']}/status",
        headers=headers,
        json={"status": "pending_pickup"},
    )
    summary = client.get("/api/dashboard/summary")
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["total_shipments"] == before["total_shipments"] + 1
    assert payload["pending_shipments"] == before["pending_shipments"] + 1
    assert (
        payload["shipments_by_status"]["pending_pickup"]
        == before["shipments_by_status"].get("pending_pickup", 0) + 1
    )
    assert payload["recent_shipments"][0]["id"] == shipment["id"]
