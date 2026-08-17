from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_csrf_token
from app.models.branch import Branch
from app.models.device import Device
from app.models.organization import Organization
from app.models.user import User
from app.services.session_service import SessionService


def authenticate(
    client: TestClient, database: Session, role: str = "admin"
) -> tuple[User, dict[str, str]]:
    identifier = uuid4().hex
    user = User(
        email=f"{role}-{identifier}@example.test",
        password_hash="hash-ficticio-no-utilizable",
        full_name=f"Usuario {role}",
        role=role,
        is_active=True,
    )
    database.add(user)
    database.flush()
    device = Device(
        user_id=user.id,
        device_identifier=f"device-{identifier}",
        browser="pytest",
    )
    database.add(device)
    database.flush()
    _, access_token, _ = SessionService().create(
        database,
        user,
        device,
        "127.0.0.1",
        "pytest",
        False,
    )
    database.flush()
    csrf = generate_csrf_token()
    client.cookies.set(settings.SESSION_COOKIE_NAME, access_token)
    client.cookies.set(settings.CSRF_COOKIE_NAME, csrf)
    return user, {"X-CSRF-Token": csrf}


def create_client(
    client: TestClient, headers: dict[str, str], suffix: str | None = None
) -> dict[str, object]:
    token = suffix or uuid4().hex[:10]
    response = client.post(
        "/api/clients",
        headers=headers,
        json={
            "document_type": "RUC",
            "document_number": f"DOC-{token}",
            "business_name": f"Cliente Test {token}",
            "contact_name": "Contacto Ficticio",
            "email": f"{token}@example.com",
            "phone": "900000000",
            "address": "Av. Pruebas 123",
            "district": "Ate",
            "province": "Lima",
            "department": "Lima",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_shipment(
    client: TestClient,
    headers: dict[str, str],
    client_id: UUID | str,
) -> dict[str, object]:
    response = client.post(
        "/api/shipments",
        headers=headers,
        json={
            "client_id": str(client_id),
            "origin_address": "Origen ficticio 1",
            "destination_address": "Destino ficticio 2",
            "origin_district": "Ate",
            "destination_district": "Miraflores",
            "package_description": "Paquete de prueba",
            "package_count": 2,
            "total_weight": "4.5",
            "declared_value": "150.00",
            "priority": "normal",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_organization_branch(
    database: Session, *, org_code: str | None = None, branch_code: str = "SEDE"
) -> tuple[Organization, Branch]:
    """Crea una organizacion con una sede activa y las deja disponibles en la sesion.

    Desde F004 todo almacen debe colgar de una sede, asi que las suites que solo
    necesitan "un almacen cualquiera" necesitan primero esta pareja.
    """
    organization = Organization(
        code=org_code or f"ORG-{uuid4().hex[:8].upper()}",
        name="Organizacion de prueba",
        country_code="PE",
        timezone="America/Lima",
    )
    database.add(organization)
    database.flush()
    branch = Branch(
        organization_id=organization.id,
        code=f"{branch_code}-{uuid4().hex[:4].upper()}",
        name="Sede de prueba",
        timezone="America/Lima",
    )
    database.add(branch)
    database.flush()
    return organization, branch
