import argparse
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import delete, func, select, text

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database.base import utc_now
from app.database.session import SessionLocal
from app.models.client import Client
from app.models.incident import Incident
from app.models.inventory_item import InventoryItem
from app.models.inventory_movement import InventoryMovement
from app.models.logistics_route import LogisticsRoute
from app.models.route_shipment import RouteShipment
from app.models.shipment import Shipment
from app.models.shipment_event import ShipmentEvent
from app.models.user import User
from app.models.warehouse import Warehouse


def reset_demo(database) -> None:
    database.execute(delete(Incident).where(Incident.is_demo.is_(True)))
    database.execute(
        delete(InventoryMovement).where(InventoryMovement.is_demo.is_(True))
    )
    database.execute(delete(Shipment).where(Shipment.is_demo.is_(True)))
    database.execute(delete(InventoryItem).where(InventoryItem.is_demo.is_(True)))
    database.execute(
        delete(LogisticsRoute).where(LogisticsRoute.is_demo.is_(True))
    )
    database.execute(delete(Warehouse).where(Warehouse.is_demo.is_(True)))
    database.execute(delete(Client).where(Client.is_demo.is_(True)))
    database.commit()


def seed(database) -> dict[str, int]:
    actor = database.scalar(
        select(User)
        .order_by((User.role == "admin").desc(), User.created_at.asc())
        .limit(1)
    )
    if not actor:
        raise RuntimeError(
            "Se requiere al menos un usuario antes de insertar datos demo."
        )

    clients: list[Client] = []
    for index in range(1, 11):
        document = f"DEMO20{index:06d}"
        client = database.scalar(
            select(Client).where(Client.document_number == document)
        )
        if not client:
            client = Client(
                document_type="RUC",
                document_number=document,
                business_name=f"Empresa Demo Andina {index:02d} S.A.C.",
                contact_name=f"Contacto Demo {index:02d}",
                email=f"contacto{index:02d}@example.com",
                phone=f"900000{index:03d}",
                address=f"Av. Logística {100 + index}",
                district="Ate",
                province="Lima",
                department="Lima",
                is_demo=True,
            )
            database.add(client)
        clients.append(client)
    database.flush()

    warehouse_specs = [
        ("DEMO-LIM", "Almacén Demo Lima", "Lima"),
        ("DEMO-AQP", "Almacén Demo Arequipa", "Arequipa"),
        ("DEMO-TRU", "Almacén Demo Trujillo", "Trujillo"),
    ]
    warehouses: list[Warehouse] = []
    for code, name, province in warehouse_specs:
        warehouse = database.scalar(
            select(Warehouse).where(Warehouse.code == code)
        )
        if not warehouse:
            warehouse = Warehouse(
                code=code,
                name=name,
                address="Av. Operaciones 100",
                district=province,
                province=province,
                department=province,
                capacity=Decimal("10000"),
                is_demo=True,
            )
            database.add(warehouse)
        warehouses.append(warehouse)
    database.flush()

    items: list[InventoryItem] = []
    for index in range(1, 21):
        warehouse = warehouses[(index - 1) % len(warehouses)]
        sku = f"DEMO-SKU-{index:03d}"
        item = database.scalar(
            select(InventoryItem).where(
                InventoryItem.warehouse_id == warehouse.id,
                InventoryItem.sku == sku,
            )
        )
        if not item:
            stock = Decimal(str((index % 8) + 2))
            item = InventoryItem(
                warehouse_id=warehouse.id,
                sku=sku,
                name=f"Material logístico demo {index:02d}",
                description="Artículo ficticio para demostración.",
                current_stock=stock,
                minimum_stock=Decimal("5"),
                unit="unidad",
                is_demo=True,
            )
            database.add(item)
        items.append(item)
    database.flush()

    routes: list[LogisticsRoute] = []
    for index in range(1, 7):
        route_code = f"DEMO-RUTA-{index:02d}"
        route = database.scalar(
            select(LogisticsRoute).where(LogisticsRoute.route_code == route_code)
        )
        if not route:
            route = LogisticsRoute(
                route_code=route_code,
                name=f"Ruta Demo {index:02d}",
                origin="Lima",
                destination=("Arequipa", "Trujillo", "Cusco")[index % 3],
                driver_name=f"Conductor Demo {index:02d}",
                vehicle_plate=f"DMO-{index:03d}",
                scheduled_date=date.today() + timedelta(days=(index % 3) - 1),
                status=("planned", "active", "completed")[index % 3],
                is_demo=True,
            )
            database.add(route)
        routes.append(route)
    database.flush()

    existing_shipments = list(
        database.scalars(
            select(Shipment)
            .where(Shipment.is_demo.is_(True))
            .order_by(Shipment.created_at)
        )
    )
    shipment_states = [
        "registered",
        "pending_pickup",
        "picked_up",
        "warehouse_received",
        "in_transit",
        "out_for_delivery",
        "delivered",
        "delayed",
    ]
    for index in range(len(existing_shipments) + 1, 41):
        sequence = database.execute(
            text("SELECT nextval('shipment_tracking_seq')")
        ).scalar_one()
        state = shipment_states[(index - 1) % len(shipment_states)]
        shipment = Shipment(
            tracking_code=f"ALG-{utc_now().year}-{int(sequence):06d}",
            client_id=clients[(index - 1) % len(clients)].id,
            origin_address="Centro de distribución Demo Lima",
            destination_address=f"Dirección ficticia {index:03d}",
            origin_district="Ate",
            destination_district=("Miraflores", "Yanahuara", "Víctor Larco")[
                index % 3
            ],
            package_description=f"Envío ficticio de demostración {index:03d}",
            package_count=(index % 5) + 1,
            total_weight=Decimal(str((index % 12) + 1)),
            declared_value=Decimal(str(100 + index * 10)),
            priority=("low", "normal", "high", "urgent")[index % 4],
            status=state,
            delivered_at=utc_now() if state == "delivered" else None,
            created_by=actor.id,
            is_demo=True,
        )
        database.add(shipment)
        database.flush()
        database.add(
            ShipmentEvent(
                shipment_id=shipment.id,
                previous_status=None,
                new_status="registered",
                description="Creado por el seed de demostración.",
                created_by=actor.id,
            )
        )
        if state != "registered":
            database.add(
                ShipmentEvent(
                    shipment_id=shipment.id,
                    previous_status="registered",
                    new_status=state,
                    description="Estado demo consolidado.",
                    created_by=actor.id,
                )
            )
        existing_shipments.append(shipment)
    database.flush()

    for index, shipment in enumerate(existing_shipments[:24]):
        route = routes[index % len(routes)]
        assignment = database.scalar(
            select(RouteShipment).where(
                RouteShipment.route_id == route.id,
                RouteShipment.shipment_id == shipment.id,
            )
        )
        if not assignment and shipment.status not in {
            "delivered",
            "cancelled",
            "returned",
        }:
            database.add(
                RouteShipment(
                    route_id=route.id,
                    shipment_id=shipment.id,
                    assigned_by=actor.id,
                )
            )
            shipment.assigned_route_id = route.id

    incident_count = database.scalar(
        select(func.count())
        .select_from(Incident)
        .where(Incident.is_demo.is_(True))
    ) or 0
    incident_types = [
        "delay",
        "damaged_package",
        "missing_package",
        "incorrect_address",
        "failed_delivery",
        "vehicle_problem",
        "inventory_difference",
        "other",
    ]
    for index in range(incident_count + 1, 11):
        database.add(
            Incident(
                shipment_id=existing_shipments[index - 1].id,
                incident_type=incident_types[(index - 1) % len(incident_types)],
                title=f"Incidencia demo {index:02d}",
                description="Incidencia ficticia para validar el módulo.",
                severity=("low", "medium", "high", "critical")[index % 4],
                status=("open", "investigating", "resolved")[index % 3],
                reported_by=actor.id,
                assigned_to=actor.id if index % 3 == 0 else None,
                resolution="Resolución ficticia." if index % 3 == 0 else None,
                resolved_at=utc_now() if index % 3 == 0 else None,
                is_demo=True,
            )
        )
    database.commit()
    return {
        "clients": 10,
        "warehouses": 3,
        "inventory_items": 20,
        "shipments": 40,
        "routes": 6,
        "incidents": 10,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Datos ficticios de AndesLog.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Elimina únicamente registros marcados como demo antes de reinsertarlos.",
    )
    arguments = parser.parse_args()
    with SessionLocal() as database:
        if arguments.reset:
            reset_demo(database)
        totals = seed(database)
    print("Seed logístico completado de forma idempotente:")
    for entity, total in totals.items():
        print(f"- {entity}: {total}")


if __name__ == "__main__":
    main()
