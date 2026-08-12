"""Phase 039 contract and safety-invariant tests (no production migration)."""
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.modules.logistics.audit.catalog import is_valid_event_code
from app.modules.logistics.inbound.receiving.domain.enums import RECEIPT_TRANSITIONS, ReceiptStatus
from app.modules.logistics.inbound.receiving.domain.services import BarcodeParserRegistry, canonical_hash, require_receipt_transition, strict_decimal
from app.modules.logistics.inbound.receiving.infrastructure.jobs.jobs import PHASE_039_JOBS
from app.modules.logistics.inbound.receiving.infrastructure.persistence.models import PHASE_039_TABLES
from app.modules.logistics.inbound.receiving.presentation.schemas import ApplyReceivedQuantityRequest, InboundExpirationObservationCreate, InboundReceiptCreate, InboundReceiptCompletionRequest, InboundScanEventBatchCreate, InboundScanEventCreate
from app.modules.logistics.rbac.permission_catalog import PHASE_039_PERMISSIONS
from app.modules.logistics.security.step_up_policy import POLICY_CATALOG

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = BACKEND_ROOT.parent / "docs" / "architecture" / "phase_039" / "backend"
UUID1 = "00000000-0000-0000-0000-000000000001"


@pytest.mark.parametrize("field,value", [("started_at","2026-08-02T00:00:00Z"),("started_by_user_id",UUID1),("completed_by_user_id",UUID1),("received_base_quantity","1"),("operator_user_id",UUID1),("risk_level","LOW"),("step_up_passed",True)])
def test_receipt_create_rejects_server_owned_fields(field, value):
    with pytest.raises(ValidationError): InboundReceiptCreate.model_validate({"unloading_operation_id":UUID1,field:value})


@pytest.mark.parametrize("schema,payload", [
    (InboundReceiptCompletionRequest,{"row_version":1,"completed_at":"2026-08-02T00:00:00Z"}),
    (ApplyReceivedQuantityRequest,{"quantity":"1","unit_id":UUID1,"row_version":1,"received_base_quantity":"1"}),
    (InboundScanEventCreate,{"scan_session_id":UUID1,"client_scan_id":"a","raw_code":"00123457","requested_quantity":"1","scan_source":"CAMERA","operator_user_id":UUID1}),
])
def test_commands_forbid_authoritative_fields(schema,payload):
    with pytest.raises(ValidationError): schema.model_validate(payload)


@pytest.mark.parametrize("schema,payload", [
    (ApplyReceivedQuantityRequest,{"quantity":1.5,"unit_id":UUID1,"row_version":1}),
    (InboundScanEventCreate,{"scan_session_id":UUID1,"client_scan_id":"a","raw_code":"00123457","requested_quantity":1.0,"scan_source":"CAMERA"}),
])
def test_float_is_rejected_at_api_boundary(schema,payload):
    with pytest.raises(ValidationError): schema.model_validate(payload)


@pytest.mark.parametrize("value", [float("nan"),float("inf"),"NaN","Infinity","0","-1"])
def test_decimal_guard_rejects_non_finite_or_non_positive(value):
    with pytest.raises(Exception): strict_decimal(value)


def test_decimal_guard_preserves_exact_value(): assert strict_decimal("123.4500") == Decimal("123.4500")
def test_internal_code_preserves_leading_zeroes(): assert BarcodeParserRegistry.parse("000123", "CODE128").normalized_code == "000123"
def test_empty_code_is_classified(): assert str(BarcodeParserRegistry.parse("").parse_status) == "EMPTY"
def test_control_characters_are_rejected(): assert str(BarcodeParserRegistry.parse("ABC\x00DEF").parse_status) == "INVALID_FORMAT"
def test_long_code_is_rejected(): assert str(BarcodeParserRegistry.parse("A"*513).parse_status) == "TOO_LONG"
def test_invalid_gtin_checksum_is_rejected(): assert str(BarcodeParserRegistry.parse("12345678","EAN8").parse_status) == "INVALID_FORMAT"
def test_valid_ean8_is_parsed(): assert str(BarcodeParserRegistry.parse("96385074","EAN8").parse_status) == "PARSED"
def test_qr_url_is_data_not_opened(): assert BarcodeParserRegistry.parse("https://example.invalid/payload","QR_INTERNAL").elements["identifier"].startswith("https://")
def test_gs1_parser_extracts_gtin(): assert BarcodeParserRegistry.parse("]C1010950110153000317251231","GS1_128").elements["gtin"] == "09501101530003"


def test_state_machine_happy_path():
    for current,target in [("CREATED","PREPARING"),("PREPARING","READY"),("READY","IN_PROGRESS"),("IN_PROGRESS","VALIDATING"),("VALIDATING","FULLY_RECEIVED"),("FULLY_RECEIVED","COMPLETED")]: require_receipt_transition(current,target)
def test_state_machine_rejects_direct_complete():
    with pytest.raises(Exception): require_receipt_transition("CREATED","COMPLETED")
def test_all_nonterminal_states_have_explicit_transitions(): assert set(RECEIPT_TRANSITIONS) >= {ReceiptStatus.CREATED,ReceiptStatus.PREPARING,ReceiptStatus.READY,ReceiptStatus.IN_PROGRESS}
def test_canonical_hash_is_order_independent(): assert canonical_hash({"a":1,"b":2}) == canonical_hash({"b":2,"a":1})


def test_batch_limit_is_500():
    event={"scan_session_id":UUID1,"client_scan_id":"x","raw_code":"ABC","requested_quantity":"1","scan_source":"CAMERA"}
    with pytest.raises(ValidationError): InboundScanEventBatchCreate(events=[event|{"client_scan_id":str(i)} for i in range(501)])
def test_expiration_before_manufacture_is_rejected():
    with pytest.raises(ValidationError): InboundExpirationObservationCreate(manufacturing_date="2026-08-02",expiration_date="2026-08-01",source="MANUAL_ENTRY")


def test_phase039_migration_manifest_and_chain():
    import importlib.util
    path=BACKEND_ROOT/"alembic"/"versions"/"ac390110039dc_phase_039_inbound_receiving.py";spec=importlib.util.spec_from_file_location("phase039_migration",path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.revision=="ac390110039dc";assert module.down_revision=="ab380110038dc";assert len(PHASE_039_TABLES)==18;assert len(PHASE_039_TABLES)==len(set(PHASE_039_TABLES))


def test_phase039_document_pack_is_complete():
    files=[x for x in DOCS_ROOT.iterdir() if x.is_file()];assert len(files)==52;markdown=[x.read_text(encoding="utf-8") for x in files if x.suffix==".md"];assert sum(x.count("```mermaid") for x in markdown)==19


def test_permission_catalog_is_complete_and_unique():
    codes=[str(x["code"]) for x in PHASE_039_PERMISSIONS];assert len(codes)==26;assert len(codes)==len(set(codes));assert "logistics.inbound_receipt_scans.compensate" in codes
def test_sensitive_permissions_have_step_up_policy():
    codes=[str(x["code"]) for x in PHASE_039_PERMISSIONS if x.get("requires_step_up")];assert not [x for x in codes if x not in POLICY_CATALOG]
def test_jobs_are_external_scheduler_entrypoints(): assert len(PHASE_039_JOBS)==12 and all(callable(x) for x in PHASE_039_JOBS.values())


@pytest.mark.parametrize("event_code", ["logistics.inbound_receipt.created","logistics.inbound_receipt.code_scanned","logistics.inbound_receipt.scan_compensated","logistics.inbound_receipt.difference_candidate_created","logistics.inbound_receipt.completed","logistics.inbound_receipt.integrity_failed"])
def test_audit_codes_are_registered(event_code): assert is_valid_event_code(event_code)


def test_openapi_exposes_required_phase039_contract_and_idempotency():
    from app.main import app
    schema=app.openapi();required={"/api/logistics/inbound-receipts","/api/logistics/inbound-receipts/from-unloading-operation","/api/logistics/inbound-receipts/{receipt_id}/prepare","/api/logistics/inbound-receipts/{receipt_id}/complete","/api/logistics/inbound-receipts/{receipt_id}/scan-events","/api/logistics/inbound-receipts/{receipt_id}/scan-events/batch","/api/logistics/inbound-scan-events/{event_id}/compensate","/api/logistics/inbound-receipts/{receipt_id}/difference-preparation"};assert required<=set(schema["paths"])
    for path,method in [("/api/logistics/inbound-receipts","post"),("/api/logistics/inbound-receipts/{receipt_id}/prepare","post"),("/api/logistics/inbound-receipts/{receipt_id}/scan-events","post"),("/api/logistics/inbound-receipts/{receipt_id}/complete","post")]: assert any(x["name"]=="Idempotency-Key" and x.get("required") for x in schema["paths"][path][method]["parameters"])


def test_scan_events_have_no_delete_or_patch():
    from app.main import app
    schema=app.openapi();paths=[v for k,v in schema["paths"].items() if "inbound-scan-events" in k or "/scan-events" in k];assert not any("delete" in x or "patch" in x for x in paths)


def test_phase039_has_no_inventory_effect_tables_or_columns():
    from app.database.base import Base
    banned_tables={"inventory_balances","inventory_movements","stock","kardex","quarantine","putaway"};assert not (banned_tables & set(PHASE_039_TABLES))
    banned_columns={"stock_id","inventory_movement_id","kardex_id","quarantine_id","putaway_id","lot_master_id","serial_master_id"}
    for name in PHASE_039_TABLES: assert not (banned_columns & set(Base.metadata.tables[name].columns.keys())),name
