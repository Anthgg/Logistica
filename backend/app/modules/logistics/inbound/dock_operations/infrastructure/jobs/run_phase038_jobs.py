"""CLI entrypoint for persistent Phase 038 jobs."""

import argparse
import json

from app.database.session import SessionLocal
from app.modules.logistics.inbound.dock_operations.infrastructure.jobs.jobs import (
    detect_abandoned_unloading,
    detect_stale_dock_movements,
    expire_assignment_plans,
    process_pending_exports,
    refresh_operational_projections,
)


JOBS = {
    "expire-plans": expire_assignment_plans,
    "stale-movements": detect_stale_dock_movements,
    "abandoned-unloading": detect_abandoned_unloading,
    "refresh-projections": refresh_operational_projections,
    "generate-exports": process_pending_exports,
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
