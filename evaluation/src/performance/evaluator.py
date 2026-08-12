from __future__ import annotations

import json
import platform

import pandas as pd
import psutil

from evaluation.src.common.config import FinalEvaluationConfig, PROJECT_ROOT
from evaluation.src.common.io import JsonValue, json_value, read_json, write_json_atomic
from evaluation.src.common.metrics import latency_statistics, save_histogram


def _approved_model_size(config: FinalEvaluationConfig) -> int:
    approval = read_json(config.paths.integration_approval)
    checksums = approval.get("checksums")
    if not isinstance(checksums, dict):
        return 0
    size = 0
    for relative in checksums:
        path = (PROJECT_ROOT / relative).resolve()
        try:
            path.relative_to(PROJECT_ROOT)
        except ValueError:
            continue
        if path.is_file():
            size += path.stat().st_size
    return size


def evaluate_performance(
    predictions: pd.DataFrame,
    config: FinalEvaluationConfig,
) -> tuple[pd.DataFrame, dict[str, JsonValue]]:
    columns = [
        column
        for column in (
            "facial_decode_ms",
            "facial_model_inference_ms",
            "facial_latency_ms",
            "pad_decode_ms",
            "pad_model_inference_ms",
            "pad_latency_ms",
            "behavioral_latency_ms",
            "fusion_latency_ms",
            "total_inference_latency_ms",
        )
        if column in predictions
    ]
    if not columns:
        raise ValueError("No existen mediciones de latencia.")
    rows: list[dict[str, object]] = []
    for column in columns:
        values = predictions[column].dropna().astype(float)
        if values.empty:
            continue
        stage = column.removesuffix("_ms")
        for index, value in enumerate(values):
            rows.append(
                {
                    "stage": stage,
                    "latency_ms": float(value),
                    "measurement_order": index,
                    "temperature": "cold" if index == 0 else "warm",
                    "device": "runtime-selected",
                    "source": "single_final_test_pass",
                }
            )
    measurements = pd.DataFrame(rows)
    summaries = {
        stage: latency_statistics(
            group["latency_ms"].astype(float).to_numpy()
        )
        for stage, group in measurements.groupby("stage")
    }
    process = psutil.Process()
    summary: dict[str, object] = {
        "latency": summaries,
        "warmup_iterations_configured": config.latency.warmup_iterations,
        "measurement_iterations_configured": (
            config.latency.measurement_iterations
        ),
        "measurement_policy": (
            "Una sola pasada sobre test; no se repitieron muestras para evitar "
            "uso iterativo del conjunto congelado."
        ),
        "cold_start_reported_separately": True,
        "rss_before_models_bytes": predictions.attrs.get(
            "rss_before_models_bytes"
        ),
        "rss_after_models_bytes": predictions.attrs.get(
            "rss_after_models_bytes"
        ),
        "peak_rss_during_inference_bytes": predictions.attrs.get(
            "peak_rss_during_inference_bytes"
        ),
        "model_load_ms": predictions.attrs.get("model_load_ms"),
        "rss_bytes_after_inference": int(process.memory_info().rss),
        "system_ram_bytes": int(psutil.virtual_memory().total),
        "approved_model_bytes": _approved_model_size(config),
        "cpu": platform.processor() or platform.machine(),
        "concurrency": [
            {
                "level": level,
                "status": "requires_separate_validation_fixture",
            }
            for level in config.latency.concurrency_levels
        ],
        "production_load_test_executed": False,
        "unavailable_stage_measurements": {
            "facial_detection_vs_embedding_vs_comparison": (
                "El runtime aprobado expone únicamente decode, inferencia "
                "facial agregada y total."
            ),
            "behavioral_scaling_vs_autoencoder": (
                "El runtime aprobado expone latencia conductual agregada."
            ),
            "normalization": (
                "No instrumentada por separado en el runtime aprobado."
            ),
            "postgresql_write": (
                "Requiere fixture de integración separada del test."
            ),
            "http_response": (
                "Requiere fixture de integración separada del test."
            ),
            "frontend_capture_to_backend": (
                "Requiere instrumentación end-to-end del frontend."
            ),
        },
    }
    output = config.paths.output_directory / "performance"
    output.mkdir(parents=True, exist_ok=True)
    measurements.to_parquet(
        output / "latency_measurements.parquet", index=False
    )
    typed_summary = json_value(summary)
    if not isinstance(typed_summary, dict):
        raise TypeError("El resumen de rendimiento debe ser un objeto.")
    write_json_atomic(
        output / "performance_summary.json", typed_summary
    )
    total = measurements[
        measurements["stage"] == "total_inference_latency"
    ]["latency_ms"]
    if not total.empty:
        save_histogram(
            total.astype(float).to_numpy(),
            config.paths.output_directory / "figures" / "latency.png",
            title="Distribución de latencia total",
            x_label="Latencia total (ms)",
        )
    (output / "performance_report.md").write_text(
        "\n".join(
            [
                "# Latencia y rendimiento",
                "",
                "Cold start y mediciones warm se reportan por separado.",
                "No se ejecutó carga contra producción.",
                "",
                "```json",
                json.dumps(typed_summary, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return measurements, typed_summary
