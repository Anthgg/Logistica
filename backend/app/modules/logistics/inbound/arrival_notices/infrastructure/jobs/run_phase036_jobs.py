"""CLI entrypoint for persistent Phase 036 maintenance jobs."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.modules.logistics.inbound.arrival_notices.infrastructure.jobs.jobs import (
    cleanup_external_portal_sessions,
    detect_blackout_affected_appointments,
    detect_driver_license_expirations,
    detect_pending_appointment_documents,
    detect_vehicle_verification_expirations,
    enqueue_reception_appointment_reminders,
    expire_reception_holds,
    mark_elapsed_appointment_windows,
    process_appointment_package_jobs,
    publish_arrival_notice_outbox,
    reconcile_expected_quantity_allocations,
    retry_failed_outbox_events,
)


Job = Callable[[Session], int]

JOBS: dict[str, Job] = {
    "expire-holds": expire_reception_holds,
    "reminders-24h": lambda db: enqueue_reception_appointment_reminders(
        db, horizon_minutes=1440
    ),
    "reminders-2h": lambda db: enqueue_reception_appointment_reminders(
        db, horizon_minutes=120
    ),
    "mark-elapsed": mark_elapsed_appointment_windows,
    "pending-documents": detect_pending_appointment_documents,
    "driver-license-expirations": detect_driver_license_expirations,
    "vehicle-verification-expirations": detect_vehicle_verification_expirations,
    "blackout-affected": detect_blackout_affected_appointments,
    "retry-outbox": retry_failed_outbox_events,
    "publish-outbox": publish_arrival_notice_outbox,
    "cleanup-external-sessions": cleanup_external_portal_sessions,
    "reconcile-allocations": reconcile_expected_quantity_allocations,
    "appointment-packages": process_appointment_package_jobs,
}


def run(job_name: str) -> dict[str, int]:
    selected = JOBS if job_name == "all" else {job_name: JOBS[job_name]}
    results: dict[str, int] = {}
    with SessionLocal() as db:
        try:
            for name, job in selected.items():
                results[name] = job(db)
                db.commit()
        except Exception:
            db.rollback()
            raise
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", choices=["all", *JOBS])
    args = parser.parse_args()
    print(json.dumps(run(args.job), sort_keys=True))


if __name__ == "__main__":
    main()

