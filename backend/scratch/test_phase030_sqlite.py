"""Standalone SQLite Runner for Phase 030 Files and Evidence Centralization."""

import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

# Ensure backend root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
import app.models.registry  # Register all ORM models

from app.modules.logistics.files.application.services.upload_session_service import FileUploadSessionService
from app.modules.logistics.files.application.services.file_asset_service import FileAssetService
from app.modules.logistics.files.application.services.association_service import FileAssociationService
from app.modules.logistics.files.application.services.evidence_custody_service import EvidenceCustodyService
from app.modules.logistics.files.application.services.retention_legal_hold_service import RetentionLegalHoldService
from app.modules.logistics.files.application.services.preview_download_service import FilePreviewDownloadService
from app.modules.logistics.files.domain.value_objects.enums import (
    FileAssetType,
    FileClassification,
    FileLifecycleStatus,
    EvidenceAcceptanceStatus,
)
from app.modules.logistics.files.domain.errors.exceptions import (
    FileLegalHoldActiveError,
    FileContentInvalidError,
    FileTypeNotAllowedError,
    FileMalwareDetectedError,
)


def main():
    print("=== STARTING PHASE 030 FILES & EVIDENCE SQLITE TEST RUNNER ===")

    engine = create_engine("sqlite:///:memory:", echo=False)
    allowed_prefixes = (
        "organizations", "logistics_", "vehicles", "vehicle_", "assisted_",
        "business_", "units_", "measurement_", "product",
        "purchase_", "audit_logs", "users", "drivers", "driver_",
        "file_", "files", "evidence_", "signature_", "logistics_audit",
    )
    for table in Base.metadata.sorted_tables:
        if any(table.name.startswith(p) for p in allowed_prefixes):
            try:
                table.create(engine, checkfirst=True)
            except Exception:
                pass
    Session = sessionmaker(bind=engine)
    db = Session()

    org_id = uuid4()
    user_id = uuid4()

    # 1. Create Upload Session & Finalize PDF File
    print("1. Testing Upload Session & PDF Upload Finalization...")
    upload_svc = FileUploadSessionService(db)
    session = upload_svc.create_upload_session(
        organization_id=org_id,
        user_id=user_id,
        expected_filename="contrato_transporte_2026.pdf",
        expected_size_bytes=1024,
        declared_mime_type="application/pdf",
        asset_type=FileAssetType.DOCUMENT,
        classification=FileClassification.CONFIDENTIAL,
    )
    assert session.status == "CREATED"

    pdf_bytes = b"%PDF-1.7\n1 0 obj<<>>endobj\ntrailer<<>>startxref\n11\n%%EOF"
    asset, version = upload_svc.finalize_upload_session(
        session_id=session.id,
        user_id=user_id,
        uploaded_content=pdf_bytes,
        title="Contrato de Transporte Oficial 2026",
    )
    assert asset.file_code.startswith("FIL-")
    assert asset.lifecycle_status == "AVAILABLE"
    assert version.SHA256 is not None
    assert version.detected_MIME_type == "application/pdf"
    print(f"   [SUCCESS] FileAsset created code={asset.file_code}, SHA256={version.SHA256[:16]}...")

    # 2. Test File Content Validation (XXE in XML & SVG Block)
    print("2. Testing Content Security Validation (XXE & SVG Block)...")
    try:
        xxe_xml = b'<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>'
        upload_svc.validator.validate_content(xxe_xml, "application/xml", "factura.xml")
        assert False, "Should have failed XXE validation"
    except FileContentInvalidError as ex:
        print(f"   [SUCCESS] Blocked XXE Attack: {ex.message}")

    try:
        upload_svc.validator.validate_content(b"<svg></svg>", "image/svg+xml", "logo.svg")
        assert False, "Should have blocked SVG"
    except FileTypeNotAllowedError as ex:
        print(f"   [SUCCESS] Blocked SVG Upload: {ex.message}")

    # 3. Test Malware Detection
    print("3. Testing Malware Scanning & Quarantine...")
    eicar_bytes = b"%PDF-1.7\nEICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    session_eicar = upload_svc.create_upload_session(
        organization_id=org_id,
        user_id=user_id,
        expected_filename="malware_test.pdf",
        expected_size_bytes=len(eicar_bytes),
        declared_mime_type="application/pdf",
    )
    try:
        upload_svc.finalize_upload_session(
            session_id=session_eicar.id,
            user_id=user_id,
            uploaded_content=eicar_bytes,
        )
        assert False, "Should have detected malware"
    except FileMalwareDetectedError as ex:
        print(f"   [SUCCESS] Detected & Rejected Malware File: {ex.message}")

    # 4. Test File Association to Vehicle Document
    print("4. Testing Resource Association (Vehicle Document)...")
    assoc_svc = FileAssociationService(db)
    assoc = assoc_svc.associate_file(
        file_id=asset.id,
        organization_id=org_id,
        user_id=user_id,
        resource_type="VEHICLE_DOCUMENT",
        resource_id="VEH-DOC-9001",
        association_type="ORIGINAL",
        is_primary=True,
    )
    assert assoc.resource_type == "VEHICLE_DOCUMENT"
    assert assoc.status == "ACTIVE"
    print(f"   [SUCCESS] Associated File to Vehicle Document ID={assoc.resource_id}")

    # 5. Test Evidence Registration & Acceptance (Chain of Custody)
    print("5. Testing Evidence Registration & Immutable Acceptance...")
    ev_svc = EvidenceCustodyService(db)
    evidence = ev_svc.register_evidence(
        organization_id=org_id,
        user_id=user_id,
        file_asset_id=asset.id,
        evidence_type="DOCUMENT",
        subject_type="VEHICLE_VERIFICATION",
        subject_id="VERIF-1001",
        description="Evidencia documental de verificación vehicular.",
    )
    assert evidence.acceptance_status == "PENDING"

    evidence_acc = ev_svc.accept_evidence(
        evidence_id=evidence.id,
        organization_id=org_id,
        user_id=user_id,
    )
    assert evidence_acc.acceptance_status == "ACCEPTED"

    custody_events = ev_svc.get_custody_events(evidence.id, org_id)
    assert len(custody_events) >= 2  # CAPTURED, ACCEPTED
    print(f"   [SUCCESS] Evidence Accepted code={evidence_acc.evidence_code}, Chain Events={len(custody_events)}")

    # 6. Test Legal Hold Application & Deletion Request Protection
    print("6. Testing Legal Hold Application & Controlled Deletion Protection...")
    ret_svc = RetentionLegalHoldService(db)
    hold = ret_svc.apply_legal_hold(
        file_id=asset.id,
        organization_id=org_id,
        user_id=user_id,
        reason="Auditoría legal en curso.",
        authority_reference="AUD-2026-X",
    )
    assert hold.status == "ACTIVE"

    try:
        ret_svc.request_file_deletion(
            file_id=asset.id,
            organization_id=org_id,
            user_id=user_id,
            reason="Solicitud de prueba",
        )
        assert False, "Should have blocked deletion request due to active legal hold"
    except FileLegalHoldActiveError as ex:
        print(f"   [SUCCESS] Deletion blocked by Legal Hold: {ex.message}")

    # Release Legal Hold & Request Deletion
    ret_svc.release_legal_hold(
        hold_id=hold.id,
        organization_id=org_id,
        user_id=user_id,
        release_reason="Auditoría legal concluida.",
    )
    del_req = ret_svc.request_file_deletion(
        file_id=asset.id,
        organization_id=org_id,
        user_id=user_id,
        reason="Limpieza autorizada.",
    )
    assert del_req.status == "REQUESTED"
    print("   [SUCCESS] Released Legal Hold and registered Deletion Request.")

    # 7. Test Download & Preview Access
    print("7. Testing Download & Preview Access Services...")
    dl_svc = FilePreviewDownloadService(db)
    signed_dl, _, _ = dl_svc.get_download_access(asset.id, org_id, user_id)
    signed_pv, _, _ = dl_svc.get_preview_access(asset.id, org_id, user_id)
    assert signed_dl.url is not None
    assert signed_pv.url is not None
    print(f"   [SUCCESS] Generated Download URL={signed_dl.url[:45]}...")

    print("\n=== PHASE 030 FILES & EVIDENCE SQLITE TEST RUNNER PASSED 100% ===")


if __name__ == "__main__":
    main()
