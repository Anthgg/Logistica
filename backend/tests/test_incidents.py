from tests.support import authenticate, create_client, create_shipment


def test_incident_create_filter_and_resolve(client, database) -> None:
    _, headers = authenticate(client, database)
    customer = create_client(client, headers)
    shipment = create_shipment(client, headers, customer["id"])
    response = client.post(
        "/api/incidents",
        headers=headers,
        json={
            "shipment_id": shipment["id"],
            "incident_type": "damaged_package",
            "title": "Daño de prueba",
            "description": "Empaque dañado durante una prueba.",
            "severity": "critical",
        },
    )
    assert response.status_code == 201
    incident = response.json()
    listed = client.get(
        "/api/incidents",
        params={"severity": "critical", "search": "Daño de prueba"},
    )
    assert listed.json()["total"] == 1
    missing_resolution = client.post(
        f"/api/incidents/{incident['id']}/resolve",
        headers=headers,
        json={"resolution": ""},
    )
    assert missing_resolution.status_code == 422
    resolved = client.post(
        f"/api/incidents/{incident['id']}/resolve",
        headers=headers,
        json={"resolution": "Se sustituyó el empaque de manera segura."},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["resolved_at"] is not None
