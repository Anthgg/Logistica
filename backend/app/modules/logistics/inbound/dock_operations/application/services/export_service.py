"""Persistent, non-official operational exports for Phase 038."""

from __future__ import annotations

import csv
import hashlib
import io
from datetime import datetime, timezone
from html import escape
from uuid import UUID, uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.warehouse import Warehouse
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.files.application.services.preview_download_service import (
    FilePreviewDownloadService,
)
from app.modules.logistics.files.domain.services.services import FileCodeService
from app.modules.logistics.files.infrastructure.persistence.models import (
    FileAssetModel,
    FileVersionModel,
)
from app.modules.logistics.files.infrastructure.storage.storage_gateway import (
    get_storage_gateway,
)
from app.modules.logistics.inbound.dock_operations.application.services.common import (
    server_now,
)
from app.modules.logistics.inbound.dock_operations.application.services.unloading_services import (
    DockOperationalProjectionService,
)
from app.modules.logistics.inbound.dock_operations.infrastructure.persistence.models import (
    DockOperationExportJobModel,
    DockOperationalEventModel,
    InboundDockAssignmentModel,
    UnloadingOperationModel,
    UnloadingPauseModel,
    UnloadingResponsibleAssignmentModel,
    WarehouseDockModel,
)
from app.modules.logistics.inbound.gate_control.infrastructure.persistence.models import (
    GateCheckInModel,
)
from app.modules.logistics.principal import LogisticsPrincipal


_HEADERS = (
    "ALMACEN",
    "MUELLE",
    "CPV",
    "CIT",
    "PLACA",
    "PROVEEDOR",
    "RESPONSABLES",
    "EVENTOS",
    "TIEMPOS",
    "PAUSAS",
    "ESTADO",
    "CALIDAD_DATOS",
)


def _csv_safe(value: object) -> str:
    text = "" if value is None else str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text.replace("\x00", "")


def _csv_bytes(rows: list[list[str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, dialect="excel", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["REPORTE OPERATIVO - NO OFICIAL", *([""] * (len(_HEADERS) - 1))])
    writer.writerow(_HEADERS)
    writer.writerows([[_csv_safe(value) for value in row] for row in rows])
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def _column_name(index: int) -> str:
    value = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        value = chr(65 + remainder) + value
    return value


def _xlsx_bytes(rows: list[list[str]]) -> bytes:
    all_rows = [["REPORTE OPERATIVO - NO OFICIAL", *([""] * (len(_HEADERS) - 1))], list(_HEADERS), *rows]
    xml_rows: list[str] = []
    for row_number, row in enumerate(all_rows, start=1):
        cells = []
        for column_number, value in enumerate(row, start=1):
            reference = f"{_column_name(column_number)}{row_number}"
            cells.append(
                f'<c r="{reference}" t="inlineStr"><is><t xml:space="preserve">{escape(_csv_safe(value))}</t></is></c>'
            )
        xml_rows.append(f'<row r="{row_number}">{"".join(cells)}</row>')
    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData>' + "".join(xml_rows) + '</sheetData></worksheet>'
    )
    output = io.BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '</Types>',
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>',
        )
        archive.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Operaciones" sheetId="1" r:id="rId1"/></sheets></workbook>',
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '</Relationships>',
        )
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    return output.getvalue()


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_bytes(rows: list[list[str]]) -> bytes:
    lines = ["REPORTE OPERATIVO - NO OFICIAL", " | ".join(_HEADERS)]
    lines.extend(" | ".join(_csv_safe(value) for value in row)[:180] for row in rows)
    pages = [lines[index:index + 45] for index in range(0, len(lines), 45)] or [["REPORTE OPERATIVO - NO OFICIAL"]]
    objects: dict[int, bytes] = {}
    page_refs: list[int] = []
    next_object = 4
    for page_lines in pages:
        page_number, content_number = next_object, next_object + 1
        next_object += 2
        page_refs.append(page_number)
        commands = ["BT", "/F1 8 Tf", "36 806 Td", "11 TL"]
        for line in page_lines:
            encoded = _pdf_escape(line).encode("latin-1", "replace").decode("latin-1")
            commands.append(f"({encoded}) Tj")
            commands.append("T*")
        commands.append("ET")
        stream = "\n".join(commands).encode("latin-1")
        objects[page_number] = f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_number} 0 R >>".encode()
        objects[content_number] = b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"
    objects[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[2] = f"<< /Type /Pages /Kids [{' '.join(f'{ref} 0 R' for ref in page_refs)}] /Count {len(page_refs)} >>".encode()
    objects[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    output = io.BytesIO()
    output.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {0: 0}
    for number in range(1, max(objects) + 1):
        offsets[number] = output.tell()
        output.write(f"{number} 0 obj\n".encode())
        output.write(objects[number])
        output.write(b"\nendobj\n")
    xref = output.tell()
    output.write(f"xref\n0 {max(objects) + 1}\n".encode())
    output.write(b"0000000000 65535 f \n")
    for number in range(1, max(objects) + 1):
        output.write(f"{offsets[number]:010d} 00000 n \n".encode())
    output.write(f"trailer\n<< /Size {max(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return output.getvalue()


class DockOperationExportService:
    def __init__(self, db: Session):
        self.db = db
        self.storage = get_storage_gateway()

    def request(self, principal: LogisticsPrincipal, organization_id: UUID, export_format: str, filters: dict) -> DockOperationExportJobModel:
        row = DockOperationExportJobModel(
            id=uuid4(),
            organization_id=organization_id,
            warehouse_id=filters.get("warehouse_id"),
            export_format=export_format,
            filters=filters,
            status="PENDING",
            requested_by=principal.user_id,
        )
        self.db.add(row)
        self.db.flush()
        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.dock_operation_export.requested",
                actor_user_id=principal.user_id,
                organization_id=organization_id,
                resource_type="dock_operation_export_job",
                resource_id=str(row.id),
                payload={"format": export_format, "filters": filters},
            ),
        )
        return row

    def get(self, job_id: UUID, organization_id: UUID) -> DockOperationExportJobModel:
        row = self.db.scalar(select(DockOperationExportJobModel).where(DockOperationExportJobModel.id == job_id, DockOperationExportJobModel.organization_id == organization_id))
        if row is None:
            raise LookupError("DOCK_OPERATION_EXPORT_NOT_FOUND")
        return row

    def _rows(self, job: DockOperationExportJobModel) -> list[list[str]]:
        query = (
            select(UnloadingOperationModel, InboundDockAssignmentModel, GateCheckInModel, WarehouseDockModel, Warehouse)
            .join(InboundDockAssignmentModel, InboundDockAssignmentModel.id == UnloadingOperationModel.dock_assignment_id)
            .join(GateCheckInModel, GateCheckInModel.id == UnloadingOperationModel.gate_check_in_id)
            .join(WarehouseDockModel, WarehouseDockModel.id == UnloadingOperationModel.dock_id)
            .join(Warehouse, Warehouse.id == UnloadingOperationModel.warehouse_id)
            .where(UnloadingOperationModel.organization_id == job.organization_id)
        )
        filters = job.filters or {}
        if filters.get("warehouse_id"):
            query = query.where(UnloadingOperationModel.warehouse_id == UUID(str(filters["warehouse_id"])))
        elif filters.get("authorized_warehouse_ids"):
            query = query.where(
                UnloadingOperationModel.warehouse_id.in_(
                    [UUID(str(value)) for value in filters["authorized_warehouse_ids"]]
                )
            )
        if filters.get("dock_id"):
            query = query.where(UnloadingOperationModel.dock_id == UUID(str(filters["dock_id"])))
        if filters.get("unloading_status"):
            query = query.where(UnloadingOperationModel.status == filters["unloading_status"])
        if filters.get("started_from"):
            query = query.where(UnloadingOperationModel.started_at >= datetime.fromisoformat(str(filters["started_from"])))
        if filters.get("started_to"):
            query = query.where(UnloadingOperationModel.started_at <= datetime.fromisoformat(str(filters["started_to"])))
        rows: list[list[str]] = []
        for operation, assignment, gate, dock, warehouse in self.db.execute(query.order_by(UnloadingOperationModel.created_at)):
            responsibles = list(self.db.scalars(select(UnloadingResponsibleAssignmentModel).where(UnloadingResponsibleAssignmentModel.unloading_operation_id == operation.id)))
            pauses = list(self.db.scalars(select(UnloadingPauseModel).where(UnloadingPauseModel.unloading_operation_id == operation.id).order_by(UnloadingPauseModel.pause_number)))
            events = list(self.db.scalars(select(DockOperationalEventModel).where(DockOperationalEventModel.unloading_operation_id == operation.id).order_by(DockOperationalEventModel.sequence_number)))
            supplier = gate.supplier_snapshot or {}
            supplier_name = supplier.get("legal_name") or supplier.get("trade_name") or supplier.get("partner_code") or ""
            time_summary = "; ".join(
                f"{name}={value.isoformat()}" for name, value in (
                    ("gate_cleared", gate.entry_authorized_at),
                    ("dock_arrived", assignment.dock_arrived_at),
                    ("unloading_started", operation.started_at),
                    ("unloading_completed", operation.completed_at),
                    ("dock_released", assignment.released_at),
                ) if value is not None
            )
            pause_summary = "; ".join(f"{row.reason_code}:{row.status}:{row.duration_seconds or 0}s" for row in pauses)
            responsible_summary = "; ".join(f"{row.responsibility_type}:{row.status}" for row in responsibles)
            event_summary = "; ".join(f"{row.event_type}@{row.event_at.isoformat()}" for row in events)
            quality = DockOperationalProjectionService(self.db).metrics(operation).get("data_quality_status")
            rows.append([
                f"{warehouse.code} - {warehouse.name}", f"{dock.code} - {dock.name}",
                gate.check_in_code or "", gate.appointment_code_snapshot or "",
                assignment.observed_plate_snapshot, supplier_name, responsible_summary,
                event_summary, time_summary, pause_summary, operation.status, str(quality or "INCOMPLETE"),
            ])
        return rows

    def process(self, job: DockOperationExportJobModel) -> DockOperationExportJobModel:
        job.status = "PROCESSING"
        self.db.flush()
        try:
            rows = self._rows(job)
            formatters = {"CSV": (_csv_bytes, "csv", "text/csv"), "XLSX": (_xlsx_bytes, "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"), "PDF": (_pdf_bytes, "pdf", "application/pdf")}
            formatter, extension, content_type = formatters[job.export_format]
            content = formatter(rows)
            asset_id, version_id = uuid4(), uuid4()
            filename = f"reporte_operativo_muelles_{job.id}.{extension}"
            bucket = "files-private"
            object_key = f"organizations/{job.organization_id}/dock-operation-exports/{job.id}/{filename}"
            metadata = self.storage.write_bytes(bucket, object_key, content, content_type, {"report-type": "OPERATIONAL-NON-OFFICIAL"})
            file_code = FileCodeService.generate_file_code(self.db, job.organization_id)
            asset = FileAssetModel(
                id=asset_id, organization_id=job.organization_id, file_code=file_code,
                normalized_file_code=file_code.upper(), title="REPORTE OPERATIVO - NO OFICIAL",
                description="Exportación operativa de muelles y descarga; no constituye documento legal.",
                asset_type="DOCUMENT", classification="CONFIDENTIAL", lifecycle_status="AVAILABLE",
                evidence_status="NOT_EVIDENCE", owner_type="USER", owner_user_id=job.requested_by,
                owner_resource_type="DOCK_OPERATION_EXPORT", owner_resource_id=str(job.id),
                current_version_id=version_id, access_scope="RESOURCE_INHERITED",
                created_by=job.requested_by, updated_by=job.requested_by,
            )
            version = FileVersionModel(
                id=version_id, file_asset_id=asset_id, version_number=1, status="AVAILABLE",
                storage_provider="GCS", bucket_reference=bucket, object_key=object_key,
                object_generation=getattr(metadata, "generation", None), original_filename=filename,
                sanitized_filename=filename, extension=extension, declared_MIME_type=content_type,
                detected_MIME_type=content_type, size_bytes=len(content), SHA256=hashlib.sha256(content).hexdigest(),
                content_validation_status="VALID", malware_scan_status="CLEAN",
                malware_scanner_version="trusted-system-generated", source_type="GENERATED",
                source_reference=str(job.id), uploaded_by=job.requested_by, finalized_at=server_now(),
            )
            self.db.add_all([asset, version])
            job.file_asset_id = asset_id
            job.status = "COMPLETED"
            job.completed_at = server_now()
            audit_service.write_event(self.db, AuditEventCommand(event_code="logistics.dock_operation_export.ready", actor_user_id=job.requested_by, organization_id=job.organization_id, resource_type="dock_operation_export_job", resource_id=str(job.id), payload={"format": job.export_format, "rows": len(rows), "file_asset_id": str(asset_id)}))
        except Exception as exc:
            job.status = "FAILED"
            job.error_detail = type(exc).__name__
            job.completed_at = server_now()
            audit_service.write_event(self.db, AuditEventCommand(event_code="logistics.dock_operation_export.failed", actor_user_id=job.requested_by, organization_id=job.organization_id, resource_type="dock_operation_export_job", resource_id=str(job.id), payload={"error_type": type(exc).__name__}))
        self.db.flush()
        return job

    def download(self, job: DockOperationExportJobModel, principal: LogisticsPrincipal) -> dict:
        if job.status != "COMPLETED" or job.file_asset_id is None:
            raise RuntimeError("DOCK_OPERATION_EXPORT_NOT_READY")
        signed, _asset, version = FilePreviewDownloadService(self.db).get_download_access(job.file_asset_id, job.organization_id, principal.user_id, correlation_id=str(job.id))
        audit_service.write_event(self.db, AuditEventCommand(event_code="logistics.dock_operation_export.downloaded", actor_user_id=principal.user_id, organization_id=job.organization_id, resource_type="dock_operation_export_job", resource_id=str(job.id), payload={"file_asset_id": str(job.file_asset_id), "version_id": str(version.id)}))
        return {"export_job_id": job.id, "download_url": signed.url, "expires_at": signed.expires_at, "label": "REPORTE OPERATIVO - NO OFICIAL"}


def process_pending_exports(db: Session, *, batch_size: int = 10) -> int:
    jobs = list(db.scalars(select(DockOperationExportJobModel).where(DockOperationExportJobModel.status == "PENDING").order_by(DockOperationExportJobModel.created_at).with_for_update(skip_locked=True).limit(batch_size)))
    service = DockOperationExportService(db)
    for job in jobs:
        service.process(job)
    return len(jobs)
