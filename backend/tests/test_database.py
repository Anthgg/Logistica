from datetime import timedelta

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.database.base import Base, utc_now
from app.models.audit_log import AuditLog
from app.models.device import Device
from app.models.session import UserSession
from app.models.user import User


def test_metadata_registers_core_tables() -> None:
    # Verify that all original core tables are still registered in the metadata.
    # Uses subset check (<=) so that new tables added by logistics phases
    # (document_types, logistics_organizations, etc.) do not break this test.
    assert {
        "users",
        "devices",
        "sessions",
        "audit_logs",
        "clients",
        "shipments",
        "shipment_events",
        "warehouses",
        "inventory_items",
        "inventory_movements",
        "logistics_routes",
        "route_shipments",
        "incidents",
        "research_participants",
        "consent_records",
        "experimental_sessions",
        "facial_captures",
        "behavioral_batches",
        "continuous_auth_evaluations",
        "risk_events",
    } <= set(Base.metadata.tables)


def test_postgresql_connection_and_tables(database) -> None:
    assert database.execute(text("SELECT 1")).scalar_one() == 1
    schema_map = database.bind.get_execution_options().get("schema_translate_map")
    schema = schema_map[None] if schema_map else "public"
    assert {"users", "devices", "sessions", "audit_logs"} <= set(
        inspect(database.bind).get_table_names(schema=schema)
    )


def test_relations_and_cascade(database) -> None:
    user = User(
        email="relations-test@example.com",
        password_hash="temporary-test-hash-not-for-production",
        full_name="Relations Test",
    )
    device = Device(user=user, device_identifier="test-browser")
    user_session = UserSession(
        user=user,
        device=device,
        token_hash="temporary-token-hash-not-for-production",
        expires_at=utc_now() + timedelta(hours=1),
    )
    audit = AuditLog(user=user, session=user_session, event_type="test_event")
    database.add_all([user, device, user_session, audit])
    database.flush()

    assert device.user is user
    assert user_session.user is user
    assert audit.session is user_session

    database.delete(user)
    database.flush()
    assert database.get(Device, device.id) is None
    assert database.get(UserSession, user_session.id) is None


def test_duplicate_device_identifier_is_rejected(database) -> None:
    user = User(
        email="device-unique@example.com",
        password_hash="temporary-test-hash-not-for-production",
        full_name="Device Unique",
    )
    database.add(user)
    database.flush()
    database.add_all(
        [
            Device(user_id=user.id, device_identifier="same-device"),
            Device(user_id=user.id, device_identifier="same-device"),
        ]
    )
    with pytest.raises(IntegrityError):
        database.flush()
    database.rollback()
