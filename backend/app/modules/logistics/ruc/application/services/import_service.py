"""RucRegistryImportService — Atomic dataset importer and activator (Phase 026)."""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import and_, func, select, update
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.ruc.domain.errors.exceptions import (
    RucImportAnomalousRowCountError,
    RucImportArchiveInvalidError,
)
from app.modules.logistics.ruc.infrastructure.cache.ruc_cache import ruc_cache
from app.modules.logistics.ruc.infrastructure.importers.safe_downloader import (
    SafeZipDownloader,
    SafeZipExtractor,
)
from app.modules.logistics.ruc.infrastructure.parsers.ruc_parser import RucRegistryParser
from app.modules.logistics.ruc.infrastructure.persistence.models import (
    RucDataSourceModel,
    RucDatasetVersionModel,
    RucImportJobModel,
    RucRegistryAnnexAddressModel,
    RucRegistryEntryModel,
)


class RucRegistryImportService:
    """Manages secure download, streaming parse, staging load, atomic activation, and rollback of RUC datasets."""

    ROW_DROP_THRESHOLD_PERCENT = 20.0  # Max 20% row drop without review

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_default_source(self, dataset_type: str = "RUC_GENERAL") -> RucDataSourceModel:
        code = f"SUNAT_REDUCED_{dataset_type}"
        source = self.db.scalars(
            select(RucDataSourceModel).where(RucDataSourceModel.code == code)
        ).first()

        if not source:
            url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/padron_reducido_ruc.zip" if dataset_type == "RUC_GENERAL" else "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/padron_reducido_locanx.zip"
            source = RucDataSourceModel(
                id=uuid4(),
                code=code,
                name=f"Padrón Reducido SUNAT ({dataset_type})",
                source_type="SUNAT_REDUCED_REGISTRY" if dataset_type == "RUC_GENERAL" else "SUNAT_REDUCED_ANNEX_REGISTRY",
                authority="SUNAT",
                source_reference=url,
                base_domain="e-consultaruc.sunat.gob.pe",
                enabled=True,
                priority=10,
                status="ACTIVE",
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)

        return source

    def create_import_job(
        self,
        dataset_type: str = "RUC_GENERAL",
        trigger_type: str = "MANUAL",
        requested_by: Optional[UUID] = None,
        custom_url: Optional[str] = None,
    ) -> RucImportJobModel:
        source = self.get_or_create_default_source(dataset_type)

        if custom_url:
            source.source_reference = custom_url
            self.db.commit()

        job = RucImportJobModel(
            id=uuid4(),
            data_source_id=source.id,
            dataset_type=dataset_type,
            trigger_type=trigger_type,
            requested_by=requested_by,
            status="QUEUED",
            current_stage="INIT",
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def execute_import_job(self, job_id: UUID, raw_zip_bytes: Optional[bytes] = None) -> RucDatasetVersionModel:
        """Executes full download, parse, load, and atomic activation pipeline."""
        job = self.db.get(RucImportJobModel, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job de importación no encontrado.")

        source = self.db.get(RucDataSourceModel, job.data_source_id)
        job.status = "DOWNLOADING"
        job.started_at = utc_now()
        self.db.commit()

        audit_service.log_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.ruc.import_started",
                category="INTEGRATION",
                severity="MEDIUM",
                description=f"Importación de RUC iniciada ({job.dataset_type})",
                actor_user_id=job.requested_by,
                payload={"job_id": str(job.id), "dataset_type": job.dataset_type},
            ),
        )

        try:
            # Step 1: Download or use provided bytes
            if raw_zip_bytes:
                zip_bytes = raw_zip_bytes
                sha256_hash = hashlib.sha256(zip_bytes).hexdigest()
                size_bytes = len(zip_bytes)
            else:
                zip_bytes, sha256_hash, size_bytes = SafeZipDownloader.download_and_verify(source.source_reference)

            job.downloaded_bytes = size_bytes
            job.current_stage = "PARSING"
            job.status = "PARSING"
            self.db.commit()

            # Step 2: Safe Extract
            filename, file_bytes = SafeZipExtractor.inspect_and_extract_file(zip_bytes)

            # Step 3: Create Dataset Version
            dataset_version = RucDatasetVersionModel(
                id=uuid4(),
                data_source_id=source.id,
                dataset_type=job.dataset_type,
                fetched_at=utc_now(),
                import_started_at=job.started_at,
                status="IMPORTING",
                source_filename=filename,
                compressed_size_bytes=size_bytes,
                uncompressed_size_bytes=len(file_bytes),
                archive_hash=sha256_hash,
                import_job_id=job.id,
            )
            self.db.add(dataset_version)
            self.db.commit()

            # Step 4: Stream parse & batch insert
            job.current_stage = "STAGING"
            self.db.commit()

            total_accepted = 0
            batch = []
            BATCH_SIZE = 2000

            if job.dataset_type == "RUC_GENERAL":
                for record in RucRegistryParser.parse_general_padron_stream(file_bytes):
                    entry = RucRegistryEntryModel(
                        id=uuid4(),
                        dataset_version_id=dataset_version.id,
                        ruc=record["ruc"],
                        normalized_ruc=record["normalized_ruc"],
                        legal_name=record["legal_name"],
                        normalized_legal_name=record["normalized_legal_name"],
                        taxpayer_status_raw=record["taxpayer_status_raw"],
                        taxpayer_status_normalized=record["taxpayer_status_normalized"],
                        domicile_condition_raw=record["domicile_condition_raw"],
                        domicile_condition_normalized=record["domicile_condition_normalized"],
                        ubigeo_code=record["ubigeo_code"],
                        record_hash=record["record_hash"],
                    )
                    batch.append(entry)
                    total_accepted += 1

                    if len(batch) >= BATCH_SIZE:
                        self.db.bulk_save_objects(batch)
                        self.db.commit()
                        batch.clear()

                if batch:
                    self.db.bulk_save_objects(batch)
                    self.db.commit()
                    batch.clear()

            else:
                for record in RucRegistryParser.parse_annex_padron_stream(file_bytes):
                    annex = RucRegistryAnnexAddressModel(
                        id=uuid4(),
                        dataset_version_id=dataset_version.id,
                        ruc=record["ruc"],
                        ubigeo_code=record["ubigeo_code"],
                        address_raw=record["address_raw"],
                        address_normalized=record["address_normalized"],
                        record_hash=record["record_hash"],
                    )
                    batch.append(annex)
                    total_accepted += 1

                    if len(batch) >= BATCH_SIZE:
                        self.db.bulk_save_objects(batch)
                        self.db.commit()
                        batch.clear()

                if batch:
                    self.db.bulk_save_objects(batch)
                    self.db.commit()
                    batch.clear()

            dataset_version.total_rows = total_accepted
            dataset_version.accepted_rows = total_accepted
            dataset_version.status = "VALIDATED"
            self.db.commit()

            # Step 5: Anomaly Control
            self._verify_row_drop_anomaly(source.id, job.dataset_type, total_accepted)

            # Step 6: Atomic Activation
            self.activate_dataset(dataset_version.id, actor_id=job.requested_by)

            job.status = "COMPLETED"
            job.current_stage = "COMPLETED"
            job.completed_at = utc_now()
            job.accepted_rows = total_accepted
            job.processed_rows = total_accepted
            self.db.commit()

            source.last_successful_sync_at = utc_now()
            source.consecutive_failures = 0
            self.db.commit()

            return dataset_version

        except Exception as e:
            job.status = "FAILED"
            job.error_summary = str(e)
            source.last_failed_sync_at = utc_now()
            source.consecutive_failures += 1
            self.db.commit()

            audit_service.log_event(
                self.db,
                AuditEventCommand(
                    event_code="logistics.ruc.import_failed",
                    category="INTEGRATION",
                    severity="HIGH",
                    description=f"Fallo en importación RUC: {str(e)}",
                    actor_user_id=job.requested_by,
                ),
            )
            raise e

    def _verify_row_drop_anomaly(self, source_id: UUID, dataset_type: str, new_rows: int):
        active = self.db.scalars(
            select(RucDatasetVersionModel).where(
                and_(
                    RucDatasetVersionModel.data_source_id == source_id,
                    RucDatasetVersionModel.dataset_type == dataset_type,
                    RucDatasetVersionModel.status == "ACTIVE",
                )
            )
        ).first()

        if active and active.total_rows > 0:
            drop_percent = ((active.total_rows - new_rows) / active.total_rows) * 100.0
            if drop_percent > self.ROW_DROP_THRESHOLD_PERCENT:
                raise RucImportAnomalousRowCountError(
                    f"Caída de registros de {drop_percent:.1f}% excede el máximo permitido ({self.ROW_DROP_THRESHOLD_PERCENT}%). Se requiere revisión."
                )

    def activate_dataset(self, dataset_version_id: UUID, actor_id: Optional[UUID] = None) -> RucDatasetVersionModel:
        target = self.db.get(RucDatasetVersionModel, dataset_version_id)
        if not target:
            raise HTTPException(status_code=404, detail="Dataset no encontrado.")

        # Supersede current active
        self.db.execute(
            update(RucDatasetVersionModel)
            .where(
                and_(
                    RucDatasetVersionModel.data_source_id == target.data_source_id,
                    RucDatasetVersionModel.dataset_type == target.dataset_type,
                    RucDatasetVersionModel.status == "ACTIVE",
                    RucDatasetVersionModel.id != target.id,
                )
            )
            .values(status="SUPERSEDED")
        )

        target.status = "ACTIVE"
        target.activated_at = utc_now()
        target.activated_by = actor_id
        self.db.commit()

        # Invalidate cache for dataset
        ruc_cache.invalidate_dataset(str(target.id))

        audit_service.log_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.ruc.dataset_activated",
                category="INTEGRATION",
                severity="HIGH",
                description=f"Dataset RUC activado ({target.dataset_type})",
                actor_user_id=actor_id,
                payload={"dataset_id": str(target.id), "total_rows": target.total_rows},
            ),
        )

        return target

    def rollback_dataset(self, source_id: UUID, dataset_type: str, actor_id: Optional[UUID] = None) -> RucDatasetVersionModel:
        """Rolls back active pointer to previous SUPERSEDED dataset."""
        current_active = self.db.scalars(
            select(RucDatasetVersionModel).where(
                and_(
                    RucDatasetVersionModel.data_source_id == source_id,
                    RucDatasetVersionModel.dataset_type == dataset_type,
                    RucDatasetVersionModel.status == "ACTIVE",
                )
            )
        ).first()

        previous = self.db.scalars(
            select(RucDatasetVersionModel)
            .where(
                and_(
                    RucDatasetVersionModel.data_source_id == source_id,
                    RucDatasetVersionModel.dataset_type == dataset_type,
                    RucDatasetVersionModel.status == "SUPERSEDED",
                )
            )
            .order_by(RucDatasetVersionModel.activated_at.desc())
        ).first()

        if not previous:
            raise HTTPException(status_code=400, detail="No existe una versión anterior disponible para rollback.")

        if current_active:
            current_active.status = "ROLLED_BACK"

        previous.status = "ACTIVE"
        previous.activated_at = utc_now()
        previous.activated_by = actor_id
        self.db.commit()

        ruc_cache.invalidate_dataset(str(previous.id))

        audit_service.log_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.ruc.dataset_rolled_back",
                category="INTEGRATION",
                severity="CRITICAL",
                description=f"Rollback de dataset RUC realizado ({dataset_type})",
                actor_user_id=actor_id,
            ),
        )

        return previous
