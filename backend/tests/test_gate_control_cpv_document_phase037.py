"""Regression tests for the Phase 037 CPV issuance and PDF contract."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.main import app
from app.modules.logistics.documents.application.lifecycle_service import (
    DocumentLifecycleService,
)
from app.modules.logistics.documents.models import DocumentInstanceModel
from app.modules.logistics.inbound.gate_control.application.document_service import (
    GateCheckInDocumentService,
)
from app.modules.logistics.inbound.gate_control.infrastructure.persistence.models import (
    WarehouseGateModel,
)


def _check_in(*, document_instance_id=None, status="ENTRY_AUTHORIZED"):
    return SimpleNamespace(
        id=uuid4(),
        organization_id=uuid4(),
        branch_id=uuid4(),
        warehouse_id=uuid4(),
        gate_id=uuid4(),
        guard_user_id=uuid4(),
        appointment_code_snapshot="CIT-LIM-2026-000001",
        check_in_code="GCI-000001",
        document_instance_id=document_instance_id,
        status=status,
        row_version=1,
    )


def _snapshot():
    return {
        "content_hash": "a" * 64,
        "arrived_at": datetime.now(timezone.utc).isoformat(),
        "guard": {"display_name": "Agente de puerta"},
        "carrier": {"legal_name": "Transportes Prueba S.A.C."},
        "observed_transport": {"vehicle_type": "Camión"},
        "vehicle_inspection": {"observed_plate": "ABC-123"},
        "driver_inspection": {
            "observed_name_snapshot": "Conductor Prueba",
            "observed_document_number_redacted": "******42",
            "license_number_redacted": "*******21",
        },
        "seal_inspection": {
            "observed_seal_number": "SELLO-01",
            "seal_match_status": "MATCH",
        },
    }


def test_legacy_placeholder_is_replaced_by_real_document_instance():
    db = MagicMock()
    legacy_placeholder = uuid4()
    check_in = _check_in(document_instance_id=legacy_placeholder)
    issued_draft = SimpleNamespace(id=uuid4(), status="DRAFT")

    def fake_get(model, object_id):
        if model is DocumentInstanceModel and object_id == legacy_placeholder:
            return None
        if model is WarehouseGateModel:
            return SimpleNamespace(code="P01", name="Puerta principal")
        return None

    db.get.side_effect = fake_get
    service = GateCheckInDocumentService(db)
    service._get_check_in = MagicMock(return_value=check_in)
    service.snapshots.build = MagicMock(return_value=_snapshot())
    service.documents.create_draft = MagicMock(return_value=issued_draft)

    document = service.ensure_draft(
        check_in.id, check_in.organization_id, check_in.guard_user_id
    )

    assert document is issued_draft
    assert check_in.document_instance_id == issued_draft.id
    assert check_in.document_instance_id != legacy_placeholder
    assert check_in.row_version == 2
    payload = service.documents.create_draft.call_args.kwargs["structured_data"]
    assert payload["plate"] == "ABC-123"
    assert payload["driver_dni_masked"] == "******42"
    assert payload["driver_license_masked"] == "*******21"
    assert "driver_dni_raw" not in payload
    assert payload["gate_check_in_snapshot"]["content_hash"] == "a" * 64


def test_issue_is_resource_idempotent_when_cpv_is_already_issued():
    db = MagicMock()
    check_in = _check_in()
    issued = SimpleNamespace(
        id=uuid4(),
        status="ISSUED",
        current_snapshot_id=None,
    )
    service = GateCheckInDocumentService(db)
    service.ensure_draft = MagicMock(return_value=issued)
    service.documents.issue_document = MagicMock()

    result, snapshot_hash = service.issue(
        check_in.id,
        check_in.organization_id,
        check_in.guard_user_id,
        "same-request-key",
    )

    assert result is issued
    assert snapshot_hash is None
    service.documents.issue_document.assert_not_called()


def test_document_lifecycle_loads_issued_pdf_and_audits_download():
    db = MagicMock()
    document = SimpleNamespace(
        id=uuid4(),
        status="ISSUED",
        organization_id=uuid4(),
        branch_id=uuid4(),
        warehouse_id=uuid4(),
        authoritative_artifact_id=uuid4(),
        document_code="CPV-LIM-2026-000001",
    )
    artifact = SimpleNamespace(
        filename="CPV-LIM-2026-000001.pdf",
        storage_key="documents/cpv.pdf",
    )
    db.get.return_value = document
    db.scalars.return_value.first.return_value = artifact
    service = DocumentLifecycleService(db)
    service.storage = MagicMock()
    service.storage.get.return_value = b"%PDF-1.7 test"
    service._write_audit = MagicMock()

    resolved, resolved_artifact, pdf_bytes = service.get_downloadable_pdf(
        document.id, uuid4()
    )

    assert resolved is document
    assert resolved_artifact is artifact
    assert pdf_bytes.startswith(b"%PDF")
    service._write_audit.assert_called_once()


def test_openapi_publishes_gate_cpv_pdf_as_application_pdf():
    schema = app.openapi()
    operation = schema["paths"][
        "/api/logistics/gate-check-ins/{check_in_id}/document/pdf"
    ]["get"]
    content = operation["responses"]["200"]["content"]

    assert "application/pdf" in content
    issue_operation = schema["paths"][
        "/api/logistics/gate-check-ins/{check_in_id}/issue-document"
    ]["post"]
    assert any(
        parameter["in"] == "header" and parameter["name"] == "Idempotency-Key"
        for parameter in issue_operation["parameters"]
    )
    metadata_schema = schema["paths"][
        "/api/logistics/gate-check-ins/{check_in_id}/document"
    ]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert metadata_schema["$ref"].endswith("/GateCpvDocumentResponse")
