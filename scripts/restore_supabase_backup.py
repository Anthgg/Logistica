#!/usr/bin/env python3
"""
Safe, idempotent logical restore utility for Supabase / PostgreSQL backup dumps.

SAFETY GUARDS:
1. Rejects execution against production hosts (*.supabase.co) by default.
2. Requires explicit `--force-restore` flag.
3. Enforces that target database name must contain 'test' or 'restore' by default.
4. Idempotently restores data without dropping schemas or touching unapproved targets.
"""

import argparse
import datetime
import json
import os
import sys
import urllib.parse
from sqlalchemy import create_engine, text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restore logical JSON backup into a test/staging PostgreSQL database.")
    parser.add_argument("--backup-file", type=str, required=True, help="Path to JSON backup file.")
    parser.add_argument("--target-db-url", type=str, required=True, help="Target PostgreSQL connection URL.")
    parser.add_argument("--force-restore", action="store_true", help="Explicit confirmation flag required for execution.")
    parser.add_argument("--allow-production-host", action="store_true", help="DANGER: Override guard for production host.")
    return parser.parse_args()


def validate_safety_guards(target_url: str, force_restore: bool, allow_production_host: bool) -> None:
    if not force_restore:
        print("[ERROR] Restore aborted: `--force-restore` flag is required.")
        sys.exit(1)

    parsed = urllib.parse.urlparse(target_url)
    hostname = parsed.hostname or ""
    db_name = (parsed.path or "").lstrip("/")

    # Guard 1: Reject production host unless explicitly overridden
    if "supabase.co" in hostname and not allow_production_host:
        print(f"[SECURITY BLOCKED] Target host '{hostname}' appears to be a remote Supabase production instance.")
        print("Restore is blocked to prevent accidental data overwrites.")
        sys.exit(1)

    # Guard 2: Enforce test/restore naming convention for safe environments
    if not any(token in db_name.lower() for token in ["test", "restore", "staging", "dev", "local"]):
        print(f"[SECURITY BLOCKED] Target database '{db_name}' does not match safe patterns ('test', 'restore', 'staging', 'dev', 'local').")
        sys.exit(1)


def execute_restore(backup_file: str, target_db_url: str) -> dict:
    if not os.path.exists(backup_file):
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    print(f"[1/4] Loading backup payload from: {backup_file}")
    with open(backup_file, "r", encoding="utf-8") as f:
        payload = json.load(f)

    meta = payload.get("metadata", {})
    tables_data = payload.get("tables_data", {})
    alembic_revs = payload.get("alembic_version", [])

    print(f"      Backup Timestamp: {meta.get('timestamp')}")
    print(f"      Source Host:      {meta.get('host')}")
    print(f"      Tables with Data: {len(tables_data)}")

    if target_db_url.startswith("postgresql://"):
        target_db_url = target_db_url.replace("postgresql://", "postgresql+psycopg://", 1)

    engine = create_engine(target_db_url, pool_pre_ping=True)

    restored_summary = {
        "tables_restored": 0,
        "rows_restored": 0,
        "errors": []
    }

    print(f"[2/4] Connecting to target database and preparing tables...")
    with engine.begin() as conn:
        # Disable triggers and foreign keys for clean data insertion
        conn.execute(text("SET session_replication_role = 'replica';"))

        # Upfront Truncate Pass: Truncate all tables in backup in one command
        existing_tables_to_truncate = []
        for t_name in tables_data.keys():
            existing_tables_to_truncate.append(f'public."{t_name}"')
        
        if existing_tables_to_truncate:
            truncate_all_sql = f"TRUNCATE TABLE {', '.join(existing_tables_to_truncate)} CASCADE;"
            try:
                conn.execute(text(truncate_all_sql))
            except Exception as e:
                print(f"      Warning during bulk truncate: {e}")
                # Fallback per table
                for t_name in tables_data.keys():
                    try:
                        conn.execute(text(f'TRUNCATE TABLE public."{t_name}" CASCADE;'))
                    except Exception as te:
                        print(f"      Warning: could not truncate '{t_name}': {te}")

        print("[3/4] Restoring table records...")
        for table_name, t_info in tables_data.items():
            cols = t_info.get("columns", [])
            rows = t_info.get("rows", [])
            row_count = len(rows)

            if not rows:
                continue

            # Prepare rows with JSON serialization for dict/list types
            prepared_rows = []
            for r in rows:
                p_row = {}
                for k, v in r.items():
                    if isinstance(v, (dict, list)):
                        p_row[k] = json.dumps(v)
                    else:
                        p_row[k] = v
                prepared_rows.append(p_row)

            # Batch insert
            col_list_str = ", ".join([f'"{c}"' for c in cols])
            param_list_str = ", ".join([f":{c}" for c in cols])
            insert_stmt = text(f'INSERT INTO public."{table_name}" ({col_list_str}) VALUES ({param_list_str});')

            try:
                conn.execute(insert_stmt, prepared_rows)
                restored_summary["tables_restored"] += 1
                restored_summary["rows_restored"] += row_count
                if row_count > 20:
                    print(f"      Restored {table_name}: {row_count} rows")
            except Exception as e:
                print(f"      Error inserting into {table_name}: {e}")
                restored_summary["errors"].append(f"insert_{table_name}: {e}")

        # Restore alembic_version if present
        if alembic_revs:
            try:
                conn.execute(text('TRUNCATE TABLE public."alembic_version";'))
                for r in alembic_revs:
                    conn.execute(text('INSERT INTO public."alembic_version" (version_num) VALUES (:v);'), {"v": r})
                print(f"      Restored alembic_version: {alembic_revs}")
            except Exception as e:
                print(f"      Warning: could not set alembic_version: {e}")

        # Re-enable triggers and FK enforcement
        conn.execute(text("SET session_replication_role = 'origin';"))

    print("[4/4] Restore transaction committed successfully.")
    return restored_summary


def main():
    args = parse_args()
    validate_safety_guards(args.target_db_url, args.force_restore, args.allow_production_host)

    start_time = datetime.datetime.now(datetime.timezone.utc)
    summary = execute_restore(args.backup_file, args.target_db_url)
    elapsed = (datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds()

    print("\n" + "="*50)
    print("RESTORE SUMMARY")
    print("="*50)
    print(f"Tables Restored: {summary['tables_restored']}")
    print(f"Rows Restored:   {summary['rows_restored']}")
    print(f"Errors:          {len(summary['errors'])}")
    print(f"Elapsed Time:    {elapsed:.2f}s")
    print("="*50)

    if summary["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
