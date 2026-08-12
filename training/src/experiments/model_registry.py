from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.common.serialization import write_json_atomic

MODEL_STATUSES = {"experimental", "candidate", "rejected", "approved_for_integration"}


class ModelRegistry:
    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {"schema_version": "1.0", "models": []}
        import json

        return json.loads(self.path.read_text(encoding="utf-8"))

    def register(self, record: dict[str, Any], *, force: bool = False) -> None:
        status = str(record.get("status"))
        if status not in MODEL_STATUSES:
            raise ValueError(f"Estado de modelo inválido: {status}.")
        version = str(record.get("model_version") or "")
        if not version or version.casefold() in {"final", "final2", "definitivo", "ahora_si"}:
            raise ValueError("model_version debe ser explícita y versionada.")
        registry = self.read()
        models = list(registry.get("models", []))
        existing = [
            item
            for item in models
            if item.get("model_version") == version
            and item.get("participant_id") == record.get("participant_id")
        ]
        if existing and not force:
            raise FileExistsError(f"El modelo {version} ya está registrado.")
        if existing:
            models = [item for item in models if item not in existing]
        models.append(
            {
                **record,
                "registered_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        registry["models"] = sorted(
            models,
            key=lambda item: (
                str(item.get("model_family")),
                str(item.get("participant_id") or ""),
                str(item.get("model_version")),
            ),
        )
        write_json_atomic(self.path, registry)
