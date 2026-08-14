"""Application service managing the lifecycle of documents (Phase 020).

Handles drafts, issuance, previews, prints, reprints, and cancellations.
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Sequence
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.pdf_response import assert_pdf_bytes
from app.modules.logistics.documents.models import (
    DocumentInstanceModel,
    DocumentSnapshotModel,
    DocumentArtifactModel,
    DocumentReprintModel,
    DocumentCancellationModel,
    DocumentTypeModel,
    DocumentTypeVersionModel,
)
from app.modules.logistics.documents.rendering.template_models import (
    DocumentTemplateVersionModel,
)
from app.modules.logistics.documents.series.series_models import (
    DocumentSeriesModel,
    DocumentNumberModel,
)
from app.modules.logistics.documents.series.series_repository import (
    DocumentSeriesRepository,
    DocumentNumberRepository,
)
from app.modules.logistics.documents.infrastructure.storage import DocumentArtifactStorage
from app.modules.logistics.documents.rendering.rendering import (
    DocumentRenderCommand,
    DocumentRendererEngine,
    PdfRenderResult,
)
from app.modules.logistics.documents.codes.domain import DocumentCodeFormatter
from app.modules.logistics.documents.codes.code_repository import DocumentSiteCodeRepository

# Import logistics audit service
from app.modules.logistics.audit.service import audit_service, AuditEventCommand


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentServiceException(HTTPException):
    def __init__(self, status_code: int, error_code: str, detail: str) -> None:
        super().__init__(status_code=status_code, detail=f"[{error_code}] {detail}")


def stable_json_hash(payload: dict) -> tuple[str, str]:
    """Generates a stable, key-sorted JSON serialization and its SHA-256 hash."""
    serialized = json.dumps(payload, sort_keys=True, default=str)
    sha256_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return serialized, sha256_hash


class DocumentLifecycleService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.storage = DocumentArtifactStorage()
        self.renderer = DocumentRendererEngine()
        self.series_repo = DocumentSeriesRepository(db)
        self.number_repo = DocumentNumberRepository(db)
        self.site_repo = DocumentSiteCodeRepository(db)

    def _write_audit(
        self,
        event_code: str,
        actor_id: UUID | None,
        org_id: UUID,
        branch_id: UUID,
        warehouse_id: UUID | None,
        doc_id: UUID | None = None,
        doc_code: str | None = None,
        reason: str | None = None,
        metadata: dict | None = None,
        previous_data: dict | None = None,
        new_data: dict | None = None,
    ) -> None:
        """Helper to write audit events."""
        cmd = AuditEventCommand(
            event_code=event_code,
            actor_user_id=actor_id,
            severity="info",
            organization_id=org_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            resource_type="document_instance" if doc_id else None,
            resource_id=str(doc_id) if doc_id else None,
            resource_code=doc_code,
            reason_text=reason,
            previous_data=previous_data,
            new_data=new_data,
            metadata=metadata,
            source_module="logistics",
            source_service="DocumentLifecycleService",
        )
        audit_service.write_event(self.db, cmd)

    def create_draft(
        self,
        organization_id: UUID,
        branch_id: UUID,
        warehouse_id: UUID | None,
        doc_type_code: str,
        source_resource_type: str,
        source_resource_id: UUID | None,
        source_operation_id: UUID | None,
        title: str,
        structured_data: dict[str, Any],
        sensitivity: str,
        actor_id: UUID | None,
    ) -> DocumentInstanceModel:
        """Creates a document draft (Phase 020)."""
        # Validate Document Type
        dt = self.db.scalars(
            select(DocumentTypeModel).where(DocumentTypeModel.code == doc_type_code.upper())
        ).first()
        if not dt:
            raise DocumentServiceException(404, "DOCUMENT_TYPE_NOT_FOUND", f"Tipo documental {doc_type_code} no existe.")

        # Find active type version
        dt_version = self.db.scalars(
            select(DocumentTypeVersionModel)
            .where(
                and_(
                    DocumentTypeVersionModel.document_type_id == dt.id,
                    DocumentTypeVersionModel.status == "ACTIVE"
                )
            )
            .order_by(DocumentTypeVersionModel.created_at.desc())
        ).first()

        inst = DocumentInstanceModel(
            organization_id=organization_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            document_type_id=dt.id,
            document_type_version_id=dt_version.id if dt_version else None,
            source_resource_type=source_resource_type,
            source_resource_id=source_resource_id,
            source_operation_id=source_operation_id,
            title=title,
            status="DRAFT",
            lifecycle_status="DRAFT",
            sensitivity=sensitivity,
            created_by=actor_id,
        )
        self.db.add(inst)
        self.db.flush()

        # Save initial draft snapshot if structured_data is present
        clean_payload = json.loads(json.dumps(structured_data, default=str))
        _, payload_hash = stable_json_hash(clean_payload)
        snap = DocumentSnapshotModel(
            document_id=inst.id,
            snapshot_version=1,
            snapshot_type="ISSUANCE",
            snapshot_schema_version=dt_version.schema_version if dt_version else "1.0.0",
            canonical_payload=clean_payload,
            canonical_payload_hash=payload_hash,
            document_type_code=dt.code,
            document_type_version=dt_version.version if dt_version else "1.0.0",
            catalog_version="1.0.0",
            template_key=dt_version.template_key if dt_version else "PENDING_PHASE_014",
            template_version=(
                dt_version.template_version
                if dt_version and dt_version.template_version
                else "1.0.0"
            ),
            organization_snapshot={"id": str(organization_id)},
            branch_snapshot={"id": str(branch_id)},
            warehouse_snapshot={"id": str(warehouse_id)} if warehouse_id else None,
            created_by=actor_id,
        )
        self.db.add(snap)
        self.db.flush()

        inst.current_snapshot_id = snap.id
        self.db.flush()

        self._write_audit(
            "logistics.document.draft_created",
            actor_id,
            organization_id,
            branch_id,
            warehouse_id,
            inst.id,
            new_data={"title": title, "document_type_code": doc_type_code},
        )
        return inst

    def update_draft(
        self,
        document_id: UUID,
        title: str | None,
        structured_data: dict[str, Any] | None,
        warehouse_id: UUID | None,
        sensitivity: str | None,
        actor_id: UUID | None,
    ) -> DocumentInstanceModel:
        """Updates a document draft's information (Phase 020)."""
        inst = self.db.get(DocumentInstanceModel, document_id)
        if not inst:
            raise DocumentServiceException(404, "DOCUMENT_DRAFT_NOT_FOUND", "Borrador de documento no encontrado.")
        if inst.status != "DRAFT":
            raise DocumentServiceException(400, "DOCUMENT_ALREADY_ISSUED", "El documento ya fue emitido y no se puede modificar.")

        if title is not None:
            inst.title = title
        if warehouse_id is not None:
            inst.warehouse_id = warehouse_id
        if sensitivity is not None:
            inst.sensitivity = sensitivity

        if structured_data is not None:
            # Query last snapshot to update or create a new one
            last_snap = self.db.get(DocumentSnapshotModel, inst.current_snapshot_id) if inst.current_snapshot_id else None
            clean_payload = json.loads(json.dumps(structured_data, default=str))
            _, payload_hash = stable_json_hash(clean_payload)

            if last_snap:
                last_snap.canonical_payload = clean_payload
                last_snap.canonical_payload_hash = payload_hash
            else:
                dt_version = self.db.get(DocumentTypeVersionModel, inst.document_type_version_id)
                dt = self.db.get(DocumentTypeModel, inst.document_type_id)
                snap = DocumentSnapshotModel(
                    document_id=inst.id,
                    snapshot_version=1,
                    snapshot_type="ISSUANCE",
                    snapshot_schema_version=dt_version.schema_version if dt_version else "1.0.0",
                    canonical_payload=clean_payload,
                    canonical_payload_hash=payload_hash,
                    document_type_code=dt.code if dt else "UNKNOWN",
                    document_type_version=dt_version.version if dt_version else "1.0.0",
                    catalog_version="1.0.0",
                    template_key=dt_version.template_key if dt_version else "PENDING_PHASE_014",
                    template_version=(
                        dt_version.template_version
                        if dt_version and dt_version.template_version
                        else "1.0.0"
                    ),
                    organization_snapshot={"id": str(inst.organization_id)},
                    branch_snapshot={"id": str(inst.branch_id)},
                    warehouse_snapshot={"id": str(inst.warehouse_id)} if inst.warehouse_id else None,
                    created_by=actor_id,
                )
                self.db.add(snap)
                self.db.flush()
                inst.current_snapshot_id = snap.id

        inst.updated_at = utc_now()
        self.db.flush()

        self._write_audit(
            "logistics.document.draft_updated",
            actor_id,
            inst.organization_id,
            inst.branch_id,
            inst.warehouse_id,
            inst.id,
        )
        return inst

    def get_document(self, document_id: UUID) -> DocumentInstanceModel:
        inst = self.db.get(DocumentInstanceModel, document_id)
        if not inst:
            raise DocumentServiceException(404, "DOCUMENT_NOT_FOUND", "Documento no encontrado.")
        return inst

    def get_downloadable_pdf(
        self,
        document_id: UUID,
        actor_id: UUID | None,
        *,
        original: bool = False,
    ) -> tuple[DocumentInstanceModel, DocumentArtifactModel, bytes]:
        """Resolve an issued PDF artifact, load it and record the download audit."""
        inst = self.get_document(document_id)
        if inst.status not in ("ISSUED", "CANCELLED"):
            raise DocumentServiceException(
                400,
                "DOCUMENT_NOT_ISSUED",
                "El documento no ha sido emitido.",
            )

        artifact_type = "ISSUED_PDF"
        if inst.status == "CANCELLED" and not original:
            artifact_type = "CANCELLED_PDF"

        artifact = self.db.scalars(
            select(DocumentArtifactModel).where(
                and_(
                    DocumentArtifactModel.document_id == inst.id,
                    DocumentArtifactModel.artifact_type == artifact_type,
                )
            )
        ).first()
        if artifact is None and inst.authoritative_artifact_id:
            artifact = self.db.get(
                DocumentArtifactModel, inst.authoritative_artifact_id
            )
        if artifact is None:
            raise DocumentServiceException(
                404,
                "DOCUMENT_PDF_NOT_FOUND",
                "El archivo PDF del documento no se encuentra disponible.",
            )

        # Validate before auditing: a stored artifact that is empty, truncated or
        # not a PDF must raise here rather than be recorded as a successful
        # download that the caller then fails to deliver.
        pdf_bytes = assert_pdf_bytes(self.storage.get(artifact.storage_key))
        self._write_audit(
            "logistics.document.downloaded",
            actor_id,
            inst.organization_id,
            inst.branch_id,
            inst.warehouse_id,
            inst.id,
            inst.document_code,
        )
        return inst, artifact, pdf_bytes

    def preview_document(
        self,
        document_id: UUID,
        actor_id: UUID | None,
    ) -> tuple[bytes, str]:
        """Generates a preview PDF without emitting/numbering (Phase 020)."""
        inst = self.get_document(document_id)
        
        # If already issued, return the authoritative artifact directly
        if inst.status == "ISSUED" and inst.authoritative_artifact_id:
            art = self.db.get(DocumentArtifactModel, inst.authoritative_artifact_id)
            if art:
                return self.storage.get(art.storage_key), art.filename

        # If cancelled, return the cancelled artifact
        if inst.status == "CANCELLED":
            # Find the cancelled PDF artifact
            art = self.db.scalars(
                select(DocumentArtifactModel)
                .where(
                    and_(
                        DocumentArtifactModel.document_id == inst.id,
                        DocumentArtifactModel.artifact_type == "CANCELLED_PDF"
                    )
                )
            ).first()
            if art:
                return self.storage.get(art.storage_key), art.filename

        # For drafts or other statuses, render preview dynamically from last snapshot
        if not inst.current_snapshot_id:
            raise DocumentServiceException(400, "DOCUMENT_NOT_READY_TO_ISSUE", "El borrador no tiene datos estructurados.")

        snap = self.db.get(DocumentSnapshotModel, inst.current_snapshot_id)
        dt = self.db.get(DocumentTypeModel, inst.document_type_id)

        # Resolve organization/branch names
        from app.models.organization import Organization
        from app.models.branch import Branch
        org = self.db.get(Organization, inst.organization_id)
        br = self.db.get(Branch, inst.branch_id)

        header_data: dict[str, Any] = {}
        signature_data: dict[str, Any] = {}
        try:
            from app.modules.logistics.company_profile.models import (
                OrganizationProfileModel,
                OrganizationAddressModel,
                OrganizationContactModel,
                OrganizationAssetModel,
                AuthorizedSignerModel,
            )
            prof = self.db.scalars(
                select(OrganizationProfileModel).where(OrganizationProfileModel.organization_id == inst.organization_id)
            ).first()
            if prof:
                header_data["legal_name"] = prof.legal_name
                header_data["trade_name"] = prof.trade_name
                header_data["ruc"] = prof.tax_id

            addr = self.db.scalars(
                select(OrganizationAddressModel).where(
                    and_(
                        OrganizationAddressModel.organization_id == inst.organization_id,
                        OrganizationAddressModel.is_fiscal_address.is_(True),
                    )
                )
            ).first() or self.db.scalars(
                select(OrganizationAddressModel).where(OrganizationAddressModel.organization_id == inst.organization_id)
            ).first()
            if addr:
                header_data["fiscal_address"] = f"{addr.address_line1}, {addr.district or ''}, {addr.city or ''}".strip(", ")

            contact_email = self.db.scalars(
                select(OrganizationContactModel).where(
                    and_(
                        OrganizationContactModel.organization_id == inst.organization_id,
                        OrganizationContactModel.contact_type == "EMAIL",
                    )
                )
            ).first()
            if contact_email:
                header_data["email"] = contact_email.value

            contact_phone = self.db.scalars(
                select(OrganizationContactModel).where(
                    and_(
                        OrganizationContactModel.organization_id == inst.organization_id,
                        OrganizationContactModel.contact_type == "PHONE",
                    )
                )
            ).first()
            if contact_phone:
                header_data["phone"] = contact_phone.value

            logo_asset = self.db.scalars(
                select(OrganizationAssetModel).where(
                    and_(
                        OrganizationAssetModel.organization_id == inst.organization_id,
                        OrganizationAssetModel.asset_type.in_(["LOGO", "BRANDING"]),
                    )
                )
            ).first()
            if logo_asset and logo_asset.file_bytes:
                header_data["logo_bytes"] = logo_asset.file_bytes

            if snap.canonical_payload and isinstance(snap.canonical_payload, dict):
                rs = snap.canonical_payload.get("resolved_signer")
                if isinstance(rs, dict):
                    full_name = f"{rs.get('first_name', '')} {rs.get('last_name', '')}".strip()
                    if full_name:
                        signature_data["signer_name"] = full_name
                    if rs.get("job_title"):
                        signature_data["signer_role"] = rs.get("job_title")
                    if rs.get("identity_document_number"):
                        signature_data["signer_dni"] = rs.get("identity_document_number")

            if not signature_data.get("signer_name"):
                signer = self.db.scalars(
                    select(AuthorizedSignerModel).where(
                        and_(
                            AuthorizedSignerModel.organization_id == inst.organization_id,
                            AuthorizedSignerModel.status == "ACTIVE",
                        )
                    ).order_by(AuthorizedSignerModel.created_at.desc())
                ).first()
                if signer:
                    signature_data["signer_name"] = f"{signer.first_name} {signer.last_name}"
                    signature_data["signer_role"] = signer.job_title
                    signature_data["signer_dni"] = signer.identity_document_number
        except Exception:
            pass

        if br:
            header_data["branch_name"] = br.name

        cmd = DocumentRenderCommand(
            document_type_code=dt.code if dt else "UNKNOWN",
            template_key=snap.template_key,
            template_version=snap.template_version,
            catalog_version=snap.catalog_version,
            code_standard_version=snap.code_standard_version,
            document_code=f"PREV-{dt.code if dt else 'DOC'}-2026-000142",
            document_status="PREVIEW",
            document_title=inst.title,
            organization_name=org.name if org else "PROYECTO T1 LOGÍSTICA S.A.C.",
            branch_name=br.name if br else "SEDE PRINCIPAL",
            document_data=snap.canonical_payload or {},
            header_data=header_data,
            signature_data=signature_data,
            watermark_text="VISTA PREVIA",
            preview_mode=True,
            requested_by=str(actor_id) if actor_id else None,
        )

        res = self.renderer.render_pdf(cmd)
        
        self._write_audit(
            "logistics.document.preview_rendered",
            actor_id,
            inst.organization_id,
            inst.branch_id,
            inst.warehouse_id,
            inst.id,
        )
        return res.pdf_bytes, f"PREVIEW_{dt.code}_{inst.id}.pdf"

    def issue_document(
        self,
        document_id: UUID,
        idempotency_key: str | None,
        actor_id: UUID | None,
    ) -> DocumentInstanceModel:
        """Atomically emits the document with unique code and snapshot (Phase 020)."""
        # Block row level lock to prevent concurrent emission
        inst = self.db.scalars(
            select(DocumentInstanceModel)
            .where(DocumentInstanceModel.id == document_id)
            .with_for_update()
        ).first()

        if not inst:
            raise DocumentServiceException(404, "DOCUMENT_NOT_FOUND", "Documento no encontrado.")

        if inst.status == "ISSUED":
            # Idempotency check: if it is already issued, verify if we used the same idempotency key
            if idempotency_key:
                # Find the number associated with this issuance
                num = self.db.get(DocumentNumberModel, inst.document_number_id)
                if num and num.idempotency_key == idempotency_key:
                    return inst
                else:
                    raise DocumentServiceException(409, "DOCUMENT_ALREADY_ISSUED", "El documento ya fue emitido.")
            else:
                raise DocumentServiceException(409, "DOCUMENT_ALREADY_ISSUED", "El documento ya fue emitido.")

        if inst.status != "DRAFT":
            raise DocumentServiceException(400, "DOCUMENT_NOT_READY_TO_ISSUE", f"Estado {inst.status} no es válido para emisión.")

        if not inst.current_snapshot_id:
            raise DocumentServiceException(400, "DOCUMENT_NOT_READY_TO_ISSUE", "El borrador no tiene datos estructurados.")

        snap = self.db.get(DocumentSnapshotModel, inst.current_snapshot_id)
        dt = self.db.get(DocumentTypeModel, inst.document_type_id)

        # 1. Resolve Document Series
        # Get primary site code for this branch
        site_code_obj = self.site_repo.get_primary_by_branch(inst.branch_id)
        site_id = site_code_obj.id if site_code_obj else inst.branch_id
        current_year = utc_now().year

        series = self.db.scalars(
            select(DocumentSeriesModel)
            .where(
                and_(
                    DocumentSeriesModel.organization_id == inst.organization_id,
                    DocumentSeriesModel.document_type_id == dt.id,
                    DocumentSeriesModel.document_site_code_id == site_id,
                    DocumentSeriesModel.document_year == current_year,
                    DocumentSeriesModel.status == "ACTIVE"
                )
            )
            .with_for_update()
        ).first()

        if not series:
            raise DocumentServiceException(
                400,
                "DOCUMENT_ISSUE_CONFLICT",
                f"No hay serie activa para el tipo {dt.code} en el año {current_year}."
            )

        # 2. Reserve next number
        if series.next_sequence > series.sequence_max:
            raise DocumentServiceException(409, "DOCUMENT_ISSUE_FAILED", "Serie de correlativos agotada.")

        seq_num = series.next_sequence
        series.next_sequence += 1
        self.db.add(series)

        site_code = site_code_obj.code if site_code_obj else "LIM"
        full_code = DocumentCodeFormatter.format(dt.code, site_code, current_year, seq_num)

        # Create DocumentNumberModel
        num_obj = DocumentNumberModel(
            organization_id=inst.organization_id,
            series_id=series.id,
            sequence_number=seq_num,
            full_document_code=full_code,
            status="ISSUED",
            reservation_type="INDIVIDUAL",
            reservation_purpose=f"Emisión de {inst.title}",
            reserved_by=actor_id,
            assigned_resource_type=inst.source_resource_type,
            assigned_resource_id=inst.source_resource_id,
            assigned_at=utc_now(),
            issued_at=utc_now(),
            idempotency_key=idempotency_key,
        )
        self.db.add(num_obj)
        self.db.flush()

        # Update snapshot metadata
        c_payload = dict(snap.canonical_payload)
        c_payload["document_code"] = full_code
        c_payload["issued_at"] = utc_now().isoformat()
        c_payload["sequence_number"] = seq_num
        clean_payload = json.loads(json.dumps(c_payload, default=str))
        _, payload_hash = stable_json_hash(clean_payload)
        snap.canonical_payload = clean_payload
        snap.canonical_payload_hash = payload_hash
        self.db.add(snap)

        # 3. Render PDF
        from app.models.organization import Organization
        from app.models.branch import Branch
        org = self.db.get(Organization, inst.organization_id)
        br = self.db.get(Branch, inst.branch_id)

        # Calculate QR verification code / url
        qr_verification_url = f"{settings.FRONTEND_URL}/verify/{full_code}"

        cmd = DocumentRenderCommand(
            document_type_code=dt.code,
            template_key=snap.template_key,
            template_version=snap.template_version,
            catalog_version=snap.catalog_version,
            code_standard_version=snap.code_standard_version,
            document_code=full_code,
            document_status="ISSUED",
            document_title=inst.title,
            organization_name=org.name if org else "PROYECTO T1 LOGÍSTICA",
            branch_name=br.name if br else "SEDE PRINCIPAL",
            document_data=snap.canonical_payload,
            qr_data=qr_verification_url,
            watermark_text=None,
            preview_mode=False,
            requested_by=str(actor_id) if actor_id else None,
        )

        try:
            res = self.renderer.render_pdf(cmd)
        except Exception as e:
            raise DocumentServiceException(500, "DOCUMENT_ISSUE_FAILED", f"Fallo al renderizar el documento PDF: {str(e)}")

        file_hash = hashlib.sha256(res.pdf_bytes).hexdigest()
        filename = f"{dt.code}_{full_code}.pdf"
        storage_key = f"documents/{inst.organization_id}/{current_year}/{inst.id}/issued/{filename}"

        # 4. Save to Storage
        self.storage.put(storage_key, res.pdf_bytes)

        # Create DocumentArtifactModel
        art = DocumentArtifactModel(
            document_id=inst.id,
            snapshot_id=snap.id,
            artifact_type="ISSUED_PDF",
            representation_status="ACTIVE",
            mime_type="application/pdf",
            filename=filename,
            storage_provider=settings.STORAGE_PROVIDER,
            storage_key=storage_key,
            size_bytes=len(res.pdf_bytes),
            file_hash=file_hash,
            content_hash=payload_hash,
            template_version=snap.template_version,
            renderer_version=res.renderer_version,
            generated_by=actor_id,
            is_authoritative=True,
            is_sensitive=dt.is_sensitive,
        )
        self.db.add(art)
        self.db.flush()

        # Update instance properties
        inst.document_number_id = num_obj.id
        inst.document_code = full_code
        inst.status = "ISSUED"
        inst.lifecycle_status = "ISSUED"
        inst.authoritative_artifact_id = art.id
        inst.issued_at = utc_now()
        inst.issued_by = actor_id
        inst.updated_at = utc_now()
        self.db.add(inst)
        self.db.flush()

        self._write_audit(
            "logistics.document.snapshot_created",
            actor_id,
            inst.organization_id,
            inst.branch_id,
            inst.warehouse_id,
            inst.id,
            doc_code=full_code,
        )
        self._write_audit(
            "logistics.document.artifact_created",
            actor_id,
            inst.organization_id,
            inst.branch_id,
            inst.warehouse_id,
            inst.id,
            doc_code=full_code,
            metadata={"artifact_id": str(art.id)},
        )
        self._write_audit(
            "logistics.document.issued",
            actor_id,
            inst.organization_id,
            inst.branch_id,
            inst.warehouse_id,
            inst.id,
            doc_code=full_code,
        )

        return inst

    def register_print_intent(
        self,
        document_id: UUID,
        actor_id: UUID | None,
        reason: str | None = None,
        client_context: dict | None = None,
    ) -> None:
        """Registers a print intent (Phase 020)."""
        inst = self.get_document(document_id)
        inst.print_request_count += 1
        self.db.add(inst)
        self.db.flush()

        self._write_audit(
            "logistics.document.print_requested",
            actor_id,
            inst.organization_id,
            inst.branch_id,
            inst.warehouse_id,
            inst.id,
            doc_code=inst.document_code,
            reason=reason,
            metadata=client_context,
        )

    def reprint_document(
        self,
        document_id: UUID,
        reason: str,
        actor_id: UUID | None,
        idempotency_key: str | None = None,
    ) -> DocumentReprintModel:
        """Re-issues a physical-copy reprint of an issued document from its snapshot (Phase 020)."""
        inst = self.get_document(document_id)
        if inst.status not in ("ISSUED", "CANCELLED"):
            raise DocumentServiceException(400, "DOCUMENT_CANNOT_BE_REPRINTED", "Solo se pueden reimprimir documentos vigentes o anulados.")

        if not reason.strip():
            raise DocumentServiceException(400, "DOCUMENT_REPRINT_REASON_REQUIRED", "El motivo de reimpresión es obligatorio.")

        # Concurrency / Idempotency control
        # If idempotency_key is present, check if reprint already exists for this idempotency key
        idem_hash = hashlib.sha256(idempotency_key.encode()).hexdigest() if idempotency_key else None
        if idem_hash:
            existing = self.db.scalars(
                select(DocumentReprintModel)
                .where(
                    and_(
                        DocumentReprintModel.document_id == inst.id,
                        DocumentReprintModel.idempotency_key_hash == idem_hash
                    )
                )
            ).first()
            if existing:
                return existing

        inst.reprint_count += 1
        copy_num = inst.reprint_count
        self.db.add(inst)

        # Get the original issuance snapshot
        snap = self.db.scalars(
            select(DocumentSnapshotModel)
            .where(
                and_(
                    DocumentSnapshotModel.document_id == inst.id,
                    DocumentSnapshotModel.snapshot_version == 1
                )
            )
        ).first()

        if not snap:
            raise DocumentServiceException(500, "DOCUMENT_SNAPSHOT_MISSING", "Falta el snapshot de emisión original.")

        # Retrieve the original issued artifact to serve as source
        orig_art = self.db.get(DocumentArtifactModel, inst.authoritative_artifact_id)
        if not orig_art:
            raise DocumentServiceException(500, "DOCUMENT_ARTIFACT_MISSING", "Falta el PDF autoritativo original.")

        # Render reprint copy with watermark
        from app.models.organization import Organization
        from app.models.branch import Branch
        org = self.db.get(Organization, inst.organization_id)
        br = self.db.get(Branch, inst.branch_id)

        dt = self.db.get(DocumentTypeModel, inst.document_type_id)

        # In case the document is cancelled, it must keep the ANULADO water mark as well as reprint
        watermark = f"REIMPRESIÓN - COPIA N° {copy_num}"
        if inst.status == "CANCELLED":
            watermark = f"REIMPRESIÓN ANULADA - COPIA N° {copy_num}"

        cmd = DocumentRenderCommand(
            document_type_code=dt.code if dt else "UNKNOWN",
            template_key=snap.template_key,
            template_version=snap.template_version,
            catalog_version=snap.catalog_version,
            code_standard_version=snap.code_standard_version,
            document_code=inst.document_code,
            document_status="REPRINT",
            document_title=inst.title,
            organization_name=org.name if org else "PROYECTO T1 LOGÍSTICA",
            branch_name=br.name if br else "SEDE PRINCIPAL",
            document_data=snap.canonical_payload,
            watermark_text=watermark,
            preview_mode=False,
            requested_by=str(actor_id) if actor_id else None,
        )

        res = self.renderer.render_pdf(cmd)
        file_hash = hashlib.sha256(res.pdf_bytes).hexdigest()
        filename = f"REPRINT_C{copy_num}_{dt.code}_{inst.document_code}.pdf"
        storage_key = f"documents/{inst.organization_id}/{inst.created_at.year}/{inst.id}/reprints/{filename}"

        # Save reprint copy PDF to storage
        self.storage.put(storage_key, res.pdf_bytes)

        # Create new artifact
        rep_art = DocumentArtifactModel(
            document_id=inst.id,
            snapshot_id=snap.id,
            artifact_type="REPRINT_PDF",
            representation_status="ACTIVE",
            mime_type="application/pdf",
            filename=filename,
            storage_provider=settings.STORAGE_PROVIDER,
            storage_key=storage_key,
            size_bytes=len(res.pdf_bytes),
            file_hash=file_hash,
            content_hash=snap.canonical_payload_hash,
            template_version=snap.template_version,
            renderer_version=res.renderer_version,
            copy_number=copy_num,
            generated_by=actor_id,
            is_authoritative=False,
            is_sensitive=orig_art.is_sensitive,
        )
        self.db.add(rep_art)
        self.db.flush()

        reprint_rec = DocumentReprintModel(
            document_id=inst.id,
            snapshot_id=snap.id,
            source_artifact_id=orig_art.id,
            generated_artifact_id=rep_art.id,
            copy_number=copy_num,
            reason=reason,
            requested_by=actor_id or inst.organization_id,
            requested_at=utc_now(),
            idempotency_key_hash=idem_hash or f"NO_KEY_{uuid4()}",
        )
        self.db.add(reprint_rec)
        self.db.flush()

        self._write_audit(
            "logistics.document.reprinted",
            actor_id,
            inst.organization_id,
            inst.branch_id,
            inst.warehouse_id,
            inst.id,
            doc_code=inst.document_code,
            reason=reason,
            metadata={"copy_number": copy_num, "reprint_id": str(reprint_rec.id)},
        )

        return reprint_rec

    def cancel_document(
        self,
        document_id: UUID,
        reason: str,
        actor_id: UUID | None,
        idempotency_key: str | None = None,
    ) -> DocumentCancellationModel:
        """Annulls/cancels an issued document without reusing its correlative number (Phase 020)."""
        inst = self.db.scalars(
            select(DocumentInstanceModel)
            .where(DocumentInstanceModel.id == document_id)
            .with_for_update()
        ).first()

        if not inst:
            raise DocumentServiceException(404, "DOCUMENT_NOT_FOUND", "Documento no encontrado.")

        if inst.status == "CANCELLED":
            # Idempotency check: if it is already cancelled, verify if we used the same idempotency key
            idem_hash = hashlib.sha256(idempotency_key.encode()).hexdigest() if idempotency_key else None
            existing = self.db.scalars(
                select(DocumentCancellationModel)
                .where(DocumentCancellationModel.document_id == inst.id)
            ).first()
            if existing and idempotency_key and existing.idempotency_key_hash == idem_hash:
                return existing
            raise DocumentServiceException(400, "DOCUMENT_ALREADY_CANCELLED", "El documento ya se encuentra anulado.")

        if inst.status != "ISSUED":
            raise DocumentServiceException(400, "DOCUMENT_CANNOT_BE_CANCELLED", f"El documento no puede ser anulado desde el estado {inst.status}.")

        if not reason.strip():
            raise DocumentServiceException(400, "DOCUMENT_CANCELLATION_REASON_REQUIRED", "El motivo de la anulación es obligatorio.")

        # Find original snapshot
        snap = self.db.scalars(
            select(DocumentSnapshotModel)
            .where(
                and_(
                    DocumentSnapshotModel.document_id == inst.id,
                    DocumentSnapshotModel.snapshot_version == 1
                )
            )
        ).first()
        if not snap:
            raise DocumentServiceException(500, "DOCUMENT_SNAPSHOT_MISSING", "Falta el snapshot de emisión original.")

        orig_art = self.db.get(DocumentArtifactModel, inst.authoritative_artifact_id)
        if not orig_art:
            raise DocumentServiceException(500, "DOCUMENT_ARTIFACT_MISSING", "Falta el PDF autoritativo original.")

        # Render Cancelled PDF
        from app.models.organization import Organization
        from app.models.branch import Branch
        org = self.db.get(Organization, inst.organization_id)
        br = self.db.get(Branch, inst.branch_id)
        dt = self.db.get(DocumentTypeModel, inst.document_type_id)

        # Update status
        inst.status = "CANCELLED"
        inst.lifecycle_status = "CANCELLED"
        inst.cancelled_at = utc_now()
        inst.cancelled_by = actor_id
        inst.cancellation_reason = reason
        self.db.add(inst)

        # Create cancellation snapshot (version 2)
        cxl_payload = dict(snap.canonical_payload)
        cxl_payload["cancelled_at"] = utc_now().isoformat()
        cxl_payload["cancellation_reason"] = reason
        _, cxl_hash = stable_json_hash(cxl_payload)

        cxl_snap = DocumentSnapshotModel(
            document_id=inst.id,
            snapshot_version=2,
            snapshot_type="REPLACEMENT",
            snapshot_schema_version=snap.snapshot_schema_version,
            canonical_payload=cxl_payload,
            canonical_payload_hash=cxl_hash,
            document_type_code=snap.document_type_code,
            document_type_version=snap.document_type_version,
            catalog_version=snap.catalog_version,
            template_key=snap.template_key,
            template_version=snap.template_version,
            organization_snapshot=snap.organization_snapshot,
            branch_snapshot=snap.branch_snapshot,
            warehouse_snapshot=snap.warehouse_snapshot,
            created_by=actor_id,
        )
        self.db.add(cxl_snap)
        self.db.flush()

        cmd = DocumentRenderCommand(
            document_type_code=dt.code if dt else "UNKNOWN",
            template_key=snap.template_key,
            template_version=snap.template_version,
            catalog_version=snap.catalog_version,
            code_standard_version=snap.code_standard_version,
            document_code=inst.document_code,
            document_status="CANCELLED",
            document_title=inst.title,
            organization_name=org.name if org else "PROYECTO T1 LOGÍSTICA",
            branch_name=br.name if br else "SEDE PRINCIPAL",
            document_data=cxl_payload,
            watermark_text="ANULADO",
            preview_mode=False,
            requested_by=str(actor_id) if actor_id else None,
        )

        res = self.renderer.render_pdf(cmd)
        file_hash = hashlib.sha256(res.pdf_bytes).hexdigest()
        filename = f"CANCELLED_{dt.code}_{inst.document_code}.pdf"
        storage_key = f"documents/{inst.organization_id}/{inst.created_at.year}/{inst.id}/cancelled/{filename}"

        # Save cancelled PDF to storage
        self.storage.put(storage_key, res.pdf_bytes)

        # Create Cancelled Artifact
        cxl_art = DocumentArtifactModel(
            document_id=inst.id,
            snapshot_id=cxl_snap.id,
            artifact_type="CANCELLED_PDF",
            representation_status="ACTIVE",
            mime_type="application/pdf",
            filename=filename,
            storage_provider=settings.STORAGE_PROVIDER,
            storage_key=storage_key,
            size_bytes=len(res.pdf_bytes),
            file_hash=file_hash,
            content_hash=cxl_hash,
            template_version=snap.template_version,
            renderer_version=res.renderer_version,
            generated_by=actor_id,
            is_authoritative=True,
            is_sensitive=orig_art.is_sensitive,
        )
        self.db.add(cxl_art)
        self.db.flush()

        # Update DocumentNumber status to CANCELLED
        if inst.document_number_id:
            num = self.db.scalars(
                select(DocumentNumberModel)
                .where(DocumentNumberModel.id == inst.document_number_id)
                .with_for_update()
            ).first()
            if num:
                num.status = "CANCELLED"
                num.cancelled_at = utc_now()
                num.cancelled_by = actor_id
                num.cancellation_reason = reason
                self.db.add(num)

        # Create cancellation audit record
        idem_hash = hashlib.sha256(idempotency_key.encode()).hexdigest() if idempotency_key else None
        cxl_rec = DocumentCancellationModel(
            document_id=inst.id,
            snapshot_id=cxl_snap.id,
            issued_artifact_id=orig_art.id,
            cancelled_artifact_id=cxl_art.id,
            reason=reason,
            cancelled_by=actor_id or inst.organization_id,
            cancelled_at=utc_now(),
            idempotency_key_hash=idem_hash or f"NO_KEY_{uuid4()}",
        )
        self.db.add(cxl_rec)
        self.db.flush()

        self._write_audit(
            "logistics.document.cancelled",
            actor_id,
            inst.organization_id,
            inst.branch_id,
            inst.warehouse_id,
            inst.id,
            doc_code=inst.document_code,
            reason=reason,
            metadata={"cancellation_id": str(cxl_rec.id)},
        )

        return cxl_rec

    def get_history(self, document_id: UUID) -> list[dict]:
        """Compiles a complete audit history lifecycle timeline for a document."""
        inst = self.get_document(document_id)

        # Fetch audit events relating to this document
        # Let's search database table `logistics_audit_events`
        from app.modules.logistics.audit.models_event import LogisticsAuditEvent
        events = list(self.db.scalars(
            select(LogisticsAuditEvent)
            .where(
                and_(
                    LogisticsAuditEvent.resource_type == "document_instance",
                    LogisticsAuditEvent.resource_id == str(document_id)
                )
            )
            .order_by(LogisticsAuditEvent.occurred_at.asc())
        ))

        # Format events into timeline items
        history = []
        for ev in events:
            # Safely resolve actor name
            actor_name = ev.actor_display_name_snapshot
            if not actor_name and ev.actor_user_id:
                from app.models.user import User
                user = self.db.get(User, ev.actor_user_id)
                actor_name = user.full_name if user else "Usuario Logístico"

            history.append({
                "event_type": ev.event_code,
                "timestamp": ev.occurred_at,
                "actor_user_id": ev.actor_user_id,
                "actor_name": actor_name,
                "reason": ev.reason_text,
                "details": ev.metadata_ or {},
            })

        return history
