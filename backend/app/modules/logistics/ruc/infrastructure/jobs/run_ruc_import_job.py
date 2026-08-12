"""CLI entrypoint script for Cloud Run Job execution of periodic SUNAT RUC import."""

import os
import sys
from uuid import uuid4

from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.logistics.ruc.application.services.import_service import RucRegistryImportService


def main():
    print("[RUC Import Job] Starting periodic SUNAT padrón import job...")
    db_gen = get_db()
    db: Session = next(db_gen)

    dataset_type = os.getenv("RUC_IMPORT_DATASET_TYPE", "RUC_GENERAL")
    service = RucRegistryImportService(db)

    try:
        job = service.create_import_job(dataset_type=dataset_type, trigger_type="SCHEDULED")
        print(f"[RUC Import Job] Created job {job.id} for dataset_type={dataset_type}. Executing pipeline...")
        version = service.execute_import_job(job.id)
        print(f"[RUC Import Job] SUCCESS. Activated dataset version {version.id} with {version.total_rows} rows.")
        sys.exit(0)
    except Exception as e:
        print(f"[RUC Import Job] FAILED: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
