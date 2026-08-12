from datetime import date
from uuid import uuid4

from tests.support import authenticate, create_client, create_shipment


def test_assign_duplicate_delivered_and_remove_shipment(client, database) -> None:
    _, headers = authenticate(client, database)
    customer = create_client(client, headers)
    shipment = create_shipment(client, headers, customer["id"])
    route = client.post(
        "/api/routes",
        headers=headers,
        json={
            "route_code": f"R-{uuid4().hex[:8]}",
            "name": "Ruta de prueba",
            "origin": "Lima",
            "destination": "Callao",
            "scheduled_date": date.today().isoformat(),
            "status": "planned",
        },
    )
    assert route.status_code == 201
    route_id = route.json()["id"]
    assigned = client.post(
        f"/api/routes/{route_id}/assign-shipments",
        headers=headers,
        json={"shipment_ids": [shipment["id"]]},
    )
    assert assigned.status_code == 200
    duplicate = client.post(
        f"/api/routes/{route_id}/assign-shipments",
        headers=headers,
        json={"shipment_ids": [shipment["id"]]},
    )
    assert duplicate.status_code == 409
    removed = client.delete(
        f"/api/routes/{route_id}/shipments/{shipment['id']}", headers=headers
    )
    assert removed.status_code == 200
