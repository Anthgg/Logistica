from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.main import app
from app.schemas.research import (
    BehavioralBatchCreate,
    ExperimentalSessionAnnotationUpdate,
    ExperimentalSessionStart,
)


def test_openapi_exposes_research_profile_and_annotation_routes() -> None:
    schema = app.openapi()
    assert "/api/research/participants/me" in schema["paths"]
    assert "get" in schema["paths"]["/api/research/participants/me"]
    assert "/api/research/participants/self-enroll" in schema["paths"]
    assert "post" in schema["paths"]["/api/research/participants/self-enroll"]
    assert "/api/research/sessions/{session_id}/annotation" in schema["paths"]
    assert (
        "patch"
        in schema["paths"]["/api/research/sessions/{session_id}/annotation"]
    )


def test_pad_annotation_requires_consistent_attack_metadata() -> None:
    valid = ExperimentalSessionAnnotationUpdate(
        identity_label="genuine",
        sample_role="verification",
        presentation_label="attack",
        attack_type="printed_photo",
        source_device="tablet-controlado",
        confirmed=True,
    )
    assert valid.attack_type == "printed_photo"
    with pytest.raises(ValidationError):
        ExperimentalSessionAnnotationUpdate(
            identity_label="genuine",
            sample_role="verification",
            presentation_label="bona_fide",
            attack_type="printed_photo",
        )
    with pytest.raises(ValidationError):
        ExperimentalSessionAnnotationUpdate(
            identity_label="impostor",
            sample_role="change_operator",
        )


def test_collector_metadata_ranges_are_validated() -> None:
    start = ExperimentalSessionStart(
        participant_id="00000000-0000-0000-0000-000000000001",
        scenario="mixed_operations",
        expected_duration_minutes=10,
        client_timezone="America/Lima",
        client_timezone_offset_minutes=-300,
        client_language="es-PE",
        screen_width=1920,
        screen_height=1080,
        screen_pixel_ratio=1.25,
        collector_version="web-v0.2.0",
    )
    assert start.client_timezone_offset_minutes == -300
    with pytest.raises(ValidationError):
        BehavioralBatchCreate(
            batch_id="00000000-0000-0000-0000-000000000002",
            sequence_number=1,
            started_at=datetime.now(timezone.utc),
            ended_at=datetime.now(timezone.utc),
            events=[{}],
            client_timezone_offset_minutes=900,
        )
