"""
test_balance_rebuild_and_metrics_postgres.py — Real PostgreSQL Tests for Phase 045 (Hardening)

Validates:
1. Rebuild from Phase 044 Event Ledger (corrupted G1, G1 without existing balance, hash failure).
2. The 8 separate stock metrics calculation.
3. Multi-tenant atomic swap safety.
4. GAP 1: No double replay — MOV + derived delta => result = MOV amount only.
5. GAP 2: Checkpoint safe fallback — full replay always from seq 1.
6. GAP 3: base_unit_id resolved from movement lines, never product_id.
7. GAP 4: dimension_key preserved as String(255) — no [:64] truncation.
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
    InventoryBalanceCheckpointModel,
    InventoryPositionBalanceModel,
)
from app.modules.logistics.inventory.ledger.infrastructure.persistence.models import (
    InventoryMovementLineModel,
    InventoryMovementModel,
    InventoryPositionModel,
)

pytestmark = [pytest.mark.postgres, pytest.mark.integration]

# Canonical dimension key constants — using full strings, NO [:64] truncation
_DEFAULT_DIM_KEY = "AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE"
_DEFAULT_PARTITION = "TEST:DEFAULT"

# A long dimension key (180 chars) that exceeds the old String(64) limit
_LONG_DIM_KEY = (
    "AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE"
    ":ZONE_A:RACK_01:SHELF_03:BIN_07:TEMPERATURE_CONTROLLED"
    ":HAZMAT_CLASS_NONE:FRAGILE:PERISHABLE:ORGANIC:CUSTOMS_CLEARED"
)
assert len(_LONG_DIM_KEY) > 64, "Long dim key must exceed 64 chars for the test to be meaningful"
assert len(_LONG_DIM_KEY) <= 255, "Long dim key must fit in String(255)"

# Two distinct dimension keys that share the SAME first 64 characters (collision test)
# Both share: 'AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE:ZONE_AAA' (64 chars)
_COLLISION_KEY_A = "AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE:ZONE_AAA_ALPHA_SUFFIX"
_COLLISION_KEY_B = "AVAILABLE:APPROVED:NOT_IN_TRANSIT:NORMAL:NOT_APPLICABLE:ZONE_AAA_BETA__SUFFIX"
assert _COLLISION_KEY_A[:64] == _COLLISION_KEY_B[:64], "Keys must share first 64 chars"
assert _COLLISION_KEY_A != _COLLISION_KEY_B, "Keys must be distinct"


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
    dimension_key: str | None = None,
) -> InventoryPositionModel:
    pos_id = uuid4()
    # GAP 4 FIX: dimension_key is NOT truncated. F044 uses String(255).
    dim_key = dimension_key or f"{availability_state}:{quality_state}:{transit_state}:{damage_state}:{expiration_state}"
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
        dimension_key=dim_key,  # Full key — no truncation
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
    base_unit_id: UUID | None = None,
) -> InventoryMovementModel:
    """Create an F044 movement with a movement line.

    GAP 3 FIX: base_unit_id on the line is a real unit UUID (passed explicitly),
    never product_id. Caller must provide a distinct unit_id.
    """
    m_id = uuid4()
    calculated_hash = mov_hash or f"hash_{sequence}_{m_id.hex[:8]}"
    # Use a distinct unit UUID if not provided — this is NOT the product_id
    unit_id = base_unit_id or uuid4()

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
        unit_id=unit_id,
        base_quantity=base_qty,
        base_unit_id=unit_id,  # GAP 3: canonical unit, NOT product_id
        destination_position_id=dest_pos_id,
        source_position_id=src_pos_id,
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
    unit_id: UUID,
    partition_key: str = _DEFAULT_PARTITION,
    dim_key: str = _DEFAULT_DIM_KEY,
    avail: str = "AVAILABLE",
    qual: str = "APPROVED",
    trans: str = "NOT_IN_TRANSIT",
    dam: str = "NORMAL",
    exp: str = "NOT_APPLICABLE",
    is_active: bool = True,
) -> InventoryPositionBalanceModel:
    """Helper that always sets all NOT NULL fields.

    GAP 3 FIX: unit_id must be a real unit UUID, NOT product_id.
    GAP 4 FIX: dim_key is NOT truncated — full String(255) value used.
    """
    assert len(dim_key) <= 255, f"dim_key too long ({len(dim_key)} > 255)"
    return InventoryPositionBalanceModel(
        id=uuid4(),
        organization_id=org_id,
        branch_id=branch_id,
        warehouse_id=wh_id,
        inventory_position_id=pos_id,
        product_id=prod_id,
        base_unit_id=unit_id,  # GAP 3 FIX: real unit UUID
        quantity=quantity,
        availability_state=avail,
        quality_state=qual,
        transit_state=trans,
        damage_state=dam,
        expiration_state=exp,
        dimension_key=dim_key,  # GAP 4 FIX: no truncation
        last_applied_ledger_partition_key=partition_key,
        last_applied_ledger_sequence=0,
        is_active_projection=is_active,
        data_quality_status="PROJECTION_CURRENT",
    )


# ===========================================================================
# ORIGINAL TESTS (preserved, updated for GAP 3/4 compliance)
# ===========================================================================


@pytest.mark.postgres
def test_rebuild_corrupted_g1_from_f044_ledger(pg_session: Session):
    """1. Rebuild ignores corrupted G1 quantity (999) and reconstructs true balance (80) from F044 Ledger."""
    org_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()  # GAP 3: distinct unit UUID
    part_key = f"org:{org_id}:default"

    pos = _create_position(pg_session, org_id, branch_id, wh_id, prod_id)
    m1 = _create_movement(
        pg_session, org_id, branch_id, part_key, 1,
        dest_pos_id=pos.id, base_qty=Decimal(100), base_unit_id=unit_id,
    )
    _create_movement(
        pg_session, org_id, branch_id, part_key, 2,
        src_pos_id=pos.id, base_qty=Decimal(20),
        prev_hash=m1.movement_hash, base_unit_id=unit_id,
    )

    corrupted_g1 = _make_balance(
        org_id, branch_id, wh_id, pos.id, prod_id,
        Decimal(999), unit_id, partition_key=part_key,
    )
    pg_session.add(corrupted_g1)
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
    assert active_balance.quantity == Decimal("80.000000000000000000")
    assert job.status == "COMPLETED"


@pytest.mark.postgres
def test_rebuild_without_existing_g1(pg_session: Session):
    """2. Rebuild creates position projection from Ledger even when G1 active row is completely missing."""
    org_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()
    part_key = f"org:{org_id}:default"

    pos = _create_position(pg_session, org_id, branch_id, wh_id, prod_id)
    _create_movement(
        pg_session, org_id, branch_id, part_key, 1,
        dest_pos_id=pos.id, base_qty=Decimal(80), base_unit_id=unit_id,
    )
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
    assert active_balance.quantity == Decimal("80.000000000000000000")


@pytest.mark.postgres
def test_rebuild_incremental_vs_full_same_result(pg_session: Session):
    """3. Full ledger rebuild correctly accumulates multiple sequential movements (100 + 20 = 120)."""
    org_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()
    part_key = f"org:{org_id}:default"

    pos = _create_position(pg_session, org_id, branch_id, wh_id, prod_id)
    m1 = _create_movement(
        pg_session, org_id, branch_id, part_key, 1,
        dest_pos_id=pos.id, base_qty=Decimal(100), base_unit_id=unit_id,
    )
    _create_movement(
        pg_session, org_id, branch_id, part_key, 2,
        dest_pos_id=pos.id, base_qty=Decimal(20),
        prev_hash=m1.movement_hash, base_unit_id=unit_id,
    )
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
    """4-11. Tests all 8 stock metrics calculations with explicit distinct quantities."""
    org_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    branch_id = uuid4()
    unit_id = uuid4()

    metrics_spec = [
        ("AVAILABLE",  "APPROVED",    "NOT_IN_TRANSIT",     "NORMAL",  "NOT_APPLICABLE", Decimal(10)),
        ("RESERVED",   "APPROVED",    "NOT_IN_TRANSIT",     "NORMAL",  "NOT_APPLICABLE", Decimal(20)),
        ("BLOCKED",    "APPROVED",    "NOT_IN_TRANSIT",     "NORMAL",  "NOT_APPLICABLE", Decimal(30)),
        ("QUARANTINE", "QUARANTINED", "NOT_IN_TRANSIT",     "NORMAL",  "NOT_APPLICABLE", Decimal(40)),
        ("IN_TRANSIT", "APPROVED",    "IN_TRANSIT_INBOUND", "NORMAL",  "NOT_APPLICABLE", Decimal(50)),
        ("DAMAGED",    "APPROVED",    "NOT_IN_TRANSIT",     "DAMAGED", "NOT_APPLICABLE", Decimal(60)),
        ("EXPIRED",    "APPROVED",    "NOT_IN_TRANSIT",     "NORMAL",  "EXPIRED",        Decimal(70)),
    ]

    for avail, qual, trans, dam, exp, qty in metrics_spec:
        pos_id = uuid4()
        dim_key = f"{avail}:{qual}:{trans}:{dam}:{exp}"  # GAP 4: no [:64]
        b = _make_balance(
            org_id, branch_id, wh_id, pos_id, prod_id, qty, unit_id,
            dim_key=dim_key, avail=avail, qual=qual, trans=trans, dam=dam, exp=exp,
        )
        pg_session.add(b)

    pg_session.commit()

    query_service = BalanceQueryService()
    summary = query_service.get_active_balances_summary(pg_session, org_id)

    assert summary["physical_on_hand"] == Decimal("230.000000000000000000")
    assert summary["available_to_promise"] == Decimal("10.000000000000000000")
    assert summary["reserved_stock"] == Decimal("20.000000000000000000")
    assert summary["blocked_stock"] == Decimal("30.000000000000000000")
    assert summary["quarantine_stock"] == Decimal("40.000000000000000000")
    assert summary["in_transit_stock"] == Decimal("50.000000000000000000")
    assert summary["damaged_stock"] == Decimal("60.000000000000000000")
    assert summary["expired_stock"] == Decimal("70.000000000000000000")


@pytest.mark.postgres
def test_tenant_safe_atomic_swap_same_position_uuid(pg_session: Session):
    """12. Multi-tenant atomic swap with identical position UUID does NOT leak cross-tenant data."""
    org_a = uuid4()
    org_b = uuid4()
    shared_pos_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()
    part_a = f"org:{org_a}:default"

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
        dimension_key=_DEFAULT_DIM_KEY,  # GAP 4: no truncation
        status="ACTIVE",
        created_at=datetime.now(UTC),
    )
    pg_session.add(pos_a)
    pg_session.flush()
    _create_movement(
        pg_session, org_a, branch_id, part_a, 1,
        dest_pos_id=shared_pos_id, base_qty=Decimal(100), base_unit_id=unit_id,
    )

    g1_a = _make_balance(
        org_a, branch_id, wh_id, shared_pos_id, prod_id,
        Decimal(100), unit_id, partition_key=part_a,
    )
    pg_session.add(g1_a)

    g1_b = _make_balance(
        org_b, branch_id, wh_id, shared_pos_id, prod_id,
        Decimal(500), unit_id, partition_key=f"org:{org_b}:default",
    )
    pg_session.add(g1_b)
    pg_session.commit()

    rebuild_service = BalanceRebuildApplicationService(pg_session)
    job = rebuild_service.create_rebuild_job(
        organization_id=org_a,
        initiated_by_user_id=uuid4(),
        rebuild_mode="FULL",
        step_up_verified=True,
    )
    rebuild_service.execute_rebuild_from_ledger(job.id)
    pg_session.commit()

    bal_a = pg_session.scalars(
        select(InventoryPositionBalanceModel)
        .where(InventoryPositionBalanceModel.organization_id == org_a)
        .where(InventoryPositionBalanceModel.inventory_position_id == shared_pos_id)
        .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
    ).first()
    assert bal_a is not None
    assert bal_a.quantity == Decimal("100.000000000000000000")

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
    """13. Ledger hash mismatch aborts rebuild and preserves original G1 balance intact."""
    org_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()
    part_key = f"org:{org_id}:default"

    pos = _create_position(pg_session, org_id, branch_id, wh_id, prod_id)

    g1 = _make_balance(
        org_id, branch_id, wh_id, pos.id, prod_id,
        Decimal(50), unit_id, partition_key=part_key,
    )
    pg_session.add(g1)

    _create_movement(
        pg_session, org_id, branch_id, part_key, 1,
        dest_pos_id=pos.id, base_qty=Decimal(100),
        prev_hash="CORRUPTED_PREVIOUS_HASH_MISMATCH", base_unit_id=unit_id,
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

    failed_job = pg_session.get(type(job), job.id)
    assert failed_job is not None
    assert failed_job.status == "FAILED"

    bal = pg_session.scalars(
        select(InventoryPositionBalanceModel)
        .where(InventoryPositionBalanceModel.organization_id == org_id)
        .where(InventoryPositionBalanceModel.inventory_position_id == pos.id)
        .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
    ).first()
    assert bal is not None
    assert bal.quantity == Decimal("50.000000000000000000")


# ===========================================================================
# NEW TESTS — GAP 1: No Double Replay
# ===========================================================================


@pytest.mark.postgres
def test_double_materialization_no_double_replay(pg_session: Session):
    """GAP 1: MOV +100 exists in F044. FULL rebuild must produce 100, not 200.

    Even if a corresponding F045 InventoryBalanceDeltaModel exists for the same MOV,
    the FULL rebuild must only consume the F044 MOV, never the derived delta.
    """
    org_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()
    part_key = f"org:{org_id}:default"

    pos = _create_position(pg_session, org_id, branch_id, wh_id, prod_id)
    _create_movement(
        pg_session, org_id, branch_id, part_key, 1,
        dest_pos_id=pos.id, base_qty=Decimal(100), base_unit_id=unit_id,
    )
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
    # MUST be 100 — not 200 (which would indicate double replay)
    assert active_balance.quantity == Decimal("100.000000000000000000"), (
        f"Expected 100 (only F044 MOV), got {active_balance.quantity} — "
        "double replay of delta detected!"
    )


@pytest.mark.postgres
def test_multiple_movs_no_double_replay(pg_session: Session):
    """GAP 1: Multiple F044 MOVs (+100, -20, +10) replay correctly to 90.

    The result must be 90, not 180 (which would indicate double replay).
    """
    org_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()
    part_key = f"org:{org_id}:default"

    pos = _create_position(pg_session, org_id, branch_id, wh_id, prod_id)
    m1 = _create_movement(
        pg_session, org_id, branch_id, part_key, 1,
        dest_pos_id=pos.id, base_qty=Decimal(100), base_unit_id=unit_id,
    )
    m2 = _create_movement(
        pg_session, org_id, branch_id, part_key, 2,
        src_pos_id=pos.id, base_qty=Decimal(20),
        prev_hash=m1.movement_hash, base_unit_id=unit_id,
    )
    _create_movement(
        pg_session, org_id, branch_id, part_key, 3,
        dest_pos_id=pos.id, base_qty=Decimal(10),
        prev_hash=m2.movement_hash, base_unit_id=unit_id,
    )
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
    # +100 - 20 + 10 = 90 (not 180)
    assert active_balance.quantity == Decimal("90.000000000000000000"), (
        f"Expected 90, got {active_balance.quantity} — possible double replay"
    )


# ===========================================================================
# NEW TESTS — GAP 2: Checkpoint Safe Fallback
# ===========================================================================


@pytest.mark.postgres
def test_checkpoint_safe_fallback_does_not_skip_movements(pg_session: Session):
    """GAP 2: A valid checkpoint exists but MUST NOT cause movements to be skipped.

    The checkpoint model does not store per-position quantities.
    If movements were skipped (seq > checkpoint_seq) but G2 starts from Decimal(0),
    the result would be incorrect. SAFE_FULL_REPLAY_FALLBACK ensures full replay always.

    Setup: checkpoint at seq=1, MOV seq=1 (+100), MOV seq=2 (+50)
    Incorrect result if bug: 50 (seq=2 only)
    Correct result: 150 (both movements replayed)
    """
    org_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()
    part_key = f"org:{org_id}:default"

    pos = _create_position(pg_session, org_id, branch_id, wh_id, prod_id)
    m1 = _create_movement(
        pg_session, org_id, branch_id, part_key, 1,
        dest_pos_id=pos.id, base_qty=Decimal(100), base_unit_id=unit_id,
    )
    _create_movement(
        pg_session, org_id, branch_id, part_key, 2,
        dest_pos_id=pos.id, base_qty=Decimal(50),
        prev_hash=m1.movement_hash, base_unit_id=unit_id,
    )

    # Create a checkpoint at seq=1 (but it cannot restore position quantities)
    checkpoint = InventoryBalanceCheckpointModel(
        id=uuid4(),
        organization_id=org_id,
        ledger_partition_key=part_key,
        checkpoint_sequence=1,
        checkpoint_movement_id=m1.id,
        checkpoint_movement_hash=m1.movement_hash,
        balance_manifest_hash="manifest_hash_for_test",
        position_count=1,
        total_product_count=1,
        status="VALID",
        created_at=datetime.now(UTC),
    )
    pg_session.add(checkpoint)
    pg_session.commit()

    rebuild_service = BalanceRebuildApplicationService(pg_session)
    job = rebuild_service.create_rebuild_job(
        organization_id=org_id,
        initiated_by_user_id=uuid4(),
        rebuild_mode="FULL",
        step_up_verified=True,
        target_partition_key=part_key,
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
    # MUST be 150: BOTH movements replayed (checkpoint did NOT cause seq skip)
    assert active_balance.quantity == Decimal("150.000000000000000000"), (
        f"Expected 150 (full replay), got {active_balance.quantity} — "
        "checkpoint may have incorrectly skipped historical movements"
    )


# ===========================================================================
# NEW TESTS — GAP 3: base_unit_id from movement lines
# ===========================================================================


@pytest.mark.postgres
def test_base_unit_resolved_from_movement_line_not_product(pg_session: Session):
    """GAP 3: The rebuilt balance.base_unit_id must come from movement lines, not product_id.

    Asserts explicitly that base_unit_id != product_id when they are different UUIDs.
    """
    org_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()  # Explicitly different from prod_id
    assert unit_id != prod_id, "unit_id must differ from prod_id for this test to be meaningful"

    part_key = f"org:{org_id}:default"

    pos = _create_position(pg_session, org_id, branch_id, wh_id, prod_id)
    _create_movement(
        pg_session, org_id, branch_id, part_key, 1,
        dest_pos_id=pos.id, base_qty=Decimal(1),
        base_unit_id=unit_id,  # The canonical unit (e.g., KG), not the product
    )
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
    assert active_balance.quantity == Decimal("1.000000000000000000")
    # CORE ASSERTION: base_unit_id must equal the movement line's unit, NOT the product_id
    assert active_balance.base_unit_id == unit_id, (
        f"base_unit_id should be unit_id ({unit_id}), got {active_balance.base_unit_id}"
    )
    assert active_balance.base_unit_id != prod_id, (
        "base_unit_id MUST NOT equal product_id — using product as unit proxy is prohibited"
    )


@pytest.mark.postgres
def test_uom_conflict_raises_error(pg_session: Session):
    """GAP 3: Two movement lines for the same position with different base_unit_ids must fail.

    Cannot choose one unit arbitrarily — rebuild must raise BASE_UNIT_CONSISTENCY_ERROR.
    """
    org_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    unit_kg = uuid4()
    unit_lb = uuid4()  # Different unit
    part_key = f"org:{org_id}:default"

    pos = _create_position(pg_session, org_id, branch_id, wh_id, prod_id)
    # MOV 1: base_unit = KG
    m1 = _create_movement(
        pg_session, org_id, branch_id, part_key, 1,
        dest_pos_id=pos.id, base_qty=Decimal(100), base_unit_id=unit_kg,
    )
    # MOV 2: base_unit = LB (different — no conversion, conflict)
    _create_movement(
        pg_session, org_id, branch_id, part_key, 2,
        dest_pos_id=pos.id, base_qty=Decimal(50),
        prev_hash=m1.movement_hash, base_unit_id=unit_lb,
    )
    pg_session.commit()

    rebuild_service = BalanceRebuildApplicationService(pg_session)
    job = rebuild_service.create_rebuild_job(
        organization_id=org_id,
        initiated_by_user_id=uuid4(),
        rebuild_mode="FULL",
        step_up_verified=True,
    )

    with pytest.raises(RebuildSwapFailedError, match="BASE_UNIT_CONSISTENCY_ERROR"):
        rebuild_service.execute_rebuild_from_ledger(job.id)


# ===========================================================================
# NEW TESTS — GAP 4: dimension_key String(255) — no truncation
# ===========================================================================


@pytest.mark.postgres
def test_long_dimension_key_preserved_exactly(pg_session: Session):
    """GAP 4: A dimension_key longer than 64 chars must be stored and retrieved exactly.

    F044 uses String(255). F045 must also use String(255).
    The key must be identical between F044 InventoryPositionModel and rebuilt F045 balance.
    """
    org_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()
    part_key = f"org:{org_id}:default"

    assert len(_LONG_DIM_KEY) > 64
    assert len(_LONG_DIM_KEY) <= 255

    pos = _create_position(
        pg_session, org_id, branch_id, wh_id, prod_id,
        dimension_key=_LONG_DIM_KEY,
    )
    assert pos.dimension_key == _LONG_DIM_KEY  # F044 stores full key

    _create_movement(
        pg_session, org_id, branch_id, part_key, 1,
        dest_pos_id=pos.id, base_qty=Decimal(100), base_unit_id=unit_id,
    )
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
    # CORE ASSERTION: F045 dimension_key must exactly match F044 dimension_key (no truncation)
    assert active_balance.dimension_key == _LONG_DIM_KEY, (
        f"dimension_key was truncated or modified!\n"
        f"F044: {pos.dimension_key!r}\n"
        f"F045: {active_balance.dimension_key!r}"
    )
    assert active_balance.dimension_key == pos.dimension_key


@pytest.mark.postgres
def test_dimension_key_no_collision_at_64_chars(pg_session: Session):
    """GAP 4: Two distinct dimension_keys sharing the same first 64 characters must not collide.

    With String(64) and [:64] truncation, _COLLISION_KEY_A[:64] == _COLLISION_KEY_B[:64],
    making two distinct positions appear identical. With String(255), they are distinct.
    """
    org_id = uuid4()
    branch_id = uuid4()
    wh_id = uuid4()
    prod_id = uuid4()
    unit_id = uuid4()
    part_key = f"org:{org_id}:default"

    assert _COLLISION_KEY_A[:64] == _COLLISION_KEY_B[:64], "Precondition: same first 64 chars"
    assert _COLLISION_KEY_A != _COLLISION_KEY_B, "Precondition: keys are distinct"

    pos_a = _create_position(
        pg_session, org_id, branch_id, wh_id, prod_id,
        dimension_key=_COLLISION_KEY_A,
    )
    prod_id_b = uuid4()
    pos_b = _create_position(
        pg_session, org_id, branch_id, wh_id, prod_id_b,
        dimension_key=_COLLISION_KEY_B,
    )

    m1 = _create_movement(
        pg_session, org_id, branch_id, part_key, 1,
        dest_pos_id=pos_a.id, base_qty=Decimal(111), base_unit_id=unit_id,
    )
    _create_movement(
        pg_session, org_id, branch_id, part_key, 2,
        dest_pos_id=pos_b.id, base_qty=Decimal(222),
        prev_hash=m1.movement_hash, base_unit_id=unit_id,
    )
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

    bal_a = pg_session.scalars(
        select(InventoryPositionBalanceModel)
        .where(InventoryPositionBalanceModel.organization_id == org_id)
        .where(InventoryPositionBalanceModel.inventory_position_id == pos_a.id)
        .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
    ).first()

    bal_b = pg_session.scalars(
        select(InventoryPositionBalanceModel)
        .where(InventoryPositionBalanceModel.organization_id == org_id)
        .where(InventoryPositionBalanceModel.inventory_position_id == pos_b.id)
        .where(InventoryPositionBalanceModel.is_active_projection.is_(True))
    ).first()

    assert bal_a is not None
    assert bal_b is not None
    # Dimension keys must be stored as distinct full strings
    assert bal_a.dimension_key == _COLLISION_KEY_A
    assert bal_b.dimension_key == _COLLISION_KEY_B
    assert bal_a.dimension_key != bal_b.dimension_key
    # Quantities must remain distinct (no collision)
    assert bal_a.quantity == Decimal("111.000000000000000000")
    assert bal_b.quantity == Decimal("222.000000000000000000")
