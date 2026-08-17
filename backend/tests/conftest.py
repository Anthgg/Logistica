import os

import pytest
from sqlalchemy import create_engine, func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from fastapi.testclient import TestClient

# Guardas de aislamiento disponibles para toda la suite.
from tests.isolation import (  # noqa: F401
    isolated_database,
    isolated_document_storage,
)


@pytest.fixture(scope="session")
def test_engine():
    database_url = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    is_sqlite = database_url.startswith("sqlite")

    if database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://", "postgresql+psycopg://", 1
        )
    use_existing = os.getenv("TEST_USE_EXISTING_SCHEMA", "").lower() == "true"
    schema = os.getenv("TEST_DATABASE_SCHEMA", "continuous_authentication_test")
    if not is_sqlite and not schema.replace("_", "").isalnum():
        raise ValueError("TEST_DATABASE_SCHEMA contiene caracteres no permitidos.")
    
    if is_sqlite:
        from sqlalchemy.ext.compiler import compiles
        from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

        @compiles(JSONB, "sqlite")
        def compile_jsonb_sqlite(type_, compiler, **kw):
            return "JSON"

        @compiles(PG_UUID, "sqlite")
        def compile_uuid_sqlite(type_, compiler, **kw):
            return "VARCHAR(36)"

        from sqlalchemy.sql.functions import char_length

        @compiles(char_length, "sqlite")
        def compile_char_length_sqlite(element, compiler, **kw):
            return f"LENGTH({compiler.process(element.clauses.clauses[0], **kw)})"

        engine = create_engine(database_url, connect_args={"check_same_thread": False})
        import app.models.registry  # register ORM models
        allowed_prefixes = (
            "organizations", "logistics_", "geo_", "vehicles", "vehicle_", "assisted_",
            "business_", "units_", "measurement_", "document_", "product",
            "purchase_", "po_", "audit_logs", "users", "sessions", "devices", "step_up_", "drivers", "driver_",
            "file_", "files", "evidence_", "signature_",
            "arrival_", "inbound_", "idempotency_", "reception_", "warehouse_reception_",
            "warehouses", "warehouse_", "gate_control_", "gate_", "dock_", "unloading_",
            "inventory_", "clients", "incidents", "continuous_", "facial_", "behavioral_",
            "consent_", "research_",
        )
        for table in Base.metadata.sorted_tables:
            if any(table.name.startswith(p) for p in allowed_prefixes):
                try:
                    table.create(engine, checkfirst=True)
                except Exception:
                    pass
        yield engine
        engine.dispose()
        return

    try:
        base_engine = create_engine(database_url, pool_pre_ping=True)
        with base_engine.connect():
            pass
        if not use_existing:
            with base_engine.begin() as connection:
                connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
    except Exception:
        # Fallback to SQLite in-memory
        from sqlalchemy.ext.compiler import compiles
        from sqlalchemy.dialects.postgresql import JSONB
        from sqlalchemy.sql.functions import GenericFunction

        @compiles(JSONB, "sqlite")
        def compile_jsonb_sqlite(type_, compiler, **kw):
            return "JSON"

        @compiles(func.char_length, "sqlite")
        def compile_char_length_sqlite(element, compiler, **kw):
            return compiler.process(func.length(*element.clauses), **kw)

        sqlite_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        import app.models.registry  # register ORM models
        allowed_prefixes = (
            "organizations", "logistics_", "geo_", "vehicles", "vehicle_", "assisted_",
            "business_", "units_", "measurement_", "document_", "product",
            "purchase_", "po_", "audit_logs", "users", "sessions", "devices", "step_up_", "drivers", "driver_",
            "file_", "files", "evidence_", "signature_",
            "arrival_", "inbound_", "idempotency_", "reception_", "warehouse_reception_",
            "warehouses", "warehouse_", "gate_control_", "gate_", "dock_", "unloading_",
            "inventory_", "clients", "incidents", "continuous_", "facial_", "behavioral_",
            "consent_", "research_",
        )
        for table in Base.metadata.sorted_tables:
            if any(table.name.startswith(p) for p in allowed_prefixes):
                try:
                    table.create(sqlite_engine, checkfirst=True)
                except Exception:
                    pass
        yield sqlite_engine
        sqlite_engine.dispose()
        return
    engine = (
        base_engine
        if use_existing
        else base_engine.execution_options(schema_translate_map={None: schema})
    )
    Base.metadata.create_all(engine, checkfirst=True)

    yield engine
    if not use_existing:
        Base.metadata.drop_all(engine)
        with base_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
    engine.dispose()
    base_engine.dispose()


@pytest.fixture
def database(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def client(database):
    def override_database():
        yield database

    app.dependency_overrides[get_db] = override_database
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
