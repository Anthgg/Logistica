"""Pytest Test Suite for Phase 030 — Files and Evidence Centralization."""

from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
import app.models.registry  # register ORM models

from app.modules.logistics.files.application.services.association_service import FileAssociationService
from app.modules.logistics.files.application.services.evidence_custody_service import EvidenceCustodyService
from app.modules.logistics.files.application.services.file_asset_service import FileAssetService
from app.modules.logistics.files.application.services.preview_download_service import FilePreviewDownloadService
from app.modules.logistics.files.application.services.retention_legal_hold_service import RetentionLegalHoldService
from app.modules.logistics.files.application.services.upload_session_service import FileUploadSessionService
from app.modules.logistics.files.domain.errors.exceptions import (
    FileContentInvalidError,
    FileLegalHoldActiveError,
    FileMalwareDetectedError,
    FileTypeNotAllowedError,
)
from app.modules.logistics.files.domain.value_objects.enums import FileAssetType, FileClassification


@pytest.fixture
def db_session():
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
    session = Session()
    yield session
    session.close()


def test_phase030_upload_session_and_pdf_promotion(db_session):
    org_id = uuid4()
    user_id = uuid4()

    upload_svc = FileUploadSessionService(db_session)
    session = upload_svc.create_upload_session(
        organization_id=org_id,
        user_id=user_id,
        expected_filename="tarjeta_propiedad_fase030.pdf",
        expected_size_bytes=512,
        declared_mime_type="application/pdf",
        asset_type=FileAssetType.DOCUMENT,
        classification=FileClassification.RESTRICTED,
    )
    assert session.status == "CREATED"

    pdf_bytes = b"%PDF-1.7\n1 0 obj<<>>endobj\ntrailer<<>>startxref\n11\n%%EOF"
    asset, version = upload_svc.finalize_upload_session(
        session_id=session.id,
        user_id=user_id,
        uploaded_content=pdf_bytes,
        title="Tarjeta de Propiedad Vehicular",
    )

    assert asset.file_code.startswith("FIL-")
    assert asset.lifecycle_status == "AVAILABLE"
    assert version.detected_MIME_type == "application/pdf"
    assert version.SHA256 is not None


def test_phase030_content_security_validation(db_session):
    upload_svc = FileUploadSessionService(db_session)

    # 1. XXE attack
    xxe_payload = b'<?xml version="1.0"?><!DOCTYPE test [<!ENTITY xxe SYSTEM "file:///etc/hosts">]><test>&xxe;</test>'
    with pytest.raises(FileContentInvalidError):
        upload_svc.validator.validate_content(xxe_payload, "application/xml", "document.xml")

    # 2. SVG block
    with pytest.raises(FileTypeNotAllowedError):
        upload_svc.validator.validate_content(b"<svg></svg>", "image/svg+xml", "icon.svg")

    # 3. Executable block
    with pytest.raises(FileTypeNotAllowedError):
        upload_svc.validator.validate_content(b"MZ...", "application/x-msdownload", "virus.exe")


def test_phase030_malware_detection_and_quarantine(db_session):
    org_id = uuid4()
    user_id = uuid4()

    upload_svc = FileUploadSessionService(db_session)
    eicar_content = b"%PDF-1.7\nEICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    
    session = upload_svc.create_upload_session(
        organization_id=org_id,
        user_id=user_id,
        expected_filename="eicar_virus.pdf",
        expected_size_bytes=len(eicar_content),
        declared_mime_type="application/pdf",
    )

    with pytest.raises(FileMalwareDetectedError):
        upload_svc.finalize_upload_session(
            session_id=session.id,
            user_id=user_id,
            uploaded_content=eicar_content,
        )


def test_phase030_resource_association_and_evidence_custody(db_session):
    org_id = uuid4()
    user_id = uuid4()

    upload_svc = FileUploadSessionService(db_session)
    session = upload_svc.create_upload_session(
        organization_id=org_id,
        user_id=user_id,
        expected_filename="evidencia_verificacion.pdf",
        expected_size_bytes=256,
        declared_mime_type="application/pdf",
    )
    asset, _ = upload_svc.finalize_upload_session(
        session_id=session.id,
        user_id=user_id,
        uploaded_content=b"%PDF-1.7\n1 0 obj<<>>endobj\ntrailer<<>>startxref\n11\n%%EOF",
    )

    # Associate to Driver Document
    assoc_svc = FileAssociationService(db_session)
    assoc = assoc_svc.associate_file(
        file_id=asset.id,
        organization_id=org_id,
        user_id=user_id,
        resource_type="DRIVER_DOCUMENT",
        resource_id="DRV-DOC-101",
        association_type="EVIDENCE",
        is_primary=True,
    )
    assert assoc.resource_type == "DRIVER_DOCUMENT"
    assert assoc.status == "ACTIVE"

    # Register Evidence & Accept
    ev_svc = EvidenceCustodyService(db_session)
    evidence = ev_svc.register_evidence(
        organization_id=org_id,
        user_id=user_id,
        file_asset_id=asset.id,
        evidence_type="DOCUMENT",
        subject_type="DRIVER_DOCUMENT",
        subject_id="DRV-DOC-101",
    )
    assert evidence.acceptance_status == "PENDING"

    accepted_ev = ev_svc.accept_evidence(evidence.id, org_id, user_id)
    assert accepted_ev.acceptance_status == "ACCEPTED"

    events = ev_svc.get_custody_events(evidence.id, org_id)
    assert len(events) >= 2


def test_phase030_legal_hold_blocks_deletion(db_session):
    org_id = uuid4()
    user_id = uuid4()

    upload_svc = FileUploadSessionService(db_session)
    session = upload_svc.create_upload_session(
        organization_id=org_id,
        user_id=user_id,
        expected_filename="contrato_legal.pdf",
        expected_size_bytes=100,
        declared_mime_type="application/pdf",
    )
    asset, _ = upload_svc.finalize_upload_session(
        session_id=session.id,
        user_id=user_id,
        uploaded_content=b"%PDF-1.7\n1 0 obj<<>>endobj\ntrailer<<>>startxref\n11\n%%EOF",
    )

    ret_svc = RetentionLegalHoldService(db_session)
    hold = ret_svc.apply_legal_hold(
        file_id=asset.id,
        organization_id=org_id,
        user_id=user_id,
        reason="Litigio legal activo",
    )
    assert hold.status == "ACTIVE"

    with pytest.raises(FileLegalHoldActiveError):
        ret_svc.request_file_deletion(asset.id, org_id, user_id, "Eliminación solicitada")
