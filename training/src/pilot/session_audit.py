from pathlib import Path

import pandas as pd

from src.behavioral.event_loader import capture_file_path
from src.common.config import PreparationConfig
from src.pilot.session_validator import validate_session

AUDIT_COLUMNS = [
    "participant_id",
    "session_id",
    "scenario",
    "status",
    "started_at",
    "ended_at",
    "duration_seconds",
    "facial_capture_count",
    "keyboard_event_count",
    "mouse_event_count",
    "batch_count",
    "error_count",
    "consent_valid",
    "protocol_version",
    "collector_version",
    "identity_label",
    "sample_role",
    "operator_change_at",
    "presentation_label",
    "attack_type",
    "source_device",
    "pad_source_id",
    "annotation_status",
    "missing_files",
    "duplicate_files",
    "duplicate_batches",
    "session_valid",
    "invalid_reasons",
]


def audit_sessions(
    sessions: pd.DataFrame,
    captures: pd.DataFrame,
    batches: pd.DataFrame,
    config: PreparationConfig,
    capture_root: Path,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for session in sessions.to_dict(orient="records"):
        session_id = str(session["session_id"])
        session_captures = captures[captures["session_id"] == session_id]
        session_batches = batches[batches["session_id"] == session_id]
        missing = 0
        for storage_path in session_captures.get(
            "storage_path", pd.Series(dtype=str)
        ).dropna():
            try:
                exists = capture_file_path(capture_root, str(storage_path)).is_file()
            except ValueError:
                exists = False
            missing += not exists
        duplicate_files = int(
            session_captures.get("checksum", pd.Series(dtype=str))
            .dropna()
            .duplicated(keep=False)
            .sum()
        )
        duplicate_batches = int(
            session_batches.get("batch_id", pd.Series(dtype=str))
            .dropna()
            .duplicated(keep=False)
            .sum()
        )
        declared_capture_count = int(session.get("facial_capture_count") or 0)
        declared_batch_count = int(session.get("batch_count") or 0)
        declared_keyboard_count = int(session.get("keyboard_event_count") or 0)
        declared_mouse_count = int(session.get("mouse_event_count") or 0)
        audit_row = {
            **session,
            "missing_files": int(missing),
            "duplicate_files": duplicate_files,
            "duplicate_batches": duplicate_batches,
            "capture_count_mismatch": declared_capture_count
            != len(session_captures),
            "batch_count_mismatch": declared_batch_count != len(session_batches),
            "keyboard_count_mismatch": declared_keyboard_count
            != int(
                session_batches.get(
                    "keyboard_event_count", pd.Series(dtype=int)
                )
                .fillna(0)
                .sum()
            ),
            "mouse_count_mismatch": declared_mouse_count
            != int(
                session_batches.get("mouse_event_count", pd.Series(dtype=int))
                .fillna(0)
                .sum()
            ),
        }
        result = validate_session(audit_row, config.protocol)
        audit_row["session_valid"] = result.valid
        audit_row["invalid_reasons"] = result.reasons
        rows.append(audit_row)
    return pd.DataFrame(rows, columns=AUDIT_COLUMNS)


def write_raw_audit(
    audit: pd.DataFrame, report_root: Path, *, dry_run: bool = False
) -> tuple[Path, Path]:
    parquet_path = report_root / "raw_data_audit.parquet"
    csv_path = report_root / "raw_data_audit.csv"
    if not dry_run:
        report_root.mkdir(parents=True, exist_ok=True)
        audit.to_parquet(parquet_path, index=False)
        csv_frame = audit.copy()
        if "invalid_reasons" in csv_frame:
            csv_frame["invalid_reasons"] = csv_frame["invalid_reasons"].apply(
                lambda values: "|".join(values) if isinstance(values, list) else ""
            )
        csv_frame.to_csv(csv_path, index=False)
    return parquet_path, csv_path
