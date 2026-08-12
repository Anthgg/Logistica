from sqlalchemy import func, select

from app.models.client import Client
from app.models.shipment import Shipment
from app.models.user import User
from scripts.seed_logistics import reset_demo, seed
from tests.support import authenticate


def test_seed_is_idempotent_and_reset_preserves_users(client, database) -> None:
    user, _ = authenticate(client, database)
    first = seed(database)
    second = seed(database)
    assert first == second
    assert database.scalar(
        select(func.count()).select_from(Client).where(Client.is_demo.is_(True))
    ) == 10
    assert database.scalar(
        select(func.count()).select_from(Shipment).where(Shipment.is_demo.is_(True))
    ) == 40
    listed_clients = client.get(
        "/api/clients",
        params={"page_size": 100, "is_active": True},
    )
    assert listed_clients.status_code == 200, listed_clients.text
    assert listed_clients.json()["total"] == 10
    reset_demo(database)
    assert database.get(User, user.id) is not None
    assert database.scalar(
        select(func.count()).select_from(Client).where(Client.is_demo.is_(True))
    ) == 0
