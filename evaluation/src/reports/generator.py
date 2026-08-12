from __future__ import annotations

import importlib.metadata
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import pandas as pd
import psutil

from evaluation.src.common.config import FinalEvaluationConfig
from evaluation.src.common.io import JsonValue, json_value, sha256_file, write_json_atomic
from evaluation.src.common.metrics import save_bar_plot


def _version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def _docker_version() -> str | None:
    try:
        result = subprocess.run(
            ["docker", "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _flatten_metrics(
    components: Mapping[str, Mapping[str, JsonValue]],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    accepted = (
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "pr_auc",
        "far",
        "frr",
        "eer",
        "apcer",
        "bpcer",
        "acer",
    )
    for component, metrics in components.items():
        for metric in accepted:
            value = metrics.get(metric)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                rows.append(
                    {
                        "component": component,
                        "metric": metric,
                        "value": float(value),
                    }
                )
        macro = metrics.get("macro_statistics")
        if isinstance(macro, dict):
            for metric in accepted:
                aggregate = macro.get(metric)
                if not isinstance(aggregate, dict):
                    continue
                value = aggregate.get("mean")
                if isinstance(value, (int, float)) and not isinstance(
                    value, bool
                ):
                    rows.append(
                        {
                            "component": component,
                            "metric": f"{metric}_macro_mean",
                            "value": float(value),
                        }
                    )
    return pd.DataFrame(rows)


def _report_markdown(
    config: FinalEvaluationConfig,
    summary: Mapping[str, JsonValue],
) -> str:
    return "\n".join(
        [
            "# Informe de evaluación final",
            "",
            "## 1. Objetivo",
            "",
            "Evaluar el sistema de autenticación continua multimodal sin reajustar modelos ni decisiones con el conjunto test.",
            "",
            "## 2. Arquitectura evaluada",
            "",
            "FastAPI, ArcFace, PAD MobileNetV2, autoencoders conductuales y fusión tardía ponderada.",
            "",
            "## 3. Dataset",
            "",
            f"Versión: `{config.dataset_version}`. Protocolo: `{config.protocol_version}`.",
            "",
            "## 4. Participantes",
            "",
            "Los resultados usan códigos seudonimizados; no se publica una clave de vinculación.",
            "",
            "## 5. Sesiones",
            "",
            "La comparación usa la sesión experimental como unidad pareada.",
            "",
            "## 6. Protocolos",
            "",
            f"Protocolo aprobado: `{config.protocol_version}`.",
            "",
            "## 7. División de datos",
            "",
            "Train y validation se verificaron únicamente para descartar fugas; las métricas finales proceden del test.",
            "",
            "## 8. Congelamiento de test",
            "",
            "El manifiesto test fue verificado mediante SHA-256 después de crear el lock y el marcador de inicio.",
            "",
            "## 9. Versiones de modelos",
            "",
            f"- Facial: `{config.approved_versions.facial}`",
            f"- PAD: `{config.approved_versions.pad}`",
            f"- Conductual: `{config.approved_versions.behavioral}`",
            "",
            "## 10. Configuración de fusión",
            "",
            f"- Fusión: `{config.approved_versions.fusion}`",
            f"- Normalización: `{config.approved_versions.normalization}`",
            "Los pesos, límites e histéresis proceden de la aprobación técnica.",
            "",
            "## 11. Entorno de evaluación",
            "",
            "El equipo, runtime y versiones de librerías se conservan en `run_metadata.json`.",
            "",
            "## 12. Métricas faciales",
            "",
            "Véanse `facial/facial_test_metrics.json` y sus predicciones seudonimizadas.",
            "",
            "## 13. Métricas PAD",
            "",
            "Véanse `pad/pad_test_metrics.json`, incluidos APCER, BPCER y ACER.",
            "",
            "## 14. Métricas conductuales",
            "",
            "Se informan resultados individuales y agregados sin reajustar scalers ni umbrales.",
            "",
            "## 15. Métricas multimodales",
            "",
            "Véase `fusion/fusion_test_metrics.json`, con disponibilidad, histéresis y tiempo hasta detección.",
            "",
            "## 16. Resultados de ablación",
            "",
            "Las variantes fueron aprobadas antes de abrir test y utilizaron la misma población de casos completos.",
            "",
            "## 17. Pretest y postest",
            "",
            "La unidad de análisis es la sesión experimental. El pretest representa autenticación estática posterior al login.",
            "",
            "## 18. Latencia",
            "",
            "Cold start y pasada warm se separan sin repetir muestras del test.",
            "",
            "## 19. Memoria",
            "",
            "Se registran RSS antes/después de modelos, pico observado y tamaño aprobado.",
            "",
            "## 20. Concurrencia",
            "",
            "La concurrencia 1/5/10 queda reservada para una fixture de validation separada; no se ejecutó carga contra producción.",
            "",
            "## 21. Intervalos de confianza",
            "",
            "Se aplicaron bootstrap reproducible y Wilson al 95 % según el estimando.",
            "",
            "## 22. Pruebas estadísticas",
            "",
            "Se aplicaron McNemar exacta, la prueba pareada compatible con los supuestos y Friedman cuando los datos lo permitieron.",
            "",
            "## 23. Tamaños de efecto",
            "",
            "Se informan odds ratio, Cohen d pareada o r de Wilcoxon y Kendall W cuando corresponden.",
            "",
            "## 24. Limitaciones",
            "",
            "- Diseño preexperimental: las diferencias no establecen causalidad absoluta.",
            "- El rendimiento depende del equipo y del conjunto disponible.",
            "- Las configuraciones ausentes o no aprobadas detienen la ejecución.",
            "- La concurrencia requiere una fixture de validation separada para no repetir test.",
            "",
            "## 25. Amenazas a la validez",
            "",
            "La población, escenarios, dispositivos y condiciones delimitan la validez externa; la instrumentación y el baseline estático delimitan la validez interna.",
            "",
            "## 26. Consideraciones éticas",
            "",
            "La evaluación se limita a sesiones consentidas y a los fines declarados del protocolo.",
            "",
            "## 27. Privacidad",
            "",
            "No se publican nombres, correos, imágenes, embeddings, texto escrito, cookies, tokens ni rutas internas.",
            "",
            "## 28. Fallos técnicos",
            "",
            "Los fallos, si existieron, quedaron en `evaluation_failure.json` sin payloads sensibles.",
            "",
            "## 29. Resultados por participante",
            "",
            "Los resultados seudonimizados están en los artefactos conductuales y exportaciones estadísticas.",
            "",
            "## 30. Conclusiones técnicas",
            "",
            "Las conclusiones deben basarse exclusivamente en los valores producidos por esta ejecución bloqueada y reproducible.",
            "",
            "## 31. Recomendaciones",
            "",
            "Validar externamente, medir concurrencia con validation y conservar el protocolo antes de generalizar a producción.",
            "",
            "## 32. Versiones y checksums",
            "",
            "Las versiones están en este informe y `run_metadata.json`; los hashes finales están en `artifact_checksums.json`.",
            "",
            "## Resumen estructurado",
            "",
            "```json",
            json.dumps(summary, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )


def _metric_value(
    metrics: Mapping[str, JsonValue],
    metric: str,
) -> float | None:
    value = metrics.get(metric)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    macro = metrics.get("macro_statistics")
    if not isinstance(macro, dict):
        return None
    aggregate = macro.get(metric)
    if not isinstance(aggregate, dict):
        return None
    mean = aggregate.get("mean")
    if isinstance(mean, (int, float)) and not isinstance(mean, bool):
        return float(mean)
    return None


def _write_thesis_tables(
    output: Path,
    *,
    component_metrics: Mapping[str, Mapping[str, JsonValue]],
    thesis_metrics: pd.DataFrame,
    ablation_summary: pd.DataFrame,
    comparison: pd.DataFrame,
    latency: pd.DataFrame,
    statistical_tests: pd.DataFrame,
    confidence_intervals: pd.DataFrame,
    effect_sizes: pd.DataFrame,
) -> None:
    tables = output / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    participant_distribution = (
        comparison.groupby("participant_id")
        .size()
        .rename("session_count")
        .reset_index()
    )
    participant_distribution.to_csv(
        tables / "participant_distribution.csv", index=False
    )
    (
        comparison.groupby("true_condition")
        .size()
        .rename("session_count")
        .reset_index()
    ).to_csv(tables / "session_distribution.csv", index=False)
    quality_rows: list[dict[str, object]] = []
    for component, metrics in component_metrics.items():
        for metric in (
            "capture_rejection_rate",
            "rejection_rate",
            "unavailable_decision_rate",
        ):
            value = metrics.get(metric)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                quality_rows.append(
                    {
                        "component": component,
                        "metric": metric,
                        "value": float(value),
                    }
                )
    pd.DataFrame(quality_rows).to_csv(
        tables / "capture_quality.csv", index=False
    )
    thesis_metrics.to_csv(tables / "component_metrics.csv", index=False)
    ablation_summary.to_csv(tables / "ablation_results.csv", index=False)
    comparison.to_csv(tables / "pretest_posttest.csv", index=False)
    latency.to_csv(tables / "latency.csv", index=False)
    statistical_tests.to_csv(
        tables / "statistical_tests.csv", index=False
    )
    confidence_intervals.to_csv(
        tables / "confidence_intervals.csv", index=False
    )
    effect_sizes.to_csv(tables / "effect_sizes.csv", index=False)
    pd.DataFrame(
        [
            {
                "topic": "design",
                "limitation": (
                    "Diseño preexperimental; no demuestra causalidad absoluta."
                ),
            },
            {
                "topic": "concurrency",
                "limitation": (
                    "Debe medirse con validation sin repetir el test final."
                ),
            },
        ]
    ).to_csv(tables / "errors_and_limitations.csv", index=False)


def generate_final_outputs(
    config: FinalEvaluationConfig,
    *,
    component_metrics: Mapping[str, Mapping[str, JsonValue]],
    ablation_summary: pd.DataFrame,
    comparison: pd.DataFrame,
    comparison_summary: Mapping[str, JsonValue],
    latency: pd.DataFrame,
    performance_summary: Mapping[str, JsonValue],
    statistical_tests: pd.DataFrame,
    confidence_intervals: pd.DataFrame,
    effect_sizes: pd.DataFrame,
) -> dict[str, JsonValue]:
    output = config.paths.output_directory
    output.mkdir(parents=True, exist_ok=True)
    summary_value = json_value(
        {
            "dataset_version": config.dataset_version,
            "protocol_version": config.protocol_version,
            "approved_versions": {
                "facial": config.approved_versions.facial,
                "pad": config.approved_versions.pad,
                "behavioral": config.approved_versions.behavioral,
                "fusion": config.approved_versions.fusion,
                "normalization": config.approved_versions.normalization,
            },
            "components": dict(component_metrics),
            "comparison": dict(comparison_summary),
            "performance": dict(performance_summary),
            "ablation_configuration_count": len(ablation_summary),
            "statistical_test_count": len(statistical_tests),
            "confidence_interval_count": len(confidence_intervals),
            "effect_size_count": len(effect_sizes),
            "results_are_final_test_only": True,
            "models_retrained": False,
            "thresholds_recalibrated": False,
        }
    )
    if not isinstance(summary_value, dict):
        raise TypeError("El resumen final debe ser un objeto.")
    write_json_atomic(
        output / "final_evaluation_summary.json", summary_value
    )
    (output / "final_evaluation_report.md").write_text(
        _report_markdown(config, summary_value),
        encoding="utf-8",
    )
    thesis_metrics = _flatten_metrics(component_metrics)
    thesis_metrics.to_csv(
        output / "final_results_for_thesis.csv", index=False
    )
    _write_thesis_tables(
        output,
        component_metrics=component_metrics,
        thesis_metrics=thesis_metrics,
        ablation_summary=ablation_summary,
        comparison=comparison,
        latency=latency,
        statistical_tests=statistical_tests,
        confidence_intervals=confidence_intervals,
        effect_sizes=effect_sizes,
    )
    error_labels: list[str] = []
    error_values: list[float] = []
    for component, metrics in component_metrics.items():
        for metric in ("far", "frr"):
            value = _metric_value(metrics, metric)
            if value is not None:
                error_labels.append(f"{component} {metric.upper()}")
                error_values.append(value)
    save_bar_plot(
        error_labels,
        error_values,
        output / "figures" / "far_frr.png",
        title="FAR y FRR por componente",
        y_label="Tasa",
        rotate_labels=True,
    )
    with pd.ExcelWriter(
        output / "final_results.xlsx", engine="openpyxl"
    ) as writer:
        thesis_metrics.to_excel(
            writer, sheet_name="component_metrics", index=False
        )
        ablation_summary.to_excel(
            writer, sheet_name="ablation", index=False
        )
        comparison.to_excel(
            writer, sheet_name="pretest_posttest", index=False
        )
        latency.to_excel(writer, sheet_name="latency", index=False)
        statistical_tests.to_excel(
            writer, sheet_name="statistical_tests", index=False
        )
        confidence_intervals.to_excel(
            writer, sheet_name="confidence_intervals", index=False
        )
        effect_sizes.to_excel(
            writer, sheet_name="effect_sizes", index=False
        )
    (output / "reproduce.md").write_text(
        "\n".join(
            [
                "# Reproducción",
                "",
                "1. Instalar Docker Engine con Compose v2.",
                "2. Proveer variables mediante `.env` sin versionar.",
                "3. Montar modelos y test congelado como solo lectura.",
                "4. Verificar hashes y aprobación técnica.",
                "5. Ejecutar el dry-run.",
                "6. Revisar que no existan bloqueos.",
                "7. Ejecutar una sola vez la evaluación final.",
                "",
                "```text",
                "docker compose --profile evaluation run --rm evaluation "
                "python evaluation/scripts/run_final_evaluation.py "
                "--config evaluation/configs/final_evaluation.yaml --dry-run",
                "```",
                "",
                "La ejecución definitiva elimina `--dry-run`. Una repetición exige autorización y motivo documentado.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return summary_value


def write_run_metadata(
    config: FinalEvaluationConfig,
    *,
    run_id: str,
    duration_seconds: float,
    status: str,
    device: str,
    authorized_rerun: bool,
    rerun_reason: str | None,
    errors: list[str],
) -> None:
    write_json_atomic(
        config.paths.output_directory / "run_metadata.json",
        {
            "run_id": run_id,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": duration_seconds,
            "status": status,
            "equipment": {
                "cpu": platform.processor() or platform.machine(),
                "gpu": device if device == "gpu" else None,
                "ram_bytes": int(psutil.virtual_memory().total),
                "operating_system": platform.platform(),
            },
            "versions": {
                "python": platform.python_version(),
                "tensorflow": _version("tensorflow-cpu")
                or _version("tensorflow"),
                "insightface": _version("insightface"),
                "onnxruntime": _version("onnxruntime"),
                "numpy": _version("numpy"),
                "scikit_learn": _version("scikit-learn"),
                "docker": _docker_version(),
            },
            "dataset_version": config.dataset_version,
            "protocol_version": config.protocol_version,
            "model_versions": {
                "facial": config.approved_versions.facial,
                "pad": config.approved_versions.pad,
                "behavioral": config.approved_versions.behavioral,
                "fusion": config.approved_versions.fusion,
                "normalization": config.approved_versions.normalization,
            },
            "seed": config.random_seed,
            "command": "run_final_evaluation.py",
            "errors": errors,
            "authorized_rerun": authorized_rerun,
            "rerun_reason": rerun_reason,
        },
    )


def artifact_checksums(output: Path) -> dict[str, str]:
    excluded = {
        "artifact_checksums.json",
        "test_evaluation_completed.json",
    }
    checksums = {
        path.relative_to(output).as_posix(): sha256_file(path)
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name not in excluded
    }
    write_json_atomic(output / "artifact_checksums.json", checksums)
    return checksums


def verify_final_artifacts(output: Path) -> None:
    required = (
        "facial/facial_test_predictions.parquet",
        "facial/facial_test_metrics.json",
        "facial/facial_test_report.md",
        "pad/pad_test_predictions.parquet",
        "pad/pad_test_metrics.json",
        "pad/pad_test_report.md",
        "behavioral/behavioral_test_metrics.parquet",
        "behavioral/behavioral_test_predictions.parquet",
        "behavioral/behavioral_test_summary.json",
        "behavioral/behavioral_test_report.md",
        "fusion/fusion_test_predictions.parquet",
        "fusion/fusion_test_metrics.json",
        "fusion/fusion_test_report.md",
        "ablation/ablation_results.parquet",
        "ablation/ablation_summary.csv",
        "ablation/ablation_report.md",
        "comparison/pretest_posttest.parquet",
        "comparison/pretest_posttest_summary.json",
        "comparison/pretest_posttest_report.md",
        "performance/latency_measurements.parquet",
        "performance/performance_summary.json",
        "performance/performance_report.md",
        "statistics/statistical_tests.csv",
        "statistics/confidence_intervals.csv",
        "statistics/effect_sizes.csv",
        "statistics/statistical_report.md",
        "statistics/pretest_posttest_spss.csv",
        "statistics/session_metrics_spss.csv",
        "statistics/latency_spss.csv",
        "statistics/participant_metrics_spss.csv",
        "statistics/spss_variable_dictionary.csv",
        "tables/participant_distribution.csv",
        "tables/session_distribution.csv",
        "tables/capture_quality.csv",
        "tables/component_metrics.csv",
        "tables/ablation_results.csv",
        "tables/pretest_posttest.csv",
        "tables/latency.csv",
        "tables/statistical_tests.csv",
        "tables/confidence_intervals.csv",
        "tables/effect_sizes.csv",
        "tables/errors_and_limitations.csv",
        "figures/facial_roc.png",
        "figures/facial_precision_recall.png",
        "figures/facial_confusion_matrix.png",
        "figures/pad_roc.png",
        "figures/pad_precision_recall.png",
        "figures/pad_confusion_matrix.png",
        "figures/behavioral_aggregate_roc.png",
        "figures/behavioral_aggregate_precision_recall.png",
        "figures/behavioral_confusion_matrix.png",
        "figures/behavioral_metrics_by_participant.png",
        "figures/fusion_roc.png",
        "figures/fusion_precision_recall.png",
        "figures/fusion_confusion_matrix.png",
        "figures/fusion_risk_distribution.png",
        "figures/component_availability.png",
        "figures/ablation_f1.png",
        "figures/pretest_posttest_f1.png",
        "figures/false_alerts.png",
        "figures/pretest_confusion_matrix.png",
        "figures/posttest_confusion_matrix.png",
        "figures/latency.png",
        "figures/far_frr.png",
        "final_evaluation_report.md",
        "final_evaluation_summary.json",
        "final_results.xlsx",
        "final_results_for_thesis.csv",
        "run_metadata.json",
        "reproduce.md",
    )
    missing = [relative for relative in required if not (output / relative).is_file()]
    if missing:
        raise RuntimeError(
            "Faltan artefactos finales: " + ", ".join(missing)
        )
