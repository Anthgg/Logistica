from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from src.common.config import PreparationConfig
from src.datasets.leakage_checker import LeakageFinding


@dataclass(frozen=True)
class ReadinessCheck:
    check: str
    passed: bool
    severity: str
    observed: object
    expected: object
    message: str


def _feature_health(features: pd.DataFrame) -> tuple[int, float]:
    if features.empty:
        return 0, 1.0
    numeric = features.select_dtypes(include=[np.number])
    infinite = int(np.isinf(numeric.to_numpy(dtype=float)).sum())
    missing_ratio = (
        float(numeric.isna().sum().sum() / numeric.size) if numeric.size else 0.0
    )
    return infinite, missing_ratio


def evaluate_readiness(
    *,
    config: PreparationConfig,
    audit: pd.DataFrame,
    face_quality: pd.DataFrame,
    validated_batches: pd.DataFrame,
    windows: pd.DataFrame,
    features: pd.DataFrame,
    manifests: dict[str, pd.DataFrame],
    leakage_findings: list[LeakageFinding],
    frozen_test_exists: bool,
    freeze_requested: bool,
    raw_unchanged: bool,
) -> dict[str, object]:
    checks: list[ReadinessCheck] = []

    def add(
        check: str,
        passed: bool,
        severity: str,
        observed: object,
        expected: object,
        message: str,
    ) -> None:
        checks.append(
            ReadinessCheck(
                check=check,
                passed=passed,
                severity=severity,
                observed=observed,
                expected=expected,
                message=message,
            )
        )

    participants = int(audit["participant_id"].nunique()) if not audit.empty else 0
    add(
        "pilot_participants",
        participants >= config.protocol.pilot_participants,
        "critical",
        participants,
        f">={config.protocol.pilot_participants}",
        "El piloto requiere participantes reales y consentidos.",
    )
    invalid_consent = (
        int((~audit["consent_valid"].fillna(False).astype(bool)).sum())
        if not audit.empty
        else 0
    )
    add(
        "valid_consent",
        participants > 0 and invalid_consent == 0,
        "critical",
        invalid_consent,
        0,
        "No se permite preparar muestras sin consentimiento vigente.",
    )
    if audit.empty:
        minimum_sessions_met = False
        minimum_observed = 0
    else:
        session_counts = audit.groupby("participant_id")["session_id"].nunique()
        minimum_observed = int(session_counts.min())
        minimum_sessions_met = bool(
            (session_counts >= config.protocol.minimum_sessions_per_participant).all()
        )
    add(
        "sessions_per_participant",
        minimum_sessions_met,
        "critical",
        minimum_observed,
        f">={config.protocol.minimum_sessions_per_participant}",
        "Cada participante debe completar el protocolo mínimo.",
    )
    valid_sessions = (
        int(audit["session_valid"].fillna(False).astype(bool).sum())
        if not audit.empty
        else 0
    )
    add(
        "valid_sessions",
        valid_sessions > 0 and valid_sessions == len(audit),
        "critical",
        f"{valid_sessions}/{len(audit)}",
        "all",
        "Las sesiones inválidas deben resolverse antes del entrenamiento.",
    )
    forbidden_batches = 0
    if not validated_batches.empty:
        forbidden_batches = int(
            validated_batches["rejection_reasons"].apply(
                lambda reasons: isinstance(reasons, list)
                and "FORBIDDEN_TEXTUAL_DATA_DETECTED" in reasons
            ).sum()
        )
    add(
        "no_forbidden_text",
        forbidden_batches == 0,
        "critical",
        forbidden_batches,
        0,
        "El pipeline no admite teclas, texto, contraseñas ni contenido escrito.",
    )
    accepted_faces = (
        int((face_quality["quality_status"] == "accepted").sum())
        if not face_quality.empty
        else 0
    )
    unreadable_faces = (
        int(
            face_quality["rejection_reasons"].apply(
                lambda reasons: isinstance(reasons, list)
                and bool({"FILE_NOT_FOUND", "UNREADABLE_IMAGE"} & set(reasons))
            ).sum()
        )
        if not face_quality.empty
        else 0
    )
    add(
        "readable_face_captures",
        accepted_faces > 0 and unreadable_faces == 0,
        "critical",
        {"accepted": accepted_faces, "unreadable": unreadable_faces},
        {"accepted": ">0", "unreadable": 0},
        "Deben existir capturas faciales aceptadas y legibles.",
    )
    facial_rejection_rate = (
        float(1 - accepted_faces / len(face_quality)) if len(face_quality) else 1.0
    )
    add(
        "facial_rejection_rate",
        bool(face_quality is not None)
        and not face_quality.empty
        and facial_rejection_rate <= config.face_quality.maximum_rejection_rate,
        "critical",
        round(facial_rejection_rate, 6),
        f"<={config.face_quality.maximum_rejection_rate}",
        "La tasa de rechazo facial supera el límite configurado.",
    )
    duplicate_faces = (
        int(
            face_quality["rejection_reasons"].apply(
                lambda reasons: isinstance(reasons, list)
                and "DUPLICATE_CAPTURE" in reasons
            ).sum()
        )
        if not face_quality.empty
        else 0
    )
    add(
        "no_duplicate_faces",
        duplicate_faces == 0,
        "critical",
        duplicate_faces,
        0,
        "Las capturas duplicadas pueden sesgar la evaluación.",
    )
    duplicate_batches = (
        int(
            validated_batches["rejection_reasons"].apply(
                lambda reasons: isinstance(reasons, list)
                and "DUPLICATE_BATCH" in reasons
            ).sum()
        )
        if not validated_batches.empty
        else 0
    )
    add(
        "no_severe_batch_duplication",
        duplicate_batches == 0,
        "critical",
        duplicate_batches,
        0,
        "Los batch_id duplicados deben investigarse y excluirse.",
    )
    valid_event_count = (
        int(
            validated_batches.loc[
                validated_batches["valid"].fillna(False).astype(bool),
                ["keyboard_event_count", "mouse_event_count"],
            ]
            .fillna(0)
            .sum()
            .sum()
        )
        if not validated_batches.empty
        else 0
    )
    add(
        "sufficient_behavioral_events",
        valid_event_count >= config.protocol.minimum_behavioral_events,
        "critical",
        valid_event_count,
        f">={config.protocol.minimum_behavioral_events}",
        "No hay suficientes eventos conductuales válidos.",
    )
    accepted_windows = (
        int((windows["quality_status"] == "accepted").sum())
        if not windows.empty
        else 0
    )
    add(
        "accepted_behavioral_windows",
        accepted_windows > 0,
        "critical",
        accepted_windows,
        ">0",
        "Se requieren ventanas conductuales con actividad suficiente.",
    )
    infinite_features, missing_ratio = _feature_health(features)
    feature_ok = (
        not features.empty
        and infinite_features == 0
        and missing_ratio <= config.behavioral.maximum_missing_feature_ratio
    )
    add(
        "finite_complete_features",
        feature_ok,
        "critical",
        {"infinite": infinite_features, "missing_ratio": round(missing_ratio, 6)},
        {
            "infinite": 0,
            "missing_ratio": f"<={config.behavioral.maximum_missing_feature_ratio}",
        },
        "Las características deben ser finitas y suficientemente completas.",
    )
    split_problems: list[str] = []
    for name, manifest in manifests.items():
        if manifest.empty:
            split_problems.append(f"{name}:empty")
            continue
        present = set(manifest["split"].dropna().astype(str))
        if present != {"train", "validation", "test"}:
            split_problems.append(f"{name}:{','.join(sorted(present)) or 'none'}")
    add(
        "complete_splits",
        bool(manifests) and not split_problems,
        "critical",
        split_problems,
        "train,validation,test in every dataset",
        "Cada conjunto no vacío debe tener las tres particiones.",
    )
    add(
        "no_critical_leakage",
        not leakage_findings,
        "critical",
        [finding.check for finding in leakage_findings],
        [],
        "No puede existir una misma fuente o segmento en más de una partición.",
    )
    add(
        "frozen_test_set",
        frozen_test_exists,
        "critical",
        frozen_test_exists,
        True,
        "El test debe congelarse de forma inmutable antes de entrenar.",
    )
    add(
        "raw_data_immutable",
        raw_unchanged,
        "critical",
        raw_unchanged,
        True,
        "La ejecución no puede alterar data/raw.",
    )
    severe_incidents = (
        int(
            (
                audit[["error_count", "missing_files", "duplicate_batches"]]
                .fillna(0)
                .astype(float)
                .sum(axis=1)
                > 0
            ).sum()
        )
        if not audit.empty
        else 0
    )
    add(
        "severe_incidents_resolved",
        severe_incidents == 0,
        "critical",
        severe_incidents,
        0,
        "Los incidentes técnicos graves deben resolverse antes de recolectar formalmente.",
    )
    critical_failures = [
        item for item in checks if item.severity == "critical" and not item.passed
    ]
    observations = [
        item for item in checks if item.severity != "critical" and not item.passed
    ]
    status = (
        "not_ready"
        if critical_failures
        else "ready_with_observations"
        if observations
        else "ready"
    )
    return {
        "status": status,
        "ready": status != "not_ready",
        "checks": [asdict(item) for item in checks],
        "critical_failures": [item.check for item in critical_failures],
        "observations": [item.check for item in observations],
    }
