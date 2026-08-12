from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def generate_training_report(
    *,
    report_root: Path,
    models_root: Path,
    dataset_version: str,
    protocol_version: str,
) -> Path:
    facial = _load_json(report_root / "facial" / "facial_validation_metrics.json")
    pad = _load_json(report_root / "pad" / "pad_validation_metrics.json")
    behavioral = _load_json(report_root / "behavioral" / "behavioral_summary.json")
    registry = _load_json(models_root / "registry" / "model_registry.json") or {
        "models": []
    }
    lines = [
        "# Informe técnico de entrenamiento biométrico",
        "",
        "## 1. Objetivo",
        "",
        "Entrenar y calibrar por separado ArcFace, MobileNetV2 PAD y autoencoders conductuales.",
        "",
        "## 2. Dataset y protocolo",
        "",
        f"- Dataset: `{dataset_version}`",
        f"- Protocolo: `{protocol_version}`",
        "- Particiones utilizadas: train y validation.",
        "- Uso del conjunto test congelado: 0 filas.",
        "",
        "## 3. Verificación facial ArcFace",
        "",
        "```json",
        json.dumps(facial or {"status": "not_generated"}, ensure_ascii=False, indent=2),
        "```",
        "",
        "## 4. MobileNetV2 PAD",
        "",
        "```json",
        json.dumps(pad or {"status": "not_generated"}, ensure_ascii=False, indent=2),
        "```",
        "",
        "## 5. Autoencoders conductuales",
        "",
        "```json",
        json.dumps(
            behavioral or {"status": "not_generated"}, ensure_ascii=False, indent=2
        ),
        "```",
        "",
        "## 6. Modelos y checksums",
        "",
        "```json",
        json.dumps(registry, ensure_ascii=False, indent=2),
        "```",
        "",
        "## 7. Limitaciones y preparación para Fase 9",
        "",
        "- No se implementó fusión de puntajes.",
        "- No se integraron modelos en FastAPI ni Cloud Run.",
        "- No se realizó evaluación definitiva con test.",
        "- Los resultados ausentes no se sustituyen por valores inventados.",
        "",
    ]
    destination = report_root / "training_report.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")
    return destination
