from uuid import uuid4

from tests.support import authenticate


def _warehouse(client, headers) -> dict[str, object]:
    response = client.post(
        "/api/warehouses",
        headers=headers,
        json={
            "code": f"WH-{uuid4().hex[:8]}",
            "name": "Almacén de prueba",
            "address": "Av. Almacén 100",
            "district": "Ate",
            "province": "Lima",
            "department": "Lima",
            "capacity": "1000",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _item(client, headers, warehouse_id) -> dict[str, object]:
    response = client.post(
        "/api/inventory",
        headers=headers,
        json={
            "warehouse_id": warehouse_id,
            "sku": f"SKU-{uuid4().hex[:8]}",
            "name": "Caja de prueba",
            "current_stock": "10",
            "minimum_stock": "5",
            "unit": "unidad",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_inventory_atomic_movements_and_negative_stock(client, database) -> None:
    _, headers = authenticate(client, database)
    warehouse = _warehouse(client, headers)
    item = _item(client, headers, warehouse["id"])
    entry = client.post(
        "/api/inventory/movements",
        headers=headers,
        json={
            "inventory_item_id": item["id"],
            "movement_type": "entry",
            "quantity": "3",
            "reason": "Ingreso de prueba",
        },
    )
    assert entry.status_code == 201
    assert entry.json()["previous_stock"] == "10.000"
    assert entry.json()["resulting_stock"] == "13.000"

    exit_response = client.post(
        "/api/inventory/movements",
        headers=headers,
        json={
            "inventory_item_id": item["id"],
            "movement_type": "exit",
            "quantity": "4",
            "reason": "Salida de prueba",
        },
    )
    assert exit_response.status_code == 201
    assert exit_response.json()["resulting_stock"] == "9.000"

    negative = client.post(
        "/api/inventory/movements",
        headers=headers,
        json={
            "inventory_item_id": item["id"],
            "movement_type": "exit",
            "quantity": "100",
            "reason": "Salida imposible",
        },
    )
    assert negative.status_code == 409
    assert client.get(f"/api/inventory/{item['id']}").json()["current_stock"] == "9.000"

    adjustment = client.post(
        "/api/inventory/movements",
        headers=headers,
        json={
            "inventory_item_id": item["id"],
            "movement_type": "adjustment",
            "quantity": "1",
            "adjustment_resulting_stock": "2",
            "reason": "Conteo físico justificado",
        },
    )
    assert adjustment.status_code == 201
    assert adjustment.json()["resulting_stock"] == "2.000"


def test_duplicate_sku_per_warehouse_is_rejected(client, database) -> None:
    _, headers = authenticate(client, database)
    warehouse = _warehouse(client, headers)
    item = _item(client, headers, warehouse["id"])
    duplicate = client.post(
        "/api/inventory",
        headers=headers,
        json={
            "warehouse_id": warehouse["id"],
            "sku": item["sku"],
            "name": "Duplicado",
            "current_stock": "0",
            "minimum_stock": "0",
            "unit": "unidad",
        },
    )
    assert duplicate.status_code == 409
