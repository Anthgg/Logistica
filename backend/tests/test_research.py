from datetime import timedelta
from io import BytesIO
from uuid import uuid4

from PIL import Image
from sqlalchemy import func, select

from app.database.base import utc_now
from app.models.audit_log import AuditLog
from app.models.behavioral_batch import BehavioralBatch
from app.models.experimental_session import ExperimentalSession
from app.models.facial_capture import FacialCapture
from app.models.research_participant import ResearchParticipant
from app.services.research_service import ResearchService
from tests.support import authenticate


def _participant_and_consent(client, headers, user_id):
    participant_response = client.post(
        "/api/research/participants",
        headers=headers,
        json={"linked_user_id": str(user_id)},
    )
    assert participant_response.status_code == 201, participant_response.text
    participant = participant_response.json()
    consent = client.post(
        "/api/research/consent",
        headers=headers,
        json={
            "participant_id": participant["id"],
            "consent_version": "v1-test",
            "accepted": True,
        },
    )
    assert consent.status_code == 201, consent.text
    return participant


def _start(client, headers, participant_id):
    return client.post(
        "/api/research/sessions/start",
        headers=headers,
        json={
            "participant_id": participant_id,
            "scenario": "register_shipment",
            "expected_duration_minutes": 10,
            "client_timezone": "America/Lima",
            "client_timezone_offset_minutes": -300,
            "client_language": "es-PE",
            "screen_width": 1920,
            "screen_height": 1080,
            "screen_pixel_ratio": 1.25,
            "browser": "Chrome",
            "operating_system": "Windows",
            "device_type": "desktop",
            "collector_version": "web-test-v1",
        },
    )


def _jpeg() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (64, 64), color=(40, 80, 120)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _events():
    now = utc_now().isoformat()
    return [
        {
            "type": "keyboard",
            "event": "timing",
            "category": "alphanumeric",
            "dwell_time_ms": 85,
            "flight_time_ms": 120,
            "timestamp": now,
            "sequence_index": 1,
        },
        {
            "type": "mouse",
            "event": "move",
            "normalized_x": 0.42,
            "normalized_y": 0.61,
            "velocity": 10,
            "timestamp": now,
            "sequence_index": 2,
        },
    ]


def test_any_authenticated_user_can_self_enroll_idempotently(
    client, database
) -> None:
    user, headers = authenticate(client, database, "dispatcher")

    missing = client.get("/api/research/participants/me")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "PARTICIPANT_NOT_FOUND"

    enrolled = client.post(
        "/api/research/participants/self-enroll",
        headers=headers,
    )
    assert enrolled.status_code == 201, enrolled.text
    body = enrolled.json()
    assert body["created"] is True
    assert body["participant"]["linked_user_id"] == str(user.id)
    assert body["participant"]["participant_code"].startswith("P-")

    replay = client.post(
        "/api/research/participants/self-enroll",
        headers=headers,
    )
    assert replay.status_code == 200, replay.text
    assert replay.json()["created"] is False
    assert replay.json()["participant"]["id"] == body["participant"]["id"]

    current = client.get("/api/research/participants/me")
    assert current.status_code == 200
    assert current.json()["id"] == body["participant"]["id"]
    participant_count = database.scalar(
        select(func.count())
        .select_from(ResearchParticipant)
        .where(ResearchParticipant.linked_user_id == user.id)
    )
    assert participant_count == 1

    consent = client.post(
        "/api/research/consent",
        headers=headers,
        json={
            "participant_id": body["participant"]["id"],
            "consent_version": "v1-self-enrollment-test",
            "accepted": True,
        },
    )
    assert consent.status_code == 201, consent.text
    started = _start(client, headers, body["participant"]["id"])
    assert started.status_code == 201, started.text


def test_session_requires_consent_and_prevents_parallel_session(client, database) -> None:
    user, headers = authenticate(client, database)
    participant = client.post(
        "/api/research/participants",
        headers=headers,
        json={"linked_user_id": str(user.id)},
    ).json()
    denied = _start(client, headers, participant["id"])
    assert denied.status_code == 409
    assert denied.json()["error"]["code"] == "CONSENT_REQUIRED"
    client.post(
        "/api/research/consent",
        headers=headers,
        json={
            "participant_id": participant["id"],
            "consent_version": "v1",
            "accepted": True,
        },
    )
    started = _start(client, headers, participant["id"])
    assert started.status_code == 201
    assert started.json()["session"]["status"] == "active"
    session_id = started.json()["session"]["id"]
    annotated = client.patch(
        f"/api/research/sessions/{session_id}/annotation",
        headers=headers,
        json={
            "identity_label": "genuine",
            "sample_role": "enrollment",
            "presentation_label": "bona_fide",
            "attack_type": "none",
            "source_device": "integrated_webcam",
            "pad_source_id": "controlled-source-1",
            "annotation_notes": "Etiqueta ficticia de prueba",
            "confirmed": True,
        },
    )
    assert annotated.status_code == 200, annotated.text
    assert annotated.json()["annotation_status"] == "confirmed"
    assert annotated.json()["sample_role"] == "enrollment"
    assert _start(client, headers, participant["id"]).status_code == 409


def test_capture_behavior_privacy_idempotency_and_finish(
    client, database, tmp_path, monkeypatch
) -> None:
    user, headers = authenticate(client, database)
    participant = _participant_and_consent(client, headers, user.id)
    started = _start(client, headers, participant["id"])
    session_id = started.json()["session"]["id"]
    from app.services import capture_storage_service

    monkeypatch.setattr(
        capture_storage_service.settings, "CAPTURE_LOCAL_PATH", str(tmp_path)
    )
    captured_at = utc_now().isoformat()
    capture = client.post(
        f"/api/research/sessions/{session_id}/face-captures",
        headers=headers,
        data={
            "captured_at": captured_at,
            "sequence_number": "1",
            "width": "64",
            "height": "64",
            "visibility_state": "visible",
            "client_timezone_offset": "-300",
            "capture_source": "webcam",
            "camera_facing_mode": "user",
        },
        files={"image": ("ignored.jpg", _jpeg(), "image/jpeg")},
    )
    assert capture.status_code == 201, capture.text
    assert "storage_path" not in capture.text
    replay_capture = client.post(
        f"/api/research/sessions/{session_id}/face-captures",
        headers=headers,
        data={
            "captured_at": captured_at,
            "sequence_number": "1",
            "width": "64",
            "height": "64",
        },
        files={"image": ("different-name.jpg", _jpeg(), "image/jpeg")},
    )
    assert replay_capture.status_code == 200
    assert replay_capture.json()["idempotent_replay"] is True

    batch_id = str(uuid4())
    started_at = utc_now()
    behavior_body = {
        "batch_id": batch_id,
        "sequence_number": 1,
        "started_at": started_at.isoformat(),
        "ended_at": (started_at + timedelta(seconds=3)).isoformat(),
        "visibility_state": "visible",
        "client_timezone_offset_minutes": -300,
        "dropped_event_count": 2,
        "collector_error_count": 1,
        "events": _events(),
    }
    accepted = client.post(
        f"/api/research/sessions/{session_id}/behavior-batches",
        headers=headers,
        json=behavior_body,
    )
    assert accepted.status_code == 201, accepted.text
    assert accepted.json()["keyboard_event_count"] == 1
    assert accepted.json()["mouse_event_count"] == 1
    replay = client.post(
        f"/api/research/sessions/{session_id}/behavior-batches",
        headers=headers,
        json=behavior_body,
    )
    assert replay.status_code == 200
    assert replay.json()["idempotent_replay"] is True
    stored_capture = database.scalar(
        select(FacialCapture).where(
            FacialCapture.experimental_session_id == session_id
        )
    )
    assert stored_capture is not None
    assert stored_capture.client_timezone_offset_minutes == -300
    assert stored_capture.capture_source == "webcam"
    assert stored_capture.camera_facing_mode == "user"
    stored_batch = database.scalar(
        select(BehavioralBatch).where(
            BehavioralBatch.experimental_session_id == session_id
        )
    )
    assert stored_batch is not None
    assert stored_batch.visibility_state == "visible"
    assert stored_batch.client_timezone_offset_minutes == -300
    assert stored_batch.dropped_event_count == 2
    assert stored_batch.collector_error_count == 1

    forbidden = dict(behavior_body)
    forbidden["batch_id"] = str(uuid4())
    forbidden["sequence_number"] = 2
    forbidden["events"] = [
        {
            "type": "keyboard",
            "event": "timing",
            "category": "alphanumeric",
            "timestamp": utc_now().isoformat(),
            "sequence_index": 1,
            "metadata": {"password": "nunca"},
        }
    ]
    rejected = client.post(
        f"/api/research/sessions/{session_id}/behavior-batches",
        headers=headers,
        json=forbidden,
    )
    assert rejected.status_code == 422
    assert (
        rejected.json()["error"]["code"]
        == "BEHAVIOR_PAYLOAD_CONTAINS_FORBIDDEN_DATA"
    )

    session = database.get(ExperimentalSession, session_id)
    session.started_at = utc_now() - timedelta(seconds=20)
    database.flush()
    finished = client.post(
        f"/api/research/sessions/{session_id}/finish",
        headers=headers,
        json={"client_ended_at": utc_now().isoformat(), "client_error_count": 0},
    )
    assert finished.status_code == 200, finished.text
    assert finished.json()["session"]["status"] == "completed"
    assert finished.json()["session"]["facial_capture_count"] == 1
    assert finished.json()["session"]["batch_count"] == 1
    after_finish = client.post(
        f"/api/research/sessions/{session_id}/behavior-batches",
        headers=headers,
        json={**behavior_body, "batch_id": str(uuid4()), "sequence_number": 3},
    )
    assert after_finish.status_code == 409
    audit_types = set(
        database.scalars(
            select(AuditLog.event_type).where(AuditLog.user_id == user.id)
        )
    )
    assert {
        "CONSENT_ACCEPTED",
        "EXPERIMENTAL_SESSION_STARTED",
        "FACIAL_CAPTURE_RECEIVED",
        "BEHAVIOR_BATCH_RECEIVED",
        "EXPERIMENTAL_SESSION_COMPLETED",
    } <= audit_types


def test_fake_image_coordinates_cancel_separation_and_stale(
    client, database
) -> None:
    user, headers = authenticate(client, database)
    participant = _participant_and_consent(client, headers, user.id)
    started = _start(client, headers, participant["id"])
    session_id = started.json()["session"]["id"]
    fake = client.post(
        f"/api/research/sessions/{session_id}/face-captures",
        headers=headers,
        data={
            "captured_at": utc_now().isoformat(),
            "sequence_number": "1",
            "width": "64",
            "height": "64",
        },
        files={"image": ("fake.jpg", b"not-an-image", "image/jpeg")},
    )
    assert fake.status_code == 422
    bad_coordinates = client.post(
        f"/api/research/sessions/{session_id}/behavior-batches",
        headers=headers,
        json={
            "batch_id": str(uuid4()),
            "sequence_number": 1,
            "started_at": utc_now().isoformat(),
            "ended_at": utc_now().isoformat(),
            "events": [
                {
                    "type": "mouse",
                    "event": "move",
                    "normalized_x": 2,
                    "normalized_y": 0.5,
                    "timestamp": utc_now().isoformat(),
                    "sequence_index": 1,
                }
            ],
        },
    )
    assert bad_coordinates.status_code == 422
    cancelled = client.post(
        f"/api/research/sessions/{session_id}/cancel",
        headers=headers,
        json={"reason": "camera_permission_lost"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["session"]["status"] == "cancelled"

    other_user, _ = authenticate(client, database, "dispatcher")
    own_session = database.get(ExperimentalSession, session_id)
    assert own_session.user_id != other_user.id
    forbidden = client.get(f"/api/research/sessions/{session_id}")
    assert forbidden.status_code == 403

    own_session.status = "active"
    own_session.last_activity_at = utc_now() - timedelta(minutes=30)
    own_session.ended_at = None
    database.flush()
    count = ResearchService().invalidate_stale_sessions(database)
    assert count == 1
    database.refresh(own_session)
    assert own_session.status == "invalid"
