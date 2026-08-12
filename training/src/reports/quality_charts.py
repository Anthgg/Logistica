from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def _save_bar(
    labels: list[str],
    values: list[int],
    *,
    title: str,
    ylabel: str,
    target: Path,
    dry_run: bool,
) -> Path:
    if dry_run:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    figure = plt.figure(figsize=(8, 4.5))
    axis = figure.gca()
    if labels:
        axis.bar(labels, values)
        axis.tick_params(axis="x", rotation=25)
    else:
        axis.text(
            0.5,
            0.5,
            "Sin datos disponibles",
            ha="center",
            va="center",
            transform=axis.transAxes,
        )
    axis.set_title(title)
    axis.set_ylabel(ylabel)
    figure.tight_layout()
    figure.savefig(target, dpi=150)
    plt.close(figure)
    return target


def _save_histogram(
    values: list[float],
    *,
    title: str,
    xlabel: str,
    target: Path,
    dry_run: bool,
) -> Path:
    if dry_run:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    figure = plt.figure(figsize=(8, 4.5))
    axis = figure.gca()
    if values:
        axis.hist(values)
    else:
        axis.text(
            0.5,
            0.5,
            "Sin datos disponibles",
            ha="center",
            va="center",
            transform=axis.transAxes,
        )
    axis.set_title(title)
    axis.set_xlabel(xlabel)
    axis.set_ylabel("Frecuencia")
    figure.tight_layout()
    figure.savefig(target, dpi=150)
    plt.close(figure)
    return target


def generate_quality_charts(
    facial_table: pd.DataFrame,
    behavioral_table: pd.DataFrame,
    split_table: pd.DataFrame,
    report_root: Path,
    *,
    audit: pd.DataFrame | None = None,
    face_quality: pd.DataFrame | None = None,
    windows: pd.DataFrame | None = None,
    dry_run: bool = False,
) -> list[Path]:
    audit = audit if audit is not None else pd.DataFrame()
    face_quality = face_quality if face_quality is not None else pd.DataFrame()
    windows = windows if windows is not None else pd.DataFrame()
    facial_reasons = facial_table[
        (facial_table.get("quality_status") == "rejected")
        & (facial_table.get("reason") != "ALL")
    ]
    behavior_reasons = behavioral_table[
        (behavioral_table.get("quality_status") == "rejected")
        & (behavioral_table.get("reason") != "ALL")
    ]
    capture_counts = (
        audit.groupby("participant_id")["facial_capture_count"].sum()
        if not audit.empty
        else pd.Series(dtype=int)
    )
    face_statuses = (
        face_quality["quality_status"].value_counts()
        if not face_quality.empty
        else pd.Series(dtype=int)
    )
    event_counts = (
        audit.assign(
            behavioral_events=audit["keyboard_event_count"]
            + audit["mouse_event_count"]
        ).set_index("session_id")["behavioral_events"]
        if not audit.empty
        else pd.Series(dtype=int)
    )
    valid_windows = (
        windows[windows["quality_status"] == "accepted"]
        .groupby("participant_id")
        .size()
        if not windows.empty
        else pd.Series(dtype=int)
    )
    scenarios = (
        audit["scenario"].value_counts()
        if not audit.empty
        else pd.Series(dtype=int)
    )
    durations = (
        audit["duration_seconds"].dropna().astype(float).tolist()
        if not audit.empty
        else []
    )
    intervals = (
        face_quality["time_since_previous_capture"]
        .replace([float("inf"), float("-inf")], pd.NA)
        .dropna()
        .astype(float)
        .tolist()
        if not face_quality.empty
        and "time_since_previous_capture" in face_quality
        else []
    )
    charts = [
        _save_bar(
            capture_counts.index.astype(str).tolist(),
            capture_counts.astype(int).tolist(),
            title="Capturas por participante",
            ylabel="Capturas",
            target=report_root / "captures_by_participant.png",
            dry_run=dry_run,
        ),
        _save_bar(
            face_statuses.index.astype(str).tolist(),
            face_statuses.astype(int).tolist(),
            title="Capturas aceptadas y rechazadas",
            ylabel="Capturas",
            target=report_root / "facial_quality_status.png",
            dry_run=dry_run,
        ),
        _save_bar(
            facial_reasons.get("reason", pd.Series(dtype=str)).astype(str).tolist(),
            facial_reasons.get("count", pd.Series(dtype=int)).astype(int).tolist(),
            title="Rechazos de calidad facial",
            ylabel="Capturas",
            target=report_root / "facial_rejections.png",
            dry_run=dry_run,
        ),
        _save_bar(
            event_counts.index.astype(str).tolist(),
            event_counts.astype(int).tolist(),
            title="Eventos conductuales por sesión",
            ylabel="Eventos",
            target=report_root / "behavioral_events_by_session.png",
            dry_run=dry_run,
        ),
        _save_bar(
            valid_windows.index.astype(str).tolist(),
            valid_windows.astype(int).tolist(),
            title="Ventanas válidas por participante",
            ylabel="Ventanas",
            target=report_root / "valid_windows_by_participant.png",
            dry_run=dry_run,
        ),
        _save_bar(
            scenarios.index.astype(str).tolist(),
            scenarios.astype(int).tolist(),
            title="Distribución de escenarios",
            ylabel="Sesiones",
            target=report_root / "scenario_distribution.png",
            dry_run=dry_run,
        ),
        _save_bar(
            (
                behavior_reasons.get("stage", pd.Series(dtype=str)).astype(str)
                + ":"
                + behavior_reasons.get("reason", pd.Series(dtype=str)).astype(str)
            ).tolist(),
            behavior_reasons.get("count", pd.Series(dtype=int)).astype(int).tolist(),
            title="Rechazos de datos conductuales",
            ylabel="Registros",
            target=report_root / "behavioral_rejections.png",
            dry_run=dry_run,
        ),
        _save_bar(
            (
                split_table.get("dataset", pd.Series(dtype=str)).astype(str)
                + ":"
                + split_table.get("split", pd.Series(dtype=str)).astype(str)
            ).tolist(),
            split_table.get("count", pd.Series(dtype=int)).astype(int).tolist(),
            title="Distribución por partición",
            ylabel="Muestras",
            target=report_root / "split_distribution.png",
            dry_run=dry_run,
        ),
        _save_histogram(
            durations,
            title="Duración de sesiones",
            xlabel="Segundos",
            target=report_root / "session_durations.png",
            dry_run=dry_run,
        ),
        _save_histogram(
            intervals,
            title="Intervalos reales entre capturas",
            xlabel="Segundos",
            target=report_root / "capture_intervals.png",
            dry_run=dry_run,
        ),
    ]
    return charts
