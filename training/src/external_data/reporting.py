from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.datasets.manifest_builder import write_manifest
from src.external_data.registry import load_registry

PAD_COMPARISON_COLUMNS = [
    "experiment_id",
    "training_datasets",
    "fine_tuning_dataset",
    "validation_dataset",
    "test_dataset",
    "Accuracy",
    "Precision",
    "Recall",
    "F1",
    "ROC_AUC",
    "APCER",
    "BPCER",
    "ACER",
    "EER",
    "latency_ms",
    "model_size_mb",
    "protocol_notes",
]
BEHAVIORAL_COMPARISON_COLUMNS = [
    "experiment_id",
    "dataset",
    "modality",
    "subject_count",
    "train_samples",
    "validation_samples",
    "test_samples",
    "feature_count",
    "Accuracy",
    "Precision",
    "Recall",
    "F1",
    "ROC_AUC",
    "FAR",
    "FRR",
    "EER",
    "latency_ms",
    "protocol_notes",
]


def _load_completed_records(results_dir: Path, family: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(results_dir.glob(f"{family}-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("status") != "completed":
            continue
        if not payload.get("artifact_paths"):
            raise ValueError(f"Resultado completado sin artefactos: {path}")
        records.append(payload)
    return records


def build_comparison(
    *,
    family: str,
    results_dir: str | Path,
    output_path: str | Path,
) -> Path:
    if family not in {"pad", "behavioral"}:
        raise ValueError("family debe ser pad o behavioral.")
    columns = (
        PAD_COMPARISON_COLUMNS if family == "pad" else BEHAVIORAL_COMPARISON_COLUMNS
    )
    records = _load_completed_records(Path(results_dir), family)
    frame = pd.DataFrame(records).reindex(columns=columns)
    if records and frame["protocol_notes"].isna().any():
        raise ValueError("Toda comparación debe documentar diferencias de protocolo.")
    return write_manifest(frame, output_path, csv_copy=True)


def readiness_evidence(
    *,
    registry_path: str | Path,
    pad_comparison: str | Path,
    behavioral_comparison: str | Path,
    frozen_test_consumed: bool,
) -> dict[str, object]:
    registry = load_registry(registry_path)
    downloaded = [entry.dataset_id for entry in registry.datasets if entry.status == "downloaded"]
    pad_path = Path(pad_comparison)
    behavioral_path = Path(behavioral_comparison)
    pad_rows = len(pd.read_parquet(pad_path)) if pad_path.is_file() else 0
    behavioral_rows = (
        len(pd.read_parquet(behavioral_path)) if behavioral_path.is_file() else 0
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "downloaded_datasets": downloaded,
        "pad_completed_experiments": pad_rows,
        "behavioral_completed_experiments": behavioral_rows,
        "frozen_test_consumed": frozen_test_consumed,
    }


def determine_readiness(evidence: dict[str, object]) -> str:
    downloaded = len(evidence["downloaded_datasets"])
    pad = int(evidence["pad_completed_experiments"])
    behavioral = int(evidence["behavioral_completed_experiments"])
    if downloaded >= 4 and pad >= 4 and behavioral >= 4:
        return "pilot_only"
    return "not_ready"


def generate_readiness_report(
    *,
    registry_path: str | Path,
    pad_comparison: str | Path,
    behavioral_comparison: str | Path,
    output_path: str | Path,
    frozen_test_consumed: bool = False,
) -> Path:
    evidence = readiness_evidence(
        registry_path=registry_path,
        pad_comparison=pad_comparison,
        behavioral_comparison=behavioral_comparison,
        frozen_test_consumed=frozen_test_consumed,
    )
    status = determine_readiness(evidence)
    sections = [
        ("Generalización", "Pendiente de resultados cross-dataset y pruebas propias."),
        ("Ataques no vistos", "No demostrado; deben incluirse impresiones, teléfono y monitor."),
        ("Dispositivos no vistos", "Pendiente de cámaras y equipos reales de la operación."),
        ("Iluminación", "Pendiente de estratificación por condiciones reales."),
        ("Sesgo", "Requiere análisis por participante, dispositivo y contexto."),
        ("Falsos positivos", "No estimados en prueba propia congelada."),
        ("Falsos negativos", "No estimados en prueba propia congelada."),
        ("Latencia", "Debe medirse con el artefacto candidato en Cloud Run."),
        ("Memoria", "Debe medirse con límites reales del servicio."),
        ("Disponibilidad de cámara", "Definir reverificación y modo degradado."),
        ("Cambios conductuales", "Evaluar día, fatiga, hardware, navegador y actividad."),
        ("Drift", "Monitorear distribuciones; nunca reentrenar automáticamente."),
        ("Privacidad", "Conservar solo timings/coordenadas normalizadas y trazabilidad."),
        ("Licencias", "Los datasets restringidos siguen bloqueados hasta acuerdo."),
        ("Limitaciones", "Un benchmark externo no garantiza ausencia de fallos en producción."),
    ]
    lines = [
        "# Informe de preparación para producción — Fase 7.5",
        "",
        f"**Estado: `{status}`**",
        "",
        "Escala permitida: `not_ready`, `pilot_only`, "
        "`ready_for_controlled_deployment` y `ready_for_limited_production`. "
        "Los dos últimos estados requieren evaluación propia congelada y "
        "aprobación humana; no se derivan automáticamente de una métrica alta.",
        "",
        "Este estado se deriva únicamente de artefactos verificables; no se fabricaron métricas.",
        "",
        "## Evidencia",
        "",
        "```json",
        json.dumps(evidence, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    for title, body in sections:
        lines.extend([f"## {title}", "", body, ""])
    lines.extend(
        [
            "## Monitoreo posterior",
            "",
            "- Distribución agregada de scores y drift de características.",
            "- Reverificaciones, falsas alertas reportadas y fallos de cámara.",
            "- Activación de modo degradado, latencia y versiones desplegadas.",
            "- Sin eventos crudos, texto, teclas, imágenes ni reentrenamiento automático.",
            "",
            "Todo nuevo entrenamiento requiere consentimiento, versión de dataset, "
            "splits separados, evaluación, aprobación y despliegue controlado.",
            "",
        ]
    )
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
