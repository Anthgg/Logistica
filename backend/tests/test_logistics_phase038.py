"""Phase 038 contract, safety-invariant and integration-registration tests."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.modules.logistics.audit.catalog import is_valid_event_code
from app.modules.logistics.inbound.dock_operations.domain.policies.state_machine import (
    ASSIGNMENT_TRANSITIONS,
    UNLOADING_TRANSITIONS,
    require_transition,
)
from app.modules.logistics.inbound.dock_operations.domain.services.metrics import DockOperationalMetricsService
from app.modules.logistics.inbound.dock_operations.application.services.export_service import (
    _csv_bytes,
    _pdf_bytes,
    _xlsx_bytes,
)
from app.modules.logistics.inbound.dock_operations.infrastructure.persistence.models import (
    InboundDockQueueEntryModel,
)
from app.modules.logistics.inbound.dock_operations.presentation.schemas import (
    DockAssignmentCreate,
    DockAssignmentPlanRequest,
    InboundDockQueueCreate,
    UnloadingCompleteRequest,
    UnloadingOperationCreate,
    UnloadingPauseRequest,
    WarehouseDockCreate,
)
from app.modules.logistics.inbound.dock_operations.application.services.dock_services import InboundDockQueueOrderingService
from app.modules.logistics.rbac.permission_catalog import PHASE_038_PERMISSIONS
from app.modules.logistics.security.step_up_policy import POLICY_CATALOG


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
DOCS_ROOT = REPO_ROOT / "docs" / "architecture" / "phase_038" / "backend"


def _valid_dock_payload() -> dict:
    return {
        "warehouse_id": "00000000-0000-0000-0000-000000000001",
        "branch_id": "00000000-0000-0000-0000-000000000002",
        "code": "D-01",
        "name": "Muelle 1",
        "timezone": "America/Lima",
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("created_by", "00000000-0000-0000-0000-000000000003"),
        ("status", "ACTIVE"),
        ("created_at", "2026-08-01T00:00:00Z"),
        ("row_version", 99),
    ],
)
def test_dock_create_rejects_server_owned_fields(field, value):
    payload = _valid_dock_payload() | {field: value}
    with pytest.raises(ValidationError):
        WarehouseDockCreate.model_validate(payload)


@pytest.mark.parametrize(
    "field,value",
    [
        ("assigned_at", "2026-08-01T00:00:00Z"),
        ("assigned_by_user_id", "00000000-0000-0000-0000-000000000003"),
        ("status", "ASSIGNED"),
        ("movement_started_at", "2026-08-01T00:00:00Z"),
    ],
)
def test_assignment_create_rejects_authoritative_fields(field, value):
    payload = {
        "gate_check_in_id": "00000000-0000-0000-0000-000000000010",
        "dock_id": "00000000-0000-0000-0000-000000000011",
        "assignment_reason": "Operación normal",
        "assignment_hash": "a" * 64,
        field: value,
    }
    with pytest.raises(ValidationError):
        DockAssignmentCreate.model_validate(payload)


@pytest.mark.parametrize(
    "schema,payload,field,value",
    [
        (UnloadingOperationCreate, {"unloading_method": "MANUAL"}, "started_at", "2026-08-01T00:00:00Z"),
        (UnloadingCompleteRequest, {}, "completed_at", "2026-08-01T01:00:00Z"),
        (UnloadingCompleteRequest, {}, "gross_duration_seconds", 3600),
        (UnloadingCompleteRequest, {}, "completed_by_user_id", "00000000-0000-0000-0000-000000000003"),
    ],
)
def test_unloading_commands_reject_server_authority(schema, payload, field, value):
    with pytest.raises(ValidationError):
        schema.model_validate(payload | {field: value})


def test_high_severity_pause_requires_evidence():
    with pytest.raises(ValidationError):
        UnloadingPauseRequest(reason_code="SAFETY", reason="Riesgo detectado", severity="CRITICAL")


def test_urgent_queue_requires_reason():
    with pytest.raises(ValidationError):
        InboundDockQueueCreate(
            gate_check_in_id="00000000-0000-0000-0000-000000000010",
            priority="URGENT",
        )


def test_plan_rejects_client_timestamps_outside_requested_interval():
    with pytest.raises(ValidationError):
        DockAssignmentPlanRequest.model_validate({
            "gate_check_in_id": "00000000-0000-0000-0000-000000000010",
            "assigned_at": "2026-08-01T00:00:00Z",
        })


def test_assignment_state_machine_allows_expected_happy_path():
    path = ["ASSIGNED", "MOVING_TO_DOCK", "AT_DOCK", "READY_FOR_UNLOADING", "UNLOADING_IN_PROGRESS", "UNLOADING_COMPLETED", "DOCK_RELEASED"]
    for current, target in zip(path, path[1:]):
        require_transition(current, target, ASSIGNMENT_TRANSITIONS, "dock_assignment")


def test_assignment_state_machine_rejects_direct_release():
    with pytest.raises(Exception) as exc:
        require_transition("ASSIGNED", "DOCK_RELEASED", ASSIGNMENT_TRANSITIONS, "dock_assignment")
    assert getattr(exc.value, "code", None) == "DOCK_ASSIGNMENT_STATUS_INVALID"


def test_unloading_state_machine_rejects_complete_before_start():
    with pytest.raises(Exception):
        require_transition("READY", "COMPLETED", UNLOADING_TRANSITIONS, "unloading_operation")


def test_metrics_are_server_derived_and_complete():
    base = datetime(2026, 8, 1, tzinfo=timezone.utc)
    values = DockOperationalMetricsService.calculate(
        gate_arrived_at=base,
        gate_cleared_at=base + timedelta(minutes=5),
        queued_at=base + timedelta(minutes=6),
        assigned_at=base + timedelta(minutes=10),
        movement_started_at=base + timedelta(minutes=11),
        dock_arrived_at=base + timedelta(minutes=15),
        unloading_started_at=base + timedelta(minutes=20),
        unloading_completed_at=base + timedelta(minutes=50),
        dock_released_at=base + timedelta(minutes=55),
        pause_seconds=300,
    )
    assert values["unloading_gross_seconds"] == 1800
    assert values["unloading_net_seconds"] == 1500
    assert values["data_quality_status"] == "COMPLETE"


def test_metrics_never_emit_negative_duration():
    base = datetime(2026, 8, 1, tzinfo=timezone.utc)
    values = DockOperationalMetricsService.calculate(
        gate_arrived_at=base + timedelta(minutes=1), gate_cleared_at=base,
        queued_at=None, assigned_at=None, movement_started_at=None, dock_arrived_at=None,
        unloading_started_at=None, unloading_completed_at=None, dock_released_at=None, pause_seconds=-50,
    )
    assert values["gate_processing_seconds"] is None
    assert values["unloading_pause_seconds"] == 0
    assert values["data_quality_status"] == "PARTIAL"


def test_queue_order_is_deterministic():
    base = datetime(2026, 8, 1, tzinfo=timezone.utc)
    low = InboundDockQueueEntryModel(id="00000000-0000-0000-0000-000000000003", priority="LOW", queued_at=base, queue_status="READY")
    urgent_late = InboundDockQueueEntryModel(id="00000000-0000-0000-0000-000000000002", priority="URGENT", queued_at=base + timedelta(minutes=1), queue_status="READY")
    urgent_early = InboundDockQueueEntryModel(id="00000000-0000-0000-0000-000000000001", priority="URGENT", queued_at=base, queue_status="READY")
    ordered = InboundDockQueueOrderingService.order([low, urgent_late, urgent_early])
    assert ordered == [urgent_early, urgent_late, low]


def test_phase038_permission_catalog_is_complete_and_unique():
    codes = [str(item["code"]) for item in PHASE_038_PERMISSIONS]
    assert len(codes) == 32
    assert len(codes) == len(set(codes))
    assert "logistics.unloading_operations.correct_times" in codes
    assert "logistics.unloading_operations.cancel" in codes
    assert "logistics.dock_operational_integrity.read" in codes


def test_every_sensitive_phase038_permission_has_step_up_policy():
    sensitive = [str(item["code"]) for item in PHASE_038_PERMISSIONS if item.get("requires_step_up")]
    assert sensitive
    assert not [code for code in sensitive if code not in POLICY_CATALOG]


@pytest.mark.parametrize(
    "event_code",
    [
        "logistics.warehouse_dock.created",
        "logistics.warehouse_dock.blackout_created",
        "logistics.inbound_dock_queue.created",
        "logistics.inbound_dock_assignment.created",
        "logistics.inbound_dock_assignment.reassigned",
        "logistics.unloading_operation.started",
        "logistics.unloading_operation.completed",
        "logistics.unloading_operation.time_correction_approved",
        "logistics.unloading_operation.cancelled",
        "logistics.dock_operation_export.ready",
    ],
)
def test_phase038_audit_codes_are_registered(event_code):
    assert is_valid_event_code(event_code)


def test_phase038_orm_has_no_receiving_or_inventory_columns():
    from app.modules.logistics.inbound.dock_operations.infrastructure.persistence import models
    banned = {"received_quantity", "accepted_quantity", "rejected_quantity", "lot_number", "serial_number", "stock_id", "inventory_movement_id"}
    phase_tables = [table for name, table in models.Base.metadata.tables.items() if name.startswith(("warehouse_dock", "inbound_dock", "dock_", "unloading_"))]
    assert len(phase_tables) >= 21
    for table in phase_tables:
        assert not (banned & set(table.columns.keys())), table.name


def test_phase038_migration_manifest_and_chain():
    import importlib.util
    path = BACKEND_ROOT / "alembic" / "versions" / "ab380110038dc_phase_038_dock_operations.py"
    spec = importlib.util.spec_from_file_location("phase038_migration", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert module.revision == "ab380110038dc"
    assert module.down_revision == "aa370110037dc"
    assert len(module.PHASE_038_TABLES) == 21
    assert len(module.PHASE_038_TABLES) == len(set(module.PHASE_038_TABLES))


def test_phase038_document_pack_is_complete():
    files = list(DOCS_ROOT.iterdir())
    assert len([path for path in files if path.is_file()]) == 52
    markdown = [path.read_text(encoding="utf-8") for path in files if path.suffix == ".md"]
    assert sum(text.count("```mermaid") for text in markdown) == 19


def test_openapi_exposes_phase038_and_requires_idempotency_header():
    from app.main import app
    schema = app.openapi()
    required = {
        "/api/logistics/warehouse-docks",
        "/api/logistics/inbound-dock-queue",
        "/api/logistics/dock-assignment-plans",
        "/api/logistics/dock-assignment-plans/{assignment_hash}/execute",
        "/api/logistics/inbound-dock-assignments",
        "/api/logistics/unloading-operations/{operation_id}/start",
        "/api/logistics/unloading-operations/{operation_id}/receiving-preparation",
        "/api/logistics/dock-operation-exports",
    }
    assert required <= set(schema["paths"])
    for path, method in [
        ("/api/logistics/warehouse-docks", "post"),
        ("/api/logistics/dock-assignment-plans", "post"),
        ("/api/logistics/inbound-dock-assignments", "post"),
        ("/api/logistics/unloading-operations/{operation_id}/start", "post"),
    ]:
        parameters = schema["paths"][path][method]["parameters"]
        assert any(item["name"] == "Idempotency-Key" and item.get("required") for item in parameters)


def test_receiving_preparation_is_read_only_endpoint():
    from app.main import app
    path = app.openapi()["paths"]["/api/logistics/unloading-operations/{operation_id}/receiving-preparation"]
    assert set(path) == {"get"}


def test_operational_export_formats_are_real_and_labeled():
    rows = [["WH-01", "D-01", "CPV-1", "CIT-1", "ABC-123", "=unsafe", "lead", "started", "start=now", "", "COMPLETED", "COMPLETE"]]
    csv_data = _csv_bytes(rows)
    xlsx_data = _xlsx_bytes(rows)
    pdf_data = _pdf_bytes(rows)
    assert csv_data.startswith(b"\xef\xbb\xbf")
    assert b"'=unsafe" in csv_data
    assert xlsx_data.startswith(b"PK")
    assert pdf_data.startswith(b"%PDF-1.4")
    assert b"NO OFICIAL" in pdf_data
