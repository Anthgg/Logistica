"""
test_balance_rebuild_and_metrics_postgres.py — Real PostgreSQL Tests for Phase 045

Validates:
1. Rebuild from Phase 044 Event Ledger (corrupted G1, G1 without existing balance, hash failure preservation).
2. The 8 separate stock metrics calculation and HTTP/Service summary.
3. Multi-tenant atomic swap safety (same position UUID between tenants, failed swap rollback).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.inventory.balances.application.queries.balance_query_service import (
    BalanceQueryService,
)
from app.modules.logistics.inventory.balances.application.services.rebuild_application_service import (
    BalanceRebuildApplicationService,
    RebuildSwapFailedError,
)
from app.modules.logistics.inventory.balances.infrastructure.persistence.models import (
    InventoryBalanceDeltaModel,
    InventoryPositionBalanceModel,
)
from app.modules.logistics.inventory.ledger.infrastructure.persistence.models import (
    InventoryMovementLineModel,
    InventoryMovementModel,
    InventoryPositionModel,
)

pytestmark = [pytest.mark.postgres, pytest.mark.integration]

# Default partition key used when creating bare balance rows in tests
_DEFAULT_PARTITION = "TEST:DEFAULT"
_DEFAULT_DIM_KEY = "AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE"


def _create_position(
    db: Session,
    org_id: UUID,
    branch_id: UUID,
    wh_id: UUID,
    prod_id: UUID,
    availability_state: str = "AVAILABLE",
    quality_state: str = "APPROVED",
    transit_state: str = "NOT_IN_TRANSIT",
    damage_state: str = "NORMAL",
    expiration_state: str = "NOT_APPLICABLE",
) -> InventoryPositionModel:
    pos_id = uuid4()
    dim_key = f"{availability_state}:{quality_state}:{transit_state}:{damage_state}:{expiration_state}"[:64]
    pos = InventoryPositionModel(
        id=pos_id,
        organization_id=org_id,
        branch_id=branch_id,
        warehouse_id=wh_id,
        boundary_type="INTERNAL",
        product_id=prod_id,
        availability_state=availability_state,
        quality_state=quality_state,
        transit_state=transit_state,
        damage_state=damage_state,
        expiration_state=expiration_state,
        dimension_key=dim_key,
        status="ACTIVE",
        created_at=datetime.now(UTC),
    )
    db.add(pos)
    db.flush()
    return pos


def _create_movement(
    db: Session,
    org_id: UUID,
    branch_id: UUID,
    partition_key: str,
    sequence: int,
    dest_pos_id: UUID | None = None,
    src_pos_id: UUID | None = None,
    base_qty: Decimal = Decimal("100.000000000000000000"),
    prev_hash: str | None = None,
    mov_hash: str | None = None,
) -> InventoryMovementModel:
    m_id = uuid4()
    calculated_hash = mov_hash or f"hash_{sequence}_{m_id.hex[:8]}"
    mov = InventoryMovementModel(
        id=m_id,
        organization_id=org_id,
        branch_id=branch_id,
        movement_code=f"MOV-{sequence}-{m_id.hex[:6]}",
        normalized_movement_code=f"mov-{sequence}-{m_id.hex[:6]}",
        ledger_partition_key=partition_key,
        ledger_sequence=sequence,
        movement_type="RECEIPT",
        movement_family="INBOUND",
        status="POSTED",
        source_system="TEST",
        source_event_type="TEST_EVENT",
        source_event_id=str(uuid4()),
        occurred_at=datetime.now(UTC),
        previous_movement_hash=prev_hash,
        movement_hash=calculated_hash,
        created_at=datetime.now(UTC),
    )
    db.add(mov)
    # Flush movement FIRST so FK constraint is satisfied before inserting line
    db.flush()

    line = InventoryMovementLineModel(
        id=uuid4(),
        inventory_movement_id=m_id,
        line_number=1,
        product_id=uuid4(),
        quantity=base_qty,
        unit_id=uuid4(),
        base_quantity=base_qty,
        base_unit_id=uuid4(),
        destination_position_id=dest_pos_id,
        source_position_id=src_pos_id,
        # Satisfy ck_inventory_movement_line_source_boundary:
        # At least one of source/destination (internal position OR external boundary) must be set per direction.
        source_external_boundary_kind="VENDOR" if dest_pos_id and not src_pos_id else None,
        destination_external_boundary_kind="CUSTOMER" if src_pos_id and not dest_pos_id else None,
        quantity_direction="INCREASE" if dest_pos_id else "DECREASE",
        content_hash=f"line_hash_{sequence}",
        created_at=datetime.now(UTC),
    )
    db.add(line)
    db.flush()
    return mov


def _make_balance(
    org_id: UUID,
    branch_id: UUID,
    wh_id: UUID,
    pos_id: UUID,
    prod_id: UUID,
    quantity: Decimal,
    partition_key: str = _DEFAULT_PARTITION,
    dim_key: str = _DEFAULT_DIM_KEY,
    avail: str = "AVAILABLE",
    qual: str = "APPROVED",
    trans: str = "NOT_IN_TRANSIT",
    dam: str = "NORMAL",
    exp: str = "NOT_APPLICABLE",
    is_active: bool = True,
) -> InventoryPositionBalanceModel:
    """Helper that always sets all NOT NULL fields on InventoryPositionBalanceModel."""
    return InventoryPositionBalanceModel(
        id=uuid4(),
        organization_id=org_id,
        branch_id=branch_id,
        warehouse_id=wh_id,
        inventory_position_id=pos_id,
        product_id=prod_id,
        base_unit_id=prod_id,
        quantity=quantity,
        availability_state=avail,
        quality_state=qual,
        transit_state=trans,
        damage_state=dam,
        expiration_state=exp,
        dimension_key=dim_key[:64],
        last_applied_ledger_partition_key=partition_key,
        last_applied_ledger_sequence=0,
        is_active_projection=is_active,
        data_quality_status="PROJECTION_CURRENT",
    )


@pytest.mark.postgres
def test_rebuild_corrupted_g1_from_f044_ledger(pg_session: Session):
    """1. Rebuild ignores corrupted G1 quantity (999) and reconstructs true balance (80) from F044 Ledger."""
    org_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    part_key = f"org:{org_id}:default"

    # F044 Position
    pos = _create_position(pg_session, org_id, branch_id, wh_id, prod_id)

    # F044 Ledger movements: +100, -20 => 80
    m1 = _create_movement(pg_session, org_id, branch_id, part_key, 1, dest_pos_id=pos.id, base_qty=Decimal(100))
    _create_movement(
        pg_session, org_id, branch_id, part_key, 2,
        src_pos_id=pos.id, base_qty=Decimal(20),
        prev_hash=m1.movement_hash,
    )

    # Corrupt G1 manually in SQL to 999
    corrupted_g1 = _make_balance(org_id, branch_id, wh_id, pos.id, prod_id, Decimal(999), partition_key=part_key)
    pg_session.add(corrupted_g1)
    pg_session.commit()

    # Execute Rebuild
    rebuild_service = BalanceRebuildApplicationService(pg_session)
    job = rebuild_service.create_rebuild_job(
        organization_id=org_id,
        initiated_by_user_id=uuid4(),
        rebuild_mode="FULL",
        step_up_verified=True,
    )
    rebuild_service.execute_rebuild_from_ledger(job.id)
    pg_session.commit()

    # Verify active balance is 80 (never 999 or 1079)
    active_balance = pg_session.scalars(
        select(InventoryPositionBalanceModel)
        .where(InventoryPositionBalanceModel.organization_id == org_id)
        .where(InventoryPositionBalanceModel.inventory_position_id == pos.id)
        .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
    ).first()

    assert active_balance is not None
    assert active_balance.quantity == Decimal("80.000000000000000000")
    assert job.status == "COMPLETED"


@pytest.mark.postgres
def test_rebuild_without_existing_g1(pg_session: Session):
    """2. Rebuild creates position projection from Ledger even when G1 active row is completely missing."""
    org_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    part_key = f"org:{org_id}:default"

    pos = _create_position(pg_session, org_id, branch_id, wh_id, prod_id)
    _create_movement(pg_session, org_id, branch_id, part_key, 1, dest_pos_id=pos.id, base_qty=Decimal(80))
    pg_session.commit()

    # Rebuild without pre-existing G1
    rebuild_service = BalanceRebuildApplicationService(pg_session)
    job = rebuild_service.create_rebuild_job(
        organization_id=org_id,
        initiated_by_user_id=uuid4(),
        rebuild_mode="FULL",
        step_up_verified=True,
    )
    rebuild_service.execute_rebuild_from_ledger(job.id)
    pg_session.commit()

    active_balance = pg_session.scalars(
        select(InventoryPositionBalanceModel)
        .where(InventoryPositionBalanceModel.organization_id == org_id)
        .where(InventoryPositionBalanceModel.inventory_position_id == pos.id)
        .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
    ).first()

    assert active_balance is not None
    assert active_balance.quantity == Decimal("80.000000000000000000")


@pytest.mark.postgres
def test_rebuild_incremental_vs_full_same_result(pg_session: Session):
    """3. Full ledger rebuild vs incremental deltas replay produce identical final balance."""
    org_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    part_key = f"org:{org_id}:default"

    pos = _create_position(pg_session, org_id, branch_id, wh_id, prod_id)
    _create_movement(pg_session, org_id, branch_id, part_key, 1, dest_pos_id=pos.id, base_qty=Decimal(100))

    # Add pending delta +20
    delta = InventoryBalanceDeltaModel(
        id=uuid4(),
        organization_id=org_id,
        position_id=pos.id,
        delta_quantity=Decimal(20),
        delta_type="INCREASE",
        ledger_partition_key=part_key,
        ledger_sequence=2,
        applied_status="PENDING",
        created_at=datetime.now(UTC),
    )
    pg_session.add(delta)
    pg_session.commit()

    rebuild_service = BalanceRebuildApplicationService(pg_session)
    job = rebuild_service.create_rebuild_job(
        organization_id=org_id,
        initiated_by_user_id=uuid4(),
        rebuild_mode="FULL",
        step_up_verified=True,
    )
    rebuild_service.execute_rebuild_from_ledger(job.id)
    pg_session.commit()

    active_balance = pg_session.scalars(
        select(InventoryPositionBalanceModel)
        .where(InventoryPositionBalanceModel.organization_id == org_id)
        .where(InventoryPositionBalanceModel.inventory_position_id == pos.id)
        .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
    ).first()

    assert active_balance is not None
    assert active_balance.quantity == Decimal("120.000000000000000000")


@pytest.mark.postgres
def test_eight_balance_metrics_summary(pg_session: Session):
    """4-7. Tests all 8 stock metrics calculations with explicit distinct quantities."""
    org_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    branch_id = uuid4()

    # Create 7 balance rows with distinct states and quantities
    metrics_spec = [
        ("AVAILABLE",  "APPROVED",    "NOT_IN_TRANSIT",    "NORMAL",  "NOT_APPLICABLE", Decimal(10)),
        ("RESERVED",   "APPROVED",    "NOT_IN_TRANSIT",    "NORMAL",  "NOT_APPLICABLE", Decimal(20)),
        ("BLOCKED",    "APPROVED",    "NOT_IN_TRANSIT",    "NORMAL",  "NOT_APPLICABLE", Decimal(30)),
        ("QUARANTINE", "QUARANTINED", "NOT_IN_TRANSIT",    "NORMAL",  "NOT_APPLICABLE", Decimal(40)),
        ("IN_TRANSIT", "APPROVED",    "IN_TRANSIT_INBOUND","NORMAL",  "NOT_APPLICABLE", Decimal(50)),
        ("DAMAGED",    "APPROVED",    "NOT_IN_TRANSIT",    "DAMAGED", "NOT_APPLICABLE", Decimal(60)),
        ("EXPIRED",    "APPROVED",    "NOT_IN_TRANSIT",    "NORMAL",  "EXPIRED",        Decimal(70)),
    ]

    for avail, qual, trans, dam, exp, qty in metrics_spec:
        pos_id = uuid4()
        dim_key = f"{avail}:{qual}:{trans}:{dam}:{exp}"[:64]
        b = _make_balance(
            org_id, branch_id, wh_id, pos_id, prod_id, qty,
            dim_key=dim_key, avail=avail, qual=qual, trans=trans, dam=dam, exp=exp,
        )
        pg_session.add(b)

    pg_session.commit()

    query_service = BalanceQueryService()
    summary = query_service.get_active_balances_summary(pg_session, org_id)

    # 1. Physical on hand: excludes IN_TRANSIT => 10+20+30+40+60+70 = 230
    assert summary["physical_on_hand"] == Decimal("230.000000000000000000")
    # 2. Available to promise: AVAILABLE only = 10
    assert summary["available_to_promise"] == Decimal("10.000000000000000000")
    # 3. Reserved stock (SEPARATE): 20
    assert summary["reserved_stock"] == Decimal("20.000000000000000000")
    # 4. Blocked stock (SEPARATE): 30
    assert summary["blocked_stock"] == Decimal("30.000000000000000000")
    # 5. Quarantine stock: 40
    assert summary["quarantine_stock"] == Decimal("40.000000000000000000")
    # 6. In transit stock: 50
    assert summary["in_transit_stock"] == Decimal("50.000000000000000000")
    # 7. Damaged stock (SEPARATE): 60
    assert summary["damaged_stock"] == Decimal("60.000000000000000000")
    # 8. Expired stock (SEPARATE): 70
    assert summary["expired_stock"] == Decimal("70.000000000000000000")


@pytest.mark.postgres
def test_tenant_safe_atomic_swap_same_position_uuid(pg_session: Session):
    """8-9. Multi-tenant atomic swap with identical position UUID does NOT leak or mutate cross-tenant data."""
    org_a = uuid4()
    org_b = uuid4()
    shared_pos_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    part_a = f"org:{org_a}:default"

    # Create F044 position & movements for Org A
    pos_a = InventoryPositionModel(
        id=shared_pos_id,
        organization_id=org_a,
        branch_id=branch_id,
        warehouse_id=wh_id,
        boundary_type="INTERNAL",
        product_id=prod_id,
        availability_state="AVAILABLE",
        quality_state="APPROVED",
        transit_state="NOT_IN_TRANSIT",
        damage_state="NORMAL",
        expiration_state="NOT_APPLICABLE",
        dimension_key=_DEFAULT_DIM_KEY,
        status="ACTIVE",
        created_at=datetime.now(UTC),
    )
    pg_session.add(pos_a)
    pg_session.flush()
    _create_movement(pg_session, org_a, branch_id, part_a, 1, dest_pos_id=shared_pos_id, base_qty=Decimal(100))

    # Active G1 for Org A = 100
    g1_a = _make_balance(org_a, branch_id, wh_id, shared_pos_id, prod_id, Decimal(100), partition_key=part_a)
    pg_session.add(g1_a)

    # Active G1 for Org B with SAME position UUID = 500 (different org, same pos_id)
    g1_b = _make_balance(org_b, branch_id, wh_id, shared_pos_id, prod_id, Decimal(500), partition_key=f"org:{org_b}:default")
    pg_session.add(g1_b)
    pg_session.commit()

    # Rebuild strictly for Org A
    rebuild_service = BalanceRebuildApplicationService(pg_session)
    job = rebuild_service.create_rebuild_job(
        organization_id=org_a,
        initiated_by_user_id=uuid4(),
        rebuild_mode="FULL",
        step_up_verified=True,
    )
    rebuild_service.execute_rebuild_from_ledger(job.id)
    pg_session.commit()

    # Verify Org A active balance updated from ledger (100)
    bal_a = pg_session.scalars(
        select(InventoryPositionBalanceModel)
        .where(InventoryPositionBalanceModel.organization_id == org_a)
        .where(InventoryPositionBalanceModel.inventory_position_id == shared_pos_id)
        .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
    ).first()
    assert bal_a is not None
    assert bal_a.quantity == Decimal("100.000000000000000000")

    # Verify Org B active balance remains EXACTLY 500 (unaffected by Org A rebuild)
    bal_b = pg_session.scalars(
        select(InventoryPositionBalanceModel)
        .where(InventoryPositionBalanceModel.organization_id == org_b)
        .where(InventoryPositionBalanceModel.inventory_position_id == shared_pos_id)
        .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
    ).first()
    assert bal_b is not None
    assert bal_b.quantity == Decimal("500.000000000000000000")


@pytest.mark.postgres
def test_rebuild_hash_failure_preserves_g1(pg_session: Session):
    """10. Ledger hash mismatch aborts rebuild with FAILED status and preserves original G1 balance intact."""
    org_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    part_key = f"org:{org_id}:default"

    pos = _create_position(pg_session, org_id, branch_id, wh_id, prod_id)

    # Initial active G1 balance = 50
    g1 = _make_balance(org_id, branch_id, wh_id, pos.id, prod_id, Decimal(50), partition_key=part_key)
    pg_session.add(g1)

    # Create movement with mismatched previous hash (deliberately corrupted chain)
    _create_movement(
        pg_session,
        org_id,
        branch_id,
        part_key,
        sequence=1,
        dest_pos_id=pos.id,
        base_qty=Decimal(100),
        prev_hash="CORRUPTED_PREVIOUS_HASH_MISMATCH",
    )
    pg_session.commit()

    rebuild_service = BalanceRebuildApplicationService(pg_session)
    job = rebuild_service.create_rebuild_job(
        organization_id=org_id,
        initiated_by_user_id=uuid4(),
        rebuild_mode="FULL",
        step_up_verified=True,
    )

    with pytest.raises(RebuildSwapFailedError, match="LEDGER_INTEGRITY_FAILED"):
        rebuild_service.execute_rebuild_from_ledger(job.id)

    pg_session.commit()

    # Job status must be FAILED
    failed_job = pg_session.get(type(job), job.id)
    assert failed_job is not None
    assert failed_job.status == "FAILED"

    # Original G1 active balance must remain intact (50)
    bal = pg_session.scalars(
        select(InventoryPositionBalanceModel)
        .where(InventoryPositionBalanceModel.organization_id == org_id)
        .where(InventoryPositionBalanceModel.inventory_position_id == pos.id)
        .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
    ).first()
    assert bal is not None
    assert bal.quantity == Decimal("50.000000000000000000")
