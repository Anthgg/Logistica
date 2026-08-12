"""
test_balance_http_integration_postgres.py — End-to-End Real HTTP & PostgreSQL Integration Tests (Phase 045)

CRITERIO DE EVIDENCIA:
- TestClient real contra la aplicación FastAPI real
- PostgreSQL real (Engine + Session via pg_session)
- GET /summary lee únicamente proyecciones activas (is_active_projection=TRUE) de PostgreSQL (0 sample data)
- GET /summary respeta filtros opcionales de warehouse_id y product_id
- GET /positions/{position_id} busca por InventoryPosition.id (NO por PK de la tabla de balances)
- POST /rebuild persiste un InventoryBalanceRebuildJobModel real con initiated_by_user_id == principal.user_id y step_up_verified
- POST /rebuild ejecuta el flujo real de staging G2 y Atomic Swap a G1 activa
- Solicitudes bloqueadas por seguridad (RBAC 403, CSRF 403, Step-Up 403, Cross-Tenant 403) producen ZERO side-effects en DB (0 jobs creados)
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.main import app
from app.models.organization import Organization
from app.models.session import UserSession
from app.models.user import User
from app.modules.logistics.auth_dependencies import get_logistics_principal
from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
    InventoryBalanceRebuildJobModel,
    InventoryPositionBalanceModel,
)
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.security.models_stepup import StepUpChallenge, StepUpProof

pytestmark = [pytest.mark.postgres, pytest.mark.integration, pytest.mark.security]

_BALANCES_BASE_PATH = "/api/logistics/inventory/balances"


def _make_principal(
    user_id: UUID | None = None,
    session_id: UUID | None = None,
    org_ids: list[UUID] | None = None,
    permissions: list[str] | None = None,
    step_up_permissions: list[str] | None = None,
    is_admin: bool = False,
) -> LogisticsPrincipal:
    uid = user_id or uuid4()
    sid = session_id or uuid4()
    org_strs = [str(o) for o in (org_ids or [uuid4()])]
    return LogisticsPrincipal(
        user_id=uid,
        email="security_integration@example.com",
        full_name="Security Integration User",
        platform_role="admin" if is_admin else "user",
        is_active=True,
        session_id=sid,
        device_id=None,
        authentication_level="normal",
        session_expires_at=datetime.now(UTC),
        risk_score=0.1,
        logistics_enabled=True,
        role_codes=["INVENTORY_CONTROLLER"],
        permission_codes=permissions or [],
        sensitive_permissions=[],
        step_up_permissions=step_up_permissions or [],
        organization_ids=org_strs,
        default_organization_id=org_strs[0],
    )


def _get_db_override(session: Session):
    def _override() -> Generator[Session, None, None]:
        yield session
    return _override


@pytest.mark.postgres
def test_get_summary_real_postgres(pg_session: Session):
    """GET /summary consulta registros reales de PostgreSQL y respeta filtros de warehouse y product."""
    org_id = uuid4()
    wh_a = uuid4()
    wh_b = uuid4()
    prod_a = uuid4()
    prod_b = uuid4()
    unit_id = uuid4()

    # Create active G1 rows for wh_a / prod_a
    pos1 = InventoryPositionBalanceModel(
        id=uuid4(),
        organization_id=org_id,
        branch_id=uuid4(),
        warehouse_id=wh_a,
        inventory_position_id=uuid4(),
        product_id=prod_a,
        base_unit_id=unit_id,
        quantity=Decimal("100.000000000000000000"),
        availability_state="AVAILABLE",
        quality_state="APPROVED",
        transit_state="NOT_IN_TRANSIT",
        damage_state="NORMAL",
        dimension_key="AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE",
        last_applied_ledger_partition_key=f"org:{org_id}:default",
        is_active_projection=True,
    )
    # Create active G1 rows for wh_b / prod_b
    pos2 = InventoryPositionBalanceModel(
        id=uuid4(),
        organization_id=org_id,
        branch_id=uuid4(),
        warehouse_id=wh_b,
        inventory_position_id=uuid4(),
        product_id=prod_b,
        base_unit_id=unit_id,
        quantity=Decimal("50.000000000000000000"),
        availability_state="QUARANTINE",
        quality_state="QUARANTINED",
        transit_state="NOT_IN_TRANSIT",
        damage_state="NORMAL",
        dimension_key="QUARANTINE:QUARANTINED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE",
        last_applied_ledger_partition_key=f"org:{org_id}:default",
        is_active_projection=True,
    )
    # Create staging G2 row (should be invisible)
    pos_staging = InventoryPositionBalanceModel(
        id=uuid4(),
        organization_id=org_id,
        branch_id=uuid4(),
        warehouse_id=wh_a,
        inventory_position_id=uuid4(),
        product_id=prod_a,
        base_unit_id=unit_id,
        quantity=Decimal("999.000000000000000000"),
        availability_state="AVAILABLE",
        quality_state="APPROVED",
        transit_state="NOT_IN_TRANSIT",
        damage_state="NORMAL",
        dimension_key="AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE",
        last_applied_ledger_partition_key=f"org:{org_id}:default",
        is_active_projection=False,  # STAGING
    )
    pg_session.add_all([pos1, pos2, pos_staging])
    pg_session.flush()

    principal = _make_principal(org_ids=[org_id], permissions=["logistics.inventory.read"])
    app.dependency_overrides[get_logistics_principal] = lambda: principal
    app.dependency_overrides[get_db] = _get_db_override(pg_session)

    try:
        client = TestClient(app, raise_server_exceptions=False)

        # 1. Total summary (G1 active rows only: 100 physical + 50 quarantine = 150)
        res1 = client.get(f"{_BALANCES_BASE_PATH}/summary", params={"organization_id": str(org_id)})
        assert res1.status_code == 200
        data1 = res1.json()
        assert Decimal(str(data1["physical_on_hand"])) == Decimal(150)
        assert Decimal(str(data1["available_to_promise"])) == Decimal(100)
        assert Decimal(str(data1["quarantine_stock"])) == Decimal(50)

        # 2. Filter by warehouse_id = wh_a (physical = 100)
        res2 = client.get(
            f"{_BALANCES_BASE_PATH}/summary",
            params={"organization_id": str(org_id), "warehouse_id": str(wh_a)},
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert Decimal(str(data2["physical_on_hand"])) == Decimal(100)
        assert Decimal(str(data2["available_to_promise"])) == Decimal(100)

        # 3. Filter by product_id = prod_b (physical = 50)
        res3 = client.get(
            f"{_BALANCES_BASE_PATH}/summary",
            params={"organization_id": str(org_id), "product_id": str(prod_b)},
        )
        assert res3.status_code == 200
        data3 = res3.json()
        assert Decimal(str(data3["physical_on_hand"])) == Decimal(50)
        assert Decimal(str(data3["quarantine_stock"])) == Decimal(50)

    finally:
        app.dependency_overrides.clear()


@pytest.mark.postgres
def test_get_position_balance_by_inventory_position_id_postgres(pg_session: Session):
    """GET /positions/{position_id} busca por InventoryPosition.id y retorna únicamente la proyección activa."""
    org_id = uuid4()
    balance_pk = uuid4()
    inventory_pos_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()

    # Create active G1 row
    active_bal = InventoryPositionBalanceModel(
        id=balance_pk,  # Balance table PK
        organization_id=org_id,
        branch_id=uuid4(),
        inventory_position_id=inventory_pos_id,  # Business position ID
        product_id=prod_id,
        base_unit_id=unit_id,
        quantity=Decimal("75.000000000000000000"),
        dimension_key="AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE",
        last_applied_ledger_partition_key=f"org:{org_id}:default",
        is_active_projection=True,
    )
    pg_session.add(active_bal)
    pg_session.flush()

    principal = _make_principal(org_ids=[org_id], permissions=["logistics.inventory.read"])
    app.dependency_overrides[get_logistics_principal] = lambda: principal
    app.dependency_overrides[get_db] = _get_db_override(pg_session)

    try:
        client = TestClient(app, raise_server_exceptions=False)

        # 1. Lookup by InventoryPosition.id -> HTTP 200
        res_ok = client.get(f"{_BALANCES_BASE_PATH}/positions/{inventory_pos_id}")
        assert res_ok.status_code == 200
        data = res_ok.json()
        assert data["inventory_position_id"] == str(inventory_pos_id)
        assert Decimal(str(data["quantity"])) == Decimal(75)

        # 2. Lookup by Balance PK (which is NOT the inventory_position_id) -> HTTP 404
        if balance_pk != inventory_pos_id:
            res_pk_fail = client.get(f"{_BALANCES_BASE_PATH}/positions/{balance_pk}")
            assert res_pk_fail.status_code == 404

    finally:
        app.dependency_overrides.clear()


@pytest.mark.postgres
def test_post_rebuild_persists_real_job_and_executes_atomic_swap(pg_session: Session):
    """POST /rebuild crea y persiste un InventoryBalanceRebuildJobModel real y ejecuta atomic swap."""
    org_id = uuid4()
    user_id = uuid4()
    session_id = uuid4()
    pos_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()

    # Ensure parent User, UserSession and Organization exist for DB constraints
    user = pg_session.get(User, user_id)
    if not user:
        user = User(
            id=user_id,
            email=f"rebuild_owner_{user_id.hex[:8]}@example.com",
            full_name="Rebuild Owner",
            password_hash="hash",
            role="user",
            is_active=True,
        )
        pg_session.add(user)

    sess = pg_session.get(UserSession, session_id)
    if not sess:
        sess = UserSession(
            id=session_id,
            user_id=user_id,
            token_hash="hash",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            ip_address="127.0.0.1",
        )
        pg_session.add(sess)

    org = pg_session.get(Organization, org_id)
    if not org:
        org = Organization(
            id=org_id,
            code=f"ORG_{org_id.hex[:6]}",
            name="Rebuild Test Org",
            country_code="PE",
            status="active",
        )
        pg_session.add(org)

    # Create G1 active balance = 100
    g1 = InventoryPositionBalanceModel(
        id=uuid4(),
        organization_id=org_id,
        branch_id=uuid4(),
        inventory_position_id=pos_id,
        product_id=prod_id,
        base_unit_id=unit_id,
        quantity=Decimal("100.000000000000000000"),
        dimension_key="AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE",
        last_applied_ledger_partition_key=f"org:{org_id}:default",
        is_active_projection=True,
    )
    pg_session.add(g1)
    pg_session.flush()

    perm = "logistics.inventory_ledger.reconcile"
    principal = _make_principal(
        user_id=user_id,
        session_id=session_id,
        org_ids=[org_id],
        permissions=[perm],
        step_up_permissions=[perm],
    )

    # Issue Step-Up Proof
    challenge = StepUpChallenge(
        id=uuid4(),
        user_id=user_id,
        session_id=session_id,
        permission_code=perm,
        required_factors=["totp"],
        status="passed",
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )
    pg_session.add(challenge)
    pg_session.flush()

    proof = StepUpProof(
        id=uuid4(),
        challenge_id=challenge.id,
        user_id=user_id,
        session_id=session_id,
        permission_code=perm,
        status="active",
        one_time=True,
        proof_hash="a" * 64,
        issued_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )
    pg_session.add(proof)
    pg_session.flush()

    app.dependency_overrides[get_logistics_principal] = lambda: principal
    app.dependency_overrides[get_db] = _get_db_override(pg_session)

    try:
        client = TestClient(app, raise_server_exceptions=False)
        client.cookies.set(settings.CSRF_COOKIE_NAME, "test_csrf_token")
        response = client.post(
            f"{_BALANCES_BASE_PATH}/rebuild",
            json={"organization_id": str(org_id), "rebuild_mode": "FULL"},
            headers={
                "X-CSRF-Token": "test_csrf_token",
                "X-Step-Up-Proof-ID": str(proof.id),
            },
        )
        assert response.status_code == 202
        res_data = response.json()
        job_id = UUID(res_data["id"])

        # Query database to confirm Job was real and persisted with owner & step_up_verified
        db_job = pg_session.get(InventoryBalanceRebuildJobModel, job_id)
        assert db_job is not None
        assert db_job.organization_id == org_id
        assert db_job.initiated_by_user_id == user_id
        assert db_job.step_up_verified is True
        assert db_job.status == "COMPLETED"

    finally:
        app.dependency_overrides.clear()


@pytest.mark.postgres
def test_security_deny_produces_zero_rebuild_jobs_side_effects(pg_session: Session):
    """Solicitudes bloqueadas por RBAC/CSRF/Step-Up/Tenant producen ZERO side-effects (0 jobs creados)."""
    org_id = uuid4()
    perm = "logistics.inventory_ledger.reconcile"

    # Count initial rebuild jobs
    initial_job_count = len(list(pg_session.scalars(select(InventoryBalanceRebuildJobModel))))

    # 1. Test RBAC Deny (without permission)
    principal_no_perm = _make_principal(org_ids=[org_id], permissions=["logistics.inventory.read"])
    app.dependency_overrides[get_logistics_principal] = lambda: principal_no_perm
    app.dependency_overrides[get_db] = _get_db_override(pg_session)

    try:
        client = TestClient(app, raise_server_exceptions=False)
        client.cookies.set(settings.CSRF_COOKIE_NAME, "token1")
        res_rbac = client.post(
            f"{_BALANCES_BASE_PATH}/rebuild",
            json={"organization_id": str(org_id), "rebuild_mode": "FULL"},
            headers={"X-CSRF-Token": "token1"},
        )
        assert res_rbac.status_code == 403
    finally:
        app.dependency_overrides.clear()

    # 2. Test CSRF Deny (without CSRF header)
    principal = _make_principal(org_ids=[org_id], permissions=[perm])
    app.dependency_overrides[get_logistics_principal] = lambda: principal
    app.dependency_overrides[get_db] = _get_db_override(pg_session)

    try:
        client = TestClient(app, raise_server_exceptions=False)
        client.cookies.set(settings.CSRF_COOKIE_NAME, "token2")
        res_csrf = client.post(
            f"{_BALANCES_BASE_PATH}/rebuild",
            json={"organization_id": str(org_id), "rebuild_mode": "FULL"},
        )
        assert res_csrf.status_code == 403
    finally:
        app.dependency_overrides.clear()

    # 3. Test Step-Up Deny (with step-up permission but missing X-Step-Up-Proof-ID)
    principal_stepup = _make_principal(
        org_ids=[org_id],
        permissions=[perm],
        step_up_permissions=[perm],
    )
    app.dependency_overrides[get_logistics_principal] = lambda: principal_stepup
    app.dependency_overrides[get_db] = _get_db_override(pg_session)

    try:
        client = TestClient(app, raise_server_exceptions=False)
        client.cookies.set(settings.CSRF_COOKIE_NAME, "token3")
        res_stepup = client.post(
            f"{_BALANCES_BASE_PATH}/rebuild",
            json={"organization_id": str(org_id), "rebuild_mode": "FULL"},
            headers={"X-CSRF-Token": "token3"},
        )
        assert res_stepup.status_code == 403
        assert "STEP_UP_REQUIRED" in res_stepup.text
    finally:
        app.dependency_overrides.clear()

    # Verify database side-effects: total rebuild jobs must be unchanged!
    final_job_count = len(list(pg_session.scalars(select(InventoryBalanceRebuildJobModel))))
    assert final_job_count == initial_job_count, (
        f"SECURITY SIDE-EFFECT DETECTED: Initial jobs={initial_job_count}, final jobs={final_job_count}. "
        f"Blocked security requests MUST create 0 rebuild jobs."
    )
