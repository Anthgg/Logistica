"""Phase 037 tests for gate control core domain models, enums, registry, and repositories."""

from datetime import date, datetime, timezone
from typing import Generator
from unittest.mock import MagicMock, patch
from uuid import uuid4
import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, inspect
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.models.organization import Organization
from app.models.registry import (
    WarehouseGateModel,
    GateControlRecordModel,
    GateControlHistoryModel,
)
from app.models.user import User
from app.models.warehouse import Warehouse
from app.modules.logistics.drivers.infrastructure.persistence.models import DriverLicenseModel
from app.modules.logistics.documents.rendering.inbound_schemas import mask_sensitive_id
from app.modules.logistics.gate_control.application.schemas import (
    WarehouseGateCreate,
    WarehouseGateResponse,
    GateCheckInRequest,
    GateDecisionRequest,
    GateCheckOutRequest,
    GatePreparationResponse,
    GateControlRecordResponse,
)
from app.modules.logistics.gate_control.application.services import (
    GateControlService,
    GatePreparationService,
    generate_gate_record_code,
)
from app.modules.logistics.gate_control.domain.enums import (
    AccessDecision,
    GateEventType,
    GateRecordStatus,
    GateStatus,
    GateType,
    SealStatus,
)
from app.modules.logistics.gate_control.domain.exceptions import (
    DriverLicenseExpiredError,
    GateNotFoundError,
    GateRecordNotFoundError,
    InvalidGateStateError,
    PlateMismatchWarning,
    SealStatusInvalidError,
)
from app.modules.logistics.gate_control.domain.models import (
    compute_gate_content_hash,
)
from app.modules.logistics.gate_control.infrastructure.adapters import (
    GateControlDocumentAdapter,
)
from app.modules.logistics.gate_control.infrastructure.repositories import (
    GateControlConcurrencyError,
    GateControlRecordRepository,
    WarehouseGateRepository,
)


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """In-memory SQLite database session for Phase 037 testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    target_tables = [
        t for name, t in Base.metadata.tables.items()
        if name in (
            "warehouse_gates",
            "gate_control_records",
            "gate_control_history",
            "logistics_organizations",
            "warehouses",
            "users",
            "drivers",
            "driver_licenses",
        )
    ]
    Base.metadata.create_all(bind=engine, tables=target_tables)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()



def test_gate_control_enums():
    """Verify Phase 037 StrEnum values match specification."""
    assert GateType.MAIN_ENTRY == "MAIN_ENTRY"
    assert GateType.MAIN_EXIT == "MAIN_EXIT"
    assert GateType.BI_DIRECTIONAL == "BI_DIRECTIONAL"
    assert GateType.PEDESTRIAN == "PEDESTRIAN"
    assert GateType.EMERGENCY == "EMERGENCY"
    assert GateType.SERVICE == "SERVICE"

    assert GateStatus.ACTIVE == "ACTIVE"
    assert GateStatus.INACTIVE == "INACTIVE"
    assert GateStatus.MAINTENANCE == "MAINTENANCE"
    assert GateStatus.BLOCKED == "BLOCKED"

    assert GateEventType.CHECK_IN == "CHECK_IN"
    assert GateEventType.CHECK_OUT == "CHECK_OUT"
    assert GateEventType.INSPECTION == "INSPECTION"
    assert GateEventType.DENIED_ENTRY == "DENIED_ENTRY"
    assert GateEventType.EMERGENCY_EXIT == "EMERGENCY_EXIT"

    assert AccessDecision.PENDING == "PENDING"
    assert AccessDecision.APPROVED == "APPROVED"
    assert AccessDecision.DENIED == "DENIED"
    assert AccessDecision.CONDITIONAL_APPROVED == "CONDITIONAL_APPROVED"

    assert SealStatus.INTACT == "INTACT"
    assert SealStatus.BROKEN == "BROKEN"
    assert SealStatus.TAMPERED == "TAMPERED"
    assert SealStatus.NOT_APPLICABLE == "NOT_APPLICABLE"
    assert SealStatus.MISMATCH == "MISMATCH"

    assert GateRecordStatus.DRAFT == "DRAFT"
    assert GateRecordStatus.CHECKED_IN == "CHECKED_IN"
    assert GateRecordStatus.CHECKED_OUT == "CHECKED_OUT"
    assert GateRecordStatus.REJECTED == "REJECTED"
    assert GateRecordStatus.CANCELLED == "CANCELLED"
    assert GateRecordStatus.EXPIRED == "EXPIRED"


def test_gate_control_models_schema_inspection():
    """Verify ORM model table names, columns, constraints, and mapper configuration."""
    assert WarehouseGateModel.__tablename__ == "warehouse_gates"
    assert GateControlRecordModel.__tablename__ == "gate_control_records"
    assert GateControlHistoryModel.__tablename__ == "gate_control_history"

    wg_mapper = inspect(WarehouseGateModel)
    assert "organization_id" in wg_mapper.columns
    assert "warehouse_id" in wg_mapper.columns
    assert "gate_type" in wg_mapper.columns
    assert "status" in wg_mapper.columns
    assert "row_version" in wg_mapper.columns
    assert "content_hash" in wg_mapper.columns

    gcr_mapper = inspect(GateControlRecordModel)
    assert "organization_id" in gcr_mapper.columns
    assert "record_code" in gcr_mapper.columns
    assert "gate_id" in gcr_mapper.columns
    assert "guard_user_id" in gcr_mapper.columns
    assert "arrival_at" in gcr_mapper.columns
    assert "plate_observed" in gcr_mapper.columns
    assert "status" in gcr_mapper.columns

    gch_mapper = inspect(GateControlHistoryModel)
    assert "record_id" in gch_mapper.columns
    assert "previous_status" in gch_mapper.columns
    assert "new_status" in gch_mapper.columns
    assert "changed_by_user_id" in gch_mapper.columns
    assert "change_reason" in gch_mapper.columns


def test_content_hash_computation():
    """Verify content hash function is deterministic."""
    payload = {"organization_id": "org1", "code": "GATE-01", "status": "ACTIVE"}
    hash1 = compute_gate_content_hash(payload)
    hash2 = compute_gate_content_hash(payload)
    assert hash1 == hash2
    assert len(hash1) == 64


def test_warehouse_gate_repository_unit(db_session: Session):
    """Test WarehouseGateRepository methods using db_session."""
    # Seed required parent entities
    org = Organization(
        code=f"ORG-{uuid4().hex[:8]}",
        name="Logistics Org Test",
        country_code="PE",
    )
    db_session.add(org)
    db_session.flush()

    wh = Warehouse(
        organization_id=org.id,
        code=f"WH-{uuid4().hex[:6]}",
        name="Main Distribution Warehouse",
    )
    db_session.add(wh)
    db_session.flush()

    repo = WarehouseGateRepository(db_session)

    gate = WarehouseGateModel(
        organization_id=org.id,
        code="GATE-NORTH-01",
        name="North Entry Gate",
        warehouse_id=wh.id,
        gate_type=GateType.MAIN_ENTRY,
        status=GateStatus.ACTIVE,
    )
    repo.create(gate)

    fetched = repo.get_by_id(gate.id, organization_id=org.id)
    assert fetched is not None
    assert fetched.code == "GATE-NORTH-01"
    assert fetched.content_hash is not None

    fetched_code = repo.get_by_code(org.id, "gate-north-01")
    assert fetched_code is not None
    assert fetched_code.id == gate.id

    by_wh = repo.list_by_warehouse(wh.id, organization_id=org.id)
    assert len(by_wh) == 1

    by_org = repo.list_by_organization(org.id)
    assert len(by_org) == 1

    # Optimistic locking update
    fetched.name = "North Main Gate Updated"
    repo.update(fetched, expected_version=1)
    assert fetched.row_version == 2

    with pytest.raises(GateControlConcurrencyError):
        repo.update(fetched, expected_version=1)


def test_gate_control_record_repository_unit(db_session: Session):
    """Test GateControlRecordRepository methods using db_session."""
    # Seed parent entities
    org = Organization(
        code=f"ORG-{uuid4().hex[:8]}",
        name="Logistics Org Test 2",
        country_code="PE",
    )
    db_session.add(org)
    db_session.flush()

    wh = Warehouse(
        organization_id=org.id,
        code=f"WH-{uuid4().hex[:6]}",
        name="South Distribution Warehouse",
    )
    db_session.add(wh)
    db_session.flush()

    guard = User(
        email=f"guard-{uuid4().hex[:8]}@example.com",
        password_hash="hashed_pw",
        full_name="Security Guard User",
        role="guard",
    )
    db_session.add(guard)
    db_session.flush()

    gate_repo = WarehouseGateRepository(db_session)
    record_repo = GateControlRecordRepository(db_session)

    gate = WarehouseGateModel(
        organization_id=org.id,
        code="GATE-SOUTH-01",
        name="South Exit Gate",
        warehouse_id=wh.id,
        gate_type=GateType.MAIN_EXIT,
        status=GateStatus.ACTIVE,
    )
    gate_repo.create(gate)

    now = datetime.now(timezone.utc)
    record = GateControlRecordModel(
        organization_id=org.id,
        record_code="GCR-2026-0001",
        gate_id=gate.id,
        guard_user_id=guard.id,
        event_type=GateEventType.CHECK_IN,
        arrival_at=now,
        access_decision=AccessDecision.PENDING,
        plate_observed="ABC-1234",
        seal_status=SealStatus.INTACT,
        status=GateRecordStatus.DRAFT,
    )
    record_repo.create(record)

    fetched = record_repo.get_by_id(record.id, organization_id=org.id)
    assert fetched is not None
    assert fetched.record_code == "GCR-2026-0001"
    assert fetched.content_hash is not None

    fetched_code = record_repo.get_by_code(org.id, "gcr-2026-0001")
    assert fetched_code is not None
    assert fetched_code.id == record.id

    by_gate = record_repo.list_by_gate(gate.id)
    assert len(by_gate) == 1

    by_plate = record_repo.list_by_plate(org.id, "ABC-1234")
    assert len(by_plate) == 1

    # History entry
    history = GateControlHistoryModel(
        record_id=record.id,
        previous_status=GateRecordStatus.DRAFT,
        new_status=GateRecordStatus.CHECKED_IN,
        changed_by_user_id=guard.id,
        change_reason="Driver passed physical inspection and security verification.",
    )
    record_repo.add_history(history)

    history_list = record_repo.get_history_by_record(record.id)
    assert len(history_list) == 1
    assert history_list[0].new_status == GateRecordStatus.CHECKED_IN

    # Update record
    record.status = GateRecordStatus.CHECKED_IN
    record.check_in_at = now
    record_repo.update(record, expected_version=1)
    assert record.row_version == 2

    with pytest.raises(GateControlConcurrencyError):
        record_repo.update(record, expected_version=1)


def test_warehouse_gate_concurrency_simultaneous_updates(db_session: Session):
    """Simulate simultaneous updates on WarehouseGateRepository to test optimistic locking."""
    org = Organization(code=f"ORG-CONC-{uuid4().hex[:6]}", name="Org Conc", country_code="PE")
    db_session.add(org)
    db_session.flush()

    wh = Warehouse(organization_id=org.id, code=f"WH-C-{uuid4().hex[:6]}", name="Warehouse Conc")
    db_session.add(wh)
    db_session.flush()

    repo = WarehouseGateRepository(db_session)
    gate = WarehouseGateModel(
        organization_id=org.id,
        code="GATE-CONC-01",
        name="Concurrent Gate",
        warehouse_id=wh.id,
        gate_type=GateType.MAIN_ENTRY,
        status=GateStatus.ACTIVE,
    )
    repo.create(gate)
    db_session.commit()

    # Simulate two callers holding references to gate at row_version 1
    gate_caller1 = repo.get_by_id(gate.id)
    assert gate_caller1.row_version == 1

    # Caller 1 succeeds in updating gate from version 1 -> 2
    gate_caller1.name = "Updated by Caller 1"
    repo.update(gate_caller1, expected_version=1)
    assert gate_caller1.row_version == 2
    db_session.commit()

    # Caller 2 attempts to update using stale version 1
    gate_stale = repo.get_by_id(gate.id)  # Current row_version in DB is 2
    gate_stale.name = "Updated by Caller 2 (Stale)"
    with pytest.raises(GateControlConcurrencyError) as exc_info:
        repo.update(gate_stale, expected_version=1)
    assert "Concurrency mismatch for gate" in str(exc_info.value)


def test_gate_control_record_concurrency_simultaneous_updates(db_session: Session):
    """Simulate simultaneous updates on GateControlRecordRepository to test optimistic locking."""
    org = Organization(code=f"ORG-RCONC-{uuid4().hex[:6]}", name="Org Rec Conc", country_code="PE")
    db_session.add(org)
    db_session.flush()

    wh = Warehouse(organization_id=org.id, code=f"WH-RC-{uuid4().hex[:6]}", name="Warehouse Rec Conc")
    db_session.add(wh)
    db_session.flush()

    guard = User(email=f"guard-conc-{uuid4().hex[:6]}@example.com", password_hash="hash", full_name="Guard Conc", role="guard")
    db_session.add(guard)
    db_session.flush()

    gate_repo = WarehouseGateRepository(db_session)
    gate = WarehouseGateModel(
        organization_id=org.id,
        code="GATE-CONC-02",
        name="Gate Rec Conc",
        warehouse_id=wh.id,
        gate_type=GateType.MAIN_ENTRY,
        status=GateStatus.ACTIVE,
    )
    gate_repo.create(gate)
    db_session.flush()

    record_repo = GateControlRecordRepository(db_session)
    record = GateControlRecordModel(
        organization_id=org.id,
        record_code="GCR-CONC-001",
        gate_id=gate.id,
        guard_user_id=guard.id,
        event_type=GateEventType.CHECK_IN,
        arrival_at=datetime.now(timezone.utc),
        access_decision=AccessDecision.PENDING,
        plate_observed="CONC-999",
        seal_status=SealStatus.INTACT,
        status=GateRecordStatus.DRAFT,
    )
    record_repo.create(record)
    db_session.commit()

    rec_v1 = record_repo.get_by_id(record.id)
    assert rec_v1.row_version == 1

    # Caller 1 succeeds in updating record from version 1 -> 2
    rec_v1.status = GateRecordStatus.CHECKED_IN
    record_repo.update(rec_v1, expected_version=1)
    assert rec_v1.row_version == 2
    db_session.commit()

    # Caller 2 attempts to update using stale version 1
    rec_stale = record_repo.get_by_id(record.id)  # Current row_version in DB is 2
    rec_stale.rejection_reason = "Stale attempt"
    with pytest.raises(GateControlConcurrencyError) as exc_info:
        record_repo.update(rec_stale, expected_version=1)
    assert "Concurrency mismatch for record" in str(exc_info.value)


def test_invalid_enum_values_and_handling():
    """Test validation and invalid values for Phase 037 enums."""
    with pytest.raises(ValueError):
        GateType("INVALID_GATE_TYPE")

    with pytest.raises(ValueError):
        GateStatus("INVALID_GATE_STATUS")

    with pytest.raises(ValueError):
        GateEventType("INVALID_EVENT_TYPE")

    with pytest.raises(ValueError):
        AccessDecision("INVALID_ACCESS_DECISION")

    with pytest.raises(ValueError):
        SealStatus("INVALID_SEAL_STATUS")

    with pytest.raises(ValueError):
        GateRecordStatus("INVALID_RECORD_STATUS")


def test_missing_mandatory_fields_schema_enforcement(db_session: Session):
    """Verify missing mandatory fields trigger integrity errors upon flush."""
    # Missing organization_id on WarehouseGateModel
    gate_invalid = WarehouseGateModel(
        organization_id=None,  # NOT NULL constraint
        code="GATE-FAIL-01",
        name="Invalid Gate",
        warehouse_id=uuid4(),
        gate_type=GateType.MAIN_ENTRY,
        status=GateStatus.ACTIVE,
    )
    db_session.add(gate_invalid)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

    # Missing guard_user_id on GateControlRecordModel
    record_invalid = GateControlRecordModel(
        organization_id=uuid4(),
        record_code="GCR-FAIL-01",
        gate_id=uuid4(),
        guard_user_id=None,  # NOT NULL constraint
        event_type=GateEventType.CHECK_IN,
        arrival_at=datetime.now(timezone.utc),
        access_decision=AccessDecision.PENDING,
        plate_observed="FAIL-123",
        seal_status=SealStatus.INTACT,
        status=GateRecordStatus.DRAFT,
    )
    db_session.add(record_invalid)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_content_hash_mutation_and_tampering():
    """Verify content hash mutation detection and tampering protection."""
    base_payload = {
        "organization_id": "00000000-0000-0000-0000-000000000001",
        "record_code": "GCR-TAMPER-001",
        "gate_id": "00000000-0000-0000-0000-000000000002",
        "event_type": "CHECK_IN",
        "arrival_at": "2026-07-31T12:00:00+00:00",
        "access_decision": "PENDING",
        "plate_observed": "ABC1234",
        "status": "DRAFT",
    }
    original_hash = compute_gate_content_hash(base_payload)

    # Mutate access decision (tampering)
    tampered_payload = dict(base_payload)
    tampered_payload["access_decision"] = "APPROVED"
    tampered_hash = compute_gate_content_hash(tampered_payload)

    assert original_hash != tampered_hash, "Mutated payload must yield a different content hash"

    # Mutate plate observed
    tampered_plate_payload = dict(base_payload)
    tampered_plate_payload["plate_observed"] = "XYZ9999"
    tampered_plate_hash = compute_gate_content_hash(tampered_plate_payload)

    assert original_hash != tampered_plate_hash


def test_schema_check_and_unique_constraints(db_session: Session):
    """Test row_version >= 1, check_out_at >= check_in_at, and unique organization_id+code constraints."""
    org = Organization(code=f"ORG-SCH-{uuid4().hex[:6]}", name="Org Schema", country_code="PE")
    db_session.add(org)
    db_session.flush()

    wh = Warehouse(organization_id=org.id, code=f"WH-SCH-{uuid4().hex[:6]}", name="Warehouse Schema")
    db_session.add(wh)
    db_session.flush()

    repo = WarehouseGateRepository(db_session)
    gate1 = WarehouseGateModel(
        organization_id=org.id,
        code="GATE-UNIQ-01",
        name="Gate Uniq 1",
        warehouse_id=wh.id,
        gate_type=GateType.MAIN_ENTRY,
        status=GateStatus.ACTIVE,
    )
    repo.create(gate1)
    db_session.commit()

    # Unique constraint test: duplicate organization_id + code
    gate_duplicate = WarehouseGateModel(
        organization_id=org.id,
        code="GATE-UNIQ-01",
        name="Gate Uniq 2 Duplicate",
        warehouse_id=wh.id,
        gate_type=GateType.MAIN_ENTRY,
        status=GateStatus.ACTIVE,
    )
    db_session.add(gate_duplicate)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

    # Check constraint test: row_version < 1
    gate_bad_version = WarehouseGateModel(
        organization_id=org.id,
        code="GATE-BAD-VER",
        name="Gate Bad Version",
        warehouse_id=wh.id,
        gate_type=GateType.MAIN_ENTRY,
        status=GateStatus.ACTIVE,
        row_version=0,  # Invalid: ck_warehouse_gates_row_version_positive
    )
    db_session.add(gate_bad_version)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

    # Check constraint test: checkout before checkin
    guard = User(email=f"guard-sch-{uuid4().hex[:6]}@example.com", password_hash="hash", full_name="Guard Schema", role="guard")
    db_session.add(guard)
    db_session.flush()

    t_checkin = datetime(2026, 7, 31, 14, 0, 0, tzinfo=timezone.utc)
    t_checkout_earlier = datetime(2026, 7, 31, 13, 0, 0, tzinfo=timezone.utc)

    rec_invalid_dates = GateControlRecordModel(
        organization_id=org.id,
        record_code="GCR-BAD-DATES",
        gate_id=gate1.id,
        guard_user_id=guard.id,
        event_type=GateEventType.CHECK_IN,
        arrival_at=t_checkin,
        check_in_at=t_checkin,
        check_out_at=t_checkout_earlier,  # Invalid: checkout < checkin
        access_decision=AccessDecision.APPROVED,
        plate_observed="BAD-DATE",
        seal_status=SealStatus.INTACT,
        status=GateRecordStatus.CHECKED_OUT,
    )
    db_session.add(rec_invalid_dates)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_dto_validation_and_privacy_masking():
    """Verify DTO validation, extra field rejection, and sensitive ID masking."""
    # Test mask_sensitive_id utility
    assert mask_sensitive_id("12345678", visible_end=2) == "******78"
    assert mask_sensitive_id("Q49876521", visible_end=2) == "*******21"
    assert mask_sensitive_id("12", visible_end=2) == "**"
    assert mask_sensitive_id(None) == "******"

    # Test WarehouseGateCreate extra field rejection
    with pytest.raises(ValidationError):
        WarehouseGateCreate(
            code="GATE-01",
            name="Main Gate",
            warehouse_id=uuid4(),
            extra_field="invalid",
        )

    # Test GateCheckInRequest validation
    request = GateCheckInRequest(
        gate_id=uuid4(),
        plate_observed="ABC-123",
        seal_status=SealStatus.INTACT,
        driver_dni_raw="12345678",
        driver_license_raw="Q12345678",
    )
    assert request.plate_observed == "ABC-123"
    assert request.seal_status == SealStatus.INTACT


def test_gate_preparation_service_unit():
    """Test GatePreparationService mapping from Phase 036 response dict."""
    db_mock = MagicMock()
    service = GatePreparationService(db_mock)
    service.appointment_service = MagicMock()

    apt_id = uuid4()
    an_id = uuid4()
    wh_id = uuid4()
    c_id = uuid4()

    service.appointment_service.gate_preparation.return_value = {
        "appointment_id": apt_id,
        "appointment_code": "CIT-2026-0001",
        "arrival_notice_id": an_id,
        "warehouse_id": wh_id,
        "expected_plate": "ABC-123",
        "expected_seal_reference": "SEAL-001",
        "expected_driver_dni": "87654321",
        "expected_vehicle_id": None,
        "supplier": {"name": "Test Supplier"},
        "carrier": {"carrier_id": c_id, "name": "Test Carrier"},
        "appointment_status": "CONFIRMED",
        "guide_references": ["GR-001"],
        "verification_warnings": [],
    }

    org_id = uuid4()
    res = service.get_gate_preparation(apt_id, org_id)

    assert isinstance(res, GatePreparationResponse)
    assert res.appointment_id == apt_id
    assert res.appointment_code == "CIT-2026-0001"
    assert res.expected_plate == "ABC-123"
    assert res.carrier_name == "Test Carrier"
    assert res.guide_references == ["GR-001"]


def test_gate_control_service_create_and_get_gate(db_session: Session):
    """Test creating and retrieving warehouse gates via GateControlService."""
    org = Organization(code=f"ORG-SVC-{uuid4().hex[:6]}", name="Org Service", country_code="PE")
    db_session.add(org)
    db_session.flush()

    wh = Warehouse(organization_id=org.id, code=f"WH-SVC-{uuid4().hex[:6]}", name="WH Service")
    db_session.add(wh)
    db_session.flush()

    service = GateControlService(db_session)

    payload = WarehouseGateCreate(
        code="GATE-SVC-01",
        name="Service Main Gate",
        warehouse_id=wh.id,
        gate_type=GateType.MAIN_ENTRY,
        status=GateStatus.ACTIVE,
    )
    created = service.create_gate(org.id, payload)
    assert isinstance(created, WarehouseGateResponse)
    assert created.code == "GATE-SVC-01"
    assert created.status == "ACTIVE"

    # Duplicate code error
    with pytest.raises(InvalidGateStateError):
        service.create_gate(org.id, payload)

    # Get gate
    fetched = service.get_gate(created.id, org.id)
    assert fetched.id == created.id
    assert fetched.name == "Service Main Gate"

    # Non-existent gate
    with pytest.raises(GateNotFoundError):
        service.get_gate(uuid4(), org.id)

    # List gates
    all_gates = service.list_gates(org.id)
    assert len(all_gates) == 1


def test_gate_checkin_success(db_session: Session):
    """Test processing vehicle arrival and check-in at an active gate."""
    org = Organization(code=f"ORG-CHK-{uuid4().hex[:6]}", name="Org Checkin", country_code="PE")
    db_session.add(org)
    db_session.flush()

    wh = Warehouse(organization_id=org.id, code=f"WH-CHK-{uuid4().hex[:6]}", name="WH Checkin")
    db_session.add(wh)
    db_session.flush()

    guard = User(email=f"guard-chk-{uuid4().hex[:6]}@example.com", password_hash="pw", full_name="Guard Checkin", role="guard")
    db_session.add(guard)
    db_session.flush()

    service = GateControlService(db_session)
    gate = service.create_gate(
        org.id,
        WarehouseGateCreate(code="GATE-CHK-01", name="Gate Checkin", warehouse_id=wh.id)
    )

    req = GateCheckInRequest(
        gate_id=gate.id,
        plate_observed="xyz-789",
        seal_status=SealStatus.INTACT,
        driver_dni_raw="12345678",
        driver_license_raw="Q12345678",
    )

    record_res = service.process_checkin(req, org.id, guard.id)
    assert isinstance(record_res, GateControlRecordResponse)
    assert record_res.plate_observed == "XYZ789"
    assert record_res.status == "DRAFT"
    assert record_res.access_decision == "PENDING"
    assert record_res.driver_dni_masked == "******78"
    assert record_res.driver_license_masked == "*******78"
    assert len(record_res.history_entries) == 1


def test_gate_checkin_inactive_gate_fails(db_session: Session):
    """Test check-in to an INACTIVE gate raises InvalidGateStateError."""
    org = Organization(code=f"ORG-INAC-{uuid4().hex[:6]}", name="Org Inactive", country_code="PE")
    db_session.add(org)
    db_session.flush()

    wh = Warehouse(organization_id=org.id, code=f"WH-INAC-{uuid4().hex[:6]}", name="WH Inactive")
    db_session.add(wh)
    db_session.flush()

    guard = User(email=f"guard-inac-{uuid4().hex[:6]}@example.com", password_hash="pw", full_name="Guard Inac", role="guard")
    db_session.add(guard)
    db_session.flush()

    service = GateControlService(db_session)
    gate = service.create_gate(
        org.id,
        WarehouseGateCreate(
            code="GATE-INAC-01",
            name="Inactive Gate",
            warehouse_id=wh.id,
            status=GateStatus.INACTIVE,
        )
    )

    req = GateCheckInRequest(
        gate_id=gate.id,
        plate_observed="XYZ-789",
        seal_status=SealStatus.INTACT,
    )

    with pytest.raises(InvalidGateStateError):
        service.process_checkin(req, org.id, guard.id)


def test_authorize_entry_success_and_cpv_issuance(db_session: Session):
    """Test entry authorization updates decision, status, and issues CPV document via adapter."""
    org = Organization(code=f"ORG-AUTH-{uuid4().hex[:6]}", name="Org Auth", country_code="PE")
    db_session.add(org)
    db_session.flush()

    wh = Warehouse(organization_id=org.id, code=f"WH-AUTH-{uuid4().hex[:6]}", name="WH Auth")
    db_session.add(wh)
    db_session.flush()

    guard = User(email=f"guard-auth-{uuid4().hex[:6]}@example.com", password_hash="pw", full_name="Guard Auth", role="guard")
    db_session.add(guard)
    db_session.flush()

    mock_doc_adapter = MagicMock()
    expected_cpv_id = uuid4()
    mock_doc_adapter.issue_cpv_document.return_value = expected_cpv_id

    service = GateControlService(db_session, doc_adapter=mock_doc_adapter)
    gate = service.create_gate(
        org.id,
        WarehouseGateCreate(code="GATE-AUTH-01", name="Gate Auth", warehouse_id=wh.id)
    )

    checkin = service.process_checkin(
        GateCheckInRequest(
            gate_id=gate.id,
            plate_observed="DEF-456",
            seal_status=SealStatus.INTACT,
            driver_dni_raw="44556677",
            driver_license_raw="Q44556677",
        ),
        org.id,
        guard.id,
    )

    decision_req = GateDecisionRequest(
        record_id=checkin.id,
        decision=AccessDecision.APPROVED,
    )

    auth_res = service.authorize_entry(decision_req, org.id, guard.id)
    assert auth_res.access_decision == "APPROVED"
    assert auth_res.status == "CHECKED_IN"
    assert auth_res.document_instance_id == expected_cpv_id
    assert mock_doc_adapter.issue_cpv_document.called


def test_authorize_entry_plate_mismatch_fails(db_session: Session):
    """Test that observed plate mismatching expected appointment plate raises PlateMismatchWarning."""
    org = Organization(code=f"ORG-MIS-{uuid4().hex[:6]}", name="Org Mismatch", country_code="PE")
    db_session.add(org)
    db_session.flush()

    wh = Warehouse(organization_id=org.id, code=f"WH-MIS-{uuid4().hex[:6]}", name="WH Mismatch")
    db_session.add(wh)
    db_session.flush()

    guard = User(email=f"guard-mis-{uuid4().hex[:6]}@example.com", password_hash="pw", full_name="Guard Mis", role="guard")
    db_session.add(guard)
    db_session.flush()

    mock_doc_adapter = MagicMock()
    service = GateControlService(db_session, doc_adapter=mock_doc_adapter)

    apt_id = uuid4()
    service.prep_service.get_gate_preparation = MagicMock(return_value=GatePreparationResponse(
        appointment_id=apt_id,
        arrival_notice_id=uuid4(),
        warehouse_id=wh.id,
        expected_plate="EXPECTED-99",
        appointment_status="CONFIRMED",
    ))

    gate = service.create_gate(
        org.id,
        WarehouseGateCreate(code="GATE-MIS-01", name="Gate Mismatch", warehouse_id=wh.id)
    )

    checkin = service.process_checkin(
        GateCheckInRequest(
            gate_id=gate.id,
            reception_appointment_id=apt_id,
            plate_observed="OBSERVED-11",
            seal_status=SealStatus.INTACT,
        ),
        org.id,
        guard.id,
    )

    with pytest.raises(PlateMismatchWarning):
        service.authorize_entry(
            GateDecisionRequest(record_id=checkin.id, decision=AccessDecision.APPROVED),
            org.id,
            guard.id,
        )


def test_authorize_entry_seal_broken_fails(db_session: Session):
    """Test that broken or tampered cargo seal raises SealStatusInvalidError."""
    org = Organization(code=f"ORG-SEAL-{uuid4().hex[:6]}", name="Org Seal", country_code="PE")
    db_session.add(org)
    db_session.flush()

    wh = Warehouse(organization_id=org.id, code=f"WH-SEAL-{uuid4().hex[:6]}", name="WH Seal")
    db_session.add(wh)
    db_session.flush()

    guard = User(email=f"guard-seal-{uuid4().hex[:6]}@example.com", password_hash="pw", full_name="Guard Seal", role="guard")
    db_session.add(guard)
    db_session.flush()

    mock_doc_adapter = MagicMock()
    service = GateControlService(db_session, doc_adapter=mock_doc_adapter)
    gate = service.create_gate(
        org.id,
        WarehouseGateCreate(code="GATE-SEAL-01", name="Gate Seal", warehouse_id=wh.id)
    )

    checkin = service.process_checkin(
        GateCheckInRequest(
            gate_id=gate.id,
            plate_observed="ABC-123",
            seal_status=SealStatus.BROKEN,
        ),
        org.id,
        guard.id,
    )

    with pytest.raises(SealStatusInvalidError):
        service.authorize_entry(
            GateDecisionRequest(record_id=checkin.id, decision=AccessDecision.APPROVED),
            org.id,
            guard.id,
        )


def test_authorize_entry_expired_driver_license_fails(db_session: Session):
    """Test that an expired driver's license raises DriverLicenseExpiredError."""
    org = Organization(code=f"ORG-EXP-{uuid4().hex[:6]}", name="Org Expired", country_code="PE")
    db_session.add(org)
    db_session.flush()

    wh = Warehouse(organization_id=org.id, code=f"WH-EXP-{uuid4().hex[:6]}", name="WH Expired")
    db_session.add(wh)
    db_session.flush()

    guard = User(email=f"guard-exp-{uuid4().hex[:6]}@example.com", password_hash="pw", full_name="Guard Exp", role="guard")
    db_session.add(guard)
    db_session.flush()

    # Seed expired driver license record
    lic = DriverLicenseModel(
        organization_id=org.id,
        driver_id=uuid4(),
        license_number="LIC-EXPIRED-99",
        normalized_license_number="LICEXPIRED99",
        masked_license_number="*******99",
        valid_from=date(2020, 1, 1),
        expires_at=date(2022, 1, 1),
    )
    db_session.add(lic)
    db_session.flush()

    mock_doc_adapter = MagicMock()
    service = GateControlService(db_session, doc_adapter=mock_doc_adapter)
    gate = service.create_gate(
        org.id,
        WarehouseGateCreate(code="GATE-EXP-01", name="Gate Expired", warehouse_id=wh.id)
    )

    checkin = service.process_checkin(
        GateCheckInRequest(
            gate_id=gate.id,
            plate_observed="EX-123",
            seal_status=SealStatus.INTACT,
            driver_license_raw="LIC-EXPIRED-99",
        ),
        org.id,
        guard.id,
    )

    with pytest.raises(DriverLicenseExpiredError) as exc_info:
        service.authorize_entry(
            GateDecisionRequest(record_id=checkin.id, decision=AccessDecision.APPROVED),
            org.id,
            guard.id,
        )
    assert "2022-01-01" in str(exc_info.value)


def test_deny_entry_requires_reason(db_session: Session):
    """Test denying vehicle entry requires a rejection reason and sets REJECTED status."""
    org = Organization(code=f"ORG-DENY-{uuid4().hex[:6]}", name="Org Deny", country_code="PE")
    db_session.add(org)
    db_session.flush()

    wh = Warehouse(organization_id=org.id, code=f"WH-DENY-{uuid4().hex[:6]}", name="WH Deny")
    db_session.add(wh)
    db_session.flush()

    guard = User(email=f"guard-deny-{uuid4().hex[:6]}@example.com", password_hash="pw", full_name="Guard Deny", role="guard")
    db_session.add(guard)
    db_session.flush()

    service = GateControlService(db_session)
    gate = service.create_gate(
        org.id,
        WarehouseGateCreate(code="GATE-DENY-01", name="Gate Deny", warehouse_id=wh.id)
    )

    checkin = service.process_checkin(
        GateCheckInRequest(gate_id=gate.id, plate_observed="DENY-99"),
        org.id,
        guard.id,
    )

    # Empty reason fails
    with pytest.raises(InvalidGateStateError):
        service.deny_entry(
            GateDecisionRequest(record_id=checkin.id, decision=AccessDecision.DENIED, rejection_reason=""),
            org.id,
            guard.id,
        )

    # Valid denial
    denied_res = service.deny_entry(
        GateDecisionRequest(record_id=checkin.id, decision=AccessDecision.DENIED, rejection_reason="No manifest provided"),
        org.id,
        guard.id,
    )

    assert denied_res.access_decision == "DENIED"
    assert denied_res.status == "REJECTED"
    assert denied_res.rejection_reason == "No manifest provided"


def test_checkout_success(db_session: Session):
    """Test vehicle checkout transitions status from CHECKED_IN to CHECKED_OUT."""
    org = Organization(code=f"ORG-OUT-{uuid4().hex[:6]}", name="Org Checkout", country_code="PE")
    db_session.add(org)
    db_session.flush()

    wh = Warehouse(organization_id=org.id, code=f"WH-OUT-{uuid4().hex[:6]}", name="WH Checkout")
    db_session.add(wh)
    db_session.flush()

    guard = User(email=f"guard-out-{uuid4().hex[:6]}@example.com", password_hash="pw", full_name="Guard Out", role="guard")
    db_session.add(guard)
    db_session.flush()

    mock_doc_adapter = MagicMock()
    mock_doc_adapter.issue_cpv_document.return_value = uuid4()

    service = GateControlService(db_session, doc_adapter=mock_doc_adapter)
    gate = service.create_gate(
        org.id,
        WarehouseGateCreate(code="GATE-OUT-01", name="Gate Checkout", warehouse_id=wh.id)
    )

    checkin = service.process_checkin(
        GateCheckInRequest(gate_id=gate.id, plate_observed="OUT-888"),
        org.id,
        guard.id,
    )

    service.authorize_entry(
        GateDecisionRequest(record_id=checkin.id, decision=AccessDecision.APPROVED),
        org.id,
        guard.id,
    )

    checkout_res = service.process_checkout(
        GateCheckOutRequest(record_id=checkin.id, notes="Vehicle departed cleanly"),
        org.id,
        guard.id,
    )

    assert checkout_res.status == "CHECKED_OUT"
    assert checkout_res.check_out_at is not None


def test_gate_control_document_adapter_unit(db_session: Session):
    """Test GateControlDocumentAdapter.issue_cpv_document constructs CPV context and invokes lifecycle service."""
    adapter = GateControlDocumentAdapter(db_session)
    adapter.lifecycle_service = MagicMock()

    mock_draft = MagicMock()
    mock_draft.id = uuid4()
    mock_issued = MagicMock()
    mock_issued.id = uuid4()

    adapter.lifecycle_service.create_draft.return_value = mock_draft
    adapter.lifecycle_service.issue_document.return_value = mock_issued

    record = GateControlRecordModel(
        id=uuid4(),
        organization_id=uuid4(),
        record_code="GCR-2026-TEST",
        arrival_at=datetime.now(timezone.utc),
        plate_observed="CPV-123",
        seal_status=SealStatus.INTACT,
        driver_dni_raw="12345678",
        driver_license_raw="Q12345678",
    )
    gate = WarehouseGateModel(
        id=uuid4(),
        code="GATE-01",
        name="Main Gate",
        warehouse_id=uuid4(),
    )
    actor_id = uuid4()

    result_id = adapter.issue_cpv_document(record=record, gate=gate, actor_user_id=actor_id)

    assert result_id == mock_issued.id
    adapter.lifecycle_service.create_draft.assert_called_once()
    adapter.lifecycle_service.issue_document.assert_called_once()


