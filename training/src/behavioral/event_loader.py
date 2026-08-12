from collections.abc import Iterator
from pathlib import Path
from uuid import UUID

import pandas as pd
from sqlalchemy import Engine, create_engine, text

from src.common.config import PreparationConfig

SESSION_COLUMNS = [
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
]


def create_database_engine(config: PreparationConfig) -> Engine:
    settings = config.database_settings()
    return create_engine(settings.sqlalchemy_url, pool_pre_ping=True)


def _filters(
    participant_id: UUID | str | None, session_id: UUID | str | None
) -> tuple[str, dict[str, str]]:
    clauses: list[str] = []
    parameters: dict[str, str] = {}
    if participant_id:
        clauses.append("es.participant_id = CAST(:participant_id AS uuid)")
        parameters["participant_id"] = str(participant_id)
    if session_id:
        clauses.append("es.id = CAST(:session_id AS uuid)")
        parameters["session_id"] = str(session_id)
    return (" AND " + " AND ".join(clauses) if clauses else ""), parameters


def load_sessions(
    engine: Engine,
    *,
    participant_id: UUID | str | None = None,
    session_id: UUID | str | None = None,
    consent_version: str | None = None,
) -> pd.DataFrame:
    where_sql, parameters = _filters(participant_id, session_id)
    parameters["consent_version"] = consent_version
    query = text(
        """
        SELECT
            es.participant_id::text AS participant_id,
            es.id::text AS session_id,
            es.scenario,
            es.status,
            es.started_at,
            es.ended_at,
            GREATEST(
                0,
                EXTRACT(EPOCH FROM (COALESCE(es.ended_at, NOW()) - es.started_at))
            )::double precision AS duration_seconds,
            es.facial_capture_count,
            es.keyboard_event_count,
            es.mouse_event_count,
            es.batch_count,
            es.error_count,
            es.protocol_version,
            es.collector_version,
            es.identity_label,
            es.sample_role,
            es.operator_change_at,
            es.presentation_label,
            es.attack_type,
            es.source_device,
            es.pad_source_id,
            es.annotation_status,
            EXISTS (
                SELECT 1
                FROM consent_records cr
                WHERE cr.participant_id = es.participant_id
                  AND cr.accepted = true
                  AND cr.withdrawn_at IS NULL
                  AND cr.accepted_at <= es.started_at
                  AND (
                    CAST(:consent_version AS text) IS NULL
                    OR cr.consent_version = CAST(:consent_version AS text)
                  )
            ) AS consent_valid
        FROM experimental_sessions es
        WHERE 1 = 1
        """
        + where_sql
        + " ORDER BY es.started_at, es.id"
    )
    with engine.connect() as connection:
        frame = pd.read_sql(query, connection, params=parameters)
    return frame.reindex(columns=SESSION_COLUMNS)


def load_captures(
    engine: Engine,
    *,
    participant_id: UUID | str | None = None,
    session_id: UUID | str | None = None,
) -> pd.DataFrame:
    where_sql, parameters = _filters(participant_id, session_id)
    query = text(
        """
        SELECT
            es.participant_id::text AS participant_id,
            es.id::text AS session_id,
            es.scenario,
            fc.id::text AS capture_id,
            fc.sequence_number,
            fc.storage_path,
            fc.content_type,
            fc.file_size,
            fc.width,
            fc.height,
            fc.captured_at,
            fc.visibility_state,
            fc.client_timezone_offset_minutes,
            fc.capture_source,
            fc.camera_facing_mode,
            es.protocol_version,
            es.collector_version,
            es.identity_label,
            es.sample_role,
            es.operator_change_at,
            es.presentation_label,
            es.attack_type,
            es.source_device,
            es.pad_source_id,
            es.annotation_status,
            fc.checksum
        FROM facial_captures fc
        JOIN experimental_sessions es ON es.id = fc.experimental_session_id
        WHERE 1 = 1
        """
        + where_sql
        + " ORDER BY es.id, fc.sequence_number"
    )
    with engine.connect() as connection:
        return pd.read_sql(query, connection, params=parameters)


def load_behavioral_batches(
    engine: Engine,
    *,
    participant_id: UUID | str | None = None,
    session_id: UUID | str | None = None,
) -> pd.DataFrame:
    where_sql, parameters = _filters(participant_id, session_id)
    query = text(
        """
        SELECT
            es.participant_id::text AS participant_id,
            es.id::text AS session_id,
            es.scenario,
            es.started_at AS session_started_at,
            es.ended_at AS session_ended_at,
            es.protocol_version,
            es.collector_version,
            es.identity_label,
            es.sample_role,
            es.operator_change_at,
            es.presentation_label,
            es.attack_type,
            es.source_device,
            es.pad_source_id,
            es.annotation_status,
            bb.id::text AS record_id,
            bb.batch_id::text AS batch_id,
            bb.sequence_number,
            bb.event_count,
            bb.keyboard_event_count,
            bb.mouse_event_count,
            bb.started_at,
            bb.ended_at,
            bb.visibility_state,
            bb.client_timezone_offset_minutes,
            bb.dropped_event_count,
            bb.collector_error_count,
            bb.payload,
            bb.checksum
        FROM behavioral_batches bb
        JOIN experimental_sessions es ON es.id = bb.experimental_session_id
        WHERE 1 = 1
        """
        + where_sql
        + " ORDER BY es.id, bb.sequence_number"
    )
    with engine.connect() as connection:
        return pd.read_sql(query, connection, params=parameters)


def iter_batch_rows(frame: pd.DataFrame) -> Iterator[dict[str, object]]:
    for row in frame.to_dict(orient="records"):
        yield row


def capture_file_path(storage_root: str | Path, storage_path: str) -> Path:
    root = Path(storage_root).resolve()
    relative = Path(storage_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("storage_path debe ser relativo y seguro.")
    target = (root / relative).resolve()
    target.relative_to(root)
    return target
