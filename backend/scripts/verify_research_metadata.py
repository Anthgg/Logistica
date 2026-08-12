import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.core.config import settings

EXPECTED = {
    "experimental_sessions": {
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
        "annotated_by",
        "annotated_at",
        "annotation_notes",
        "capture_interval_seconds",
        "batch_interval_seconds",
        "max_batch_events",
        "max_image_size_bytes",
        "client_timezone_offset_minutes",
        "client_language",
        "screen_pixel_ratio",
    },
    "facial_captures": {
        "client_timezone_offset_minutes",
        "capture_source",
        "camera_facing_mode",
    },
    "behavioral_batches": {
        "visibility_state",
        "client_timezone_offset_minutes",
        "dropped_event_count",
        "collector_error_count",
    },
}


def _transactional_write_test(engine) -> None:
    now = datetime.now(timezone.utc)
    user_id = uuid4()
    participant_id = uuid4()
    session_id = uuid4()
    capture_id = uuid4()
    batch_id = uuid4()
    participant_code = f"TX-{uuid4().hex[:12]}"
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(
                text(
                    """
                    INSERT INTO users (
                      id, email, password_hash, full_name, role, is_active,
                      is_verified, failed_login_attempts, created_at, updated_at
                    ) VALUES (
                      :id, :email, 'transactional-not-a-real-hash',
                      'Transactional Verification', 'admin', true, false, 0,
                      :now, :now
                    )
                    """
                ),
                {
                    "id": user_id,
                    "email": f"transactional-{user_id}@example.invalid",
                    "now": now,
                },
            )
            connection.execute(
                text(
                    """
                    INSERT INTO research_participants (
                      id, linked_user_id, participant_code, is_active,
                      enrollment_date, created_at, updated_at
                    ) VALUES (
                      :id, :user_id, :code, true, :now, :now, :now
                    )
                    """
                ),
                {
                    "id": participant_id,
                    "user_id": user_id,
                    "code": participant_code,
                    "now": now,
                },
            )
            duplicate_savepoint = connection.begin_nested()
            try:
                connection.execute(
                    text(
                        """
                        INSERT INTO research_participants (
                          id, linked_user_id, participant_code, is_active,
                          enrollment_date, created_at, updated_at
                        ) VALUES (
                          :id, :user_id, :code, true, :now, :now, :now
                        )
                        """
                    ),
                    {
                        "id": uuid4(),
                        "user_id": user_id,
                        "code": f"TX-{uuid4().hex[:12]}",
                        "now": now,
                    },
                )
            except IntegrityError:
                duplicate_savepoint.rollback()
            else:
                duplicate_savepoint.rollback()
                raise AssertionError(
                    "La base aceptó dos participantes activos para el mismo usuario."
                )
            connection.execute(
                text(
                    """
                    INSERT INTO experimental_sessions (
                      id, participant_id, user_id, scenario, status, started_at,
                      expected_duration_minutes, client_timezone, screen_width,
                      screen_height, last_activity_at, created_at, updated_at,
                      protocol_version, collector_version, identity_label,
                      sample_role, presentation_label, attack_type, source_device,
                      pad_source_id, annotation_status, annotated_by, annotated_at,
                      capture_interval_seconds, batch_interval_seconds,
                      max_batch_events, max_image_size_bytes,
                      client_timezone_offset_minutes, client_language,
                      screen_pixel_ratio
                    ) VALUES (
                      :id, :participant_id, :user_id, 'mixed_operations',
                      'active', :now, 10, 'America/Lima', 1920, 1080,
                      :now, :now, :now, 'pilot-protocol-v0.1.0', 'write-test',
                      'genuine', 'verification', 'bona_fide', 'none',
                      'transactional-camera', 'transactional-pad-source',
                      'confirmed', :user_id, :now, 5, 3, 100, 1048576,
                      -300, 'es-PE', 1.25
                    )
                    """
                ),
                {
                    "id": session_id,
                    "participant_id": participant_id,
                    "user_id": user_id,
                    "now": now,
                },
            )
            connection.execute(
                text(
                    """
                    INSERT INTO facial_captures (
                      id, experimental_session_id, sequence_number, storage_path,
                      content_type, file_size, width, height, captured_at,
                      received_at, visibility_state, checksum, created_at,
                      client_timezone_offset_minutes, capture_source,
                      camera_facing_mode
                    ) VALUES (
                      :id, :session_id, 1, 'transactional/test.jpg',
                      'image/jpeg', 100, 64, 64, :now, :now, 'visible',
                      :checksum, :now, -300, 'webcam', 'user'
                    )
                    """
                ),
                {
                    "id": capture_id,
                    "session_id": session_id,
                    "now": now,
                    "checksum": "0" * 64,
                },
            )
            connection.execute(
                text(
                    """
                    INSERT INTO behavioral_batches (
                      id, experimental_session_id, batch_id, sequence_number,
                      event_count, keyboard_event_count, mouse_event_count,
                      started_at, ended_at, payload, checksum, received_at,
                      created_at, visibility_state,
                      client_timezone_offset_minutes, dropped_event_count,
                      collector_error_count
                    ) VALUES (
                      :id, :session_id, :batch_id, 1, 0, 0, 0, :now, :now,
                      CAST('[]' AS jsonb), :checksum, :now, :now, 'visible',
                      -300, 2, 1
                    )
                    """
                ),
                {
                    "id": uuid4(),
                    "session_id": session_id,
                    "batch_id": batch_id,
                    "now": now,
                    "checksum": "1" * 64,
                },
            )
            values = connection.execute(
                text(
                    """
                    SELECT
                      es.annotation_status,
                      es.protocol_version,
                      fc.capture_source,
                      bb.dropped_event_count,
                      bb.collector_error_count
                    FROM experimental_sessions es
                    JOIN facial_captures fc
                      ON fc.experimental_session_id = es.id
                    JOIN behavioral_batches bb
                      ON bb.experimental_session_id = es.id
                    WHERE es.id = :session_id
                    """
                ),
                {"session_id": session_id},
            ).one()
            assert values == (
                "confirmed",
                "pilot-protocol-v0.1.0",
                "webcam",
                2,
                1,
            )
            savepoint = connection.begin_nested()
            try:
                connection.execute(
                    text(
                        """
                        UPDATE experimental_sessions
                        SET attack_type = 'printed_photo'
                        WHERE id = :session_id
                        """
                    ),
                    {"session_id": session_id},
                )
            except IntegrityError:
                savepoint.rollback()
            else:
                savepoint.rollback()
                raise AssertionError(
                    "La base aceptó una combinación PAD inconsistente."
                )
        finally:
            transaction.rollback()
    print("Escritura transaccional verificada y revertida.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transactional-write-test", action="store_true")
    arguments = parser.parse_args()
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name IN (
                    'experimental_sessions',
                    'facial_captures',
                    'behavioral_batches'
                  )
                """
            )
        )
        actual: dict[str, set[str]] = {}
        for table_name, column_name in rows:
            actual.setdefault(str(table_name), set()).add(str(column_name))
        self_enrollment_index = connection.execute(
            text(
                """
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename = 'research_participants'
                  AND indexname = 'uq_research_participants_active_linked_user'
                  AND indexdef ILIKE '%UNIQUE%'
                  AND indexdef ILIKE '%WHERE%'
                """
            )
        ).scalar_one_or_none()
    missing = {
        table: sorted(columns - actual.get(table, set()))
        for table, columns in EXPECTED.items()
        if columns - actual.get(table, set())
    }
    if missing:
        raise SystemExit(f"Faltan columnas: {missing}")
    if self_enrollment_index is None:
        raise SystemExit(
            "Falta el índice único parcial para autoinscripción segura."
        )
    print(
        "Metadatos de investigación verificados: "
        f"{sum(len(columns) for columns in EXPECTED.values())} columnas."
    )
    if arguments.transactional_write_test:
        _transactional_write_test(engine)
    engine.dispose()


if __name__ == "__main__":
    main()
