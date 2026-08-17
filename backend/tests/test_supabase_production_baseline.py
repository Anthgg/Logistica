"""
Unit and regression tests for Supabase production baseline and restore utility.
"""

import os
import sys
import subprocess
import pytest


def test_alembic_single_head():
    """Verify that Alembic has exactly one canonical HEAD and it is hj460110046dk."""
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    res = subprocess.run(
        [sys.executable, "-m", "alembic", "heads"],
        cwd=backend_dir,
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    heads = [line.strip().split()[0] for line in res.stdout.splitlines() if line.strip()]
    assert len(heads) == 1
    # Tras integrar F004 la cadena es gi450410045dk -> gj450510045vr -> hj460110046dk,
    # asi que la cabeza es determinista. Aceptar varias convertiria este test en uno
    # que no detecta una revision mal encadenada.
    assert heads[0] == "hj460110046dk"


def test_restore_script_missing_force_flag():
    """Verify restore utility aborts if --force-restore is omitted."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    script_path = os.path.join(root_dir, "scripts", "restore_supabase_backup.py")

    res = subprocess.run(
        [
            sys.executable,
            script_path,
            "--backup-file", "dummy.json",
            "--target-db-url", "postgresql+psycopg://user:pass@127.0.0.1:5432/continuous_auth_test"
        ],
        capture_output=True,
        text=True
    )
    assert res.returncode != 0
    assert "--force-restore" in res.stdout or "--force-restore" in res.stderr


def test_restore_script_blocks_production_host():
    """Verify restore utility blocks *.supabase.co hosts without explicit override."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    script_path = os.path.join(root_dir, "scripts", "restore_supabase_backup.py")

    res = subprocess.run(
        [
            sys.executable,
            script_path,
            "--backup-file", "dummy.json",
            "--target-db-url", "postgresql+psycopg://postgres:secret@db.xyz.supabase.co:5432/postgres",
            "--force-restore"
        ],
        capture_output=True,
        text=True
    )
    assert res.returncode != 0
    assert "remote Supabase production instance" in res.stdout


def test_restore_script_blocks_unsafe_database_name():
    """Verify restore utility blocks databases not containing test/restore/staging tokens."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    script_path = os.path.join(root_dir, "scripts", "restore_supabase_backup.py")

    res = subprocess.run(
        [
            sys.executable,
            script_path,
            "--backup-file", "dummy.json",
            "--target-db-url", "postgresql+psycopg://user:pass@127.0.0.1:5432/production_live_db",
            "--force-restore"
        ],
        capture_output=True,
        text=True
    )
    assert res.returncode != 0
    assert "does not match safe patterns" in res.stdout
