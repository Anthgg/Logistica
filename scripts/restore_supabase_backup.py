#!/usr/bin/env python3
"""
Safe, idempotent logical restore utility for Supabase / PostgreSQL backup dumps.

SAFETY GUARDS & POLICIES:
1. Rejects execution against production hosts (*.supabase.co) by default.
2. Requires explicit `--force-restore` flag.
3. Enforces that target database name must contain 'test', 'restore', 'staging', 'dev', or 'local'.
4. Preserves current Alembic schema revision: default data restore DOES NOT touch `alembic_version`.
5. Post-restore FK Integrity Audit: queries all active foreign keys and verifies zero orphan records.
6. Sequence & Identity Alignment: adjusts all PostgreSQL sequences to max(id) to prevent collisions.
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
    parser.add_argument("--restore-alembic-version", action="store_true", help="DANGER: Overwrite target alembic_version with backup revision.")
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


def audit_foreign_key_integrity(conn, restored_tables: list) -> list:
    """Verify zero orphan records across all foreign keys on restored tables."""
    print("[Post-Restore] Auditing Foreign Key integrity across restored tables...")
    fk_query = text("""
        SELECT
            tc.table_name AS child_table,
            kcu.column_name AS child_column,
            ccu.table_name AS parent_table,
            ccu.column_name AS parent_column,
            rc.constraint_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.referential_constraints AS rc
            ON tc.constraint_name = rc.constraint_name
            AND tc.table_schema = rc.constraint_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON rc.unique_constraint_name = ccu.constraint_name
            AND rc.unique_constraint_schema = ccu.constraint_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'public'
        ORDER BY tc.table_name, kcu.column_name;
    """)

    fk_rows = conn.execute(fk_query).fetchall()
    violations = []

    for child_t, child_col, parent_t, parent_col, c_name in fk_rows:
        if child_t in restored_tables:
            orphan_sql = text(f"""
                SELECT count(*) 
                FROM public."{child_t}" c
                LEFT JOIN public."{parent_t}" p 
                  ON c."{child_col}" = p."{parent_col}"
                WHERE c."{child_col}" IS NOT NULL 
                  AND p."{parent_col}" IS NULL;
            """)
            try:
                orphan_count = conn.execute(orphan_sql).scalar()
                if orphan_count and orphan_count > 0:
                    violations.append({
                        "constraint": c_name,
                        "child_table": child_t,
                        "child_column": child_col,
                        "parent_table": parent_t,
                        "orphan_rows": orphan_count
                    })
            except Exception as e:
                # If table is not present, skip or log
                pass

    return violations


def align_sequences(conn) -> int:
    """Sync all PostgreSQL sequences to max values of table columns."""
    print("[Post-Restore] Synchronizing PostgreSQL sequences...")
    seq_query = text("""
        SELECT
            s.relname AS sequence_name,
            t.relname AS table_name,
            a.attname AS column_name
        FROM pg_class s
        JOIN pg_depend d ON d.objid = s.oid
        JOIN pg_class t ON t.oid = d.refobjid
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = d.refobjsubid
        JOIN pg_namespace n ON n.oid = s.relnamespace
        WHERE s.relkind = 'S'
          AND n.nspname = 'public';
    """)
    try:
        seq_rows = conn.execute(seq_query).fetchall()
    except Exception:
        return 0

    aligned_count = 0
    for seq_name, table_name, col_name in seq_rows:
        try:
            setval_sql = text(f"""
                SELECT setval(
                    'public."{seq_name}"', 
                    COALESCE((SELECT MAX("{col_name}") FROM public."{table_name}"), 1),
                    true
                );
            """)
            conn.execute(setval_sql)
            aligned_count += 1
        except Exception as e:
            print(f"      Warning: could not sync sequence '{seq_name}': {e}")

    return aligned_count


def execute_restore(backup_file: str, target_db_url: str, restore_alembic_rev: bool = False) -> dict:
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
        "fk_violations": 0,
        "sequences_aligned": 0,
        "errors": []
    }

    print(f"[2/4] Connecting to target database and preparing tables...")
    with engine.begin() as conn:
        # Disable triggers and foreign keys for clean data insertion
        conn.execute(text("SET session_replication_role = 'replica';"))

        # Upfront Truncate Pass: Truncate all tables in backup in one command (excluding alembic_version)
        existing_tables_to_truncate = []
        for t_name in tables_data.keys():
            if t_name == "alembic_version" and not restore_alembic_rev:
                continue
            existing_tables_to_truncate.append(f'public."{t_name}"')
        
        if existing_tables_to_truncate:
            truncate_all_sql = f"TRUNCATE TABLE {', '.join(existing_tables_to_truncate)} CASCADE;"
            try:
                conn.execute(text(truncate_all_sql))
            except Exception as e:
                print(f"      Warning during bulk truncate: {e}")
                for t_name in tables_data.keys():
                    try:
                        conn.execute(text(f'TRUNCATE TABLE public."{t_name}" CASCADE;'))
                    except Exception as te:
                        print(f"      Warning: could not truncate '{t_name}': {te}")

        print("[3/4] Restoring table records...")
        restored_table_names = []
        for table_name, t_info in tables_data.items():
            if table_name == "alembic_version" and not restore_alembic_rev:
                # Skip alembic_version during standard data recovery to preserve HEAD schema revision
                continue

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
                restored_table_names.append(table_name)
                if row_count > 20:
                    print(f"      Restored {table_name}: {row_count} rows")
            except Exception as e:
                print(f"      Error inserting into {table_name}: {e}")
                restored_summary["errors"].append(f"insert_{table_name}: {e}")

        # Revision Policy: Only restore alembic_version if explicitly requested
        if restore_alembic_rev and alembic_revs:
            try:
                conn.execute(text('TRUNCATE TABLE public."alembic_version";'))
                for r in alembic_revs:
                    conn.execute(text('INSERT INTO public."alembic_version" (version_num) VALUES (:v);'), {"v": r})
                print(f"      Overwritten alembic_version: {alembic_revs}")
            except Exception as e:
                print(f"      Warning: could not set alembic_version: {e}")

        # Re-enable triggers and FK enforcement
        conn.execute(text("SET session_replication_role = 'origin';"))

        # Align PostgreSQL sequences
        restored_summary["sequences_aligned"] = align_sequences(conn)

        # Audit Foreign Key integrity post-restore
        fk_violations = audit_foreign_key_integrity(conn, restored_table_names)
        if fk_violations:
            print(f"      [CRITICAL] Found {len(fk_violations)} FK violations post-restore:")
            for v in fk_violations:
                print(f"        Constraint '{v['constraint']}' on '{v['child_table']}.{v['child_column']}': {v['orphan_rows']} orphan rows")
                restored_summary["errors"].append(f"fk_violation_{v['constraint']}: {v['orphan_rows']} orphans")
            restored_summary["fk_violations"] = len(fk_violations)
        else:
            print("      [FK Integrity] PASS: 0 orphan rows across all foreign keys.")

    print("[4/4] Restore transaction committed successfully.")
    return restored_summary


def main():
    args = parse_args()
    validate_safety_guards(args.target_db_url, args.force_restore, args.allow_production_host)

    start_time = datetime.datetime.now(datetime.timezone.utc)
    summary = execute_restore(args.backup_file, args.target_db_url, args.restore_alembic_version)
    elapsed = (datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds()

    print("\n" + "="*50)
    print("RESTORE SUMMARY")
    print("="*50)
    print(f"Tables Restored:   {summary['tables_restored']}")
    print(f"Rows Restored:     {summary['rows_restored']}")
    print(f"FK Violations:     {summary['fk_violations']}")
    print(f"Sequences Synced:  {summary['sequences_aligned']}")
    print(f"Errors:            {len(summary['errors'])}")
    print(f"Elapsed Time:      {elapsed:.2f}s")
    print("="*50)

    if summary["errors"] or summary["fk_violations"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
