from tests.support import authenticate, create_client, create_shipment


def test_shipment_tracking_timeline_filters_and_transition(client, database) -> None:
    _, headers = authenticate(client, database)
    customer = create_client(client, headers)
    first = create_shipment(client, headers, customer["id"])
    second = create_shipment(client, headers, customer["id"])
    assert first["tracking_code"].startswith("ALG-")
    assert first["tracking_code"] != second["tracking_code"]

    changed = client.post(
        f"/api/shipments/{first['id']}/status",
        headers=headers,
        json={
            "status": "pending_pickup",
            "description": "Recojo programado",
            "location": "Lima",
        },
    )
    assert changed.status_code == 200
    assert changed.json()["status"] == "pending_pickup"
    timeline = client.get(f"/api/shipments/{first['id']}/timeline")
    assert timeline.status_code == 200
    assert [event["new_status"] for event in timeline.json()] == [
        "registered",
        "pending_pickup",
    ]

    invalid = client.post(
        f"/api/shipments/{first['id']}/status",
        headers=headers,
        json={"status": "delivered"},
    )
    assert invalid.status_code == 409
    assert invalid.json()["error"]["code"] == "INVALID_SHIPMENT_STATUS_TRANSITION"

    page = client.get(
        "/api/shipments",
        params={
            "status": "pending_pickup",
            "client_id": customer["id"],
            "page": 1,
            "page_size": 1,
        },
    )
    assert page.status_code == 200
    assert page.json()["page_size"] == 1
    assert page.json()["total"] == 1


def test_client_with_shipment_is_logically_deactivated(client, database) -> None:
    _, headers = authenticate(client, database)
    customer = create_client(client, headers)
    create_shipment(client, headers, customer["id"])
    deleted = client.delete(f"/api/clients/{customer['id']}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["physically_deleted"] is False
    assert client.get(f"/api/clients/{customer['id']}").json()["is_active"] is False
