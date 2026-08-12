import json
from pathlib import Path

import pandas as pd

from src.common.timestamps import iso_utc, utc_now


def _markdown_table(frame: pd.DataFrame, limit: int = 50) -> str:
    if frame.empty:
        return "_Sin datos._"
    selected = frame.head(limit).fillna("")
    columns = [str(column) for column in selected.columns]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = [
        "| "
        + " | ".join(
            str(value).replace("|", "\\|").replace("\n", " ")
            for value in record
        )
        + " |"
        for record in selected.itertuples(index=False, name=None)
    ]
    return "\n".join([header, separator, *rows])


def build_pilot_report(
    *,
    dataset_version: str,
    protocol_version: str,
    session_summary: pd.DataFrame,
    facial_table: pd.DataFrame,
    behavioral_table: pd.DataFrame,
    split_table: pd.DataFrame,
    readiness: dict[str, object],
    audit: pd.DataFrame | None = None,
    validated_batches: pd.DataFrame | None = None,
    windows: pd.DataFrame | None = None,
) -> str:
    audit = audit if audit is not None else pd.DataFrame()
    validated_batches = (
        validated_batches if validated_batches is not None else pd.DataFrame()
    )
    windows = windows if windows is not None else pd.DataFrame()
    checks = pd.DataFrame(readiness["checks"])
    selected = (
        checks[["check", "passed", "severity", "observed", "expected"]]
        if not checks.empty
        else checks
    )
    participants = int(audit["participant_id"].nunique()) if not audit.empty else 0
    sessions = len(audit)
    received_faces = (
        int(audit["facial_capture_count"].fillna(0).sum()) if not audit.empty else 0
    )
    accepted_faces = int(
        facial_table.loc[
            (facial_table["quality_status"] == "accepted")
            & (facial_table["reason"] == "ALL"),
            "count",
        ].sum()
    ) if not facial_table.empty else 0
    rejected_faces = int(
        facial_table.loc[
            (facial_table["quality_status"] == "rejected")
            & (facial_table["reason"] == "ALL"),
            "count",
        ].sum()
    ) if not facial_table.empty else 0
    invalid_batches = (
        int((~validated_batches["valid"].fillna(False).astype(bool)).sum())
        if not validated_batches.empty
        else 0
    )
    keyboard_events = (
        int(audit["keyboard_event_count"].fillna(0).sum()) if not audit.empty else 0
    )
    mouse_events = (
        int(audit["mouse_event_count"].fillna(0).sum()) if not audit.empty else 0
    )
    accepted_windows = (
        int((windows["quality_status"] == "accepted").sum())
        if not windows.empty
        else 0
    )
    rejected_windows = len(windows) - accepted_windows
    scenarios = (
        ", ".join(sorted(audit["scenario"].dropna().astype(str).unique()))
        if not audit.empty
        else "ninguno"
    )
    technical_incidents = (
        int((~audit["session_valid"].fillna(False).astype(bool)).sum())
        if not audit.empty
        else 0
    )
    return "\n".join(
        [
            "# Informe de preparación del piloto",
            "",
            f"- Dataset: `{dataset_version}`",
            f"- Protocolo: `{protocol_version}`",
            f"- Generado: `{iso_utc(utc_now())}`",
            f"- Veredicto: **{readiness['status']}**",
            "",
            "Este informe describe preparación y control de calidad. No ejecuta "
            "entrenamiento ni inferencia.",
            "",
            "## Objetivo y protocolo",
            "",
            "Preparar de forma reproducible los datasets facial de identidad, PAD "
            "y conductual del piloto controlado, preservando privacidad y evitando "
            "fugas entre particiones.",
            "",
            f"- Participantes observados: {participants}",
            f"- Sesiones observadas: {sessions}",
            f"- Escenarios ejecutados: {scenarios}",
            f"- Capturas recibidas: {received_faces}",
            f"- Capturas aceptadas: {accepted_faces}",
            f"- Capturas rechazadas: {rejected_faces}",
            f"- Lotes recibidos: {len(validated_batches)}",
            f"- Lotes inválidos: {invalid_batches}",
            f"- Eventos de teclado declarados: {keyboard_events}",
            f"- Eventos de mouse declarados: {mouse_events}",
            f"- Ventanas generadas: {len(windows)}",
            f"- Ventanas aceptadas: {accepted_windows}",
            f"- Ventanas rechazadas: {rejected_windows}",
            "",
            "## Readiness",
            "",
            _markdown_table(selected),
            "",
            "## Resumen por participante",
            "",
            _markdown_table(session_summary),
            "",
            "## Calidad facial",
            "",
            _markdown_table(facial_table),
            "",
            "## Calidad conductual",
            "",
            _markdown_table(behavioral_table),
            "",
            "## Particiones",
            "",
            _markdown_table(split_table),
            "",
            "## Interpretación",
            "",
            (
                "El dataset no debe usarse para entrenamiento hasta resolver todos "
                "los controles críticos fallidos."
                if readiness["status"] == "not_ready"
                else "El dataset cumple los controles críticos codificados."
            ),
            "",
            "## Incidentes técnicos",
            "",
            f"Sesiones con controles inválidos pendientes: {technical_incidents}.",
            "",
            "## Limitaciones",
            "",
            "El piloto de cinco participantes es exploratorio; no representa la "
            "evaluación biométrica final. Las etiquetas de cambio de operador y PAD "
            "solo son válidas cuando constan explícitamente en el protocolo.",
            "",
            "## Recomendaciones",
            "",
            "Resolver cada control crítico, repetir la auditoría y congelar test "
            "antes de iniciar la Fase 8. No usar test para seleccionar reglas, "
            "características, umbrales ni arquitectura.",
            "",
        ]
    )


def write_pilot_report(
    report: str,
    readiness: dict[str, object],
    report_root: Path,
    *,
    dry_run: bool = False,
) -> tuple[Path, Path]:
    report_path = report_root / "pilot_report.md"
    readiness_path = report_root / "readiness_assessment.json"
    if not dry_run:
        report_root.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
        readiness_path.write_text(
            json.dumps(readiness, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
    return report_path, readiness_path
