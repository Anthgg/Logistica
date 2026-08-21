"""Warehouse inherited/custom geolocation contract and PostgreSQL migration tests."""

from __future__ import annotations

import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from app.models.branch import Branch
from app.models.warehouse import Warehouse
from app.modules.logistics.organization.schemas import (
    LogisticsWarehouseCreate,
    LogisticsWarehouseUpdate,
)

PREVIOUS_REVISION = "jl480110048dk"
CURRENT_REVISION = "km490110049wh"
BACKEND_DIR = Path(__file__).resolve().parents[1]
ORG_ID = UUID("a1000000-0000-0000-0000-000000000001")
BRANCH_ID = UUID("a2000000-0000-0000-0000-000000000002")
WAREHOUSE_ID = UUID("a3000000-0000-0000-0000-000000000003")


def _run_alembic(database_url: str, *arguments: str) -> None:
    environment = os.environ.copy()
    environment.update(DATABASE_URL=database_url, APP_ENV="testing")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=BACKEND_DIR,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"alembic {' '.join(arguments)} failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_location_schemas_accept_inherited_and_confirmed_custom() -> None:
    inherited = LogisticsWarehouseCreate(name="Heredado")
    custom = LogisticsWarehouseCreate(
        name="Propio",
        uses_branch_location=False,
        latitude=-12.1234567,
        longitude=-77.1234567,
    )

    assert inherited.uses_branch_location is True
    assert inherited.latitude is None and inherited.longitude is None
    assert custom.uses_branch_location is False
    assert custom.latitude == pytest.approx(-12.1234567)


@pytest.mark.parametrize(
    "payload",
    [
        {"uses_branch_location": False},
        {"uses_branch_location": False, "latitude": -12.0},
        {"uses_branch_location": True, "latitude": -12.0, "longitude": -77.0},
        {"uses_branch_location": False, "latitude": -90.0000001, "longitude": -77.0},
        {"uses_branch_location": False, "latitude": -12.0, "longitude": 180.0000001},
        {"uses_branch_location": False, "latitude": float("nan"), "longitude": -77.0},
        {"uses_branch_location": False, "latitude": float("inf"), "longitude": -77.0},
    ],
)
def test_location_schemas_reject_ambiguous_or_invalid_values(payload: dict) -> None:
    with pytest.raises(ValidationError):
        LogisticsWarehouseCreate(name="Inválido", **payload)


def test_update_schema_requires_coordinates_when_switching_to_custom() -> None:
    with pytest.raises(ValidationError):
        LogisticsWarehouseUpdate(uses_branch_location=False)


def test_effective_location_tracks_branch_only_in_inherited_mode() -> None:
    branch = Branch(latitude=Decimal("-12.1000000"), longitude=Decimal("-77.1000000"))
    inherited = Warehouse(uses_branch_location=True, latitude=None, longitude=None)
    inherited.branch = branch
    custom = Warehouse(
        uses_branch_location=False,
        latitude=Decimal("-12.2000000"),
        longitude=Decimal("-77.2000000"),
    )
    custom.branch = branch

    assert inherited.location_source == "BRANCH"
    assert inherited.effective_latitude == Decimal("-12.1000000")
    assert custom.location_source == "WAREHOUSE"
    assert custom.effective_latitude == Decimal("-12.2000000")

    branch.latitude = Decimal("-12.3000000")
    branch.longitude = Decimal("-77.3000000")
    assert inherited.effective_latitude == Decimal("-12.3000000")
    assert inherited.effective_longitude == Decimal("-77.3000000")
    assert custom.effective_latitude == Decimal("-12.2000000")
    assert custom.effective_longitude == Decimal("-77.2000000")


@pytest.mark.postgres
def test_migration_upgrades_existing_rows_and_enforces_constraints_on_postgres() -> None:
    database_url = os.getenv("TEST_MIGRATION_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_MIGRATION_DATABASE_URL is required for the destructive migration cycle")
    url = make_url(database_url)
    assert url.get_backend_name() == "postgresql"
    assert "warehouse_geo_test" in (url.database or ""), (
        "Safety guard: migration test requires a dedicated warehouse_geo_test database"
    )

    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        _run_alembic(database_url, "downgrade", PREVIOUS_REVISION)
        _run_alembic(database_url, "upgrade", PREVIOUS_REVISION)
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM warehouses WHERE id=:id"), {"id": WAREHOUSE_ID}
            )
            connection.execute(
                text("DELETE FROM logistics_branches WHERE id=:id"), {"id": BRANCH_ID}
            )
            connection.execute(
                text("DELETE FROM logistics_organizations WHERE id=:id"), {"id": ORG_ID}
            )
            connection.execute(
                text(
                    "INSERT INTO logistics_organizations "
                    "(id, code, name, country_code) "
                    "VALUES (:id, 'GEOMIGORG', 'Geo migration org', 'PE')"
                ),
                {"id": ORG_ID},
            )
            connection.execute(
                text(
                    "INSERT INTO logistics_branches "
                    "(id, organization_id, code, name, latitude, longitude) "
                    "VALUES (:id, :organization_id, 'GEOMIGBR', 'Geo migration branch', "
                    "-12.1000000, -77.1000000)"
                ),
                {"id": BRANCH_ID, "organization_id": ORG_ID},
            )
            connection.execute(
                text(
                    "INSERT INTO warehouses "
                    "(id, organization_id, branch_id, code, name, created_at, updated_at) "
                    "VALUES (:id, :organization_id, :branch_id, 'GEOMIGWH', "
                    "'Existing warehouse', now(), now())"
                ),
                {"id": WAREHOUSE_ID, "organization_id": ORG_ID, "branch_id": BRANCH_ID},
            )
            connection.execute(text("ALTER TABLE warehouses ENABLE ROW LEVEL SECURITY"))
            connection.execute(text("DROP POLICY IF EXISTS geo_migration_policy ON warehouses"))
            connection.execute(
                text(
                    "CREATE POLICY geo_migration_policy ON warehouses "
                    "USING (organization_id IS NOT NULL) "
                    "WITH CHECK (organization_id IS NOT NULL)"
                )
            )

        _run_alembic(database_url, "upgrade", "head")

        inspector = inspect(engine)
        columns = {column["name"]: column for column in inspector.get_columns("warehouses")}
        assert {"uses_branch_location", "latitude", "longitude"} <= columns.keys()
        assert columns["uses_branch_location"]["nullable"] is False
        checks = {constraint["name"] for constraint in inspector.get_check_constraints("warehouses")}
        assert {
            "chk_warehouses_latitude",
            "chk_warehouses_longitude",
            "chk_warehouses_location_mode",
        } <= checks

        with engine.connect() as connection:
            row = connection.execute(
                text(
                    "SELECT uses_branch_location, latitude, longitude "
                    "FROM warehouses WHERE id=:id"
                ),
                {"id": WAREHOUSE_ID},
            ).one()
            assert tuple(row) == (True, None, None)
            assert connection.scalar(
                text("SELECT relrowsecurity FROM pg_class WHERE oid='warehouses'::regclass")
            ) is True
            policy = connection.execute(
                text(
                    "SELECT qual, with_check FROM pg_policies "
                    "WHERE schemaname='public' AND tablename='warehouses' "
                    "AND policyname='geo_migration_policy'"
                )
            ).one()
            assert "organization_id IS NOT NULL" in policy.qual
            assert "organization_id IS NOT NULL" in policy.with_check

        invalid_statements = [
            (
                "BADINHERITED",
                "true, -12.0, -77.0",
            ),
            (
                "BADCUSTOMNULL",
                "false, NULL, NULL",
            ),
            (
                "BADLATITUDE",
                "false, -91.0, -77.0",
            ),
            (
                "BADLONGITUDE",
                "false, -12.0, 181.0",
            ),
        ]
        for code, location_values in invalid_statements:
            with pytest.raises(IntegrityError), engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO warehouses "
                        "(id, organization_id, branch_id, code, name, created_at, updated_at, "
                        "uses_branch_location, latitude, longitude) "
                        f"VALUES (:id, :organization_id, :branch_id, :code, "
                        f"'Invalid warehouse', now(), now(), {location_values})"
                    ),
                    {
                        "id": uuid4(),
                        "organization_id": ORG_ID,
                        "branch_id": BRANCH_ID,
                        "code": code,
                    },
                )

        with engine.begin() as connection:
            connection.execute(text("DROP POLICY geo_migration_policy ON warehouses"))
    finally:
        _run_alembic(database_url, "upgrade", CURRENT_REVISION)
        engine.dispose()
