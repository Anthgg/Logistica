"""Catalog loader module.

Loads the central document catalog JSON file into structured Python dicts/objects.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CATALOG_DIR = Path(__file__).parent
DEFAULT_CATALOG_FILE = CATALOG_DIR / "catalog_v1_0_0.json"


def load_catalog_json(path: Path | str | None = None) -> dict[str, Any]:
    """Reads and parses the central document catalog JSON file."""
    target_path = Path(path) if path else DEFAULT_CATALOG_FILE
    if not target_path.exists():
        raise FileNotFoundError(f"Document catalog file not found at: {target_path}")

    with open(target_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data
