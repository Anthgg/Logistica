"""Audit pending Alembic revisions against the live PostgreSQL schema."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import sqlalchemy as sa
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory

from app.database.session import engine


def _ancestor_ids(script: ScriptDirectory, roots: tuple[str, ...]) -> set[str]:
    ancestors: set[str] = set()
    pending = list(roots)
    while pending:
        revision_id = pending.pop()
        if revision_id in ancestors:
            continue
        revision = script.get_revision(revision_id)
        if revision is None:
            continue
        ancestors.add(revision.revision)
        down_revisions = revision.down_revision
        if isinstance(down_revisions, str):
            pending.append(down_revisions)
        elif down_revisions:
            pending.extend(down_revisions)
    return ancestors


def _literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _migration_operations(path: Path) -> dict[str, list[dict[str, str]]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    operations: dict[str, list[dict[str, str]]] = {
        "create_tables": [],
        "add_columns": [],
        "rename_tables": [],
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if not isinstance(node.func.value, ast.Name) or node.func.value.id != "op":
            continue
        if node.func.attr == "create_table" and node.args:
            table_name = _literal_string(node.args[0])
            if table_name:
                operations["create_tables"].append({"table": table_name})
        elif node.func.attr == "add_column" and len(node.args) >= 2:
            table_name = _literal_string(node.args[0])
            column_call = node.args[1]
            column_name = None
            if isinstance(column_call, ast.Call) and column_call.args:
                column_name = _literal_string(column_call.args[0])
            if table_name and column_name:
                operations["add_columns"].append(
                    {"table": table_name, "column": column_name}
                )
        elif node.func.attr == "rename_table" and len(node.args) >= 2:
            old_name = _literal_string(node.args[0])
            new_name = _literal_string(node.args[1])
            if old_name and new_name:
                operations["rename_tables"].append(
                    {"old_table": old_name, "new_table": new_name}
                )
    return operations


def main() -> None:
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)

    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        current_heads = tuple(context.get_current_heads())
        expected_heads = tuple(script.get_heads())
        applied_ids = _ancestor_ids(script, current_heads)
        expected_ids = _ancestor_ids(script, expected_heads)
        pending_ids = expected_ids - applied_ids
        inspector = sa.inspect(connection)
        existing_tables = set(inspector.get_table_names())
        columns_by_table: dict[str, set[str]] = {}
        movement_columns = (
            {column["name"] for column in inspector.get_columns("inventory_movements")}
            if "inventory_movements" in existing_tables
            else set()
        )
        movement_indexes = (
            [index["name"] for index in inspector.get_indexes("inventory_movements")]
            if "inventory_movements" in existing_tables
            else []
        )
        movement_constraints = (
            {
                "primary_key": inspector.get_pk_constraint("inventory_movements").get(
                    "name"
                ),
                "unique": [
                    constraint["name"]
                    for constraint in inspector.get_unique_constraints(
                        "inventory_movements"
                    )
                ],
                "foreign_keys": [
                    constraint["name"]
                    for constraint in inspector.get_foreign_keys("inventory_movements")
                ],
                "checks": [
                    constraint["name"]
                    for constraint in inspector.get_check_constraints("inventory_movements")
                ],
            }
            if "inventory_movements" in existing_tables
            else {}
        )

        revisions = []
        for revision in reversed(list(script.walk_revisions(base="base", head="heads"))):
            if revision.revision not in pending_ids:
                continue
            path = Path(revision.path)
            operations = _migration_operations(path)
            for item in operations["create_tables"]:
                item["exists"] = str(item["table"] in existing_tables).lower()
            for item in operations["add_columns"]:
                table_name = item["table"]
                if table_name in existing_tables and table_name not in columns_by_table:
                    columns_by_table[table_name] = {
                        column["name"] for column in inspector.get_columns(table_name)
                    }
                item["exists"] = str(
                    item["column"] in columns_by_table.get(table_name, set())
                ).lower()
            revisions.append(
                {
                    "revision": revision.revision,
                    "description": revision.doc,
                    "operations": operations,
                }
            )

    print(
        json.dumps(
            {
                "current_heads": current_heads,
                "expected_heads": expected_heads,
                "pending_revision_count": len(revisions),
                "phase044_inventory_movements_shape": {
                    "canonical_markers_present": {
                        "ledger_sequence",
                        "movement_hash",
                    }.issubset(movement_columns),
                    "legacy_markers_present": bool(
                        {"previous_stock", "resulting_stock"} & movement_columns
                    ),
                    "legacy_backup_exists": "inventory_movements_legacy"
                    in existing_tables,
                    "legacy_constraint_names": movement_constraints,
                    "legacy_index_names": sorted(movement_indexes),
                },
                "pending_revisions": revisions,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
