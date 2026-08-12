"""Application service for document exports, ZIP compilation, and talonario renderers (Phase 020).

Orchestrates bulk download jobs and packages.
"""

from __future__ import annotations

import csv
import io
import os
import zipfile
import json
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.logistics.documents.models import (
    DocumentInstanceModel,
    DocumentSnapshotModel,
    DocumentArtifactModel,
    DocumentExportJobModel,
    DocumentTypeModel,
)
from app.modules.logistics.documents.series.series_models import (
    DocumentTalonarioModel,
    DocumentNumberModel,
)
from app.modules.logistics.documents.infrastructure.storage import DocumentArtifactStorage
from app.modules.logistics.documents.rendering.rendering import (
    DocumentRenderCommand,
    DocumentRendererEngine,
)

# Constants & limits
DOCUMENT_EXPORT_MAX_ITEMS = 100
DOCUMENT_EXPORT_MAX_TOTAL_MB = 100.0
DOCUMENT_EXPORT_EXPIRATION_HOURS = 24


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExportServiceException(HTTPException):
    def __init__(self, status_code: int, error_code: str, detail: str) -> None:
        super().__init__(status_code=status_code, detail=f"[{error_code}] {detail}")


class DocumentExportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.storage = DocumentArtifactStorage()
        self.renderer = DocumentRendererEngine()

    def generate_talonario_pdf(
        self,
        talonario_id: UUID,
        actor_id: UUID | None,
    ) -> tuple[bytes, str]:
        """Generates a multi-page PDF representation of reserved numbers in a talonario (Phase 020)."""
        tal = self.db.get(DocumentTalonarioModel, talonario_id)
        if not tal:
            raise ExportServiceException(404, "DOCUMENT_TALONARIO_NOT_FOUND", "Talonario no encontrado.")

        # Find series
        from app.modules.logistics.documents.series.series_models import DocumentSeriesModel
        series = self.db.get(DocumentSeriesModel, tal.series_id)
        if not series:
            raise ExportServiceException(404, "DOCUMENT_SERIES_NOT_FOUND", "Serie asociada no encontrada.")

        # Find all numbers in the talonario
        numbers = list(self.db.scalars(
            select(DocumentNumberModel)
            .where(DocumentNumberModel.talonario_id == tal.id)
            .order_by(DocumentNumberModel.sequence_number.asc())
        ))

        # Check maximum pages limit
        if len(numbers) > 100:
            raise ExportServiceException(400, "DOCUMENT_TALONARIO_MAX_PAGES", "El talonario excede el límite máximo de 100 páginas.")

        # Render portadas / talonario context using central renderer
        dt = self.db.get(DocumentTypeModel, series.document_type_id)

        # Resolve organization/branch names
        from app.models.organization import Organization
        from app.models.branch import Branch
        org = self.db.get(Organization, tal.organization_id)
        br = self.db.get(Branch, series.branch_id)

        # Build payload detailing reserved numbers
        payload = {
            "talonario_code": tal.talonario_code,
            "range_start": tal.range_start,
            "range_end": tal.range_end,
            "total_numbers": tal.total_numbers,
            "purpose": tal.purpose,
            "numbers": [n.full_document_code for n in numbers],
        }

        # Multi-page render by executing WeasyPrint over combined template pages
        # For simplicity, we trigger the central rendering with a khusus status and watermark
        cmd = DocumentRenderCommand(
            document_type_code=dt.code if dt else "UNKNOWN",
            document_code=tal.talonario_code,
            document_status="RESERVED_TALONARIO",
            document_title=f"TALONARIO - {dt.name if dt else 'DOCUMENTOS'}",
            organization_name=org.name if org else "PROYECTO T1 LOGÍSTICA",
            branch_name=br.name if br else "SEDE PRINCIPAL",
            document_data=payload,
            watermark_text="FORMATO NO EMITIDO - NÚMERO RESERVADO",
            preview_mode=True,
            requested_by=str(actor_id) if actor_id else None,
        )

        res = self.renderer.render_pdf(cmd)
        filename = f"TALONARIO_{tal.talonario_code}.pdf"
        storage_key = f"documents/{tal.organization_id}/talonarios/{filename}"

        # Save to storage (talonarios are persistent artifacts)
        self.storage.put(storage_key, res.pdf_bytes)

        return res.pdf_bytes, filename

    def create_export_job(
        self,
        organization_id: UUID,
        document_ids: list[UUID],
        export_format: str,
        include_manifest: bool,
        include_checksums: bool,
        reason: str | None,
        actor_id: UUID,
    ) -> DocumentExportJobModel:
        """Enqueues or processes a document export (Phase 020)."""
        if len(document_ids) > DOCUMENT_EXPORT_MAX_ITEMS:
            raise ExportServiceException(
                400,
                "DOCUMENT_EXPORT_TOO_LARGE",
                f"La exportación excede el límite máximo de {DOCUMENT_EXPORT_MAX_ITEMS} elementos."
            )

        # Resolve payload stability and hash to prevent redundant concurrent requests
        req_payload = {
            "document_ids": [str(d) for d in sorted(document_ids)],
            "export_format": export_format,
            "include_manifest": include_manifest,
            "include_checksums": include_checksums,
        }
        _, req_hash = stable_json_hash(req_payload)

        # Check if identical job was requested recently and is ready
        existing_job = self.db.scalars(
            select(DocumentExportJobModel)
            .where(
                and_(
                    DocumentExportJobModel.organization_id == organization_id,
                    DocumentExportJobModel.request_hash == req_hash,
                    DocumentExportJobModel.status == "READY",
                    DocumentExportJobModel.expires_at > utc_now()
                )
            )
        ).first()
        if existing_job:
            return existing_job

        expires_at = utc_now() + timedelta(hours=DOCUMENT_EXPORT_EXPIRATION_HOURS)

        job = DocumentExportJobModel(
            organization_id=organization_id,
            requested_by=actor_id,
            export_type=export_format,
            request_hash=req_hash,
            status="QUEUED",
            total_items=len(document_ids),
            expires_at=expires_at,
        )
        self.db.add(job)
        self.db.flush()

        # If 10 elements or less, process synchronously! Otherwise process asynchronously (simulated here or run in background)
        if len(document_ids) <= 10:
            self._process_job_sync(job, document_ids, include_manifest, include_checksums, actor_id)
        else:
            # Enqueue task in background / process synchronously for testing
            self._process_job_sync(job, document_ids, include_manifest, include_checksums, actor_id)

        return job

    def _process_job_sync(
        self,
        job: DocumentExportJobModel,
        document_ids: list[UUID],
        include_manifest: bool,
        include_checksums: bool,
        actor_id: UUID,
    ) -> None:
        """Processes the ZIP compression job (Phase 020)."""
        job.status = "PROCESSING"
        job.started_at = utc_now()
        self.db.add(job)
        self.db.flush()

        try:
            # 1. Fetch all documents and verify permissions / organization matching
            docs = list(self.db.scalars(
                select(DocumentInstanceModel)
                .where(
                    and_(
                        DocumentInstanceModel.id.in_(document_ids),
                        DocumentInstanceModel.organization_id == job.organization_id
                    )
                )
            ))

            if len(docs) != len(document_ids):
                raise ExportServiceException(400, "DOCUMENT_DOWNLOAD_DENIED", "Algunos documentos no existen o no pertenecen a su organización.")

            # Create in-memory zip file
            zip_buffer = io.BytesIO()
            manifest_items = []
            checksums = []

            # 2. Add document PDFs to ZIP
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for doc in docs:
                    # Select authoritative artifact based on current status
                    art_type = "ISSUED_PDF" if doc.status != "CANCELLED" else "CANCELLED_PDF"
                    art = self.db.scalars(
                        select(DocumentArtifactModel)
                        .where(
                            and_(
                                DocumentArtifactModel.document_id == doc.id,
                                DocumentArtifactModel.artifact_type == art_type
                            )
                        )
                    ).first()

                    if not art:
                        # Fallback to any active authoritative artifact
                        art = self.db.get(DocumentArtifactModel, doc.authoritative_artifact_id)

                    if not art:
                        job.failed_items += 1
                        continue

                    # Retrieve bytes
                    pdf_bytes = self.storage.get(art.storage_key)

                    # ZIP Slip prevention: Sanitization of filename to avoid path traversal
                    safe_name = os.path.basename(art.filename)
                    if not safe_name or safe_name in (".", ".."):
                        safe_name = f"DOC_{doc.id}.pdf"

                    # Write to zip
                    zip_file.writestr(safe_name, pdf_bytes)

                    # Compute checksum
                    sha_val = hashlib.sha256(pdf_bytes).hexdigest()
                    checksums.append(f"{sha_val}  {safe_name}")

                    manifest_items.append({
                        "document_id": str(doc.id),
                        "document_code": doc.document_code,
                        "title": doc.title,
                        "status": doc.status,
                        "filename": safe_name,
                        "file_size_bytes": len(pdf_bytes),
                        "sha256": sha_val,
                    })
                    job.processed_items += 1

                # 3. Add manifest.json if requested
                if include_manifest and manifest_items:
                    manifest_data = {
                        "export_job_id": str(job.id),
                        "generated_at": utc_now().isoformat(),
                        "total_documents": len(manifest_items),
                        "documents": manifest_items,
                    }
                    zip_file.writestr("manifest.json", json.dumps(manifest_data, indent=2, default=str))

                # 4. Add checksums.sha256 if requested
                if include_checksums and checksums:
                    zip_file.writestr("checksums.sha256", "\n".join(checksums) + "\n")

            # Get final ZIP bytes
            zip_bytes = zip_buffer.getvalue()
            zip_size = len(zip_bytes)

            # Limit total MB
            if (zip_size / (1024 * 1024)) > DOCUMENT_EXPORT_MAX_TOTAL_MB:
                raise ExportServiceException(400, "DOCUMENT_EXPORT_TOO_LARGE", "El tamaño final de la exportación excede el límite de 100 MB.")

            # Save ZIP to storage
            filename = f"EXPORT_{job.id}.zip"
            storage_key = f"exports/{job.id}/{filename}"
            self.storage.put(storage_key, zip_bytes)

            # Create artifact for the ZIP
            art = DocumentArtifactModel(
                document_id=job.id,  # Map to job ID since it's the export task
                snapshot_id=job.id,
                artifact_type="EXPORT_ZIP",
                representation_status="ACTIVE",
                mime_type="application/zip",
                filename=filename,
                storage_provider=settings.STORAGE_PROVIDER,
                storage_key=storage_key,
                size_bytes=zip_size,
                file_hash=hashlib.sha256(zip_bytes).hexdigest(),
                content_hash=job.request_hash,
                template_version="1.0.0",
                renderer_version="1.0.0",
                generated_by=actor_id,
                is_authoritative=False,
                is_sensitive=False,
            )
            self.db.add(art)
            self.db.flush()

            job.status = "READY"
            job.artifact_id = art.id
            job.completed_at = utc_now()
            self.db.add(job)
            self.db.flush()

        except Exception as e:
            job.status = "FAILED"
            job.error_code = "EXPORT_COMPRESSION_FAILED"
            job.completed_at = utc_now()
            self.db.add(job)
            self.db.flush()
            if isinstance(e, ExportServiceException):
                raise e
            raise ExportServiceException(500, "EXPORT_COMPRESSION_FAILED", f"Error al compilar el archivo ZIP: {str(e)}")

    def get_export_job(self, job_id: UUID) -> DocumentExportJobModel:
        job = self.db.get(DocumentExportJobModel, job_id)
        if not job:
            raise ExportServiceException(404, "DOCUMENT_EXPORT_NOT_FOUND", "Trabajo de exportación no encontrado.")
        return job

    def download_export_zip(self, job_id: UUID, actor_id: UUID) -> tuple[bytes, str]:
        """Downloads the ready export ZIP file (Phase 020)."""
        job = self.get_export_job(job_id)
        if job.status != "READY":
            raise ExportServiceException(400, "DOCUMENT_EXPORT_NOT_READY", f"El archivo de exportación no está listo (Estado: {job.status}).")
        if job.expires_at < utc_now():
            job.status = "EXPIRED"
            self.db.add(job)
            self.db.flush()
            raise ExportServiceException(410, "DOCUMENT_EXPORT_EXPIRED", "El archivo de exportación ha expirado.")

        # Retrieve ZIP artifact
        art = self.db.get(DocumentArtifactModel, job.artifact_id)
        if not art:
            raise ExportServiceException(404, "DOCUMENT_ARTIFACT_MISSING", "Falta el artefacto de exportación.")

        pdf_bytes = self.storage.get(art.storage_key)
        return pdf_bytes, art.filename

    def get_operation_package(
        self,
        organization_id: UUID,
        operation_type: str,
        operation_id: UUID,
        actor_id: UUID | None,
    ) -> tuple[bytes, str]:
        """Gathers and compresses all issued documents associated with a resource operation (Phase 020)."""
        # Find all issued document instances associated with this operation
        # Match by source_resource_type and source_resource_id or source_operation_id
        docs = list(self.db.scalars(
            select(DocumentInstanceModel)
            .where(
                and_(
                    DocumentInstanceModel.organization_id == organization_id,
                    DocumentInstanceModel.status.in_(("ISSUED", "CANCELLED")),
                    or_(
                        and_(
                            DocumentInstanceModel.source_resource_type == operation_type.upper(),
                            DocumentInstanceModel.source_resource_id == operation_id
                        ),
                        DocumentInstanceModel.source_operation_id == operation_id
                    )
                )
            )
        ))

        # Check if package is empty/incomplete
        if not docs:
            raise ExportServiceException(409, "DOCUMENT_PACKAGE_INCOMPLETE", "El paquete de la operación no contiene documentos emitidos.")

        # Create in-memory zip
        zip_buffer = io.BytesIO()
        manifest_items = []
        checksums = []

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for doc in docs:
                art_type = "ISSUED_PDF" if doc.status != "CANCELLED" else "CANCELLED_PDF"
                art = self.db.scalars(
                    select(DocumentArtifactModel)
                    .where(
                        and_(
                            DocumentArtifactModel.document_id == doc.id,
                            DocumentArtifactModel.artifact_type == art_type
                        )
                    )
                ).first()

                if not art:
                    art = self.db.get(DocumentArtifactModel, doc.authoritative_artifact_id)

                if not art:
                    continue

                pdf_bytes = self.storage.get(art.storage_key)
                safe_name = os.path.basename(art.filename)
                zip_file.writestr(safe_name, pdf_bytes)

                sha_val = hashlib.sha256(pdf_bytes).hexdigest()
                checksums.append(f"{sha_val}  {safe_name}")
                manifest_items.append({
                    "document_id": str(doc.id),
                    "document_code": doc.document_code,
                    "title": doc.title,
                    "status": doc.status,
                    "filename": safe_name,
                    "sha256": sha_val,
                })

            manifest_data = {
                "operation_id": str(operation_id),
                "operation_type": operation_type,
                "generated_at": utc_now().isoformat(),
                "documents": manifest_items,
            }
            zip_file.writestr("manifest.json", json.dumps(manifest_data, indent=2, default=str))
            zip_file.writestr("checksums.sha256", "\n".join(checksums) + "\n")

        zip_bytes = zip_buffer.getvalue()
        filename = f"PACKAGE_{operation_type.upper()}_{operation_id}.zip"

        return zip_bytes, filename

    def export_talonario_zip(
        self,
        talonario_id: UUID,
        actor_id: UUID | None,
    ) -> tuple[bytes, str]:
        """Generates a ZIP archive containing the multipage PDF, manifests, and checksums for a talonario."""
        # 1. Generate WeasyPrint PDF talonario
        pdf_bytes, pdf_filename = self.generate_talonario_pdf(talonario_id, actor_id)

        tal = self.db.get(DocumentTalonarioModel, talonario_id)
        numbers = list(self.db.scalars(
            select(DocumentNumberModel)
            .where(DocumentNumberModel.talonario_id == tal.id)
            .order_by(DocumentNumberModel.sequence_number.asc())
        ))

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add the multipage PDF
            zip_file.writestr(pdf_filename, pdf_bytes)

            # Generate manifest.json
            manifest_data = {
                "talonario_code": tal.talonario_code,
                "range_start": tal.range_start,
                "range_end": tal.range_end,
                "total_numbers": tal.total_numbers,
                "checksum": hashlib.sha256(pdf_bytes).hexdigest(),
                "numbers": [n.full_document_code for n in numbers]
            }
            zip_file.writestr("manifest.json", json.dumps(manifest_data, indent=2, default=str))

            # Generate manifest.csv
            csv_output = io.StringIO()
            writer = csv.writer(csv_output)
            writer.writerow(["sequence_number", "full_document_code", "status"])
            for n in numbers:
                writer.writerow([n.sequence_number, n.full_document_code, n.status])
            zip_file.writestr("manifest.csv", csv_output.getvalue())

            # Generate checksums.sha256
            pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
            zip_file.writestr("checksums.sha256", f"{pdf_hash}  {pdf_filename}\n")

        zip_bytes = zip_buffer.getvalue()
        zip_filename = f"TALONARIO_EXPORT_{tal.talonario_code}.zip"
        return zip_bytes, zip_filename

