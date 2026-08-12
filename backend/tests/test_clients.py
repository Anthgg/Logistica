from tests.support import authenticate, create_client


def test_client_crud_duplicate_search_and_deactivation(client, database) -> None:
    _, headers = authenticate(client, database)
    created = create_client(client, headers)

    duplicate = client.post(
        "/api/clients",
        headers=headers,
        json={
            "document_type": "RUC",
            "document_number": created["document_number"],
            "business_name": "Duplicado",
            "address": "Av. Test",
            "district": "Ate",
            "province": "Lima",
            "department": "Lima",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "CLIENT_DOCUMENT_ALREADY_EXISTS"

    listed = client.get("/api/clients", params={"search": created["business_name"]})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    updated = client.patch(
        f"/api/clients/{created['id']}",
        headers=headers,
        json={"phone": "911111111"},
    )
    assert updated.status_code == 200
    assert updated.json()["phone"] == "911111111"

    deleted = client.delete(f"/api/clients/{created['id']}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["physically_deleted"] is True


def test_client_write_requires_admin_and_csrf(client, database) -> None:
    _, headers = authenticate(client, database, "dispatcher")
    forbidden = client.post(
        "/api/clients",
        headers=headers,
        json={
            "document_type": "RUC",
            "document_number": "NO-PERMITIDO",
            "business_name": "Sin permiso",
            "address": "Dirección de prueba",
            "district": "Ate",
            "province": "Lima",
            "department": "Lima",
        },
    )
    assert forbidden.status_code == 403
    no_csrf = client.post("/api/clients", json={})
    assert no_csrf.status_code == 403
